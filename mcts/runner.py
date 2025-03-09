from typing import Dict, List, Any, Callable, Tuple

from agents.generator import Generator
from agents.rewarder import Rewarder, ScienceRewarder, IdeaArenaRewarder
from agents.feedbacker import Feedbacker
from mcts.node import Node, Context
from typing import Literal

from utils.logger import logger
from shortuuid import uuid

class MCTSRunner:
    def __init__(self,
                 topic: str,
                 generator: Generator,
                 rewarder: Rewarder,
                 feedbacker: Feedbacker,
                 sampling_method: Literal["best", "epsilon", "v-epsilon"] = "best",
                 exploration_weight: float = 1.0,
                 *args, **kwargs
                 ):
        self.topic = topic
        self.generator = generator
        self.rewarder = rewarder
        self.feedbacker = feedbacker
        self.root: Node = Node.root_node()
        self.sampling_method = sampling_method
        self.exploration_weight = exploration_weight
        self.pre_contexts = []
        self.pre_node_profiles = []
        self.history: List[str] = []
        self.idea_db: List[str] = []

    def to_json(self) -> List[Dict[str, Any]]:
        datas = []
        def _traverse(node: Node) -> List[Dict[str, Any]]:
            data = {
                "n_id": node.n_id,
                "p_id": node.parent.n_id if node.parent else (self.pre_node_profiles[-1]["n_id"] if len(self.pre_node_profiles) else ""),
                "n_key": node.context.key,
                "content": node.context.content,
                "observation": node.context.observation if node.context.observation else "",
                "value": node.value,
                "visits": node.visits
            }
            datas.append(data)
            for child in node.children:
                _traverse(child)
        _traverse(self.root)
        return self.pre_node_profiles + datas
    
    def __expand(
        self,
        current: Node,
        contexts: List[Context],
        n_expand: int = 5
    ):
        exp_contexts = self.generator.generate(
            contexts=contexts,
            n=n_expand
        )
        logger.info(f"Expanded {len(exp_contexts)} nodes !")
        for i in range(len(exp_contexts)):
            child_context = exp_contexts[i]
            logger.info(f"{i} - child:\n{child_context}")
            child_node = Node(
                context=child_context,
                parent=current,
                depth=current.depth + 1
            )
            current.children.append(child_node)
    
    def __backprop(
        self,
        leaf_node: Node,
        reward: float
    ):
        node = leaf_node
        while node:
            node.update(reward=reward)
            node = node.parent
    
    def __rollout(
            self,
            contexts: List[Context],
            terminal_func: Callable
        ):
        rollout = contexts[:]
        temp_path = []
        yield False, [{"n_id": f"temp - [#{uuid()[:8]}]", "p_id": "", "n_key": "...", "content": ""}]
        while not terminal_func(rollout):
            gen_context = self.generator.generate(contexts=rollout)[0]
            gen_context.observation = self.feedbacker.feedback(context=gen_context)
            rollout.append(gen_context)
            temp_path.append(
                {
                    "n_id": f"temp - [#{uuid()[:8]}]",
                    "p_id": temp_path[-1]["n_id"] if len(temp_path) else "",
                    "n_key": gen_context.key,
                    "content": gen_context.content,
                    "observation": gen_context.observation if gen_context.observation else ""
                }
            )
            yield False, temp_path + [{"n_id": f"temp - [#{uuid()[:8]}]", "p_id": temp_path[-1]["n_id"], "n_key": "...", "content": ""}]
            logger.info(f"[rollout...] next step: {gen_context}")
        if len(rollout) and rollout[-1].key == "idea":
            self.idea_db.append(rollout[-1].content)
            self.history.append(rollout[-1].content)
        yield True, rollout
    
    def __run_one_trial(
        self,
        trial_id: int,
        n_rollouts: int,
        n_expand: int,
        terminal_func: Callable,
        *args, **kwargs
    ):
        logger.critical(f"Started trial [id = {trial_id}]")
        logger.info(f"Running trial {trial_id}...")
        self.idea_db = []
        if isinstance(self.rewarder, IdeaArenaRewarder):
            base_cnt = kwargs.get("base_cnt", 4)
            for _ in range(base_cnt):
                for tag, res in self.__rollout(
                    contexts=self.pre_contexts,
                    terminal_func=terminal_func
                ):
                    if not tag:
                        res[0]["p_id"] = self.root.n_id
                        yield self.to_json() + res
                    else:
                        rollout = res
                        if rollout[-1].key == "idea":
                            self.idea_db.append(rollout[-1].content)
        yield self.to_json()
        for _ in range(n_rollouts):
            current = self.root
            contexts = self.pre_contexts[:]
            while not current.is_leaf():
                if self.sampling_method == "best":
                    current = current.best_child(exploration_weight=self.exploration_weight)
                elif self.sampling_method == "epsilon":
                    current = current.epsilon_sample(epsilon=0.1, explaration_weight=self.exploration_weight)
                elif self.sampling_method == "v-epsilon":
                    current = current.epsilon_sample(epsilon=0.1 / self.root.visits, explaration_weight=self.exploration_weight)
                if current != self.root:
                    contexts.append(current.context)
            if terminal_func(contexts):
                if self.sampling_method == "best":
                    return
                continue
            if current.visits > 0:
                self.__expand(
                    current=current, 
                    contexts=contexts,
                    n_expand=n_expand
                )
                yield self.to_json()
                for child in current.children:
                    child.context.observation = self.feedbacker.feedback(context=child.context)
                yield self.to_json()
                current = current.children[0]
                contexts.append(current.context)
            for tag, res in self.__rollout(
                contexts=contexts,
                terminal_func=terminal_func
            ):
                if not tag:
                    res[0]["p_id"] = current.n_id
                    yield self.to_json() + res
                else:
                    rollout = res
            if len(rollout) == 0 or rollout[-1].key != "idea":
                continue
            reward, judges = self.rewarder.reward(self.topic, idea=rollout[-1].content, idea_db=self.idea_db)
            if isinstance(judges, list):
                for judge in judges:
                    logger.info(f"Rewarder response:\n{judge}")
            self.__backprop(
                leaf_node=current,
                reward=reward
            )
            yield self.to_json()
    
    def __next_step(self) -> bool:
        msg = "children nodes :\n"
        for idx, child in enumerate(self.root.children):
            msg += (
                f"child-{idx}: [{child.context.key}]\n"
                f"{child.context.content[:50]}...\n"
                f"AVG.value = {child.uct(exploration_weight=0)}\n\n"
            )
        logger.debug(msg=msg)
        self.pre_node_profiles.append(
            {
                "n_id": self.root.n_id,
                "p_id": self.pre_node_profiles[-1]["n_id"] if len(self.pre_node_profiles) else "",
                "n_key": self.root.context.key,
                "content": self.root.context.content,
                "observation": self.root.context.observation if self.root.context.observation else "",
                "value": self.root.value,
                "visits": self.root.visits,
                "fixed": True
            }
        )
        self.root = self.root.best_child(exploration_weight=0)
        if self.root is None:
            return False
        self.pre_contexts.append(self.root.context)
        self.root.clear()
        return True
    
    def run(
        self,
        n_trials: int,
        n_rollouts: int,
        n_expand: int,
        terminal_func: Callable,
        *args, **kwargs
    ):
        for trial_id in range(n_trials):
            yield from self.__run_one_trial(
                trial_id=trial_id,
                n_rollouts=n_rollouts,
                n_expand=n_expand,
                terminal_func=terminal_func
            )
            if not self.__next_step():
                # terminal node
                logger.critical(f"all trials were over.")
                break
            logger.critical(f"trial {trial_id} was over, next step:\n{self.root.context}")