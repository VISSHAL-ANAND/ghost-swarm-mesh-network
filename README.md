# Resilient Mesh Network Simulator

A disaster response simulation system that models a resilient mesh network of autonomous nodes coordinating to detect and rescue human groups in affected areas.

## Overview

This project simulates a ghost swarm of drone-like nodes deployed in a disaster zone. The nodes form a self-organizing mesh network to:
- Detect human groups in the affected area
- Elect a leader node for coordinating rescue operations
- Route detection signals through the mesh to reach safe servers
- Plan and execute rescue missions

## Features

- **Dynamic Mesh Networking**: Nodes communicate within a configurable communication radius
- **Leader Election**: Intelligent leader selection based on battery, temperature, and distance metrics
- **Signal Routing**: Multi-hop pathfinding using Dijkstra's algorithm for robust packet delivery
- **Battery Management**: Realistic battery drain simulation for transmission, idle, and routing operations
- **Real-time Visualization**: Interactive GUI showing the mesh network, node status, and rescue operations
- **Command Center**: User controls for managing rescue operations, adding nodes, and monitoring system state

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/resilient-mesh-network-simulator.git
cd resilient-mesh-network-simulator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the simulator:
```bash
python main.py
```

When the application starts:
1. Enter the number of safe servers to deploy (default: 3)
2. The GUI will display the mesh network visualization
3. Use the Command Center buttons to:
   - Monitor detected human groups
   - View data received by servers
   - Add new human groups in the disaster zone
   - Airdrop additional nodes for network reinforcement
   - Terminate nodes to simulate failures

## System Architecture

### Classes

- **Node**: Represents autonomous mesh network devices
  - Position, battery, temperature sensors
  - Score-based leader election
  - Mesh connectivity within communication radius

- **Human**: Represents groups of people in the disaster zone
  - Random initial positions
  - Detection by sensing nodes
  - Rescue status tracking

- **Signal**: Data packets routed through the mesh
  - Multi-hop path support
  - Battery drain for intermediate routers
  - Format conversion for server delivery

- **SafeServer**: Command centers outside the disaster zone
  - Receives formatted data from the leader
  - Logs all rescue-related information

### Core Algorithms

1. **Leader Election**: Multi-criteria scoring system
   - Battery level (30% weight)
   - Distance from disaster (50% weight)
   - Temperature (20% weight)

2. **Pathfinding**: Dijkstra's algorithm for optimal routing
   - Node-to-node paths for signal routing
   - Node-to-position paths for rescue planning

3. **Signal Processing**: Continuous streaming protocol
   - Signals transmitted every simulation tick
   - Battery drain at each hop
   - Leader aggregation and server distribution

## Configuration

Edit `main.py` to adjust simulation parameters:

```python
NUM_NODES = 200              # Initial number of mesh nodes
MAP_SIZE = 100               # Simulation area size (100x100)
DESTROY_RADIUS = 12          # Complete destruction zone
AFFECTED_RADIUS = 25         # Detection and rescue zone
COMM_RADIUS = 15             # Node communication range
SENSE_RANGE = 8              # Human detection range
```

## File Structure

```
resilient-mesh-network-simulator/
├── main.py                  # Main application
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── LICENSE                 # Project license
├── .gitignore             # Git ignore rules
├── assets/                # Images and demo materials
└── docs/                  # Documentation
    └── explanation.md     # Detailed system explanation
```

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Author

AURE Project Team

## Contributing

Contributions are welcome! Please feel free to submit pull requests with improvements.

## Troubleshooting

- **ImportError for matplotlib**: Run `pip install -r requirements.txt`
- **No leader elected**: The swarm is completely destroyed; airdrop new nodes
- **Slow visualization**: Reduce NUM_NODES in configuration
