<script setup lang="ts">
import Header from "./components/Header.vue";
import Display from "./components/Display.vue";
import { ref, provide, toValue } from 'vue';

provide("api_url", "http://127.0.0.1:5000");

const tree = ref<any[]>([]);

const demo_tree = ref<any[]>([
    {
        n_id: "0",
        p_id: "",
        n_key: "root",
        content: ""
    },
    {
        n_id: "1",
        p_id: "0",
        n_key: "reasoning",
        content: ""
    },
    {
        n_id: "2",
        p_id: "0",
        n_key: "reasoning",
        content: ""
    },
    {
        n_id: "3",
        p_id: "0",
        n_key: "reasoning",
        content: ""
    },
    {
        n_id: "4",
        p_id: "3",
        n_key: "search",
        content: ""
    }
]);

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
