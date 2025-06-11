# SimWorld-Robotics
## Overview

In addition to the human-like avatars introduced in the [Agent System](../components/agent_system.md), SimWorld also supports a wide range of robot simulations to facilitate research and development across diverse communities and use cases.
 
This section provides a comprehensive overview of robot-related features in SimWorld, including robot types, capabilities, and potential applications.

## Robot Type

SimWorld currently supports one robot platform: a **quadruped robot** similar to Spot. It features:

- A rich action space supporting both discrete and continous control
- A head-mounted camera enabling diverse and detailed observation space for perception tasks    

Although only one robot type is available at this stage, the architecture is designed to support future expansion to other robot platforms, such as wheeled, aerial, and humanoid agents.

## Action Space

SimWorld provides a rich action space for the quadruped robot, enabling both continuous and discrete control over a variety of motor and sensory behaviors. The action space is organized into the following categories:

| **Action Type**     | **Controllable Parameters**                                                 | **Control Mode**             | **Description**                                                                 |
|---------------------|------------------------------------------------------------------------------|-------------------------------|---------------------------------------------------------------------------------|
| **Transition**      | - Step length<br>- Movement speed<br>- Direction (Forward/Backward/Left/Right) | Continuous / Discrete         | Move the robot in a specified direction, controlling stride and velocity.       |
| **Rotation**        | - Rotation angle<br>- Rotation speed<br>- Direction (Clockwise/Counterclockwise) | Continuous / Discrete         | Rotate the robot body around its vertical axis.                                |
| **Look Up / Down**  | - Pitch angle adjustment                                                    | Discrete                      | Tilt the robot’s head up or down to change the camera view.                    |
| **Hold Position**   | - Duration (time to hold)                                                   | Continuous / Discrete         | Keep the robot still in its current pose for a specified duration.             |

> **Note:** All actions support both continuous and discrete modes except for **Look Up / Down**, which is available only in discrete mode. 


Demo for robot action space

```python
# Specify robot name and asset
robot_name = "Demo_Robot"
robot_asset = "/Game/Robot_Dog/Blueprint/BP_SpotRobot.BP_SpotRobot_C"

# Spawn robot in the simulator
ucv.spawn_bp_asset(robot_asset, robot_name)
ucv.enable_controller(robot_name, True)

# Robot - look up / look down
ucv.dog_look_up(robot_name)    # look up
ucv.dog_look_down(robot_name)  # look down

# Robot Movement
# direction: 0 = forward, 1 = backward, 2 = left, 3 = right
for direction in [0, 1, 2, 3]:
    speed = 200
    duration = 1
    move_parameter = [speed, duration, direction]
    ucv.dog_move(robot_name, move_parameter)
    time.sleep(duration)

# Robot Rotation
# clockwise: 1 = right turn, -1 = left turn
for angle, clockwise in [(90, 1), (-90, -1)]:
    duration = 0.7
    rotate_parameter = [duration, angle, clockwise]
    ucv.dog_rotate(robot_name, rotate_parameter)
    time.sleep(duration)

```

## Observation Space
```{image} ../assets/sensor.png 
:width: 800px
:align: center
:alt: Different Sensor
```
As previously introduced in the [Agent System](../components/agent_system.md), SimWorld supports various onboard sensors—such as RGB, segmentation, and depth cameras—to provide a rich observation space for robotic perception.

## Potential Applications

SimWorld-Robotics is designed to support advanced research in embodied AI and multi-agent collaboration. Currently, two benchmark tasks are provided to showcase the robot's capabilities in real-world inspired scenarios:

### 1. Multimodal Instruction Following

In this benchmark, a single robot is tasked with following **natural language instructions** and **visual hints** to navigate to a target destination within the simulated city. The agent must ground language into action, reason over the visual scene, and plan its trajectory accordingly.

> Example:  
```{image} ../assets/IllustrationOfMMNav.png 
:width: 800px
:align: center
:alt: Different Sensor
```

This benchmark enables research on vision-and-language navigation (VLN), multimodal grounding, and instruction-conditioned policy learning.

### 2. Multi-Robot Search via Communication

In this benchmark, **multiple robots** are spawned at different locations in the city. Their goal is to **find each other** by leveraging **natural language communication**. Robots exchange observations and hypotheses, plan joint strategies, and update beliefs based on received messages.

This setup is ideal for studying decentralized collaboration, emergent communication, multi-agent collaboration, and belief modeling.

---

> Example: 
```{image} ../assets/IllustrationOfMRS.png 
:width: 800px
:align: center
:alt: Different Sensor
```