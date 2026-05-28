import cv2
import numpy as np
from ultralytics import YOLO
from collections import defaultdict
import math
import time
import os
import sys
import torch

class SmartTrafficSystem:
    def __init__(self, video_path, model_path='yolo11n.pt'):
        """ 初始化智慧道路监测系统 """
        # === 1. 安全检查：验证视频文件是否存在 ===
        if not os.path.exists(video_path):
            print(f"\n[严重错误] 找不到视频文件: {video_path}")
            print(f"请检查文件路径是否正确。")
            sys.exit(1)
        
        # === 2. 设备选择与模型加载 ===
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"[系统启动] 正在使用计算设备: {device.upper()}")
        print(f"[系统启动] 正在加载 YOLO 模型 (初次运行可能较慢)...")
        try:
            self.model = YOLO(model_path)
            print("[系统启动] 正在预热模型...")
            self.model.predict(np.zeros((640, 640, 3), dtype='uint8'), verbose=False, device=device)
        except Exception as e:
            print(f"\n[严重错误] 模型加载失败: {e}")
            sys.exit(1)
        
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            print(f"\n[严重错误] 无法打开视频流。")
            sys.exit(1)
        
        # === 核心参数配置 ===
        self.line_height_ratio = 0.5
        self.speed_limit = 80.0
        
        # [优化] 透视映射参数 (解决近处速度超标问题)
        # 远处(画面顶部) 1像素代表多少米 (通常较大，如0.2米)
        self.ppm_top = 0.20
        # 近处(画面底部) 1像素代表多少米 (通常较小，如0.02米)
        self.ppm_bottom = 0.02
        
        # 碰撞检测比例
        self.collision_ratio = 0.4
        
        # 车道方向配置 (False = 画面右侧车向上远离相机)
        self.right_lane_moves_down = False
        
        # === 状态存储 ===
        self.prev_status = {}
        self.counted_ids = set()
        
        # === 实时数据 ===
        self.total_traffic = 0
        self.current_speeds = {}
        self.anomalies = {}
        
        # [新增] 碰撞计时器：记录两车开始靠近的时间
        # key: tuple(sorted((id1, id2))), value: start_timestamp
        self.collision_timers = {}
        
        # [新增] 超速计时器：记录车辆开始超速的时间
        # key: track_id, value: start_timestamp
        self.overspeed_timers = {}
    
    def calculate_speed(self, car_id, curr_center, curr_time, frame_height):
        """ [优化版] 带透视补偿的车速计算 """
        if car_id in self.prev_status:
            prev_center, prev_time = self.prev_status[car_id]
            dt = curr_time - prev_time
            if dt <= 0:
                return 0.0
            
            # 计算像素距离
            pixel_dist = math.sqrt((curr_center[0] - prev_center[0]) ** 2 + (curr_center[1] - prev_center[1]) ** 2)
            
            # [核心优化] 动态计算当前位置的 ppm (pixel_per_meter)
            # 车辆越靠下 (y越大)，ratio越接近1，ppm越接近 ppm_bottom
            # 车辆越靠上 (y越小)，ratio越接近0，ppm越接近 ppm_top
            y_ratio = curr_center[1] / frame_height
            current_ppm = self.ppm_top - y_ratio * (self.ppm_top - self.ppm_bottom)
            
            # 限制 ppm 范围防止异常
            current_ppm = max(self.ppm_bottom, min(self.ppm_top, current_ppm))
            
            # 换算为实际距离 (米)
            real_dist = pixel_dist * current_ppm
            
            # 计算速度 (m/s -> km/h)
            speed_kmh = (real_dist / dt) * 3.6
            
            old_speed = self.current_speeds.get(car_id, speed_kmh)
            # 增加平滑系数，让数值跳动更稳定
            avg_speed = 0.9 * speed_kmh + 0.1 * old_speed
            return avg_speed
        return 0.0
    
    def check_traffic_count(self, car_id, curr_y, prev_y, line_y):
        if car_id in self.counted_ids:
            return
        if (prev_y < line_y <= curr_y) or (prev_y > line_y >= curr_y):
            self.total_traffic += 1
            self.counted_ids.add(car_id)
    
    def detect_wrong_way(self, car_id, prev_y, curr_y, img_width, curr_x):
        if curr_x > img_width / 2:
            dy = curr_y - prev_y
            is_wrong_way = False
            if self.right_lane_moves_down:
                if dy < -2:
                    is_wrong_way = True
            else:
                if dy > 2:
                    is_wrong_way = True
            if is_wrong_way:
                if car_id not in self.anomalies:
                    self.anomalies[car_id] = []
                if "WRONG WAY" not in self.anomalies[car_id]:
                    self.anomalies[car_id].append("WRONG WAY")
    
    def detect_collisions(self, current_boxes):
        """ [优化版] 碰撞检测：需持续 5 秒才报警 """
        count = len(current_boxes)
        curr_time = time.time()
        current_close_pairs = set()  # 记录当前帧处于近距离的对
        for i in range(count):
            id_a, xa, ya, wa, ha = current_boxes[i]
            for j in range(i + 1, count):
                id_b, xb, yb, wb, hb = current_boxes[j]
                dist = math.sqrt((xa - xb) ** 2 + (ya - yb) ** 2)
                avg_width = (wa + wb) / 2
                dynamic_threshold = avg_width * self.collision_ratio
                if dist < dynamic_threshold:
                    # 使用排序后的 tuple 作为 key，确保 (id_a, id_b) 和 (id_b, id_a) 是同一个 key
                    pair_key = tuple(sorted((id_a, id_b)))
                    current_close_pairs.add(pair_key)
                    if pair_key not in self.collision_timers:
                        # 第一次检测到靠近，开始计时
                        self.collision_timers[pair_key] = curr_time
                    else:
                        # 已经处于靠近状态，计算持续时间
                        elapsed_time = curr_time - self.collision_timers[pair_key]
                        if elapsed_time > 5.0:  # 只有持续超过 5 秒才触发报警
                            for cid in [id_a, id_b]:
                                if cid not in self.anomalies:
                                    self.anomalies[cid] = []
                                if "COLLISION" not in self.anomalies[cid]:
                                    self.anomalies[cid].append("COLLISION")
        
        # 清理失效的计时器
        # 如果某对车辆不再处于近距离（分开或者消失），则删除其计时记录
        for pair_key in list(self.collision_timers.keys()):
            if pair_key not in current_close_pairs:
                del self.collision_timers[pair_key]
    
    def run(self):
        frame_idx = 0
        print("[Info] 开始处理视频流 (按 'Esc' 退出)...")
        while True:
            success, frame = self.cap.read()
            if not success:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            frame_idx += 1
            
            # 调整尺寸加速
            h, w = frame.shape[:2]
            target_width = 1024
            scale = target_width / w
            target_height = int(h * scale)
            frame = cv2.resize(frame, (target_width, target_height))
            height, width = frame.shape[:2]
            line_y = int(height * self.line_height_ratio)
            
            curr_time = time.time()
            self.anomalies.clear()
            
            if frame_idx % 10 == 0:
                print(f"正在处理第 {frame_idx} 帧...", end="\r")
            
            # 推理
            results = self.model.track(frame, persist=True, tracker="bytetrack.yaml", classes=[2, 5, 7], verbose=False)
            
            if results[0].boxes.id is not None:
                boxes = results[0].boxes.xywh.cpu()
                track_ids = results[0].boxes.id.int().cpu().tolist()
                
                current_frame_data = []  # [新增] 记录本帧活跃的ID，用于清理超速计时器
                active_ids = set()
                
                for box, track_id in zip(boxes, track_ids):
                    active_ids.add(track_id)
                    x, y, w_box, h_box = box
                    center = (float(x), float(y))
                    current_frame_data.append([track_id, center[0], center[1], float(w_box), float(h_box)])
                    
                    speed = 0.0
                    if track_id in self.prev_status:
                        prev_x, prev_y = self.prev_status[track_id][0]
                        # [传递 height 参数进行透视计算]
                        speed = self.calculate_speed(track_id, center, curr_time, height)
                        self.current_speeds[track_id] = speed
                        
                        self.check_traffic_count(track_id, center[1], prev_y, line_y)
                        self.detect_wrong_way(track_id, prev_y, center[1], width, center[0])
                    
                    # === 4.3 超速检测优化：持续1.5秒才报警 ===
                    if speed > self.speed_limit:
                        if track_id not in self.overspeed_timers:
                            # 第一次超速，开始计时
                            self.overspeed_timers[track_id] = curr_time
                        elif curr_time - self.overspeed_timers[track_id] > 1.5:
                            # 持续超速超过1.5秒，触发报警
                            if track_id not in self.anomalies:
                                self.anomalies[track_id] = []
                            self.anomalies[track_id].append("OVERSPEED")
                    else:
                        # 速度恢复正常，清除计时器
                        if track_id in self.overspeed_timers:
                            del self.overspeed_timers[track_id]
                    
                    self.prev_status[track_id] = (center, curr_time)
                
                # 清理已经消失的车辆的超速计时器
                for tid in list(self.overspeed_timers.keys()):
                    if tid not in active_ids:
                        del self.overspeed_timers[tid]
                
                self.detect_collisions(current_frame_data)
            
            # === 绘制 (删除了黄线绘制代码) ===
            # cv2.line(frame, (0, line_y), (width, line_y), (0, 255, 255), 2) <-- 已注释
            
            for box, track_id in zip(boxes, track_ids):
                x, y, w_box, h_box = box
                x1, y1 = int(x - w_box / 2), int(y - h_box / 2)
                x2, y2 = int(x + w_box / 2), int(y + h_box / 2)
                
                color = (0, 255, 0)
                warnings = self.anomalies.get(track_id, [])
                if warnings:
                    color = (0, 0, 255)
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"ID:{track_id} {int(self.current_speeds.get(track_id, 0))}km/h"
                cv2.putText(frame, label, (x1, y1 - 5), 0, 0.6, (0, 255, 0), 2)
                
                if warnings:
                    cv2.putText(frame, " ".join(warnings), (x1, y1 - 25), 0, 0.7, (0, 0, 255), 2)
            
            # 面板
            cv2.rectangle(frame, (0, 0), (250, 120), (0, 0, 0), -1)
            cv2.putText(frame, "SMART TRAFFIC", (10, 30), 0, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Total: {self.total_traffic}", (10, 70), 0, 0.8, (0, 255, 0), 2)
            
            cv2.imshow("Monitor", frame)
            
            if cv2.waitKey(1) & 0xFF == 27:
                print("\n[Info] 用户手动停止程序")
                break
        
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    VIDEO_FILE = "traffic.mp4"
    app = SmartTrafficSystem(VIDEO_FILE)
    app.run()