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

# Setup Instructions

Follow the steps below to prepare the environment and run the chat system.

1. **Install Dependencies:**
   
   Install the required Python packages using the `requirements.txt` file:
   ```bash
   pip install -r requirements.txt
   ```

3. **Generate TLS certificates:**

   If TLS certificates are not already available, generate them using the provided script:
   ```bash
   python generate_certs.py
   ```
   This will create the necessary files used for secure server communication.

5. **Start Redis:**

   Redis is required for distributed state management and cross-server messaging.
   Start Redis using one of the following methods:
   ```bash
   # Linux/Mac:
   redis-server
   
   # Windows with WSL:
   redis-server
   
   # Or use Docker:
   docker run -d -p 6379:6379 redis:7-alpine
   ```

### Running Multiple Server Instances

The project supports launching multiple chat servers simultaneously.
A helper script is provided to automatically generate a docker-compose.yml file with the desired number of server instances.
```bash
# Generate docker-compose.yml with N servers
python generate_docker_compose.py 5

# Start all services
docker-compose up --build
```
This command will start Redis along with multiple server instances.

#### **Understanding the Output**

If the script is executed with N = 5, the following services will be created:
- ✓ Redis service on port `6379`
- ✓ Server 1 on port `8000` (SERVER_ID=server1)
- ✓ Server 2 on port `8001` (SERVER_ID=server2)
- ✓ Server 3 on port `8002` (SERVER_ID=server3)
- ✓ Server 4 on port `8003` (SERVER_ID=server4)
- ✓ Server 5 on port `8004` (SERVER_ID=server5)

All servers connect to the same Redis instance and operate on a shared network.
This allows messages sent in chat rooms to propagate across different servers.

#### **Testing Cross-Server Communication**

The following example demonstrates communication between clients connected to different server instances.
```bash
# Terminal 1: Start multiple servers
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

The server includes a set of pre-registered users for testing purposes.

```
Username: a   Password: 1
Username: b   Password: 1
Username: c   Password: 1
...
Username: h   Password: 1
```

## Implementation Details

### Thread Model
The server uses a multi-threaded architecture:
- The main thread listens for incoming client connections.
- Each client connection is handled by a dedicated daemon thread.
- Background threads for Redis Pub/Sub listening and heartbeat

### Duplicate Login Policy
To prevent multiple simultaneous logins for the same user:
- The server attempts to acquire an exclusive lock in Redis during login.
- If the lock already exists, the login attempt is rejected.
- The lock remains active for `ACTIVE_TTL_SECONDS` and is periodically refreshed using a heartbeat mechanism.

### TLS Implementation
The chat system enforces secure communication using TLS.
Key properties include:
- Mandatory TLS wrapping at socket level
- Self-signed certificate provided by the server
- Client verification of the server certificate (with fallback support)
- All messages encrypted during transmission

## Files

- `server.py` - Main chat server implementation
- `client.py` - Interactive chat client
- `Dockerfile` - Container image for the server
- `docker-compose.yml` - Multi-service orchestration
- `requirements.txt` - Python dependencies
- `server.crt` - TLS server certificate (generated)
- `server.key` - TLS private key (generated)
- `gen_cert.py` - Certificate generation utility
