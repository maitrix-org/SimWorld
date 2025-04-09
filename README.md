# SimWorld: A World Simulator for Scaling Photorealistic Multi-Agent Interactions

<div align="center">
    <img src="https://github.com/user-attachments/assets/63c54687-f11a-48c4-a212-eefdac7dc175" width="400">
</div>
<div align="center">
    <a href="http://simworld-cvpr2025.maitrix.org/"><img src="https://img.shields.io/badge/Website-SimWorld-blue" alt="Website" /></a>
    <a href="https://github.com/renjw02/SimWorld"><img src="https://img.shields.io/github/stars/yourusername/SimWorld?style=social" alt="GitHub Stars" /></a>
    <a href="https://simworld-doc.readthedocs.io/en/latest/"><img src="https://img.shields.io/badge/Documentation-Read%20Docs-green" alt="Documentation" /></a>
</div>

## Introduction
We introduce **SimWorld**, a state-of-the-art simulator built with Unreal Engine to generate unlimited, dynamic urban environments for **Embodied AI** tasks.

![Overview](https://github.com/user-attachments/assets/6246ad14-2851-4a51-a534-70f59a40e460)

### What's New?
Most existing embodied simulators focus on indoor environments. While there are urban simulators, many either lack realism or are limited to specific domains, such as autonomous driving. Moreover, these simulators often don't allow users to dynamically generate new scenes or define custom AI tasks.

In contrast, **SimWorld** offers a **user-friendly Python API** and a vast collection of 3D assets, enabling users to generate realistic, dynamic city-scale environments with ease. SimWorld supports a range of **Embodied AI research tasks** and can be integrated with **large language models (LLMs)** to control agents—such as humans, vehicles, and robots—within the environment. Features include:

- **Open-ended World Generation**: Create diverse and evolving cityscapes.
- **Language Control**: Easily control the environment and agent behaviors using natural language.
- **Benchmark Support**: Evaluate your AI systems with a variety of pre-defined control levels.

SimWorld leverages Unreal Engine 5's **photorealistic rendering** and **physics simulation** to provide an immersive and realistic experience.

## Architecture

![Architecture](https://github.com/user-attachments/assets/f5f43638-7583-483f-aadc-1ddf5d6ff27a)

SimWorld's architecture is designed to be modular and flexible, supporting an array of functionalities such as dynamic world generation, agent control, and performance benchmarking. The components are seamlessly integrated to provide a robust platform for **Embodied AI** and **Agents** research and applications.
