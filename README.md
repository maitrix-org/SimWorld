# SimWorld: A World Simulator for Scaling Photorealistic Multi-Agent Interactions
![Overview](https://github.com/user-attachments/assets/6246ad14-2851-4a51-a534-70f59a40e460)

**SimWorld** is a state-of-the-art world simulator built with Unreal Engine 5 to generate unlimited, dynamic environments for various **RL + LLM + Agent** systems' benchmarking and training.

<div align="center">
    <a href="http://simworld-cvpr2025.maitrix.org/"><img src="https://img.shields.io/badge/Website-SimWorld-blue" alt="Website" /></a>
    <a href="https://github.com/renjw02/SimWorld"><img src="https://img.shields.io/github/stars/yourusername/SimWorld?style=social" alt="GitHub Stars" /></a>
    <a href="https://simworld-doc.readthedocs.io/en/latest/"><img src="https://img.shields.io/badge/Documentation-Read%20Docs-green" alt="Documentation" /></a>
</div>

## 🔥 News 
 - 2025.4 The first formal release of **SimWorld** has been published! 🚀
 - 2025.3 Our demo of **SimWolrd** been accepted by CVPR 2025 Demostration Tack! 🎉

## 💡 Introduction
Most existing embodied simulators focus on indoor environments. While there are urban simulators, many either lack realism or are limited to specific domains, such as autonomous driving. Moreover, these simulators often don't allow users to dynamically generate new scenes or define custom AI tasks.

In contrast, **SimWorld** offers a **user-friendly Python API** and a vast collection of 3D assets, enabling users to generate realistic, dynamic city-scale environments with ease. SimWorld supports a range of **Embodied AI research tasks** and can be integrated with **large language models (LLMs)** to control agents—such as humans, vehicles, and robots—within the environment. Features include:

- **Open-ended World Generation**: Create diverse and evolving cityscapes.
- **Language Control**: Easily control the environment and agent behaviors using natural language.
- **Benchmark Support**: Evaluate your AI systems with a variety of pre-defined control levels.

SimWorld leverages Unreal Engine 5's **photorealistic rendering** and **physics simulation** to provide an immersive and realistic experience.

## 🏗️ Architecture

![Architecture](https://github.com/user-attachments/assets/f5f43638-7583-483f-aadc-1ddf5d6ff27a)

SimWorld's architecture is designed to be modular and flexible, supporting an array of functionalities such as dynamic world generation, agent control, and performance benchmarking. The components are seamlessly integrated to provide a robust platform for **Embodied AI** and **Agents** research and applications.

## Precommit Setup (For Contributors)
We use Google docstring format for our docstrings and the pre-commit library to check our code. To install pre-commit, run the following command:

```bash
conda install pre-commit  # or pip install pre-commit
pre-commit install
```

The pre-commit hooks will run automatically when you try to commit changes to the repository.