<script setup lang="ts">
import { ref, onMounted } from 'vue';
const props = defineProps({
    p_id: { type: String, required: true },
    n_id: { type: String, required: true },
    n_key: { type: String, required: true },
    content: { type: String, required: true },
    observation: { type: String, required: false },
    value: { type: Number, required: false },
    visits: { type: Number, required: false }
});

function truncate(text: string, length: number = 50) {
    return text.length > length ? text.slice(0, length) + "..." : text;
}

const cdot = ref<HTMLElement | null>(null);
const fdot = ref<HTMLElement | null>(null);

const emit = defineEmits<{
    (event: 'addEvent', n_id: string, x1: number, y1: number, x2: number, y2: number): void;
}>();

const getCenter = (element: HTMLElement | null) => {
    if (!element) return { x: 0, y: 0 };
    const rect = element.getBoundingClientRect();
    return {
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2,
    };
};

onMounted(() => {
    const { x: x1, y: y1 } = getCenter(cdot.value);
    const { x: x2, y: y2 } = getCenter(fdot.value);

    emit('addEvent', props.n_id, x1, y1, x2, y2);
});
</script>

<template>
    <div class="node">
        <div ref="cdot" class="cdot"></div>
        <div class="title">
            {{ props.n_key }}
            <span v-if="props.value && props.visits && props.visits > 0" class="value">
                [{{ props.value / props.visits }}]
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
    position: absolute;
    width: 8px;
    height: 8px;
    background-color: #1565c0;
    border-radius: 50%;

    bottom: -10px;
    left: 50%;
    transform: translateX(-50%);
}
</style>
