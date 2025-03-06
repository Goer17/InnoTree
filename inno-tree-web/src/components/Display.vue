<script setup lang="ts">
import { watch, reactive, ref, type PropType, nextTick } from 'vue';
import Node from './Node.vue';

type NodeType = {
    p_id: string,
    n_id: string,
    n_key: string,
    content: string,
    observation?: string,
    value?: number,
    visits?: number,
};

const props = defineProps({
    tree: {
        type: Array as PropType<NodeType[]>,
        required: true
    }
});

const positions = reactive<Record<string, [number, number, number, number]>>({});

const add_pos = (n_id: string, x1: number, x2: number, x3: number, x4: number) => {
    positions[n_id] = [x1, x2, x3, x4];
}

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

watch(() => props.tree, (newTree) => {
    console.log(newTree);
    nodes.value = flatten_tree(newTree);
}, { deep: true });

const svgCanvas = ref<SVGSVGElement | null>(null);

const drawArrow = (x1: number, y1: number, x2: number, y2: number): void => {
  const svgNS = "http://www.w3.org/2000/svg";

  if (!svgCanvas.value) return; // 确保 SVG 画布已存在

  let defs = svgCanvas.value.querySelector("defs");
  if (!defs) {
    defs = document.createElementNS(svgNS, "defs");
    svgCanvas.value.appendChild(defs);
  }

  let marker = document.getElementById("arrowMarker") as SVGMarkerElement | null;
  if (!marker) {
    marker = document.createElementNS(svgNS, "marker") as SVGMarkerElement;
    marker.setAttribute("id", "arrowMarker");
    marker.setAttribute("markerWidth", "10");
    marker.setAttribute("markerHeight", "7");
    marker.setAttribute("refX", "10");
    marker.setAttribute("refY", "3.5");
    marker.setAttribute("orient", "auto");

    const arrow = document.createElementNS(svgNS, "polygon") as SVGPolygonElement;
    arrow.setAttribute("points", "0 0, 10 3.5, 0 7");
    arrow.setAttribute("fill", "black");

    marker.appendChild(arrow);
    defs.appendChild(marker);
  }

  const line = document.createElementNS(svgNS, "line") as SVGLineElement;
  line.setAttribute("x1", x1.toString());
  line.setAttribute("y1", y1.toString());
  line.setAttribute("x2", x2.toString());
  line.setAttribute("y2", y2.toString());
  line.setAttribute("stroke", "black");
  line.setAttribute("stroke-width", "2");
  line.setAttribute("marker-end", "url(#arrowMarker)");

  svgCanvas.value.appendChild(line);
};

watch(positions, async () => {
    await nextTick(); // 确保 positions 全部更新
    drawAllArrows();
}, { deep: true });

const drawAllArrows = () => {
    if (!svgCanvas.value) return;
    svgCanvas.value.innerHTML = '';
    for (let node of props.tree) {
        if (node.p_id) {
            let [x2, y2, , ] = positions[node.n_id];
            let [, , x1, y1] = positions[node.p_id];
            drawArrow(x1, y1, x2, y2);
        }
    }
};

</script>

<template>
    <div id="tree-box">
        <div class="layer" v-for="layer in nodes">
            <Node v-for="node in layer" :key="node.n_id" v-bind="node" @addEvent="add_pos" />
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
}

.layer {
    display: flex;
}
</style>
