/**
 * BotAvatar — 用用户名/ID 哈希出一个稳定的角色头像
 * 同一个人每次进来长得一样，不需要存任何数据（文档「给你的用户分配角色」）。
 *
 * <BotAvatar name="张三" :sizePx="32" />
 */
import { defineComponent, computed, h } from 'vue'
import AoraBot from './AoraBot'

/** 可选形状池：圆润、可爱、辨识度高（小尺寸下不糊） */
const SHAPES = [
  'circle', 'mochi', 'blob', 'pebble', 'egg', 'bun', 'tofu', 'pill',
  'hex', 'cloud', 'drop', 'star', 'heart', 'cat', 'bunny', 'bear',
  'chick', 'penguin', 'fox', 'hamster', 'koala', 'bot', 'ghost'
]
const COLORS = ['black', 'pink', 'green', 'cyan', 'violet', 'blue', 'orange', 'yellow']
const FACES = ['cute', 'eyes', 'capsule', 'button', 'brow', 'sparkle', 'glossy', 'shades']

function hash32(str: string): number {
  let h = 2166136261
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

export function botProfile(name: string) {
  const h = hash32(name || 'anonymous')
  return {
    shape: SHAPES[h % SHAPES.length],
    color: COLORS[(h >>> 5) % COLORS.length],
    face: FACES[(h >>> 11) % FACES.length]
  }
}

export const BotAvatar = defineComponent({
  name: 'BotAvatar',
  props: {
    /** 用户名 / 学号 / 任意稳定字符串 */
    name: { type: String, default: '' },
    sizePx: { type: Number, default: 32 },
    state: { type: String, default: 'idle' }
  },
  setup(props) {
    const profile = computed(() => botProfile(props.name))
    return () => h(AoraBot, {
      shape: profile.value.shape,
      color: profile.value.color,
      face: profile.value.face,
      state: props.state,
      sizePx: props.sizePx,
      seed: `avatar:${props.name}`
    })
  }
})

export default BotAvatar
