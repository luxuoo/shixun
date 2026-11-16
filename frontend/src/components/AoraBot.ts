/**
 * Aora Bot 卡通角色（Vue 包装，API 对齐 @aora-bot/react 的 CharacterMark）
 *
 * <AoraBot shape="circle" color="black" state="reading" face="eyes" :sizePx="96" followPointer />
 *
 * 参数速查（文档 https://aora-bot.vercel.app/guide/getting-started）：
 * - shape: circle / mochi / blob / pebble / egg / bun / tofu / pill / hex / star / heart /
 *          cloud / drop / leaf / cat / bunny / bear / chick / penguin / fox / bot / ghost …
 * - color: black（默认，跟随文字墨色）/ pink / green / cyan / violet / blue / orange / yellow
 * - state: idle / reading / thinking / writing / working / happy / excited / celebrate /
 *          curious / shy / sad / sleeping / listening / loading / alerting …（41 种）
 * - face:  cute（默认）/ eyes（豆豆眼）/ line / capsule / brow / glossy / sparkle / button /
 *          shades / droopy / bigmouth / pie / screen / teardrop / specs / symbol
 *
 * 交互：followPointer（眼睛跟随指针）、followTarget（跟随指定点）、emphasis（悬停聚焦）
 * 动作：ref 暴露 spin(n) / bounce(s) / burst(n) / pause() / resume()
 *
 * 角色画在 shadow DOM 内，外部样式不可达；调色用 CSS 变量：
 *   --aora-fg      线条墨色（默认取宿主文字颜色，暗色主题自动适配）
 *   --aora-bg-base 空心/玻璃变体的底色
 */
import {
  defineComponent, h, ref, watch, onMounted, onBeforeUnmount, type PropType
} from 'vue'

export interface GazeTarget { x: number; y: number }

export const AoraBot = defineComponent({
  name: 'AoraBot',
  props: {
    shape: { type: String, default: 'mochi' },
    color: { type: String, default: 'black' },
    state: { type: String, default: 'idle' },
    face: { type: String, default: 'cute' },
    /** 渲染尺寸（像素），对齐 React 版 sizePx */
    sizePx: { type: Number, default: 32 },
    /** 任意 CSS 长度，优先于 sizePx */
    sizeCss: { type: String, default: '' },
    /** 种子：同 seed 外观与眨眼节奏一致，适合做用户头像 */
    seed: { type: String, default: '' },
    /** 画风：vector / pixel / kaomoji */
    styleId: { type: String, default: 'vector' },
    /** 变体：outline / glass / bubble / sticker / paper / dot … */
    variant: { type: String, default: '' },
    lineWeight: { type: Number, default: 0 },
    eyeColor: { type: String, default: '' },
    eyeScale: { type: Number, default: 0 },
    badgeColor: { type: String, default: '' },
    /** 悬停强调：放大眼睛并聚焦 */
    emphasis: { type: Boolean, default: false },
    /** 冻结当前帧 */
    paused: { type: Boolean, default: false },
    /** 空闲时偶尔蹦跳/旋转 */
    antics: { type: Boolean, default: false },
    /** 页面隐藏/滚出视口/系统开启减弱动效时自动暂停 */
    autoPause: { type: Boolean, default: true },
    /** 眼睛自动跟随鼠标指针 */
    followPointer: { type: Boolean, default: false },
    /** 眼睛追踪的视口坐标点（优先于 followPointer） */
    followTarget: { type: Object as PropType<GazeTarget | null>, default: null },
    /** 状态入场特效 */
    entryEffects: { type: Boolean, default: true }
  },
  setup(props, { expose }) {
    const el = ref<any>(null)

    /* ---- 运行中属性就地更新（不重启动画） ---- */
    watch(() => props.state, (v) => { if (el.value) el.value.state = v })
    watch(() => props.color, (v) => { if (el.value) el.value.color = v })
    watch(() => props.face, (v) => { if (el.value) el.value.face = v })
    watch(() => props.emphasis, (v) => { if (el.value) el.value.emphasis = v })
    watch(() => props.paused, (v) => {
      if (!el.value) return
      v ? el.value.pause?.() : el.value.resume?.()
    })
    watch(() => props.followTarget, (v) => {
      el.value?.controller?.update({ followTarget: v ?? null })
    }, { deep: true })

    /* ---- 指针跟随：引擎属性表没有 follow-pointer，走 controller.update ---- */
    let tracking = false
    function onPointerMove(e: PointerEvent) {
      el.value?.controller?.update({ followTarget: { x: e.clientX, y: e.clientY } })
    }
    function onPointerLeave() {
      el.value?.controller?.update({ followTarget: null })
    }
    watch(() => props.followPointer, (on) => {
      if (on && !tracking) {
        window.addEventListener('pointermove', onPointerMove, { passive: true })
        document.addEventListener('pointerleave', onPointerLeave)
        tracking = true
      } else if (!on && tracking) {
        window.removeEventListener('pointermove', onPointerMove)
        document.removeEventListener('pointerleave', onPointerLeave)
        tracking = false
        el.value?.controller?.update({ followTarget: null })
      }
    }, { immediate: true })

    onMounted(() => {
      if (el.value?.paused) el.value.pause?.()
    })
    onBeforeUnmount(() => {
      if (tracking) {
        window.removeEventListener('pointermove', onPointerMove)
        document.removeEventListener('pointerleave', onPointerLeave)
        tracking = false
      }
      el.value = null
    })

    expose({
      bounce: (strength = 1) => el.value?.bounce?.(strength),
      spin: (turns = 1) => el.value?.spin?.(turns),
      burst: (count = 20) => el.value?.burst?.(count),
      pause: () => el.value?.pause?.(),
      resume: () => el.value?.resume?.(),
      element: () => el.value
    })

    return () => {
      const size = props.sizeCss || String(props.sizePx)
      return h('aora-bot', {
        ref: el,
        shape: props.shape,
        color: props.color,
        state: props.state,
        face: props.face,
        size,
        seed: props.seed || undefined,
        'style-id': props.styleId,
        variant: props.variant || undefined,
        'line-weight': props.lineWeight || undefined,
        'eye-color': props.eyeColor || undefined,
        'eye-scale': props.eyeScale || undefined,
        'badge-color': props.badgeColor || undefined,
        emphasis: props.emphasis ? '' : undefined,
        antics: props.antics ? '' : undefined,
        'auto-pause': props.autoPause ? '' : undefined
      })
    }
  }
})

export default AoraBot
