# Overview

SimWorld consists two parts:

1. Unreal Engine executable file.
2. Python package.

Connection between Python and UE is set up by Communicator component, which holds TCP client in Python and server in UE. In Python, it is structured as a Communicator Class. In UE, it is an embedded plugin.

Below shows the code structure of the Python Package.
```text
simworld/               # Python package
    local_planner/      # Local planner component
    agent/              # Agent system
    assets_rp/          # Live editor component for retrieval and re-placing
    citygen/            # City layout procedural generator
    communicator/       # Core component to connect Unreal Engine
    config/             # Configuration loader and default config file
    llm/                # Basic llm class
    map/                # Basic map class and waypoint system
    traffic/            # Traffic system
    utils/              # Utility functions
data/                   # Necessary input data
config/                 # Example configuration file and user configuration file
scripts/                # Examples of usage, such as layout generation and traffic simulation
docs/                   # Documentation source files
README.md
```
