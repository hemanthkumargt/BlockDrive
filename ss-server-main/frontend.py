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
# PAGE CONFIG — Must be the FIRST Streamlit call
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="BlockDrive",
    page_icon="⛓️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
CHUNK_SIZE = 1024 * 1024  # 1 MB
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

import secrets

# Generate Cryptographic Keys for User Identity
# User Identity is handled dynamically in the sidebar block below.

with st.sidebar:
    st.header("⚙️ System Config")
    # Dynamic URL detection for Hugging Face or Localhost
    default_url = os.environ.get("BACKEND_URL")
    if not default_url:
        default_url = "http://localhost:8000" # Defaults to local hub
    
    api_base = st.text_input("Hub API URL", default_url, help="The address of the central hub. Change this if you deploy to a new URL.")
    # Sanitize the URL to remove accidental spaces or trailing slashes
    API_URL = f"{api_base.strip().rstrip('/')}/api"

    st.divider()

# ── USER IDENTITY ──
with st.sidebar:
    st.header("👤 Your Profile")
    default_user = "Member"
    username = st.text_input("Username", value=default_user, help="Enter your name.")
    
    # LOGIC: Combine Username + Hostname to ensure ID is unique even if names are same
    # This prevents 'Hemanth' on Laptop A from seeing 'Hemanth' on Laptop B's data
    unique_seed = f"{username}_{socket.gethostname()}"
    public_key = hashlib.sha256(unique_seed.encode()).hexdigest()[:16]
    
    st.markdown(f"**Your Node ID:** `{public_key}`")
    st.markdown(f"*Device ID: {socket.gethostname()}*")
    
    st.divider()
    if st.button("Sync Ledger"):
        st.info("Re-syncing with distributed network...")
        requests.get(f"{API_URL}/validate")
        st.success("Ledger Syncing...")
        st.rerun()


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

# ── HELPERS ──
# Dynamic vault names per session
UPLOAD_VAULT = f"uploads_{public_key}.json"
UNLOCKED_VAULT = f"unlocked_{public_key}.json"

def save_to_uploads(file_name, file_hash, key):
    """Save user's own uploads"""
    vault = {}
    if os.path.exists(UPLOAD_VAULT):
        try:
            with open(UPLOAD_VAULT, "r") as f: vault = json.load(f)
        except: pass
    vault[file_hash] = {"name": file_name, "key": key, "date": time.strftime("%H:%M")}
    with open(UPLOAD_VAULT, "w") as f: json.dump(vault, f)

def save_to_unlocked(file_name, file_hash, key):
    """Save files unlocked via code"""
    vault = {}
    if os.path.exists(UNLOCKED_VAULT):
        try:
            with open(UNLOCKED_VAULT, "r") as f: vault = json.load(f)
        except: pass
    vault[file_hash] = {"name": file_name, "key": key, "date": time.strftime("%H:%M")}
    with open(UNLOCKED_VAULT, "w") as f: json.dump(vault, f)

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

st.title("⛓️ Distributed Blockchain Storage")

# Main Dashboard Layout
top_col1, top_col2, top_col3 = st.columns(3)
status_data = get_system_status()

with top_col1:
    st.metric("⏳ Network Events", status_data.get("lamport_clock", 0), help="The total number of events (uploads, connections) that have occurred on the network.")
with top_col2:
    st.metric("🖥️ Online Storage Providers", len(status_data.get("nodes", [])), help="The number of computers currently connected and providing their hard drive space to the network.")
with top_col3:
    chain_len = 0
    try:
        r = requests.get(f"{API_URL}/chain")
        if r.status_code == 200: chain_len = r.json()['length']
    except: pass
    st.metric("⛓️ Blocks in Chain", chain_len, help="The total number of blocks in the blockchain. More blocks means a more secure history.")

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
        required = max(1, len(nodes))
        
        status_color = "var(--electric-cyan)" if not is_requesting else "#FFD700"
        status_text = f"Requesting CS ({replies}/{required} replies)" if is_requesting else "Idle"
        
        st.markdown(f"""
        <div class="status-panel">
            <b style="color:var(--white); font-size: 1.1rem;">{node}</b><br>
            <span style="color:{status_color}">● Status: {status_text}</span><br>
            <small class="text-muted">Role: Distributed Validator</small>
        </div>
        """, unsafe_allow_html=True)

# ── MAIN DASHBOARD ──
st.markdown("---")
# Network Files section removed. Tabs are the primary interface.

# If a file is selected, show its credentials in a nice modal-like view
if 'selected_file' in st.session_state:
    f = st.session_state['selected_file']
    vault_data = get_from_vault(f['file_hash'])
    
    st.markdown("---")
    st.subheader(f"🔐 File Credentials")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Merkle Root (File ID)", f['file_hash'], disabled=True)
    with c2:
        if vault_data:
            st.success("✨ Local Vault: Key Found!")
            st.text_input("Master Key (Auto-filled)", vault_data['key'], disabled=True)
            
            

        else:
            st.warning("Key not in local vault")
            
            
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Close Details"):
            del st.session_state['selected_file']
            st.rerun()
    with col_b:
        if vault_data:
            if st.button("🚀 Fast Decrypt & Download"):
                with st.status("Fetching from Blockchain...", expanded=True) as status:
                    try:
                        # 1. Fetch metadata
                        r = requests.get(f"{API_URL}/chain")
                        chain_data = r.json()['chain']
                        tx = next((t for b in reversed(chain_data) for t in b.get('transactions', []) if t.get('file_hash') == f['file_hash']), None)
                        
                        if tx:
                            # 2. Download Chunks
                            locations = tx.get('locations', {})
                            encrypted_chunks = []
                            status.update(label=f"Downloading {len(locations)} chunks from Nodes...")
                            for chunk_name, node_info in sorted(locations.items()):
                                chunk_data = http_relay_download(node_info, chunk_name)
                                if chunk_data: encrypted_chunks.append(chunk_data)
                                else: raise Exception(f"Missing chunk: {chunk_name}")
                            
                            # 3. Decrypt
                            status.update(label="Decrypting with Vault Key...")
                            fernet = Fernet(vault_data['key'].encode())
                            decrypted_file = fernet.decrypt(b"".join(encrypted_chunks))
                            
                            st.session_state[f"dl_buffer_{f['file_hash']}"] = decrypted_file
                            status.update(label="✅ Ready for Local Download!", state="complete")
                        else:
                            st.error("File metadata not found on ledger.")
                    except Exception as e:
                        st.error(f"Download failed: {e}")

    # Show the final download button if decryption was successful
    if f"dl_buffer_{f['file_hash']}" in st.session_state:
        st.download_button(
            label="💾 Save Decrypted File to PC",
            data=st.session_state[f"dl_buffer_{f['file_hash']}"],
            file_name=f['file_name'],
            mime="application/octet-stream",
            use_container_width=True
        )

# Bottom Panel: Event Logs
st.subheader("⚡ Real-time Distributed Events")
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

# Main Dashboard Tabs
tab_share, tab_my_uploads, tab_unlocked, tab_upload, tab_code = st.tabs([
    "🤝 Manage Sharing", 
    "📁 My Uploads", 
    "📂 Unlocked Drive", 
    "📤 Upload File", 
    "📥 Unlock with Code"
])

# ── 🤝 MANAGE SHARING TAB ──
with tab_share:
    st.header("Share Your Files")
    st.markdown("Select files from your uploads to create a secure access code.")

    vault = {}
    if os.path.exists(UPLOAD_VAULT):
        try:
            with open(UPLOAD_VAULT, "r") as f: vault = json.load(f)
        except:
            st.warning("Could not read your local vault.")

    if not vault:
        st.info("Your local vault is empty. Upload a file first to be able to share it.")
    else:
        # Pre-resolve file names from the chain for better display
        all_files_names = {}
        try:
            r_c = requests.get(f"{API_URL}/chain", timeout=2)
            if r_c.status_code == 200:
                for b in r_c.json().get('chain', []):
                    for tx in b.get('transactions', []):
                        all_files_names[tx['file_hash']] = tx['file_name']
        except: pass

        files_to_share = []
        st.write("**Your Vault Files:**")
        
        # Create a form for selection
        with st.form("share_form"):
            for f_hash, f_meta in vault.items():
                display_name = f_meta['name']
                # If the name is generic, use the one from the blockchain
                if "Shared File (" in display_name and f_hash in all_files_names:
                    display_name = all_files_names[f_hash]

                if st.checkbox(f"**{display_name}** (`{f_hash[:12]}...`)", key=f"share_cb_{f_hash}"):
                    files_to_share.append({"hash": f_hash, "key": f_meta['key']})
            
            submitted = st.form_submit_button("Generate Access Code for Selected Files")

            if submitted:
                if not files_to_share:
                    st.warning("Please select at least one file to share.")
                else:
                    payload = {
                        "owner_id": public_key, # Use the new public_key (derived from username)
                        "files": files_to_share
                    }
                    try:
                        r = requests.post(f"{API_URL}/drive/generate_code", json=payload)
                        if r.status_code == 200:
                            access_code = r.json().get("access_code")
                            st.success("✅ Access Code Generated!")
                            st.markdown("Share this code with others:")
                            st.code(access_code, language="")
                        else:
                            st.error(f"Failed to generate code: {r.text}")
                    except Exception as e:
                        st.error(f"Hub connection error: {e}")

    st.divider()
    st.header("Your Active Share Links")
    if st.button("Refresh Links"):
        st.rerun()

    try:
        r = requests.get(f"{API_URL}/drive/get_my_links?owner_id={public_key}") # Use the new public_key
        if r.status_code == 200:
            my_links = r.json().get("links", {})
            if not my_links:
                st.info("You have not generated any share links yet.")
            else:
                for code, files in my_links.items():
                    with st.container():
                        st.markdown(f"**Code:** `{code}`")
                        st.markdown(f"*Grants access to {len(files)} file(s).*")
                        if st.button("Revoke this Code", key=f"revoke_{code}"):
                            payload = {"owner_id": public_key, "access_code": code} # Use the new public_key
                            try:
                                revoke_r = requests.post(f"{API_URL}/drive/revoke_code", json=payload)
                                if revoke_r.status_code == 200:
                                    st.success(f"Code {code[:8]}... has been revoked.")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to revoke: {revoke_r.text}")
                            except Exception as e:
                                st.error(f"Hub error: {e}")
                        st.markdown("---")
        else:
            st.error("Could not fetch your links from the hub.")
    except Exception as e:
        st.error(f"Hub connection error: {e}")

# ── 📁 MY UPLOADS ──
with tab_my_uploads:
    st.header("Your Uploaded Files")
    st.markdown("These are files you sharded and distributed to the network.")
    
    my_vault = {}
    if os.path.exists(UPLOAD_VAULT):
        try:
            with open(UPLOAD_VAULT, "r") as f: my_vault = json.load(f)
        except: pass

    if not my_vault:
        st.info("No personal uploads yet.")
    else:
        for f_hash, f_meta in my_vault.items():
            with st.container():
                st.markdown(f"""
                <div style="background: rgba(100, 255, 218, 0.05); padding: 12px; border-radius: 8px; border-left: 3px solid var(--electric-cyan); margin-bottom: 8px;">
                    <b style="color:white;">📄 {f_meta['name']}</b><br>
                    <code style="color:var(--slate); font-size: 0.75rem;">ID: {f_hash[:16]}...</code>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🚀 Prepare {f_meta['name']}", key=f"my_dl_{f_hash}"):
                    with st.status("Fetching...") as status:
                        try:
                            r = requests.get(f"{API_URL}/chain")
                            tx = next((t for b in reversed(r.json()['chain']) for t in b.get('transactions', []) if t.get('file_hash') == f_hash), None)
                            if tx:
                                shards = []
                                for c_name, n_info in sorted(tx['locations'].items()):
                                    data = http_relay_download(n_info, c_name)
                                    if data: shards.append(data)
                                fernet = Fernet(f_meta['key'].encode())
                                decrypted = fernet.decrypt(b"".join(shards))
                                st.session_state[f"buf_{f_hash}"] = decrypted
                                status.update(label="✅ Ready!", state="complete")
                        except: st.error("Failed.")
                
                if f"buf_{f_hash}" in st.session_state:
                    st.download_button("💾 Save to PC", st.session_state[f"buf_{f_hash}"], file_name=f_meta['name'], key=f"my_save_btn_{f_hash}")

# ── 📂 UNLOCKED DRIVE ──
with tab_unlocked:
    st.header("Unlocked Data (From Others)")
    st.markdown("Files shared by friends that you successfully unlocked.")
    
    unl_vault = {}
    if os.path.exists(UNLOCKED_VAULT):
        try:
            with open(UNLOCKED_VAULT, "r") as f: unl_vault = json.load(f)
        except: pass

    if not unl_vault:
        st.info("No unlocked files yet. Enter a code in the 'Unlock' tab.")
    else:
        for f_hash, f_meta in unl_vault.items():
            with st.container():
                st.markdown(f"""
                <div style="background: rgba(87, 86, 213, 0.1); padding: 12px; border-radius: 8px; border-left: 3px solid #5756d5; margin-bottom: 8px;">
                    <b style="color:white;">🔓 {f_meta['name']}</b><br>
                    <code style="color:var(--slate); font-size: 0.75rem;">ID: {f_hash[:16]}...</code>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🚀 Prepare Shared {f_meta['name']}", key=f"unl_dl_{f_hash}"):
                    with st.status("Fetching...") as status:
                        try:
                            r = requests.get(f"{API_URL}/chain")
                            tx = next((t for b in reversed(r.json()['chain']) for t in b.get('transactions', []) if t.get('file_hash') == f_hash), None)
                            if tx:
                                shards = []
                                for c_name, n_info in sorted(tx['locations'].items()):
                                    data = http_relay_download(n_info, c_name)
                                    if data: shards.append(data)
                                fernet = Fernet(f_meta['key'].encode())
                                decrypted = fernet.decrypt(b"".join(shards))
                                st.session_state[f"ubuf_{f_hash}"] = decrypted
                                status.update(label="✅ Ready!", state="complete")
                        except: st.error("Failed.")
                
                if f"ubuf_{f_hash}" in st.session_state:
                    st.download_button("💾 Download to PC", st.session_state[f"ubuf_{f_hash}"], file_name=f_meta['name'], key=f"unl_save_btn_{f_hash}")

# ── UPLOAD TAB ──
with tab_upload:
    st.header("Secure Data Fragment Upload")
    st.markdown("Upload a file to shard and distribute it across the peer network.")
    uploaded_file = st.file_uploader("Choose a file", type=None)
    owner_name = st.text_input("Signer (Public Key)", public_key, disabled=True)
    
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
                        "node_id": public_key, # Use the new public_key
                        "timestamp": status_data.get("lamport_clock", 0)
                    }
                    
                    try:
                        r = requests.post(f"{API_URL}/add_transaction", json=payload)
                        if r.status_code == 201:
                            # Save to UPLOADS vault (your own files)
                            save_to_uploads(original_name, merkle_root, key.decode())
                            
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

# ── 📥 UNLOCK WITH CODE TAB ──
with tab_code:
    st.header("Unlock Shared Data")
    st.markdown("Paste a friend's code to add their shared files to your Unlocked Drive.")
    code_in = st.text_input("Access Code", placeholder="XXXX-XXXX")
    if st.button("Authenticate & Unlock"):
        if code_in:
            success_unl = False
            try:
                r = requests.post(f"{API_URL}/drive/unlock", json={"access_code": code_in})
                if r.status_code == 200:
                    data = r.json().get("keys", {})
                    for f_h, f_k in data.items():
                        r_name = f"Shared File ({f_h[:8]})"
                        try:
                            meta = requests.get(f"{API_URL}/get_file/{f_h}").json()
                            status_name = meta.get("file_name", r_name)
                        except:
                            status_name = r_name
                        save_to_unlocked(status_name, f_h, f_k)
                    success_unl = True
                else:
                    st.error("Invalid Code.")
            except Exception as e:
                st.error(f"Hub Error: {e}")
            
            if success_unl:
                st.success("✅ Files added to your Unlocked Drive!")
                time.sleep(1)
                st.rerun()
# End of Unlock with Code
