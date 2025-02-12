import os
from dotenv import find_dotenv, load_dotenv
from mcts.runner import (
    MCTSRunner
)
from agents.general import (
    LLMEngine
)
from agents.generator import (
    SciGenerator
)
from agents.rewarder import (
    IdeaArena
)

load_dotenv(find_dotenv())

api_key = os.environ["API_KEY"]
base_url = os.environ["BASE_URL"]

deepseek_api_key = os.environ["DEEPSEEK_API_KEY"]
deepseek_base_url = os.environ["DEEPSEEK_BASE_URL"]

engine_list = {
    "gpt-4o": LLMEngine(api_key=api_key, base_url=base_url, model="gpt-4o"),
    "gpt-4o-mini": LLMEngine(api_key=api_key, base_url=base_url, model="gpt-4o-mini"),
    "deepseek-chat": LLMEngine(api_key=deepseek_api_key, base_url=deepseek_base_url, model="deepseek-chat")
}


def main(opt):
    topic = opt.topic
    model = opt.model
    sampling_method = opt.sampling_method
    n_rollouts = opt.n_rollouts
    n_exp = opt.n_exp
    
    engine = engine_list[model]
    
    generator = SciGenerator(
        engine=engine,
        topic=topic
    )
    rewarder = IdeaArena(
        engine=engine,
        topic=topic
    )
    runner = MCTSRunner(
        generator=generator,
        rewarder=rewarder,
        sampling_method=sampling_method,
        exploration_wright=1.0
    )
    runner.run(
        n_rollouts=n_rollouts,
        n_exp=n_exp,
        terminal_func=lambda contexts: len(contexts) > 0 and contexts[-1].key == "gen_idea"
    )

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--topic", type=str, help="The topic of research idea")
    parser.add_argument("--n_rollouts", type=int, help="number of rollouts per trial")
    parser.add_argument("--n_exp", type=int, help="number of expanded nodes")
    parser.add_argument("--model", type=str, help="The name of LLM to power the system")
    parser.add_argument("--sampling_method", type=str, help="The sampling method of MCTS")
    
    opt = parser.parse_args()
    main(opt)