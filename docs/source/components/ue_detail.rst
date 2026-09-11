Unreal Engine Backend
=====================

The Unreal Engine backend forms the foundation of SimWorld, providing high-fidelity rendering and physics simulation.

Various Scenes
--------------

.. image:: ../assets/scenes.png
   :width: 800px
   :align: center
   :alt: A Subset of Collected Scenes

SimWorld supports two scene-building modes: procedural generation and pre-built scenes.

The procedural generation module enables the creation of virtually unlimited city layouts populated with diverse buildings, roads, and street elements. This allows users to dynamically render coherent and realistic urban environments at runtime, making it ideal for large-scale experimentation under customizable conditions. See :doc:`Procedural City Generation <../components/citygen>` for details.

In addition to procedurally generated cities, SimWorld also provides a rich collection of pre-built maps (see :doc:`Additional Environments <../getting_started/additional_environments>`). These manually designed scenes can be created by users or imported from external sources such as the Unreal Engine Marketplace. The current release includes 102 curated scenes spanning a wide range of visual and structural styles—such as ancient towns, natural landscapes, futuristic cities, and fictional worlds. Each map offers distinct visual cues, spatial layouts, and interaction dynamics, enabling diverse and comprehensive evaluation of embodied agents.

Assets
------

Our simulator provides a rich collection of city-scale assets, designed to support realistic and diverse urban simulations. These assets include buildings, trees, street furniture, vehicles, pedestrians, and robots. All assets are sourced from the Unreal Engine Marketplace to ensure high visual fidelity and performance.

In addition to the curated asset library, we also offer an **Asset Generation Pipeline** that enables users to create ``.uasset`` files directly from natural language descriptions. This tool streamlines the content creation process by converting user prompts into usable Unreal Engine assets, significantly lowering the barrier for customizing city environments.

Collected Assets
~~~~~~~~~~~~~~~~

Below is a selection of the assets currently available in our simulator:

* **Buildings**: A variety of architectural styles, including residential, commercial, and industrial structures.
* **Trees**: Multiple tree species with seasonal variations to enhance environmental realism.
* **Street Furniture**: Items such as benches, streetlights, boxes, and trash bins to add detail and immersion.
* **Vehicles**: A range of vehicles including cars, buses, trucks, and scooters, each with accurate scale and animations.
* **Pedestrians**: Human characters with diverse appearances and animations to simulate crowd behavior.
* **Robots**: The detailed introduction of the robot can be found in :doc:`SimWorld-Robotics <../simworld-robotics/simworld_robotics>`.

These assets collectively enable the creation of complex, dynamic, and realistic city scenes for simulation, visualization, and research purposes.

.. image:: ../assets/assets.png
   :width: 800px
   :align: center
   :alt: A Subset of Collected Assets

.. _ue_detail-sensors:

Sensors
-------

.. image:: ../assets/sensor.png
   :width: 800px
   :align: center
   :alt: Different Sensor

As illustrated in the figure above, SimWorld supports a variety of sensors, including RGB images, segmentation maps, and depth images, enabling a rich understanding of the surrounding environment.

Runtime actors in depth and segmentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``Communicator`` methods for spawning objects, agents, scooters, vehicles,
pedestrians, traffic signals, and waypoint marks register their render components
for ``depth`` and ``object_mask`` after setting the initial transform and mobility.
In the Base20260201 Windows backend, creating an actor alone makes it visible in
``lit``, but the color annotation command is also required for these two sensors.
No Blueprint modification is needed for the bundled box, humanoid, and vehicle
assets.

Runtime labels default to a stable, nonblack RGB color derived from the actor
name. These colors are not guaranteed to be globally unique or to match a semantic
class palette. Use ``ucv.set_color(name, (r, g, b))`` for a dataset's explicit
labels. This changes the sensor annotation, not the actor's visible material.
Procedurally generated city assets keep their configured asset-library colors.

For the low-level ``spawn_bp_asset`` API, register explicitly after configuration:

.. code-block:: python

   name = 'my_box'
   ucv.spawn_bp_asset('/Game/CityDatabase/blueprints/BP_Box.BP_Box_C', name)
   ucv.set_location((0, 0, 150), name)
   ucv.set_scale((1, 1, 1), name)
   ucv.set_movable(name, True)
   ucv.set_color(name, (251, 13, 107))

Keep moving actors movable so their annotation follows subsequent transforms.
The spawn and annotation methods raise ``RuntimeError`` if the server does not
acknowledge the operation, including when an asset path is unavailable.

To verify the behavior on a dedicated server running ``/Game/Maps/empty`` with
the complete Base20260201 asset package, set its UnrealCV port to 19090 and run
from the repository root:

.. code-block:: console

   python -m examples.verify_runtime_sensors --port 19090 --output sensor-evidence

The script exercises ``spawn_object``, ``spawn_agent``, and ``spawn_vehicles`` and
then moves the actors. It writes unmodified RGB/mask PNGs, metric depth NPYs,
the request transcript, and per-actor statistics to ``sensor-evidence``. It exits
with an error if an actor is missing from its mask, lacks foreground depth, or
its mask fails to move. It removes only the actors and capture camera it creates.
The camera is placed away from the player pawn to avoid capturing its own body.

How to get images
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # viewmode can be 'lit', 'depth' and 'object_mask'
   image = communicator.get_camera_observation(camera_id, viewmode)  # Get camera image observation

   # adjust camera
   ucv.get_cameras()                                   # Get list of all available cameras
   ucv.get_camera_location(camera_id)                  # Get camera position (x, y, z)
   ucv.get_camera_rotation(camera_id)                  # Get camera rotation (pitch, yaw, roll)
   ucv.get_camera_fov(camera_id)                       # Get camera field of view
   ucv.get_camera_resolution(camera_id)                # Get camera resolution (width, height)
   ucv.set_camera_location(camera_id, location)        # Set camera position (location: tuple of x, y, z)
   ucv.set_camera_rotation(camera_id, rotation)        # Set camera rotation (rotation: tuple of pitch, yaw, roll)
   ucv.set_camera_fov(camera_id, fov)                  # Set camera field of view (fov: float)
   ucv.set_camera_resolution(camera_id, resolution)    # Set camera resolution (resolution: tuple of width, height)

**Related files:** ``communicator.py``, ``unrealcv.py``.

Synchronous and Asynchronous mode
---------------------------------

Our simulator supports both synchronous and asynchronous execution modes for communication between the Python client and the Unreal Engine (UE) server.

In synchronous mode, the Python client explicitly controls the simulation timing. At each step, it sends a tick command to the UE server and waits until the server completes the simulation update. This mode ensures deterministic behavior, which is especially important for reinforcement learning, multi-agent coordination, and evaluation tasks.

In asynchronous mode, the UE server runs continuously at its own frame rate, while the Python client retrieves data at any time. This allows for real-time interaction but can lead to non-determinism and race conditions in agent-environment interaction.

.. code-block:: python

   # Set simulation mode: choose between "sync" (synchronous) and "async" (asynchronous)
   mode = "sync"
   tick_interval = 0.05  # Duration of each simulation step in seconds (only used in sync mode)
   ucv.set_mode(mode, tick_interval)

   # Advance the simulation by one tick (tick_interval seconds)
   ucv.tick()
