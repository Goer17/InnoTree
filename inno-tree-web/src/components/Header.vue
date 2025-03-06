<script setup lang="ts">
import { ref, reactive, inject } from 'vue';

const topic = ref('Object Detection');
const showSettingModal = ref(false);
const api_url = inject("api_url");

const settingButton = ref<HTMLButtonElement | null>(null);
const startButton = ref<HTMLButtonElement | null>(null);

const emit = defineEmits(["update"]);

const setting = reactive({
    api_key: 'sk-AOlxKdZ9pbHPNDM721Bb9245183145BbA4E0F5583a9b2cAd',
    base_url: 'https://us.vveai.com/v1',
    model: 'gpt-4o-mini',
    sampling_method: 'best', // Choices: [best, epsilon, v-epsilon]
    exploration_weight: 1.0,
    n_trials: 10,
    n_rollouts: 10,
    n_expand: 4,
});

const toggleSettingModal = () => {
    showSettingModal.value = !showSettingModal.value;
};

const saveSettings = () => {
    toggleSettingModal();
};

const disableButtons = () => {
    if (settingButton.value) {
        settingButton.value.disabled = true;
    }
    if (startButton.value) {
        startButton.value.disabled = true;
    }
};

const enableButtons = () => {
    if (settingButton.value) {
        settingButton.value.disabled = false;
    }
    if (startButton.value) {
        startButton.value.disabled = false;
    }
};

const start = () => {
    disableButtons();
    fetch(api_url + "/start", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ ...setting, topic: topic.value })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Request failed with status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        const task_id = data.task_id;
        if (!task_id) {
            throw new Error(`Task ID doesn't exist!`);
        }
        const event_src = new EventSource(api_url + `/stream?task_id=${task_id}`);
        event_src.onmessage = (event) => {
            const tree: Array<any> = JSON.parse(event.data);
            console.log("updated!");
            if (tree.length == 0) {
                event_src.close();
                enableButtons();
            }
            emit("update", tree);
        }
        event_src.onerror = (error) => {
            throw new Error(`Event source error: ${error}`)
        }
    })
    .catch(error => {
        console.log(error);
        enableButtons();
    });
};
</script>


<template>
    <div id="header">
        <textarea name="topic" id="topic-input" placeholder="Target Topic..." v-model="topic"></textarea>
        <button id="setting" ref="settingButton" @click="toggleSettingModal">Setting</button>
        <button id="start" ref="startButton" @click="start">Start</button>
    </div>

    <div v-if="showSettingModal" class="modal-overlay">
        <div class="modal">
            <h2>Settings</h2>
            <label>API key: <input v-model="setting.api_key" type="text"></label>
            <label>base URL: <input v-model="setting.base_url" type="text"></label>
            <label>model: <input v-model="setting.model" type="text"></label>
            <label>sampling method:
                <select v-model="setting.sampling_method">
                    <option value="best">best</option>
                    <option value="epsilon">epsilon</option>
                    <option value="v-epsilon">v-epsilon</option>
                </select>
            </label>
            <label>exploration weight: <input v-model="setting.exploration_weight" type="number" step="0.1"></label>
            <label>number of trials: <input v-model="setting.n_trials" type="number"></label>
            <label>number of rollouts: <input v-model="setting.n_rollouts" type="number"></label>
            <label>number of expansion nodes<input v-model="setting.n_expand" type="number"></label>
            
            <div class="modal-buttons">
                <button @click="saveSettings">Save</button>
                <button @click="toggleSettingModal">Cancel</button>
            </div>
        </div>
    </div>
</template>

<style scoped>
#header {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 10vh;
    border-bottom: 1px solid #e0e0e0;
    background-color: #f9f9f9;
    padding: 0 20px;
}

#topic-input {
    width: 40%;
    height: 60%;
    resize: none;
    border: 1px solid #ccc;
    border-radius: 6px; /* 圆角使其更现代化 */
    padding: 8px;
    font-size: 16px;
    outline: none;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

#topic-input:focus {
    border-color: #007bff;
    box-shadow: 0 0 5px rgba(0, 123, 255, 0.3);
}

#header button {
    height: 60%;
    width: 10%;
    margin-left: 20px;
    border: none;
    border-radius: 6px;
    background-color: #208cff;
    color: white;
    font-size: 16px;
    cursor: pointer;
    transition: background-color 0.3s ease, transform 0.2s ease;
}

#header button:hover {
    background-color: #0056b3;
    transform: translateY(-2px);
}

#header button:active {
    transform: translateY(0);
    background-color: #004494;
}

#header button:disabled {
    background-color: #b0d0f2;
    color: white;
    cursor: not-allowed;
    transform: none;
}

/* 弹窗 */
.modal {
    position: fixed;
    right: 0;
    background: white;
    margin-top: 20px;
    margin-right: 50px;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    width: 400px;
    text-align: center;
    font-family: monospace;
}

.modal label {
    display: block;
    margin: 10px 0;
    text-align: left;
}

.modal input, .modal select {
    width: 80%;
    padding: 8px;
    margin-top: 5px;
    border: 1px solid #ccc;
    border-radius: 5px;
}

.modal-buttons {
    margin-top: 15px;
    display: flex;
    justify-content: space-between;
}

.modal-buttons button {
    width: 45%;
    padding: 10px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 16px;
}

.modal-buttons button:first-child {
    background-color: #007bff;
    color: white;
}

.modal-buttons button:first-child:hover {
    background-color: #0056b3;
}

.modal-buttons button:last-child {
    background-color: #ccc;
    color: black;
}

.modal-buttons button:last-child:hover {
    background-color: #bbb;
}
</style>