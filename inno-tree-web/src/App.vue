<script setup lang="ts">
import Header from "./components/Header.vue";
import Display from "./components/Display.vue";
import { ref, provide, toValue } from 'vue';

provide("api_url", "http://124.70.167.66:5000");

const tree = ref<any[]>([]);

const updateTree = (newTree: any[]) => {
    console.log(`new tree: ${newTree}`);
    tree.value = newTree;
    console.log(tree.value);
};
</script>

<template>
 <Header @update="updateTree" />
 <Display :tree="tree" />
</template>

<style scoped>
</style>
