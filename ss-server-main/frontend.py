import streamlit as st
import requests
import socket
import hashlib
import os
import tempfile
import time
from cryptography.fernet import Fernet
import json
from blockchain import Blockchain

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
CHUNK_SIZE = 1024 * 1024  # 1 MB
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Sidebar for controls and configuration
with st.sidebar:
    st.header("⚙️ System Config")
    # Dynamic URL detection for Hugging Face or Localhost
    default_url = os.environ.get("BACKEND_URL")
    if not default_url:
        default_url = "https://hkrox-blockdrive.hf.space" # User's current Space
    
    api_base = st.text_input("Hub API URL", default_url, help="The address of the central hub. Change this if you deploy to a new URL.")
    API_URL = f"{api_base}/api"
    
    st.divider()
    
    st.header("👤 User Identity")
    node_id_input = st.text_input("Your ID", "client-1", help="How you are identified on the network.")
    if st.button("🔄 Sync Ledger", help="Force your local view to match the global blockchain."):
        requests.get(f"{API_URL}/validate")
        st.success("Ledger Syncing...")

st.set_page_config(
    page_title="BlockDrive",
    page_icon="⛓️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern 2026 Dark Theme (Deep Navy & Electric Cyan)
st.markdown("""
<style>
    /* 2026 Modern Theme */
    :root {
        --deep-navy: #0A192F;
        --electric-cyan: #64FFDA;
        --slate: #8892B0;
        --light-slate: #CCD6F6;
        --white: #E6F1FF;
        --glass-bg: rgba(10, 25, 47, 0.7);
    }

    .stApp {
        background-color: var(--deep-navy);
        color: var(--light-slate);
    }

    /* Modern Glassmorphism Panels */
    .status-panel {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(100, 255, 218, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        transition: transform 0.3s ease;
    }
    .status-panel:hover {
        transform: translateY(-5px);
        border-color: var(--electric-cyan);
    }

    .block-card {
        background: rgba(17, 34, 64, 0.8);
        border: 1px solid rgba(100, 255, 218, 0.2);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
        border-left: 4px solid var(--electric-cyan);
    }

    .log-panel {
        background: #020C1B;
        border: 1px solid rgba(100, 255, 218, 0.1);
        border-radius: 12px;
        padding: 15px;
        font-family: 'Fira Code', 'Courier New', monospace;
        height: 350px;
        overflow-y: auto;
        color: var(--electric-cyan);
    }

    /* Modern Metrics */
    div[data-testid="stMetricValue"] {
        color: var(--electric-cyan) !important;
        font-family: 'Orbitron', sans-serif;
    }
    
    /* Buttons & Inputs */
    .stButton>button {
        background: transparent;
        color: var(--electric-cyan);
        border: 1px solid var(--electric-cyan);
        border-radius: 5px;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: rgba(100, 255, 218, 0.1);
        box-shadow: 0 0 15px rgba(100, 255, 218, 0.3);
    }

    /* Typography */
    h1, h2, h3 {
        color: var(--white) !important;
        font-weight: 700 !important;
    }
    .cyan-text { color: var(--electric-cyan); }
    .text-muted { color: var(--slate); }

    /* File List Card */
    .file-card {
        background: rgba(17, 34, 64, 0.5);
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 8px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_system_status():
    try:
        resp = requests.get(f"{API_URL}/status", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return {"lamport_clock": 0, "nodes": [], "node_states": {}, "logs": []}

def get_nodes():
    return get_system_status()["nodes"]

# ... (rest of helpers stay same)

def http_relay_upload(chunk_data, chunk_name):
    try:
        files = {"file": (chunk_name, chunk_data)}
        data = {"chunk_name": chunk_name}
        resp = requests.post(f"{API_URL}/relay_upload", files=files, data=data, timeout=30)
        
        if resp.status_code == 200:
            res = resp.json()
            if res.get("status") == "queued":
                # Returns list of target nodes (replication)
                return True, res.get("target_nodes", []), ""
            else:
                return False, [], res.get("message")
        return False, [], f"HTTP {resp.status_code}"
    except Exception as e:
        return False, [], str(e)

def http_relay_download(node_info, chunk_name):
    """Request chunk from node(s). Supports single node or list of replicas."""
    try:
        # Handle both list (replicated) and string (legacy) formats
        if isinstance(node_info, list):
            node_list = node_info
        else:
            node_list = [node_info]
        
        # Request retrieval from ALL replica nodes (first responder wins)
        for node_id in node_list:
            clean_id = node_id.split(":")[0] if ":" in node_id else node_id
            payload = {"chunk_name": chunk_name, "node_id": clean_id}
            try:
                requests.post(f"{API_URL}/request_retrieval", json=payload, timeout=5)
            except:
                pass
        
        # Poll for file (up to 30s)
        for _ in range(30):
            r = requests.get(f"{API_URL}/download_relay/{chunk_name}", timeout=5)
            if r.status_code == 200:
                return r.content
            time.sleep(1)
            
        return None
    except Exception as e:
        return None

def build_merkle_tree(chunks):
    """Build Merkle Root from list of chunk byte arrays"""
    hashes = [hashlib.sha256(c).hexdigest() for c in chunks]
    if not hashes: return ""
    while len(hashes) > 1:
        temp = []
        for i in range(0, len(hashes), 2):
            n1 = hashes[i]
            n2 = hashes[i + 1] if i + 1 < len(hashes) else n1
            combined = hashlib.sha256((n1 + n2).encode()).hexdigest()
            temp.append(combined)
        hashes = temp
    return hashes[0]

# ─────────────────────────────────────────────
# UI LAYOUT: DASHBOARD
# ─────────────────────────────────────────────

st.title("� Distributed Storage Hub")
st.markdown("##### Secure Multi-Node Storage & Immutable Ledger")

# Main Dashboard Layout
top_col1, top_col2, top_col3 = st.columns(3)
status_data = get_system_status()

with top_col1:
    st.metric("⏳ Network Time", status_data.get("lamport_clock", 0), help="Global logical counter used for ordering events across laptops.")
with top_col2:
    st.metric("🖥️ Storage Nodes", len(status_data.get("nodes", [])), help="Number of active laptops storing your data.")
with top_col3:
    chain_len = 0
    try:
        r = requests.get(f"{API_URL}/chain")
        if r.status_code == 200: chain_len = r.json()['length']
    except: pass
    st.metric("⛓️ Ledger Height", chain_len, help="The number of blocks in the blockchain.")

# Panels
left_panel, right_panel = st.columns([1, 1.5])

with left_panel:
    st.subheader("🖥️ Node Status")
    nodes = status_data.get("nodes", [])
    node_states = status_data.get("node_states", {})
    
    if not nodes:
        st.info("No active storage nodes detected.")
    
    for node in nodes:
        state = node_states.get(node, {"requesting": False, "replies": 0})
        is_requesting = state.get("requesting", False)
        replies = state.get("replies", 0)
        
        status_color = "var(--electric-cyan)" if not is_requesting else "#FFD700"
        status_text = f"Requesting CS ({replies}/3 replies)" if is_requesting else "Idle"
        
        st.markdown(f"""
        <div class="status-panel">
            <b style="color:var(--white); font-size: 1.1rem;">{node}</b><br>
            <span style="color:{status_color}">● Status: {status_text}</span><br>
            <small class="text-muted">Role: Distributed Validator</small>
        </div>
        """, unsafe_allow_html=True)

with right_panel:
    st.subheader("⛓️ File Ledger & Explorer")
    try:
        r_chain = requests.get(f"{API_URL}/chain")
        if r_chain.status_code == 200:
            chain_data = r_chain.json()
            # Get unique files from the chain
            files = {}
            for block in chain_data.get("chain", []):
                for tx in block.get("transactions", []):
                    files[tx['file_hash']] = tx
            
            if not files:
                st.info("No files recorded on the ledger yet.")
            else:
                for f_hash, f_meta in list(files.items())[::-1]: # Latest first
                    with st.container():
                        st.markdown(f"""
                        <div class="file-card">
                            <span style="color:var(--electric-cyan); font-weight:600;">📄 {f_meta['file_name']}</span><br>
                            <small class="text-muted">Owner: {f_meta['owner']} | Hash: {f_hash[:20]}...</small>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"Details for {f_meta['file_name'][:15]}...", key=f_hash):
                            st.session_state['selected_file'] = f_meta
                            st.rerun()

    except Exception as e:
        st.error(f"Failed to load chain: {e}")

# If a file is selected, show its credentials in a nice modal-like view
if 'selected_file' in st.session_state:
    f = st.session_state['selected_file']
    st.markdown("---")
    st.subheader(f"🔐 Credentials for {f['file_name']}")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Merkle Root (File ID)", f['file_hash'], disabled=True)
    with c2:
        st.info("Note: The decryption key was generated at upload. If you don't have it, use the one provided during the upload process.")
    if st.button("Close Details"):
        del st.session_state['selected_file']
        st.rerun()

# Bottom Panel: Event Logs
st.subheader("� Real-time Distributed Events")
logs = status_data.get("logs", [])
log_content = ""
for entry in logs[::-1]: # Latest logs at top
    log_content += f"[{entry['timestamp']}] [LC:{entry['lamport']}] {entry['event']}\n"

st.markdown(f"""
<div class="log-panel">
    <pre style="color: #3fb950; background: transparent; border: none;">{log_content}</pre>
</div>
""", unsafe_allow_html=True)

st.divider()

# Existing Tabs (Upload/Download) moved below
tab1, tab2 = st.tabs(["📤 Upload File", "📥 Download File"])

# ── UPLOAD TAB ──
with tab1:
    st.header("Upload File")
    uploaded_file = st.file_uploader("Choose a file", type=None)
    owner_name = st.text_input("Owner Name", "Anonymous")
    
    if st.button("🚀 Encrypt & Upload"):
        if uploaded_file is None:
            st.error("Please select a file first.")
        else:
            file_bytes = uploaded_file.read()
            original_name = uploaded_file.name
            
            if len(file_bytes) > MAX_FILE_SIZE:
                 st.error(f"File too large. Max: {MAX_FILE_SIZE // (1024*1024)} MB")
            else:
                status = st.empty()
                status.info("🔐 Encrypting...")
                
                # 1. Encrypt
                key = Fernet.generate_key()
                fernet = Fernet(key)
                encrypted = fernet.encrypt(file_bytes)
                
                # 2. Shard (always at least 2 chunks)
                status.info("✂️ Sharding...")
                # Ensure minimum 2 chunks for distribution
                effective_chunk_size = min(CHUNK_SIZE, max(1, len(encrypted) // 2))
                chunks = [encrypted[i:i + effective_chunk_size] for i in range(0, len(encrypted), effective_chunk_size)]
                
                # 3. Relay Upload
                status.info(f"📡 Uploading {len(chunks)} chunks to Relay...")
                location_map = {}
                failed = []
                progress_bar = st.progress(0)
                
                for i, chunk_data in enumerate(chunks):
                    chunk_name = f"{original_name}.part_{i}"
                    success, target_nodes, error_msg = http_relay_upload(chunk_data, chunk_name)
                    
                    if success:
                        location_map[chunk_name] = target_nodes  # Store list of replicas
                    else:
                        failed.append(f"Chunk {i}: {error_msg}")
                    
                    progress_bar.progress((i + 1) / len(chunks))

                if not location_map:
                     st.error(f"❌ Upload to Relay failed. Last error: {error_msg if 'error_msg' in locals() else 'Unknown'}")
                     if failed:
                         with st.expander("See error details"):
                             for f in failed:
                                 st.write(f)
                else:
                    status.info("⛓️ Recording on blockchain...")
                    merkle_root = build_merkle_tree(chunks)
                    
                    payload = {
                        "owner": owner_name,
                        "file_hash": merkle_root,
                        "file_name": original_name,
                        "locations": location_map,
                        "node_id": node_id_input,
                        "timestamp": status_data.get("lamport_clock", 0)
                    }
                    
                    try:
                        r = requests.post(f"{API_URL}/add_transaction", json=payload)
                        if r.status_code == 201:
                            status.success("✅ File Uploaded & Transaction Recorded! Dashboard will refresh in 5 seconds.")
                            st.markdown(f"""
                            <div class="status-panel" style="background: rgba(100, 255, 218, 0.05); border-color: var(--electric-cyan);">
                                <h4 style="color: var(--electric-cyan);">✅ Upload Successful</h4>
                                <p style="color: var(--white);">Distributed consensus reached. File sharded and replicated across nodes.</p>
                                <div style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 5px; margin-top: 10px;">
                                    <p><b>File ID:</b> <code style="color: var(--electric-cyan);">{merkle_root}</code></p>
                                    <p><b>Master Key:</b> <code style="color: #FF79C6;">{key.decode()}</code></p>
                                    <p><small style="color: var(--slate);">⚠️ Save this key now! It is required for decryption and is not stored on the ledger for security.</small></p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if failed:
                                st.warning(f"⚠️ {len(failed)} chunks failed to upload.")
                            
                            time.sleep(5)
                            st.rerun()
                        else:
                            st.error(f"❌ Blockchain error: {r.text}")
                    except Exception as e:
                        st.error(f"❌ API connection failed: {e}")

# ── DOWNLOAD TAB ──
with tab2:
    st.header("Download File")
    
    col1, col2 = st.columns(2)
    with col1:
        dl_id = st.text_input("File ID (Merkle Root)")
    with col2:
        dl_key = st.text_input("Decryption Key")
        
    if st.button("📥 Fetch & Decrypt"):
        if not dl_id or not dl_key:
            st.error("Please enter both File ID and Key.")
        else:
            status = st.empty()
            status.info("🔍 Looking up file on blockchain...")
            
            try:
                # 1. Lookup
                r = requests.get(f"{API_URL}/get_file/{dl_id}")
                if r.status_code != 200:
                    st.error("❌ File not found on blockchain.")
                else:
                    meta = r.json()
                    locations = meta['locations']
                    fname = meta['file_name']
                    
                    status.info(f"📡 Found {len(locations)} chunks. Fetching...")
                    
                    # 2. Sort chunks
                    sorted_chunks = sorted(locations.keys(), key=lambda x: int(x.split('_')[-1]))
                    full_enc = b""
                    
                    progress = st.progress(0)
                    
                    # 2a. Request ALL retrievals UPFRONT (so node gets all tasks at once)
                    status.info(f"📡 Requesting {len(sorted_chunks)} chunks from nodes...")
                    for chunk_name in sorted_chunks:
                        node_info = locations[chunk_name]
                        node_list = node_info if isinstance(node_info, list) else [node_info]
                        for node_id in node_list:
                            clean_id = node_id.split(":")[0] if ":" in node_id else node_id
                            try:
                                requests.post(f"{API_URL}/request_retrieval",
                                    json={"chunk_name": chunk_name, "node_id": clean_id}, timeout=5)
                            except:
                                pass
                    
                    # 2b. Now poll for each chunk (node is already pushing them all)
                    for i, chunk_name in enumerate(sorted_chunks):
                        status.info(f"📥 Downloading chunk {i+1}/{len(sorted_chunks)}...")
                        data = None
                        # Poll for up to 60s with retries
                        for _ in range(60):
                            try:
                                r = requests.get(f"{API_URL}/download_relay/{chunk_name}", timeout=5)
                                if r.status_code == 200:
                                    data = r.content
                                    break
                            except:
                                pass
                            time.sleep(1)
                        
                        if not data:
                             st.error(f"❌ Failed to fetch chunk {chunk_name}")
                             full_enc = None
                             break
                        full_enc += data
                        progress.progress((i + 1) / len(sorted_chunks))
                        
                    if full_enc:
                        # 3. Decrypt
                        status.info("🔓 Decrypting...")
                        try:
                            fernet = Fernet(dl_key.encode())
                            decrypted = fernet.decrypt(full_enc)
                            
                            st.download_button(
                                label=f"💾 Download {fname}",
                                data=decrypted,
                                file_name=fname,
                                mime="application/octet-stream"
                            )
                            status.success("✅ File ready for download!")
                        except:
                            st.error("❌ Decryption failed! Invalid key?")
            except Exception as e:
                st.error(f"❌ Error: {e}")


