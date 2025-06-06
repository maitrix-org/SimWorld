# Quick Start

This page shows how to download and install the packaged version of SimWorld. The package includes the executable file of SimWorld server and the Python client library.

## Before you begin
The following requirements should be fulfilled before installing SimWorld:

+ System requirements. SimWorld is built for Windows and Linux systems.
+ An adequate GPU. SimWorld aims for realistic simulations, so the server needs at least a 6 GB GPU although we would recommend 8 GB. A dedicated GPU is highly recommended for machine learning.
+ Memory. A 32 GB memory or above is recommended.
+ Disk space. SimWorld will use about 50 GB of space.
+ Python. Python is the main scripting language in SimWorld. SimWorld supports and Python 3.10 on Linux, and Python 3 on Windows.
+ Two TCP ports and good internet connection. 9000 and 9001 by default. Make sure that these ports are not blocked by firewalls or any other applications.

## Installation
### Client
Download the Python library from GitHub:

[SimWorld Python Client Library](https://github.com/maitrix-org/SimWorld)

```bash
git clone https://github.com/maitrix-org/SimWorld.git
cd SimWorld

# install simworld
conda create -n simworld python=3.10
conda activate simworld
pip install -e .
```


### Server
Download the SimWorld server executable from S3:

#### Windows

Download the [SimWorld Windows 64-bit Server (v0.1.0)](https://simworld-release.s3.us-east-1.amazonaws.com/SimWorld-Win64-v0_1_0-Foundation.zip) and unzip it.

#### Linux

Download the [SimWorld Linux 64-bit Server (v0.1.0)](https://simworld-release.s3.us-east-1.amazonaws.com/SimWorld-Linux64-v0_1_0-Foundation.zip) and unzip it.
