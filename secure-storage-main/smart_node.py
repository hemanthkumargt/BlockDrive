import requests
import time
import os
import uuid
import json
import sys

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
# Use environment variable for public URL, fallback to localhost for local testing
if len(sys.argv) > 2 and sys.argv[2]:
    HF_SPACE_URL = sys.argv[2]
else:
    HF_SPACE_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

NODE_ID_FILE = "node_id.txt"
STORAGE_DIR = "node_storage"

# Load or generate persistent Node ID
if len(sys.argv) > 1 and sys.argv[1]:
    NODE_ID = sys.argv[1]
elif os.path.exists(NODE_ID_FILE):
    with open(NODE_ID_FILE, "r") as f:
        NODE_ID = f.read().strip()
else:
    NODE_ID = f"node-{uuid.uuid4().hex[:8]}"
    with open(NODE_ID_FILE, "w") as f:
        f.write(NODE_ID)

if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

print(f"🚀 Starting BlockDrive Storage Node (Relay Mode)")
print(f"🆔 Node ID: {NODE_ID}")
print(f"📂 Storage: {os.path.abspath(STORAGE_DIR)}")
print(f"🔗 Connecting to: {HF_SPACE_URL}")

# ─────────────────────────────────────────────
# DISTRIBUTED ALGORITHMS
# ─────────────────────────────────────────────
# Lamport Logical Clock: Ensures event ordering in a distributed system.
lamport_clock = 0

def increment_clock(received_clock=None):
    """
    Update Lamport Logical Clock:
    - Before each operation: lamport_clock += 1
    - On receiving a message: lamport_clock = max(lamport_clock, received_clock) + 1
    """
    global lamport_clock
    if received_clock is not None:
        lamport_clock = max(lamport_clock, received_clock) + 1
    else:
        lamport_clock += 1
    return lamport_clock

# Ricart-Agrawala Mutual Exclusion: Ensures exclusive access to storage/blockchain.
def request_critical_section():
    """Ricart-Agrawala: Request access to critical section"""
    increment_clock()
    print(f"🕒 [LC:{lamport_clock}] REQUESTING Critical Section...")
    try:
        resp = requests.post(f"{HF_SPACE_URL}/api/request_cs", json={
            "node_id": NODE_ID,
            "timestamp": lamport_clock
        }, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            increment_clock(data.get("lamport"))
            return True
    except Exception as e:
        print(f"[-] CS Request failed: {e}")
    return False

def check_cs_status():
    """Check if we have enough replies to enter CS"""
    try:
        resp = requests.get(f"{HF_SPACE_URL}/api/status", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            increment_clock(data.get("lamport_clock"))
            node_state = data.get("node_states", {}).get(NODE_ID, {})
            replies = node_state.get("replies", 0)
            
            # In Ricart-Agrawala, a node enters CS when it receives replies from ALL other nodes.
            # Dynamic scaling: require replies from all currently active nodes (up to 5 for lab).
            total_active_nodes = len(data.get("nodes", []))
            required_replies = max(1, total_active_nodes)
            return replies >= required_replies
    except Exception as e:
        print(f"[-] CS Status check failed: {e}")
    return False

def reply_to_requests():
    """Ricart-Agrawala: Automatically reply to other nodes' requests if we are idle"""
    try:
        resp = requests.get(f"{HF_SPACE_URL}/api/status", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            increment_clock(data.get("lamport_clock"))
            for other_node, state in data.get("node_states", {}).items():
                if other_node != NODE_ID and state.get("requesting"):
                    # For this simulation, nodes automatically reply to others to allow progression.
                    # In a full RA, we would check if our timestamp is lower.
                    requests.post(f"{HF_SPACE_URL}/api/reply_cs", json={
                        "from_node": NODE_ID,
                        "target_node": other_node,
                        "timestamp": lamport_clock
                    }, timeout=5)
    except:
        pass

def release_critical_section():
    """Ricart-Agrawala: Release access to critical section"""
    increment_clock()
    print(f"🕒 [LC:{lamport_clock}] RELEASING Critical Section...")
    try:
        resp = requests.post(f"{HF_SPACE_URL}/api/release_cs", json={
            "node_id": NODE_ID,
            "timestamp": lamport_clock
        }, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            increment_clock(data.get("lamport"))
            return True
    except Exception as e:
        print(f"[-] CS Release failed: {e}")
    return False

def register():
    try:
        # We register with port 0 to indicate "Relay Mode" (or just standard)
        payload = {"ip": NODE_ID, "port": 0}
        resp = requests.post(f"{HF_SPACE_URL}/api/register", json=payload, timeout=10)
        if resp.status_code == 200:
            print(f"[+] Heartbeat sent. Online.")
        else:
            print(f"[-] Register failed: {resp.text}")
    except Exception as e:
        print(f"[-] Connection failed: {e}")

def process_tasks():
    # Ricart-Agrawala: Reply to others before starting our work
    reply_to_requests()
    
    try:
        resp = requests.get(f"{HF_SPACE_URL}/api/poll_tasks", params={"node_id": NODE_ID}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            tasks = data.get("tasks", [])
            
            for task in tasks:
                if task.get("type") == "store":
                    chunk_name = task.get("chunk_name")
                    
                    # ── RICART-AGRAWALA WORKFLOW ──
                    # 1. REQUEST CS
                    request_critical_section()
                    
                    # 2. WAIT FOR REPLIES
                    print("⌛ Waiting for replies to enter critical section...")
                    while not check_cs_status():
                        reply_to_requests() # Still reply while waiting
                        time.sleep(1)
                    
                    # 3. ENTER CS
                    print("🔓 Entering Critical Section")
                    
                    print(f"📥 Downloading chunk: {chunk_name}...")
                    # Download from Relay
                    r_file = requests.get(f"{HF_SPACE_URL}/api/download_relay/{chunk_name}", timeout=30)
                    if r_file.status_code == 200:
                        path = os.path.join(STORAGE_DIR, chunk_name)
                        with open(path, "wb") as f:
                            f.write(r_file.content)
                        
                        print(f"✅ Stored {chunk_name} ({len(r_file.content)} bytes)")
                        
                        # Confirm
                        requests.post(f"{HF_SPACE_URL}/api/confirm_task", params={
                            "node_id": NODE_ID,
                            "chunk_name": chunk_name,
                            "status": "success"
                        })
                    else:
                        print(f"❌ Failed to download {chunk_name}: {r_file.status_code}")
                    
                    # 4. RELEASE CS
                    release_critical_section()
                
                elif task.get("type") == "retrieve":
                    chunk_name = task.get("chunk_name")
                    print(f"📤 Serving request for chunk: {chunk_name}...")
                    
                    path = os.path.join(STORAGE_DIR, chunk_name)
                    if os.path.exists(path):
                        try:
                            with open(path, "rb") as f:
                                files = {"file": (chunk_name, f)}
                                data = {"chunk_name": chunk_name}
                                # Push to Relay
                                r = requests.post(f"{HF_SPACE_URL}/api/relay_push", 
                                                files=files, data=data, timeout=60)
                                if r.status_code == 200:
                                    print(f"✅ Pushed {chunk_name} to relay")
                                else:
                                    print(f"❌ Failed to push {chunk_name}: {r.text}")
                        except Exception as e:
                            print(f"❌ Error pushing {chunk_name}: {e}")
                    else:
                        print(f"❌ Requested chunk not found: {chunk_name}")
    except Exception as e:
        print(f"[-] Error polling: {e}")

# ─────────────────────────────────────────────
# BLOCKCHAIN SYNC (Decentralization)
# ─────────────────────────────────────────────
import zlib

LOCAL_CHAIN_FILE = "local_chain.bin"

def load_local_chain():
    """Load our local chain copy (binary or legacy JSON)."""
    if os.path.exists(LOCAL_CHAIN_FILE):
        try:
            with open(LOCAL_CHAIN_FILE, "rb") as f:
                raw = zlib.decompress(f.read()).decode('utf-8')
                return json.loads(raw).get("chain", [])
        except:
            pass
    # Try legacy JSON
    if os.path.exists("local_chain.json"):
        try:
            with open("local_chain.json", "r") as f:
                return json.load(f).get("chain", [])
        except:
            pass
    return []

def sync_blockchain():
    """Sync blockchain with backend. If our local chain is longer, push it back."""
    try:
        r = requests.get(f"{HF_SPACE_URL}/api/chain", timeout=10)
        if r.status_code == 200:
            data = r.json()
            server_chain = data.get("chain", [])
            local_chain = load_local_chain()
            
            # If our local chain is LONGER → push it to recover backend
            if len(local_chain) > len(server_chain):
                print(f"🔄 Backend has {len(server_chain)} blocks, we have {len(local_chain)}. Pushing recovery...")
                try:
                    resp = requests.post(
                        f"{HF_SPACE_URL}/api/sync_chain",
                        json={"chain": local_chain},
                        timeout=30
                    )
                    if resp.status_code == 200:
                        result = resp.json()
                        if result.get("status") == "adopted":
                            print(f"✅ Backend recovered! Now has {result.get('new_length')} blocks")
                        else:
                            print(f"ℹ️ Backend rejected: {result.get('reason')}")
                except Exception as e:
                    print(f"[-] Recovery push failed: {e}")
                return
            
            # Normal sync: server chain is longer or equal → save locally
            v = requests.get(f"{HF_SPACE_URL}/api/validate", timeout=10)
            if v.status_code == 200:
                result = v.json()
                if result.get("valid"):
                    raw = json.dumps({"chain": server_chain, "synced_at": time.time()}).encode('utf-8')
                    with open(LOCAL_CHAIN_FILE, "wb") as f:
                        f.write(zlib.compress(raw, level=9))
                    if os.path.exists("local_chain.json"):
                        os.remove("local_chain.json")
                    print(f"🔗 Chain synced & verified ({len(server_chain)} blocks) [binary]")
                else:
                    print(f"⚠️ WARNING: Backend chain TAMPERED at block {result.get('tampered_at')}!")
    except Exception as e:
        print(f"[-] Chain sync failed: {e}")

# ─────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────
SYNC_INTERVAL = 12  # Sync chain every 12 polls (~60s)

def main():
    poll_count = 0
    while True:
        register()
        process_tasks()
        
        # Sync blockchain periodically
        poll_count += 1
        if poll_count % SYNC_INTERVAL == 0:
            sync_blockchain()
        
        time.sleep(5) # Poll every 5 seconds

if __name__ == "__main__":
    main()