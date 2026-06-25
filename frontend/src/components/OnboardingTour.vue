<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  steps: { type: Array, required: true },
})
const emit = defineEmits(['update:modelValue', 'finish', 'skip'])

const index = ref(0)
const rect = ref(null)
const PADDING = 8

const current = computed(() => props.steps[index.value] || null)
const isFirst = computed(() => index.value === 0)
const isLast = computed(() => index.value === props.steps.length - 1)

function findTarget() {
  const step = current.value
  if (!step || !step.target) return null
  return document.querySelector(step.target)
}

async function updateRect() {
  await nextTick()
  const el = findTarget()
  if (!el) {
    rect.value = null
    return
  }
  el.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' })
  const r = el.getBoundingClientRect()
  rect.value = {
    top: r.top - PADDING,
    left: r.left - PADDING,
    width: r.width + PADDING * 2,
    height: r.height + PADDING * 2,
  }
}

const holeStyle = computed(() => {
  if (!rect.value) return null
  return {
    top: `${rect.value.top}px`,
    left: `${rect.value.left}px`,
    width: `${rect.value.width}px`,
    height: `${rect.value.height}px`,
  }
})

const tipStyle = computed(() => {
  const tipW = 320
  if (!rect.value) {
    return {
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      width: `${tipW}px`,
    }
  }
  const margin = 14
  const vh = window.innerHeight
  const vw = window.innerWidth
  const below = rect.value.top + rect.value.height + margin
  const placeBelow = below + 160 < vh
  let left = rect.value.left + rect.value.width / 2 - tipW / 2
  left = Math.max(12, Math.min(left, vw - tipW - 12))
  const style = { left: `${left}px`, width: `${tipW}px` }
  if (placeBelow) {
    style.top = `${below}px`
  } else {
    style.top = `${rect.value.top - margin}px`
    style.transform = 'translateY(-100%)'
  }
  return style
})

function next() {
  if (isLast.value) {
    finish()
  } else {
    index.value += 1
  }
}
function prev() {
  if (!isFirst.value) index.value -= 1
}
function finish() {
  emit('finish')
  emit('update:modelValue', false)
}
function skip() {
  emit('skip')
  emit('update:modelValue', false)
}
function onKey(e) {
  if (!props.modelValue) return
  if (e.key === 'Escape') skip()
  else if (e.key === 'ArrowRight' || e.key === 'Enter') next()
  else if (e.key === 'ArrowLeft') prev()
}

watch(() => props.modelValue, (open) => {
  if (open) {
    index.value = 0
    updateRect()
  }
})
watch(index, updateRect)

onMounted(() => {
  window.addEventListener('resize', updateRect)
  window.addEventListener('scroll', updateRect, true)
  window.addEventListener('keydown', onKey)
  if (props.modelValue) updateRect()
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', updateRect)
  window.removeEventListener('scroll', updateRect, true)
  window.removeEventListener('keydown', onKey)
})
</script>

<template>
  <Teleport to="body">
    <div v-if="modelValue && current" class="tour">
      <div v-if="holeStyle" class="tour-hole" :style="holeStyle" />
      <div v-else class="tour-dim" />

      <div class="tour-tip card" :style="tipStyle">
        <div class="tour-step">第 {{ index + 1 }} / {{ steps.length }} 步</div>
        <h3 class="tour-title">{{ current.title }}</h3>
        <p class="tour-text">{{ current.text }}</p>
        <div class="tour-actions">
          <button type="button" class="tour-skip" @click="skip">跳过引导</button>
          <div class="tour-actions-right">
            <button
              v-if="!isFirst"
              type="button"
              class="btn btn-outline btn-sm"
              @click="prev"
            >
              上一步
            </button>
            <button type="button" class="btn btn-sm" @click="next">
              {{ isLast ? '开始使用' : '下一步' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.tour {
  position: fixed;
  inset: 0;
  z-index: 1000;
  pointer-events: none;
}
.tour-dim {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  pointer-events: none;
}
.tour-hole {
  position: absolute;
  border-radius: 10px;
  box-shadow: 0 0 0 9999px rgba(15, 23, 42, 0.6);
  outline: 2px solid var(--primary, #2563eb);
  outline-offset: 2px;
  transition: all 0.25s ease;
  pointer-events: none;
  animation: tour-pulse 1.6s ease-in-out infinite;
}
@keyframes tour-pulse {
  0%,
  100% {
    outline-color: rgba(37, 99, 235, 0.9);
  }
  50% {
    outline-color: rgba(37, 99, 235, 0.35);
  }
}
.tour-tip {
  position: absolute;
  z-index: 1001;
  padding: 1rem 1.1rem;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.25);
  pointer-events: auto;
}
.tour-step {
  font-size: 0.78rem;
  color: var(--muted, #64748b);
  margin-bottom: 0.25rem;
}
.tour-title {
  margin: 0 0 0.4rem;
  font-size: 1.05rem;
}
.tour-text {
  margin: 0 0 0.9rem;
  color: #475569;
  line-height: 1.55;
  font-size: 0.92rem;
}
.tour-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}
.tour-actions-right {
  display: flex;
  gap: 0.5rem;
}
.tour-skip {
  color: var(--muted, #64748b);
  font-size: 0.85rem;
  padding: 0.35rem 0.5rem;
  border-radius: 6px;
}
.tour-skip:hover {
  color: #334155;
  background: var(--surface-muted, #f8fafc);
}
.btn-sm {
  padding: 0.35rem 0.8rem;
  font-size: 0.85rem;
}
</style>
