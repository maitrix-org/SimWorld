# SimWorld Examples

This folder contains example code demonstrating various functionalities of SimWorld, helping you get started quickly and understand how to use the core features.

## Example List

### `verify_runtime_sensors.py`
Verify runtime boxes, humanoids, and vehicles in depth and segmentation on a dedicated Base20260201 `/Game/Maps/empty` server. Run `python -m examples.verify_runtime_sensors --port 19090 --output sensor-evidence` from the repository root. The script saves raw PNG/NPY captures, a command transcript, and measurements before and after moving the actors; it exits nonzero on failure and removes its test actors and camera.

### `gym_interface_demo.ipynb`
Minimal demo showing how to create an LLM-based agent with a Gym-like environment interface. Demonstrates Agent-Environment interaction loop and goal-oriented tasks.

### `world_generation.ipynb`
Generate virtual worlds in Unreal Engine. Load city layouts from JSON files and render complete 3D environments in UE.

### `layout_generation.ipynb`
Procedurally generate city roads and buildings. Randomly generate city road networks, buildings and city elements, then export the layout data.

### `layout_generation_with_visualization.ipynb`
Similar to `layout_generation.ipynb` but includes visualization features to display generated city layouts.

### `traffic_simulation.ipynb`
Simulate traffic flow in the city. Initialize traffic controller, spawn vehicles and traffic signals, and run real-time traffic simulation.

### `local_action_planner.ipynb`
Test the local action planner module. Initialize humanoid agents, parse natural language instructions using LLM, and execute complex action sequences (e.g., navigation, object pickup).

### `asset_rp.ipynb`
Retrieve and place scene assets using natural language. Support natural language asset descriptions, automatically retrieve appropriate UE assets, and intelligently place them in the scene. This script will only generate json file, you need to use `world_generation.ipynb` to generate the world.

### `camera.ipynb`
Get camera observation data. Retrieve RGB images from virtual cameras and support multiple image modes (lit, depth, segmentation, etc.).

### `map.ipynb`
Test map and waypoint systems. Initialize map data, visualize road networks, and calculate shortest paths.

### `ue_command.ipynb`
Complete UE interaction command set with detailed demonstration of all available UE commands, including agent actions, object spawning, and environment control. Suitable as an API reference manual.



## Prerequisites

1. **Install SimWorld**
   ```bash
   pip install -e .
   ```

2. **Start UE Server**
   - Download and run the SimWorld UE5 executable
   - Ensure the server is running before executing example code

3. **Configure API Key** (if using LLM features)
   ```python
   import os
   os.environ['OPENAI_API_KEY'] = 'your_api_key_here'
   ```

4. **Configuration Files**
   - Copy `config/example.yaml` and modify as needed
   - Specify the configuration file path in your code


## Important Notes

- Most examples require the UE server to be running
- LLM features require OpenAI API Key configuration
- Remember to call `communicator.disconnect()` after running
- File paths in some examples need to be modified according to your actual paths
