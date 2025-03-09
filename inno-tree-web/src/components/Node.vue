<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, inject } from 'vue';

const props = defineProps({
    p_id: { type: String, required: true },
    n_id: { type: String, required: true },
    n_key: { type: String, required: true },
    content: { type: String, required: true },
    observation: { type: String, required: false },
    value: { type: Number, required: false },
    visits: { type: Number, required: false }
});

interface NodePosition {
    getCDotPosition: () => DOMRect;
    getFDotPosition: () => DOMRect;
}

interface NodeContext {
    registerNode: (key: string, position: NodePosition) => void;
    unregisterNode: (key: string) => void;
}

const parent = inject<NodeContext>('nodeContext');
const cdot = ref<HTMLElement | null>(null);
const fdot = ref<HTMLElement | null>(null);

const getCDotPosition = () => cdot.value!.getBoundingClientRect();
const getFDotPosition = () => fdot.value!.getBoundingClientRect();

onMounted(() => {
    parent?.registerNode(props.n_id, { getCDotPosition, getFDotPosition });
});

onBeforeUnmount(() => {
    parent?.unregisterNode(props.n_id);
});

function truncate(text: string, length: number = 50) {
    return text.length > length ? text.slice(0, length) + "..." : text;
}

const showTooltip = ref(false)
const tooltipPosition = ref({ x: 0, y: 0 })

const handleMouseMove = (e: MouseEvent) => {
    tooltipPosition.value = {
        x: e.clientX + 15,
        y: e.clientY + 15
    }
}

</script>

<template>
    <div class="node" @mouseenter="showTooltip = true" @mousemove="handleMouseMove" @mouseleave="showTooltip = false">
        <div v-show="showTooltip" class="tooltip" :style="{
            left: `${tooltipPosition.x}px`,
            top: `${tooltipPosition.y}px`
        }">
            <div class="tooltip-header">
                {{ props.n_key }}
                <span class="text-sm text-gray-500">#{{ props.n_id }}</span>
            </div>
            <div class="tooltip-body">
                <div v-if="props.value !== undefined">
                    <span class="label">Value:</span>
                    {{ props.value?.toFixed(2) || 'N/A' }}
                </div>
                <div v-if="props.visits !== undefined">
                    <span class="label">Visits:</span>
                    {{ props.visits }}
                </div>
                <div class="content-full">
                    {{ props.content }}
                </div>
                <div v-if="props.observation" class="observation-full">
                    ⭐️ {{ props.observation }}
                </div>
            </div>
        </div>
        <div ref="cdot" class="cdot"></div>
        <div class="title">
            {{ props.n_key }}
            <span v-if="props.value && props.visits && props.visits > 0" class="value">
                [{{ (props.value / props.visits).toFixed(2) }}]
            </span>
            <span v-else class="value">
                [NaN]
            </span>
        </div>
        <div class="content"> {{ truncate(props.content) }}</div>
        <div v-if="props.observation" class="observation">
            ⭐️ <em>{{ truncate(props.observation) }}</em>
        </div>
        <div ref="fdot" class="fdot"></div>
    </div>
</template>

<style scoped>
.node {
    position: relative;
    width: 180px;
    padding: 12px;
    background-color: #e3f2fd;
    border: 2px solid #90caf9;
    border-radius: 8px;
    font-family: "Courier New", Courier, monospace;
    box-shadow: 2px 4px 10px rgba(0, 0, 0, 0.2);
    text-align: center;
    margin: 2%;
}

.title {
    font-weight: bold;
    font-size: 14px;
    color: #000000;
    margin-bottom: 6px;
}

.title .value {
    color: rgb(30, 147, 30);
}

.content {
    font-size: 12px;
    color: #000000;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.observation {
    font-size: 12px;
    color: #000000;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.cdot {
    visibility: hidden;
    position: absolute;
    width: 8px;
    height: 8px;
    background-color: #ffffff;
    border-radius: 50%;

    top: -5px;
    left: 50%;
    transform: translateX(-50%);
}

.fdot {
    visibility: hidden;
    position: absolute;
    width: 8px;
    height: 8px;
    background-color: #1565c0;
    border-radius: 50%;

    bottom: -5px;
    left: 50%;
    transform: translateX(-50%);
}

.tooltip {
  position: fixed;
  z-index: 9999;
  min-width: 260px;
  max-width: 800px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 12px;
  pointer-events: none;
  transition: opacity 0.2s;
  border: 1px solid #e5e7eb;
}

.tooltip-header {
  font-weight: 600;
  font-size: 15px;
  color: #1f2937;
  border-bottom: 1px solid #f3f4f6;
  padding-bottom: 8px;
  margin-bottom: 8px;
}

.tooltip-body {
  font-size: 13px;
  color: #4b5563;
}

.label {
  color: #6b7280;
  display: inline-block;
  width: 60px;
}

.content-full {
  margin-top: 8px;
  white-space: normal;
  line-height: 1.4;
}

.observation-full {
  margin-top: 8px;
  color: #9333ea;
  font-style: italic;
}

.text-sm {
  font-size: 0.875rem;
}
.text-gray-500 {
  color: #6b7280;
}
</style>