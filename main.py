from agents.engine import engines
from agents.rewarder import ScienceRewarder, IdeaArenaRewarder
from agents.generator import Generator
from agents.feedbacker import Feedbacker
from mcts.runner import MCTSRunner
from utils.rag import VanillaRAG

def main(args):
    topic: str = args.topic
    model: str = args.model
    n_trials: int = args.n_trials
    n_rollouts: int = args.n_rollouts
    n_exp: int = args.n_exp
    n_results: int = args.n_results
    arena: bool = args.arena
    sampling_method: str = args.sampling
    
    engine = engines[model]
    rag = VanillaRAG()
    
    generator = Generator(
        engine=engine,
        topic=topic
    )
    feedbacker = Feedbacker(
        engine=engine,
        rag=rag,
        n_results=n_results
    )
    rewarder = IdeaArenaRewarder(engine) if arena else ScienceRewarder(engine)
    runner = MCTSRunner(
        topic=topic,
        generator=generator,
        rewarder=rewarder,
        feedbacker=feedbacker,
        sampling_method=sampling_method
    )
    for tree in runner.run(
        n_trials=n_trials,
        n_rollouts=n_rollouts,
        n_expand=n_exp,
        terminal_func=lambda ctxs: len(ctxs) and ctxs[-1].key == "idea"
    ):
        pass

def get_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--topic", type=str)
    parser.add_argument("--model", type=str)
    parser.add_argument("--n_rollouts", type=int, default=10)
    parser.add_argument("--n_trials", type=int, default=20)
    parser.add_argument("--n_exp", type=int, default=3)
    parser.add_argument("--n_results", type=int, default=5)
    parser.add_argument("--arena", action="store_true")
    parser.add_argument("--sampling", choices=["best", "epsilon", "v-epsilon"])
    
    return parser.parse_args()

if __name__ == "__main__":
    main(get_args())