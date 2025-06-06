# SimWorld

SimWorld is a simulation platform for developing and evaluating LLM/VLM-powered AI agents in complex physical and social environments. The main goal of SimWorld is to help bridge the gap between agent performance in structured digital domains and the dynamic challenges of the real world. To do so, the platform is designed to be a foundational tool for advancing real-world agent intelligence across a variety of disciplines.

SimWorld is built on Unreal Engine 5 and offers core capabilities to meet the needs of modern agent development. It provides (1) realistic, open-ended world simulation with accurate physics and language-based procedural generation. Control and interaction are handled through (2) a rich interface for LLM/VLM agents, supporting multi-modal perception and natural language actions. Finally, SimWorld includes (3) diverse and customizable physical and social reasoning scenarios, enabling systematic training and evaluation of complex agent behaviors like navigation, planning, and strategic cooperation.

## Simulator

SimWorld employs a robust and scalable client-server architecture that enables efficient simulation and agent control. The server component, built on Unreal Engine 5, serves as the simulation backbone, handling critical tasks such as sensor rendering, physical simulation and updates on the world-state.

The client component, implemented in Python, provides a flexible and developer-friendly interface for:
- Agent control logic and decision-making
- Seamless integration with LLM/VLM models
- Custom scenario configuration and management

This architecture enables efficient separation of concerns while maintaining high performance and scalability for complex simulation scenarios.

**TODO: need a figure here**
