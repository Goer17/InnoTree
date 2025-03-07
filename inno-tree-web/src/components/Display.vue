<script setup lang="ts">
import { watch, ref, onMounted, onUnmounted, provide, nextTick, type PropType } from 'vue';
import Node from './Node.vue';

type NodeType = {
  p_id: string;
  n_id: string;
  n_key: string;
  content: string;
  observation?: string;
  value?: number;
  visits?: number;
};

interface NodePosition {
  getCDotPosition: () => DOMRect;
  getFDotPosition: () => DOMRect;
}

const props = defineProps({
  tree: {
    type: Array as PropType<NodeType[]>,
    required: true
  }
});

const nodesMap = ref(new Map<string, NodePosition>());
const svgCanvas = ref<SVGSVGElement | null>(null);
const arrows = ref<SVGLineElement[]>([]);


provide('nodeContext', {
  registerNode: (key: string, position: NodePosition) => {
    nodesMap.value.set(key, position);
  },
  unregisterNode: (key: string) => {
    nodesMap.value.delete(key);
  }
});

const flatten_tree = (tree: NodeType[]) => {
    const treeDict: Record<string, NodeType> = {};
    const treeTopo: Record<string, string[]> = {};
    let root_id = "";

    for (const node of tree) {
        treeDict[node.n_id] = node;
        if (!node.p_id) root_id = node.n_id;
        if (!treeTopo[node.p_id]) treeTopo[node.p_id] = [];
        treeTopo[node.p_id].push(node.n_id);
    }

    const nodes: NodeType[][] = [];
    if (!root_id) return nodes;

    let queue: NodeType[] = [treeDict[root_id]];
    
    while (queue.length > 0) {
        nodes.push(queue);
        queue = queue.flatMap(node => treeTopo[node.n_id]?.map(id => treeDict[id]) || []);
    }

    return nodes;
}

const nodes = ref<NodeType[][]>(flatten_tree(props.tree));

// 箭头绘制逻辑
const createArrowMarker = () => {
  if (!svgCanvas.value) return;
  
  const svgNS = "http://www.w3.org/2000/svg";
  let defs = svgCanvas.value.querySelector("defs");
  if (!defs) {
    defs = document.createElementNS(svgNS, "defs");
    svgCanvas.value.appendChild(defs);
  }

  if (!document.getElementById("arrowMarker")) {
    const marker = document.createElementNS(svgNS, "marker");
    marker.setAttribute("id", "arrowMarker");
    // 缩小箭头尺寸
    marker.setAttribute("markerWidth", "8");
    marker.setAttribute("markerHeight", "5");
    marker.setAttribute("refX", "7.5");  // 调整箭头位置
    marker.setAttribute("refY", "2.5");
    marker.setAttribute("orient", "auto");

    // 更精致的三角形路径
    const path = document.createElementNS(svgNS, "path");
    path.setAttribute("d", "M0,0 L7.5,2.5 L0,5"); // 更紧凑的箭头形状
    path.setAttribute("fill", "#4a5568"); // 使用深灰色
    marker.appendChild(path);
    defs.appendChild(marker);
  }
};

const drawConnection = (parentId: string, childId: string) => {
  if (!svgCanvas.value) return;

  const parent = nodesMap.value.get(parentId);
  const child = nodesMap.value.get(childId);
  if (!parent || !child) return;

  const svgNS = "http://www.w3.org/2000/svg";
  const line = document.createElementNS(svgNS, "line");
  
  const updatePosition = () => {
    const start = parent.getFDotPosition();
    const end = child.getCDotPosition();
    
    line.setAttribute('x1', (start.left + start.width/2 + window.scrollX).toString());
    line.setAttribute('y1', (start.top + start.height/2 + window.scrollY).toString());
    line.setAttribute('x2', (end.left + end.width/2 + window.scrollX).toString());
    line.setAttribute('y2', (end.top + end.height/2 + window.scrollY).toString());
  };

  line.setAttribute('stroke', '#4a5568'); // 深灰色
  line.setAttribute('stroke-width', '1.5');
  line.setAttribute('stroke-linecap', 'round'); // 圆角端点
  line.setAttribute('marker-end', 'url(#arrowMarker)');
  line.dataset.parent = parentId;
  line.dataset.child = childId;
  
  svgCanvas.value.appendChild(line);
  arrows.value.push(line);
  updatePosition();
};

const updateAllArrows = () => {
  arrows.value.forEach(line => {
    const parentId = line.dataset.parent!;
    const childId = line.dataset.child!;
    const parent = nodesMap.value.get(parentId);
    const child = nodesMap.value.get(childId);

    if (parent && child) {
      const start = parent.getFDotPosition();
      const end = child.getCDotPosition();
      
      line.setAttribute('x1', (start.left + start.width/2 + window.scrollX).toString());
      line.setAttribute('y1', (start.top + start.height/2 + window.scrollY).toString());
      line.setAttribute('x2', (end.left + end.width/2 + window.scrollX).toString());
      line.setAttribute('y2', (end.top + end.height/2 + window.scrollY).toString());
    }
  });
};

// 事件监听
const observer = new ResizeObserver(updateAllArrows);
onMounted(() => {
  createArrowMarker();
  window.addEventListener('scroll', updateAllArrows, true);
  observer.observe(document.documentElement);
});

onUnmounted(() => {
  window.removeEventListener('scroll', updateAllArrows, true);
  observer.disconnect();
});

watch(() => props.tree, (newTree) => {
  nodes.value = flatten_tree(newTree);
  
  nextTick(() => {
    arrows.value.forEach(line => line.remove());
    arrows.value = [];
    
    newTree.forEach(node => {
      if (node.p_id) {
        drawConnection(node.p_id, node.n_id);
      }
    });
  });
}, { deep: true, immediate: true });

</script>

<template>
    <div id="tree-box">
        <div class="layer" v-for="layer in nodes">
            <Node v-for="node in layer" :key="node.n_id" v-bind="node" />
        </div>
        <svg ref="svgCanvas" class="svg-fixed" width="100%" height="100%"></svg>
    </div>
</template>

<style scoped>

.svg-fixed {
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  pointer-events: none;
  z-index: 10;
  overflow: visible; /* 允许内容溢出 */
}

.layer {
    display: flex;
}
</style>
