# ⛓️ BlockDrive: Decentralized Secure Storage
**Project Submission: Distributed Systems (2026)**

## 📁 Repository Name
**BlockDrive-v2-Distributed**

## 📝 Project Description
BlockDrive is a peer-to-peer (P2P) file storage system that eliminates the need for a central authority. It uses **Blockchain Technology** for immutable metadata logging and **Distributed Data Sharding** to store file fragments across a network of independent nodes. The system is designed with **Zero-Knowledge Architecture**, ensuring that only the file owner holds the decryption keys, while the network remains blind to the content it stores.

---

## 👥 Team Roles & Responsibilities
To ensure equal contribution, the project was split into 5 core modules.

### 1. 🥇 Hemanth (Lead Developer)
**Focus: Blockchain Core & Cryptographic Identity**
- **The Ledger:** Developed the `blockchain.py` engine, including mining (Proof of Work), Genesis block creation, and chain validation.
- **Merkle Roots:** Implemented Merkle Tree algorithms to generate unique "File IDs" (Hashes) for every upload.
- **Client-Side Encryption:** Integrated AES-256 (Fernet) encryption to ensure data is "Zero-Knowledge" before it even leaves the user's laptop.
- **Key Responsibility:** Explaining how the blockchain maintains an immutable history of file locations without storing the files themselves.

### 2. 🥈 Saran 
**Focus: Distributed Coordination & Mutual Exclusion**
- **Logical Clocks:** Implemented **Lamport Clocks** to ensure that events (like file shares) are ordered correctly across multiple nodes.
- **Mutual Exclusion:** Integrated the **Ricart-Agrawala Algorithm** logic to prevent two nodes from updating the same blockchain transaction simultaneously.
- **Event Logging:** Built the real-time event logger that tracks network traffic, consensus status, and mining progress.
- **Key Responsibility:** Explaining how we avoid "Race Conditions" in a system with no master clock.

### 3. 🥉 Shivanesh
**Focus: Data Sharding & P2P Distribution**
- **Fragmentation Logic:** Developed the sharding algorithm that breaks a single file into $N$ encrypted chunks (1MB each).
- **Physical Distribution:** Managed the `node_storage` system, ensuring shards are sent to specific IP addresses on the WiFi network.
- **Peer Discovery:** Work on the `join_network.bat` scripts that allow different laptops to discover the Hub and register as storage providers.
- **Key Responsibility:** Explaining the lifecycle of a file from a single local entity to multiple distributed fragments.

### 4. 🏅 Vimal
**Focus: Fault Tolerance & Data Replication**
- **Replication Strategy:** Implemented a **Replication Factor of 3**, ensuring every file shard exists on at least three different nodes.
- **Availability:** Programmed the health-check system that detects if a node has left the WiFi and automatically warns the user.
- **Integrity Checks:** Developed the reassembly logic that verifies each shard's hash before decrypting to prevent data corruption.
- **Key Responsibility:** Explaining how the system survives if a student's laptop suddenly disconnects or the battery dies.

### 5. 🎖️ Sarvvesh
**Focus: Frontend Experience & Session Isolation**
- **Streamlit Dashboard:** Designed the modern 2026 "Deep Navy" UI, making complex blockchain operations look simple.
- **Session Vaults:** Created the `vault_*.json` logic that keeps one student's keys private from another student, even if they use the same hub.
- **Access Protocols:** Developed the **"Unlock with Code"** workflow that facilitates the secure transfer of decryption keys between peers.
- **Key Responsibility:** Explaining the User Experience (UX) and how we simplified complex cryptographic handshakes into a 4-tab interface.

---

## ⚙️ Technical Workflow (How it Works)
1. **Upload Phase:** Hemanth's encryption encrypts the file; Shivanesh's logic shards it; Vimal's logic replicates it.
2. **Recording Phase:** Hemanth's blockchain mines a new block containing the "Merkle Root" (File ID) and the list of IP addresses where the shards are hidden.
3. **Sharing Phase:** Sarvvesh's UI generates a code; Saran's coordination logic ensures the code is unique and timestamps it.
4. **Download Phase:** The client fetches shards from multiple IPs, reassembles them, and Hemanth's key decrypts them locally.

---

## 📚 Distributed Systems Glossary (For the Professor)
- **Immutability:** Once a block is mined, it cannot be edited, preventing hackers from changing file ownership.
- **Zero-Knowledge:** The "Server" (Hub) never sees the file or the key; it only sees encrypted noise.
- **Sharding:** Breaking data into parts to increase efficiency and privacy.
- **Replication:** Storing the same data in multiple places to achieve **Fault Tolerance**.
- **Consensus:** The process by which all nodes agree on the state of the blockchain.
