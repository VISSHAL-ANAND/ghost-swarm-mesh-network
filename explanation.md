# Resilient Mesh Network Simulator - Technical Explanation

## System Overview

The Resilient Mesh Network Simulator models a disaster response system using autonomous nodes that self-organize into a mesh network to detect and coordinate rescue operations for human survivors in affected areas.

## Core Concepts

### 1. Disaster Zone Topology

The simulation operates on a 100×100 map with two critical zones:

- **Destruction Zone** (DESTROY_RADIUS = 12): Complete network failure area where all nodes are destroyed
- **Affected Zone** (AFFECTED_RADIUS = 25): Primary rescue operations area where humans are found

This creates three operational regions:
- **Dead Zone**: Within DESTROY_RADIUS (all nodes destroyed)
- **Primary Zone**: Between DESTROY_RADIUS and AFFECTED_RADIUS (ideal for detection)
- **Support Zone**: Beyond AFFECTED_RADIUS (stable nodes for routing and leader election)

### 2. Node Characteristics

Each node is an autonomous device with:

**Physical Properties:**
- Position (x, y) on the simulation map
- Battery level (0-100%, initial 30-100%)
- Temperature sensor reading (0-100°C, initial 20-80°C)

**Network Properties:**
- Node ID (unique identifier)
- Alive status (affected by destruction or battery drain)
- Leader flag (only one leader at a time)
- Forwarding queue and received data storage

**Battery Consumption:**
```
Idle drain: 0.2% per tick
Routing drain: 0.5% per routed packet
Transmission drain: 2.0% per signal generation
```

### 3. Leader Election Algorithm

The system uses a multi-criteria scoring mechanism for resilient leadership:

```
Score = (0.3 × normalized_battery) + 
         (0.5 × normalized_distance) + 
         (0.2 × normalized_temperature)
```

**Candidate Selection (Two Tiers):**

**Primary Tier:** Nodes in the affected zone (DESTROY_RADIUS < distance ≤ AFFECTED_RADIUS)
- Directly detecting humans
- Optimal position for rescue coordination

**Fallback Tier:** Stable zone nodes (distance > AFFECTED_RADIUS)
- Used if no primary candidates exist
- Higher resilience to destruction

**Normalized Metrics:**
- Battery: `battery / 100`
- Temperature: `1 - (temperature / 100)` (cooler is better)
- Distance: `1 - (distance / max_distance)` (closer is better in primary tier)

### 4. Mesh Network Connectivity

Nodes form a self-healing mesh with:
- **Communication Radius:** 15 units
- **Dynamic Connectivity:** Neighbors within COMM_RADIUS can exchange data
- **Network Graph:** Automatically updated each tick based on positions and alive status

### 5. Signal Routing

Signals represent data packets transmitted from detecting nodes to the leader:

**Routing Process:**
1. Detecting node generates Signal with target path
2. Signal hops through intermediate nodes toward leader
3. Each hop drains sender's battery by 0.5%
4. If intermediate node dies, signal is dropped
5. Leader receives signal and formats data for servers

**Pathfinding Algorithm:**
- Uses Dijkstra's algorithm with Euclidean distance
- Constraints:
  - Nodes must be alive
  - Edge distance ≤ COMM_RADIUS
  - Path must reach destination within COMM_RADIUS

**Path Types:**
- `get_shortest_path(node, position)`: Node to geographic location (for rescue planning)
- `get_node_to_node_path(start_id, end_id)`: Node to node (for signal routing)

### 6. Human Detection and Rescue

**Detection Process:**
1. Each tick, nodes check for humans within SENSE_RANGE (8 units)
2. Detected humans trigger:
   - Signal generation to leader
   - Rescue path planning from leader to human location
   - Continuous streaming (new signal each tick)

**Rescue Execution:**
1. Leader receives and aggregates detection signals
2. Data formatted with:
   - Leader ID and battery status
   - Human group ID and count
   - Precise coordinates
   - Distance from disaster center
3. Server receives formatted data
4. User executes rescue via Command Center
5. Human marked as rescued, excluded from future detection

**Continuous Streaming:**
- Detection generates new signal every simulation tick
- Ensures redundancy if packets are lost
- Heavy battery drain on detecting node (2.0% per transmission)

### 7. Data Format

**Server Data Packet Structure:**
```python
{
    'leader_id': int,                           # ID of leader node
    'leader_battery': float,                    # Current battery %
    'leader_position': (float, float),          # Leader coordinates
    'human_id': int,                            # Group identifier
    'human_count': int,                         # Number of people
    'human_coordinates': (float, float),        # Detection location
    'human_distance_from_disaster': float,      # Distance in units
    'detected_by_node': int,                    # Original detecting node
    'timestamp': int                            # Packet sequence number
}
```

## Simulation Loop

### Update Cycle (Every ~2 seconds in GUI)

```
1. Battery Drain Phase
   - All alive nodes drain 0.2% per tick
   - Node dies if battery reaches 0%
   - If leader dies, force re-election

2. Signal Processing Phase
   - Move each active signal one hop forward
   - Check if intermediate nodes are alive
   - Drain routing node battery
   - Deliver to leader if at destination
   - Drop if no path forward

3. Leader Validation Phase
   - If no leader or leader dead, elect new leader
   - Halt simulation if entire swarm is dead

4. Detection & Transmission Phase
   - For each alive node in affected zone
   - Check for nearby humans (within SENSE_RANGE)
   - If human found:
     - Create signal to leader
     - Calculate rescue path
     - Drain transmission battery
     - Generate console output

5. Visualization Update
   - Render mesh network connections
   - Draw nodes, signals, and humans
   - Update HUD with status
```

## Failure Modes and Resilience

### Node Failures

**Battery Depletion:**
- Continuous idle drain (0.2%/tick)
- Accelerated by routing (0.5%/packet)
- Accelerated by transmission (2.0%/signal)
- Dead nodes cannot route or detect

**Environmental Destruction:**
- Nodes within DESTROY_RADIUS automatically destroyed
- Dead nodes marked with 'x' on visualization

### Network Recovery

**Leader Failure:**
- System automatically detects dead leader
- Immediate re-election from remaining candidates
- If no candidates exist, swarm goes offline

**Signal Loss:**
- Intermediate node failure drops in-transit packets
- Continuous streaming generates replacement packets
- Servers maintain log of all received data

**Connectivity Loss:**
- Isolated nodes cannot reach leader
- Network partition results in signal loss
- Airdropping nodes in strategic positions restores connectivity

## User Interactions

### Command Center Controls

1. **List Detected Humans**: View all humans the leader has received data about
2. **View Server Data**: Browse data logged by safe servers
3. **Add New Human Group**: Spawn additional human group at random location
4. **Airdrop Node**: Deploy node at specified coordinates to reinforce network
5. **Rescue Group**: Execute rescue mission for detected human group
6. **Terminate Node**: Simulate node failure for testing resilience

## Performance Characteristics

### Complexity Analysis

- **Leader Election**: O(n²) where n = number of alive nodes
- **Signal Routing**: O(n × log n) per signal (Dijkstra)
- **Mesh Connectivity**: O(n²) per tick (all-pairs distance check)
- **Visualization**: O(n²) for mesh drawing + O(m) for signals (m = active signals)

### Scalability

- Recommended maximum: 200-300 nodes for real-time visualization
- Can handle 50+ active signals simultaneously
- Battery drain keeps swarm size naturally bounded over time

## Future Enhancements

Potential improvements to the system:

1. **Multi-leader coordination** for distributed decision-making
2. **Mobility simulation** with node movement patterns
3. **Network coding** for more efficient multi-hop routing
4. **Machine learning** for dynamic threshold optimization
5. **Fault injection testing** framework for reliability studies
6. **Multi-threaded simulation** engine for larger swarms
7. **Data persistence** for logging and analysis

## References

### Mesh Network Concepts
- Self-organizing networks (SON)
- Mobile Ad-Hoc Networks (MANET)
- Epidemic routing for disruption-tolerant networks

### Algorithms
- Dijkstra's shortest path algorithm
- Greedy leader election schemes
- Battery-aware routing protocols

## Author Notes

This simulator demonstrates practical applications of distributed systems principles in disaster response scenarios. The continuous streaming approach provides realistic redundancy modeling, while the battery management system adds physical constraints that drive algorithm design decisions.
