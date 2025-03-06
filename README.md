<div align="center">
  <a href="https://github.com/goer17/InnoTree">
    <img src="assets/logo.png" alt="Logo" width="256" height="256">
  </a>
<h3 align="center">InnoTree: Integrating MCTS with Language Models for Scientific Idea Generation</h3>
  <p align="center">
    💡 InnoTree is an advanced agent system specifically designed to integrate Monte Carlo Tree Search (MCTS) techniques, enabling the efficient generation and exploration of innovative scientific ideas.
  </p>
</div>

#### Quick Start

**Cloning the repo**

```bash
git clone https://github.com/Goer17/InnoTree.git
```

**Downloading the dependencies**

```bash
conda create -n inno_tree python=3.10 -y && \
conda activate inno_tree
```

```bash
pip install -r requirements.txt
```

**Running**

```bash
python run.py --topic "Generate one scientific research idea based on multi-agent system" \
    --n_rollouts 10 \
    --n_exp 4 \
    --model "gpt-4o" \
    --sampling_method "best"
```

#### Todo List

- [X] Implementing RAG interface
- [ ] More Action Node
- [ ] Benchmarking
- [X] MCTS Visualization
