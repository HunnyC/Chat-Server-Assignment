# Secure Distributed Chat Application
### CS60008 – Internet Architecture and Protocols Assignment

A **multi-threaded, TLS-secured chat server** with **distributed state management using Redis**.  
The system supports **multiple server instances**, enabling clients connected to different servers to communicate seamlessly.

---

# Features

- Multi-threaded chat server
- Secure communication using **TLS/SSL**
- Distributed messaging using **Redis**
- Global chat across multiple server instances
- Chat rooms
- Private messaging
- Publish–Subscribe messaging
- Multi-server architecture

---

# System Architecture
       +-------------------+
       |      Client A     |
       |  (Port 8000)      |
       +---------+---------+
                 |
                 |
         +-------v--------+
         |    Server 1    |
         |    Port 8000   |
         +-------+--------+
                 |
                 | Redis Pub/Sub
                 |
         +-------v--------+
         |     Redis      |
         | Distributed DB |
         +-------+--------+
                 |
         +-------v--------+
         |    Server 2    |
         |    Port 8081   |
         +-------+--------+
                 |
                 |
       +---------v---------+
       |      Client B     |
       |    (Port 8081)    |
       +-------------------+


       
Redis acts as the **central state manager**, allowing messages and room states to propagate across all servers.

---

# Prerequisites

Ensure the following are installed before running the project.

| Requirement | Version |
|-------------|--------|
| Python | 3.9+ |
| Redis | Latest |
| OS | Linux / WSL (Recommended) |

---

# Project Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate TLS certificates (if not already present):**
   ```bash
   python generate_certs.py
   ```

3. **Start Redis:**
   ```bash
   # On Linux/Mac:
   redis-server
   
   # On Windows with WSL:
   redis-server
   
   # Or use Docker:
   docker run -d -p 6379:6379 redis:7-alpine
   ```

### Running Multiple Server Instances

You can dynamically generate a `docker-compose.yml` file with **N** server instances and start them all with a single command.

```bash
# Generate docker-compose.yml with N servers
python generate_docker_compose.py 5

# Start all services
docker-compose up --build
```

#### **Understanding the Output**

When you run the above commands with N=5:
- ✓ Redis service on port `6379`
- ✓ Server 1 on port `8000` (SERVER_ID=server1)
- ✓ Server 2 on port `8001` (SERVER_ID=server2)
- ✓ Server 3 on port `8002` (SERVER_ID=server3)
- ✓ Server 4 on port `8003` (SERVER_ID=server4)
- ✓ Server 5 on port `8004` (SERVER_ID=server5)

All servers share the same **Redis instance** and **network**, ensuring **cross-server message delivery** in rooms.

#### **Test Cross-Server Communication**

```bash
# Terminal 1: Start 4 servers
python generate_docker_compose.py 4
docker-compose up -d

# Terminal 2: Connect Client A to Server 1
python client.py
> LOGIN a 1
> /join gaming
> /subscribe b

# Terminal 3: Connect Client B to Server 3
SERVER_PORT=8002 python client.py
> LOGIN b 1
> /join gaming
> /publish Hello from Server 3!

# Terminal 2: Client A should receive the notification
# Notification from b: Hello from Server 3!
```

## Default Credentials

The server comes with pre-registered users (a-h) with password "1":

```
Username: a, Password: 1
Username: b, Password: 1
Username: c, Password: 1
... (up to h)
```

## Implementation Details

### Thread Model
- Main thread accepts connections
- Each client connection spawns a daemon thread
- Background threads for Redis Pub/Sub listening and heartbeat

### Duplicate Login Policy
- When a user logs in, the server attempts to acquire an exclusive lock in Redis
- If the lock exists (user already active), the new login is rejected
- The lock is held for `ACTIVE_TTL_SECONDS` and refreshed via heartbeat

### TLS Implementation
- Mandatory TLS wrapping at socket level
- Server provides self-signed certificate
- Client verifies server certificate (with self-signed fallback)
- All communication is encrypted end-to-end

## Files

- `server.py` - Main chat server implementation
- `client.py` - Interactive chat client
- `Dockerfile` - Container image for the server
- `docker-compose.yml` - Multi-service orchestration
- `requirements.txt` - Python dependencies
- `server.crt` - TLS server certificate (generated)
- `server.key` - TLS private key (generated)
- `gen_cert.py` - Certificate generation utility
