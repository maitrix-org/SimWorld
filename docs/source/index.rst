SimWorld Documentation
====================================

.. image:: assets/simworld_overview.png
   :alt: SimWorld Overview
   :width: 800px
   :align: center

Welcome to **SimWorld** Documentation!

**SimWorld** is a novel Unreal Engine-based simulator designed to generate unlimited, diverse urban environments for embodied AI tasks.

Existing embodied simulators typically focus on indoor scenes. There have been urban simulators, but they either lack realism or are limited to autonomous driving. Critically, most of them do not allow users to flexibly generate new scenes or define new embodied AI tasks. In contrast, SimWorld provides a user-friendly Python API and diverse 3D assets that enable users to procedurally generate realistic and dynamic city-scale environments to support various Embodied AI research tasks. Our simulator can also be connected with large language models (LLMs) to drive the behavior of different types of agents (humans, vehicles, and robots) in the environments.
simulation powered by Unreal Engine 5.

.. note::

   This project is under active development.


.. toctree::
   :maxdepth: 2
   :caption: GETTING STARTED

   getting_started/introduction
   getting_started/quick_start
   simworld-robotics/simworld_robotics

.. toctree::
   :maxdepth: 2
   :caption: SIMWORLD COMPONENTS

   components/overview
   components/citygen
   components/waypoint_system
   components/traffic_system
   components/communicator
   components/agent_system
   components/ue_detail

.. toctree::
   :maxdepth: 2
   :caption: PYTHON API REFERENCE

   resources/modules

.. toctree::
   :maxdepth: 2
   :caption: SIMWORLD ROBOTICS

   simworld-robotics/simworld_robotics
