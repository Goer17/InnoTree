from typing import Dict, List, Any, Callable

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
                 root: Node = Node.root_node(),
                 sampling_method: Literal["best", "epsilon", "v-epsilon"] = "best",
                 exploration_weight: float = 1.0,
                 *args, **kwargs
                 ):
        self.topic = topic
        self.generator = generator
        self.rewarder = rewarder
        self.feedbacker = feedbacker
        self.root = root
        self.sampling_method = sampling_method
        self.exploration_weight = exploration_weight
        self.pre_contexts = []
        self.history: List[str] = []
        self.idea_db: List[str] = []

    def to_json(self) -> List[Dict[str, Any]]:
        datas = []
        def _traverse(node: Node) -> List[Dict[str, Any]]:
            data = {
                "n_id": node.n_id,
                "p_id": node.parent.n_id if node.parent else "",
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
        return datas
    
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
        ) -> List[Context]:
        rollout = contexts[:]
        while not terminal_func(rollout):
            gen_context = self.generator.generate(contexts=rollout)[0]
            gen_context.observation = self.feedbacker.feedback(context=gen_context)
            rollout.append(gen_context)
            logger.info(f"[rollout...] next step: {gen_context}")
        if len(rollout) and rollout[-1].key == "idea":
            self.idea_db.append(rollout[-1].content)
            self.history.append(rollout[-1].content)
        return rollout
    
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
            yield self.to_json() + [{
                "n_id": f"temp#{uuid()[:8]}",
                "p_id": self.root.n_id,
                "n_key": "initialize...",
                "content": f"generated {base_cnt} initial ideas..."
            }]
            for _ in range(base_cnt):
                rollout = self.__rollout(
                    contexts=self.pre_contexts,
                    terminal_func=terminal_func
                )
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
                    current = current.epsilon_sample(epsilon=self.epsilon, explaration_weight=self.exploration_weight)
                elif self.sampling_method == "v-epsilon":
                    current = current.epsilon_sample(epsilon=self.epsilon / self.root.visits, explaration_weight=self.exploration_weight)
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
            yield self.to_json() + [{
                "n_id": f"temp#{uuid()[:8]}",
                "p_id": current.n_id,
                "n_key": "rollout...",
                "content": ""
            }]
            rollout = self.__rollout(
                contexts=contexts,
                terminal_func=terminal_func
            )
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
                f"UCT = {child.uct()}\n\n"
            )
        logger.debug(msg=msg)
        self.root = self.root.best_child()
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