import random
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import heapq
import tkinter as tk
from tkinter import ttk, simpledialog

# ===============================
# SIMULATION SETTINGS
# ===============================
NUM_NODES = 200
MAP_SIZE = 100
DISASTER_POS = (50, 50)

DESTROY_RADIUS = 12
AFFECTED_RADIUS = 25
COMM_RADIUS = 15
SENSE_RANGE = 8

# Global State
safe_servers = []
leader = None
server_paths = {}
humans = []
nodes = []
active_signals = []  
server_data_log = [] 

# ===============================
# CLASSES 
# ===============================
class SafeServer:
    def __init__(self, x, y, id):
        self.position = (x, y)
        self.id = id
        self.received_data = []

class Human:
    def __init__(self, h_id):
        self.id = h_id
        self.group_size = random.randint(1, 20)
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0, AFFECTED_RADIUS) 
        self.position = (
            DISASTER_POS[0] + dist * math.cos(angle),
            DISASTER_POS[1] + dist * math.sin(angle)
        )
        self.detected = False
        self.rescued = False
        self.rescue_path = []
        self.detected_by = None  

class Node:
    def __init__(self, node_id, x=None, y=None):
        self.id = node_id
        if x is not None and y is not None:
            self.position = (x, y)
            self.just_dropped = True
        else:
            self.position = (random.uniform(0, MAP_SIZE), random.uniform(0, MAP_SIZE))
            self.just_dropped = False
            
        self.battery = random.uniform(30, 100)
        self.temperature = random.uniform(20, 80)
        self.distance_to_disaster = math.dist(self.position, DISASTER_POS)
        self.alive = self.distance_to_disaster > DESTROY_RADIUS
        self.is_leader = False
        self.score = 0
        self.received_data = [] 
        self.forwarding_queue = [] 

    def compute_score(self, fallback=False):
        if not self.alive: return 0
        battery_weight, distance_weight, temp_weight = 0.3, 0.5, 0.2
        norm_battery = self.battery / 100
        norm_temp = 1 - (self.temperature / 100)

        if not fallback:
            if not (DESTROY_RADIUS < self.distance_to_disaster <= AFFECTED_RADIUS): return 0
            norm_distance = 1 - (self.distance_to_disaster / AFFECTED_RADIUS)
        else:
            if self.distance_to_disaster <= AFFECTED_RADIUS: return 0
            max_dist = math.dist((0, 0), (MAP_SIZE, MAP_SIZE))
            norm_distance = 1 - (self.distance_to_disaster / max_dist)

        self.score = round((battery_weight * norm_battery + distance_weight * norm_distance + temp_weight * norm_temp), 4)
        return self.score

class Signal:
    """Represents a data packet sent from a detecting node to the leader"""
    def __init__(self, sender_id, human_id, count, pos, path, current_hop=0):
        self.sender_id = sender_id
        self.human_id = human_id
        self.human_count = count
        self.human_pos = pos
        self.path = path 
        self.current_hop = current_hop 
        self.human_distance_from_disaster = math.dist(pos, DISASTER_POS)

    def next_hop(self):
        """Move to next node in path"""
        if self.current_hop < len(self.path) - 1:
            self.current_hop += 1
            return True
        return False

    def get_current_node(self):
        """Get current node ID in the path"""
        if self.current_hop < len(self.path):
            return self.path[self.current_hop]
        return None

    def format_for_server(self, leader_node):
        """Format the data for server transmission"""
        return {
            'leader_id': leader_node.id,
            'leader_battery': round(leader_node.battery, 2),
            'leader_position': leader_node.position,
            'human_id': self.human_id,
            'human_count': self.human_count,
            'human_coordinates': self.human_pos,
            'human_distance_from_disaster': round(self.human_distance_from_disaster, 2),
            'detected_by_node': self.sender_id,
            'timestamp': len(server_data_log) 
        }

# ===============================
# ROUTING & LOGIC
# ===============================
def get_shortest_path(start_node, target_pos):
    distances = {n.id: float('inf') for n in nodes if n.alive}
    previous = {n.id: None for n in nodes if n.alive}
    if start_node.id not in distances: return None
    distances[start_node.id] = 0
    pq = [(0, start_node.id)]
    
    while pq:
        current_dist, current_id = heapq.heappop(pq)
        if current_dist > distances[current_id]: continue
        curr_node = nodes[current_id]
        if math.dist(curr_node.position, target_pos) <= COMM_RADIUS:
            path, temp = [], current_id
            while temp is not None:
                path.append(temp)
                temp = previous[temp]
            return path[::-1]

        for neighbor in nodes:
            if neighbor.alive and neighbor.id != current_id:
                d = math.dist(curr_node.position, neighbor.position)
                if d <= COMM_RADIUS:
                    new_dist = current_dist + d
                    if new_dist < distances[neighbor.id]:
                        distances[neighbor.id] = new_dist
                        previous[neighbor.id] = current_id
                        heapq.heappush(pq, (new_dist, neighbor.id))
    return None

def get_node_to_node_path(start_id, end_id):
    if start_id == end_id: return [start_id]
    distances = {n.id: float('inf') for n in nodes if n.alive}
    previous = {n.id: None for n in nodes if n.alive}
    if start_id not in distances: return None
    distances[start_id] = 0
    pq = [(0, start_id)]

    while pq:
        curr_dist, curr_id = heapq.heappop(pq)
        if curr_id == end_id:
            path, temp = [], curr_id
            while temp is not None:
                path.append(temp)
                temp = previous[temp]
            return path[::-1]
        
        curr_node = nodes[curr_id]
        for neighbor in nodes:
            if neighbor.alive and neighbor.id != curr_id:
                d = math.dist(curr_node.position, neighbor.position)
                if d <= COMM_RADIUS:
                    new_dist = curr_dist + d
                    if new_dist < distances[neighbor.id]:
                        distances[neighbor.id] = new_dist
                        previous[neighbor.id] = curr_id
                        heapq.heappush(pq, (new_dist, neighbor.id))
    return None

def elect_leader():
    for n in nodes: n.is_leader = False
    candidates = [n for n in nodes if n.alive and DESTROY_RADIUS < n.distance_to_disaster <= AFFECTED_RADIUS]
    if not candidates: candidates = [n for n in nodes if n.alive and n.distance_to_disaster > AFFECTED_RADIUS]
    if not candidates: return None
    for n in candidates: n.compute_score(fallback=(n.distance_to_disaster > AFFECTED_RADIUS))
    chosen = max(candidates, key=lambda n: n.score)
    chosen.is_leader = True
    return chosen

def process_signals():
    global active_signals
    signals_to_remove = []
    
    for sig in active_signals:
        current_node_id = sig.get_current_node()
        
        if current_node_id is None:
            signals_to_remove.append(sig)
            continue
            
        current_node = nodes[current_node_id]
        
        # Drain battery of routing nodes slightly as they pass packets
        if current_node.alive:
            current_node.battery -= 0.5 
            if current_node.battery <= 0:
                current_node.alive = False
        
        # If this node died while forwarding, drop the packet
        if not current_node.alive:
            signals_to_remove.append(sig)
            continue
            
        if current_node.is_leader:
            human = next((h for h in humans if h.id == sig.human_id), None)
            if human and not human.rescued:
                human.detected = True
                human.detected_by = sig.sender_id
                
                server_data = sig.format_for_server(leader)
                leader.received_data.append(server_data)
                send_to_servers(server_data)
                
                print(f"Leader {leader.id} received stream: Group {sig.human_id}")
            signals_to_remove.append(sig)
        
        elif sig.next_hop():
            pass 
        else:
            signals_to_remove.append(sig)
    
    for sig in signals_to_remove:
        if sig in active_signals:
            active_signals.remove(sig)

def send_to_servers(data):
    global server_data_log
    if not leader: return
    
    server_data_log.append(data)
    for server in safe_servers:
        path = get_shortest_path(leader, server.position)
        if path:
            server.received_data.append(data)
            server_paths[server.id] = path

def update_simulation():
    global server_paths, active_signals, leader
    
    server_paths = {}
    
    # 1. Battery Drain Phase
    for n in nodes:
        if n.alive:
            n.battery -= 0.2  # Idle battery drain over time
            if n.battery <= 0:
                n.alive = False
                n.battery = 0
                print(f"*** Node {n.id} ran out of battery and DIED ***")
                if n.is_leader:
                    leader = None # Force re-election if leader dies
    
    process_signals()
    
    # Ensure we have a leader
    if not leader or not leader.alive:
        leader = elect_leader()
        if not leader: return # Entire swarm is dead
    
    # 2. Continuous Detection & Transmission Phase
    for h in humans:
        if h.rescued: continue
        if math.dist(h.position, DISASTER_POS) > AFFECTED_RADIUS: continue
        
        for n in nodes:
            if n.alive and math.dist(n.position, h.position) <= SENSE_RANGE:
                h.detected = True
                h.detected_by = n.id
                
                path_to_leader = get_node_to_node_path(n.id, leader.id)
                if path_to_leader:
                    # CONTINUOUS STREAMING: Send a new signal every tick!
                    sig = Signal(
                        n.id, h.id, h.group_size, h.position, path_to_leader, current_hop=0
                    )
                    active_signals.append(sig)
                    
                    # Drain extra battery for heavy transmitting
                    n.battery -= 2.0 
                    
                    h.rescue_path = get_shortest_path(leader, h.position)
                    print(f"Node {n.id} (Bat: {n.battery:.1f}%) CONTINUOUS STREAM -> Group {h.id}")
                break

# ===============================
# UI AND VISUALIZATION
# ===============================
class GhostSwarmApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ghost Swarm Command Center")
        self.root.geometry("1200x800")

        self.left_frame = tk.Frame(self.root, width=800, height=800)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_frame = tk.Frame(self.root, width=400, height=800, padx=10, pady=10)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.left_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        tk.Label(self.right_frame, text="COMMAND CENTER", font=("Helvetica", 16, "bold")).pack(pady=10)

        tk.Button(self.right_frame, text="List Detected Humans", command=self.cmd_list, width=25).pack(pady=5)
        tk.Button(self.right_frame, text="View Server Data", command=self.cmd_view_server_data, width=25).pack(pady=5)
        tk.Button(self.right_frame, text="Add New Human Group", command=self.cmd_add_human, width=25).pack(pady=5)

        tk.Label(self.right_frame, text="Rescue Group ID:").pack(pady=(15, 0))
        self.entry_rescue = tk.Entry(self.right_frame)
        self.entry_rescue.pack()
        tk.Button(self.right_frame, text="Execute Rescue", command=self.cmd_rescue).pack(pady=5)

        tk.Label(self.right_frame, text="Airdrop Node (X, Y):").pack(pady=(15, 0))
        drop_frame = tk.Frame(self.right_frame)
        drop_frame.pack()
        self.entry_drop_x = tk.Entry(drop_frame, width=10)
        self.entry_drop_x.pack(side=tk.LEFT, padx=2)
        self.entry_drop_y = tk.Entry(drop_frame, width=10)
        self.entry_drop_y.pack(side=tk.LEFT, padx=2)
        tk.Button(self.right_frame, text="Airdrop", command=self.cmd_airdrop).pack(pady=5)

        tk.Label(self.right_frame, text="Kill Node ID:").pack(pady=(15, 0))
        self.entry_kill = tk.Entry(self.right_frame)
        self.entry_kill.pack()
        tk.Button(self.right_frame, text="Terminate Node", command=self.cmd_kill).pack(pady=5)

        tk.Label(self.right_frame, text="Console Output:", font=("Helvetica", 12, "bold")).pack(pady=(20, 5))
        self.console = tk.Text(self.right_frame, height=20, width=40, state=tk.DISABLED, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
        self.console.pack(fill=tk.BOTH, expand=True)

        self.log(f"System Initialized. Awaiting signals...")
        self.refresh_view()
        self.auto_update()

    def auto_update(self):
        """Auto-refresh the view every 2 seconds"""
        self.refresh_view()
        self.root.after(2000, self.auto_update)

    def log(self, message):
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    def refresh_view(self):
        update_simulation()
        self.draw_plot()

    def draw_plot(self):
        self.ax.clear()
        self.ax.add_patch(plt.Circle(DISASTER_POS, AFFECTED_RADIUS, color='orange', alpha=0.1))
        self.ax.add_patch(plt.Circle(DISASTER_POS, DESTROY_RADIUS, color='red', alpha=0.2))

        # Mesh Network
        for i in range(len(nodes)):
            if not nodes[i].alive: continue
            for j in range(i + 1, len(nodes)):
                if not nodes[j].alive: continue
                if math.dist(nodes[i].position, nodes[j].position) <= COMM_RADIUS:
                    self.ax.plot([nodes[i].position[0], nodes[j].position[0]], 
                                 [nodes[i].position[1], nodes[j].position[1]], 
                                 color='gray', linewidth=0.5, alpha=0.2, zorder=0)

        # Signals
        for sig in active_signals:
            if sig.current_hop < len(sig.path):
                current_idx = sig.current_hop
                if current_idx + 1 < len(sig.path):
                    n1 = nodes[sig.path[current_idx]]
                    n2 = nodes[sig.path[current_idx + 1]]
                    self.ax.plot([n1.position[0], n2.position[0]], 
                                 [n1.position[1], n2.position[1]], 
                                 color='cyan', linewidth=2, linestyle='--', alpha=0.8, zorder=1)
                    
                    mid_x = (n1.position[0] + n2.position[0]) / 2
                    mid_y = (n1.position[1] + n2.position[1]) / 2
                    self.ax.annotate('', xy=(n2.position[0], n2.position[1]), 
                                    xytext=(n1.position[0], n1.position[1]),
                                    arrowprops=dict(arrowstyle='->', color='cyan', lw=1),
                                    alpha=0.6)

        # Nodes
        for n in nodes:
            if not n.alive:
                self.ax.scatter(n.position[0], n.position[1], c='black', marker='x', s=15, alpha=0.3, zorder=2)
            elif n.is_leader:
                self.ax.scatter(n.position[0], n.position[1], c='gold', marker='*', s=200, edgecolors='black', zorder=4)
                self.ax.text(n.position[0]+1, n.position[1]+1, f"L:{n.id}", fontsize=9, weight='bold')
            else:
                is_forwarding = any(sig.get_current_node() == n.id for sig in active_signals)
                color = 'purple' if is_forwarding else ('blue' if n.distance_to_disaster > AFFECTED_RADIUS else 'cyan')
                size = 50 if is_forwarding else 30
                self.ax.scatter(n.position[0], n.position[1], c=color, s=size, alpha=0.8 if is_forwarding else 0.6, zorder=2)
            
            if n.just_dropped:
                self.ax.scatter(n.position[0], n.position[1], facecolors='none', edgecolors='magenta', s=800, linewidth=3, zorder=5)
                n.just_dropped = False

        # Humans
        for h in humans:
            if math.dist(h.position, DISASTER_POS) > AFFECTED_RADIUS: continue
            h_color = 'green' if h.rescued else ('red' if h.detected else 'gray')
            self.ax.scatter(h.position[0], h.position[1], marker='P', c=h_color, s=60, edgecolors='black', zorder=3)
            self.ax.text(h.position[0] + 1.5, h.position[1] + 1.5, f"{h.id} [{h.group_size}]", fontsize=9, weight='bold', color='black')
            
            if h.detected and h.rescue_path and not h.rescued:
                px = [nodes[i].position[0] for i in h.rescue_path] + [h.position[0]]
                py = [nodes[i].position[1] for i in h.rescue_path] + [h.position[1]]
                self.ax.plot(px, py, color='red', linewidth=2, alpha=0.7, zorder=1)

        # Servers
        for s in safe_servers:
            self.ax.scatter(s.position[0], s.position[1], marker='s', s=300, c='darkgreen', zorder=3)
            self.ax.text(s.position[0]+2, s.position[1]+2, f"SERVER {s.id}", weight='bold')
            if s.id in server_paths:
                path = server_paths[s.id]
                px = [nodes[i].position[0] for i in path] + [s.position[0]]
                py = [nodes[i].position[1] for i in path] + [s.position[1]]
                self.ax.plot(px, py, color='orange', linewidth=3, alpha=0.9, zorder=1)

        # HUD
        alive_count = sum(1 for n in nodes if n.alive)
        leader_info = f"L: {leader.id} (Bat: {leader.battery:.0f}%)" if leader else "SWARM OFFLINE"
        signals_info = f"Active Signals: {len(active_signals)}"
        server_data_count = sum(len(s.received_data) for s in safe_servers)
        
        hud_text = f"--- SWARM HUD ---\nNodes Alive: {alive_count}/{len(nodes)}\nLeader: {leader_info}\n{signals_info}\nServer Data Packets: {server_data_count}"
        self.ax.text(0.02, 0.98, hud_text, transform=self.ax.transAxes, fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9), zorder=5)

        total_waiting = sum(h.group_size for h in humans if h.detected and not h.rescued)
        total_rescued = sum(h.group_size for h in humans if h.rescued)
        self.ax.set_title(f"GHOST SWARM: {total_waiting} Waiting | {total_rescued} Rescued")
        self.ax.set_xlim(0, MAP_SIZE); self.ax.set_ylim(0, MAP_SIZE)
        self.ax.grid(True, alpha=0.2)
        self.canvas.draw()

    def cmd_add_human(self):
        new_human = Human(len(humans))
        humans.append(new_human)
        self.log(f"Group {new_human.id} ({new_human.group_size} people) added.")
        self.refresh_view()

    def cmd_list(self):
        detected = [h for h in humans if h.detected and not h.rescued]
        if not detected:
            self.log("No data packets received by leader.")
        else:
            self.log("--- LEADER RECEIVED DATA ---")
            for h in detected:
                detector = f" (detected by Node {h.detected_by})" if h.detected_by is not None else ""
                self.log(f"Human ID: {h.id} | Size: {h.group_size} | Loc: ({h.position[0]:.1f}, {h.position[1]:.1f}){detector}")
            
            if leader and leader.received_data:
                self.log("\n--- FORMATTED DATA READY FOR SERVERS ---")
                for data in leader.received_data[-5:]: 
                    self.log(f"Data: {data}")
            self.log("----------------------------")

    def cmd_view_server_data(self):
        total_packets = sum(len(s.received_data) for s in safe_servers)
        if total_packets == 0:
            self.log("No data has been sent to servers yet.")
        else:
            self.log("--- SERVER DATA LOGS ---")
            for s in safe_servers:
                if s.received_data:
                    self.log(f"\nServer {s.id} (at {s.position[0]:.1f}, {s.position[1]:.1f}):")
                    for data in s.received_data[-3:]:
                        self.log(f"  • Leader {data['leader_id']} (Bat: {data['leader_battery']}%) | "
                               f"Human {data['human_id']}: {data['human_count']} people | "
                               f"Dist from disaster: {data['human_distance_from_disaster']:.1f}m")
            self.log("-----------------------")

    def cmd_rescue(self):
        try:
            target_id = int(self.entry_rescue.get())
            self.entry_rescue.delete(0, tk.END)
            target = next((h for h in humans if h.id == target_id), None)
            if target is None: self.log(f"Error: Group {target_id} not found.")
            elif target.rescued: self.log(f"Group {target_id} already rescued.")
            elif not target.detected: self.log(f"Leader has no signal for Group {target_id}.")
            else:
                target.rescued = True
                self.log(f"SUCCESS: Evacuated Group {target_id} ({target.group_size} people).")
                self.refresh_view()
        except ValueError: self.log("Enter a valid ID number.")

    def cmd_airdrop(self):
        try:
            x, y = float(self.entry_drop_x.get()), float(self.entry_drop_y.get())
            self.entry_drop_x.delete(0, tk.END); self.entry_drop_y.delete(0, tk.END)
            if 0 <= x <= MAP_SIZE and 0 <= y <= MAP_SIZE:
                nodes.append(Node(len(nodes), x=x, y=y))
                self.log(f"Airdropped Node {len(nodes)-1} at ({x}, {y}).")
                global leader
                if leader is None: leader = elect_leader()
                self.refresh_view()
            else: self.log("Coordinates out of bounds.")
        except ValueError: self.log("Enter valid coordinates.")

    def cmd_kill(self):
        try:
            target_id = int(self.entry_kill.get())
            self.entry_kill.delete(0, tk.END)
            target = next(n for n in nodes if n.id == target_id)
            target.alive = False
            self.log(f"Node {target_id} terminated.")
            global leader
            if target.is_leader:
                self.log("Leader lost! Re-electing...")
                leader = elect_leader()
            self.refresh_view()
        except Exception: self.log("Invalid Node ID.")

# ===============================
# APP BOOTSTRAP
# ===============================
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    num_servers = simpledialog.askinteger("Server Setup", "Enter number of safe servers to deploy:", minvalue=1, initialvalue=3)
    if not num_servers: num_servers = 3 
    
    safe_servers = []
    for i in range(num_servers):
        x = random.choice([random.uniform(5, 20), random.uniform(80, 95)])
        y = random.choice([random.uniform(5, 20), random.uniform(80, 95)])
        safe_servers.append(SafeServer(x, y, i+1))
    
    nodes = [Node(i) for i in range(NUM_NODES)]
    humans = [Human(i) for i in range(random.randint(10, 20))]
    leader = elect_leader()

    root.deiconify()  
    app = GhostSwarmApp(root)
    root.mainloop()