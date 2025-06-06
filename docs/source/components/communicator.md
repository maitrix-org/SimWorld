# Communicator

## Overview
```{image} ../assets/communicator.png
:width: 800px
:align: center
:alt: Communicator Architecture
```
The **Communicator** module serves as the bridge between Python client and Unreal Engine server. Implemented in both Python and C++, it uses **UnrealCV** to establish a TCP connection, enabling communication between the two sides.

We extended the basic communication protocol by defining a custom set of commands for scene control, actor manipulation, and data querying. These commands are encoded in JSON format and passed through the TCP channel. For instance, Python can instruct UE to spawn an actor at a specific location, retrieve the current pose of a pedestrian, or trigger motion events on a robot.

The Communicator plays a central role in the simulation loop: Python uses it to update the virtual world, while UE reports back environmental feedback or visual state. This design allows us to decouple logic computation from rendering, achieving both flexibility and modularity.

## Communicator
```python
class Communicator:
    def __init__(self, unrealcv: UnrealCV = None):
        """Initialize the communicator.

        Args:
            unrealcv: UnrealCV instance for communication with Unreal Engine.
        """
        self.unrealcv = unrealcv
        ...

class UnrealCV:
    def __init__(self, port=9000, ip='127.0.0.1', resolution=(640, 480)):
        """Initialize the UnrealCV client.

        Args:
            port: Connection port, defaults to 9000.
            ip: Connection IP address, defaults to 127.0.0.1.
            resolution: Resolution, defaults to (320, 240).
        """
        self.ip = ip
        # Build a client to connect to the environment
        self.client = unrealcv.Client((ip, port))
        self.client.connect()
        self.resolution = resolution
        ...
```
The Communicator class acts as the bridge between Python and Unreal Engine (UE). It maintains a unrealcv attribute (an instance of the UnrealCV class), which handles the underlying TCP connection. Additionally, the Communicator is responsible for mapping Python objects to their unique name in UE.

## Using Communicator
All communication between Python and UE—such as rendering the scene, simulating traffic, or interacting with agents—is handled through the Communicator. Below are some basic use cases, including how to generate a city in UE, spawn objects, and clean the environment. For complete functionality, refer to the [Python API](../resources/modules.rst).

```python
# Instantiate unrealcv and communicator first
ucv = UnrealCV()
communicator = Communicator(ucv)

# Render a city
communicator.generate_world('path/to/city_json', 'path/to/asset_database')

# Spawn objects
## Spawn static object (non-movable)
communicator.spawn_object(object_name, model_path, position, direction)
## Spawn an agent (controlled by LLM or rule-based logic)
communicator.spawn_agent(agent, model_path, type)  
## Spawn the UE Manager actor (required for agent physical state updates)  
communicator.spawn_ue_manager(ue_manager_path)  

# Clear the UE environment (optionally keeping roads)
communicator.clear_env(keep_roads=True)
```
