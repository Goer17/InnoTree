import os, sys

sys.path.append(os.path.abspath("."))

from dotenv import find_dotenv, load_dotenv
from argparse import ArgumentParser
from mcts.node import (
    Node
)
from mcts.runner import (
    MCTSRunner
)
from agents.general import (
    PromatParser,
    LLMEngine
)
from agents.generator import (
    TestGenerator,
    SciGenerator
)
from agents.rewarder import (
    SciRewarder,
    TestRewarder,
)
from utils.log import logger

load_dotenv(find_dotenv())

api_key = os.environ["API_KEY"]
base_url = os.environ["BASE_URL"]

engine = LLMEngine(
    api_key=api_key,
    base_url=base_url
)

def test_engine():
    prompt = "Hello, glad to see you."
    results = engine.gen_from_prompt(prompt, n_choices=4)
    for i in range(4):
        print(results[i])

def mcts_demo():
    generator = TestGenerator()
    rewarder = TestRewarder()
    runner = MCTSRunner(
        root=Node.root_node(),
        generator=generator,
        rewarder=rewarder,
        sampling_method="best",
        exploration_wright=2.0
    )
    runner.run(
        n_rollouts=20,
        n_exp=3,
        terminal_func=lambda contexts: sum(int(context.content) for context in contexts) >= len(rewarder.path)
    )


def main():
    parser = ArgumentParser()
    parser.add_argument("-f", "--func", required=True, help="The testing function")

    args = parser.parse_args()
    func = args.func
    eval(func)()

if __name__ == "__main__":
    main()