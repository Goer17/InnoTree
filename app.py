import json

from flask import Flask, request, Response, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

from mcts.runner import MCTSRunner
from agents.engine import LLMEngineFactory
from agents.generator import Generator
from agents.rewarder import ScienceRewarder, IdeaArenaRewarder
from agents.feedbacker import Feedbacker

from utils.rag import VanillaRAG
from utils.logger import logger
import uuid, time

tasks = {}

@app.route("/start", methods=["POST"])
def start():
    data = request.json
    task_id = str(uuid.uuid4())
    try:
        topic: str = data["topic"]
        if len(topic.strip()) == 0:
            raise RuntimeError("Topic is empty!")
        tasks[task_id] = {
            "topic": topic,
            "api_key": data["api_key"],
            "base_url": data["base_url"],
            "model": data["model"],
            "sampling_method": data.get("sampling_method", "best"),
            "exploration_weight": data.get("exploration_weight", 1.0),
            "n_trials": data.get("n_trials", 10),
            "n_rollouts": data.get("n_rollouts", 10),
            "n_expand": data.get("n_expand", 4),
        }
        return jsonify({"task_id": task_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/stream", methods=["GET"])
def stream():
    task_id = request.args.get("task_id")
    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404

    params = tasks[task_id]
    engine = LLMEngineFactory.create_engine(
        api_key=params["api_key"],
        base_url=params["base_url"],
        model=params["model"]
    )
    
    generator = Generator(engine, params["topic"])
    rewarder = IdeaArenaRewarder(engine)
    feedbacker = Feedbacker(engine, VanillaRAG(), 3)

    runner = MCTSRunner(
        topic=params["topic"],
        generator=generator,
        rewarder=rewarder,
        feedbacker=feedbacker,
        sampling_method=params["sampling_method"],
        exploration_weight=params["exploration_weight"]
    )

    def emit():
        for tree in runner.run(
            n_trials=params["n_trials"],
            n_rollouts=params["n_rollouts"],
            n_expand=params["n_expand"],
            terminal_func=lambda ctxs: len(ctxs) > 0 and ctxs[-1].key == "idea"
        ):
            data_tree = json.dumps(tree)
            logger.critical(f"[task-id: {task_id}] updated!")
            yield f"data: {data_tree}\n\n"
            time.sleep(0.5)
        yield []

    return Response(emit(), content_type="text/event-stream")


if __name__ == "__main__":
    app.run()