# BlockDrive: Distributed Blockchain Storage System

BlockDrive is a professional-grade distributed storage system that combines the security of a blockchain ledger with multi-node sharded storage. This project is designed to demonstrate core distributed systems algorithms in a real-world application.

## 🚀 Key Features
- **Zero-Knowledge Security**: Files are encrypted locally before being sharded across the network.
- **Immutable Ledger**: Every file operation is mined into a blockchain, ensuring a tamper-proof audit trail.
- **Multi-Node Replication**: Data is sharded and replicated across multiple nodes for high availability.
- **Modern Dashboard**: A 2026 "Deep Sea & Neon" themed UI for monitoring the entire network status.

## 🧠 Distributed Algorithms
- **Lamport Logical Clocks**: Used to maintain causal ordering of events across different laptops without relying on synchronized physical clocks.
- **Ricart-Agrawala Mutual Exclusion**: A permission-based algorithm that ensures only one node can modify the blockchain/storage at a time, preventing race conditions.

## 🛠️ Project Structure
- `/ss-server-main`: The central Hub (Backend API, Blockchain, and Dashboard).
- `/secure-storage-main`: The Worker node code for laptops storing the data.

## 🏁 Quick Start

### 1. Start the Hub (Cloud/Server)
```bash
cd ss-server-main
pip install -r requirements.txt
python backend.py
streamlit run frontend.py
```

### 2. Connect a Storage Node (Laptops)
```bash
cd secure-storage-main
# On Windows PowerShell
$env:BACKEND_URL="http://your-hub-url:8000"; python smart_node.py YourNodeName
```

## 📜 Presentation Test Flow
1. **Network Discovery**: Watch nodes appear in the "Storage Nodes" panel as they connect.
2. **Permission Request**: Observe the logs for `REQUEST` and `REPLY` events during an upload.
3. **Ledger Consistency**: Verify that the "Network Time" (Lamport Clock) increments consistently across all nodes.
4. **Data Retrieval**: Use the "File Ledger" to find a file and download it using the secure Merkle Root and Master Key.

---
Created by [hemanthkumargt](https://github.com/hemanthkumargt)
