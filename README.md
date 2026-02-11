Chat Application (CS60008 Assignment)
This project implements a multi-threaded, secure chat server with distributed state management using Redis. It supports features like chat rooms, private messaging, and a publish-subscribe model.

1. Prerequisites
OS: Linux or WSL (Windows Subsystem for Linux) recommended.


Python: Version 3.9 or higher.


Redis: Must be installed and running.

2. Environment Setup
Follow these steps to set up the project environment.

2.1. Create & Activate Virtual Environment
Open your terminal and run:

2.2. Install Dependencies
Install the required Python libraries for security and database connections:

2.3. Generate SSL Certificates
The server uses TLS for secure connections. Generate a self-signed certificate:

Output: You should see Generated server.crt and server.key.

3. Starting Services (Redis)
The server relies on Redis for handling room state and cross-server communication.
using command: sudo service redis-server start 


3.1. Install Redis (if not installed)
3.2. Start Redis Server
Verify: Run redis-cli ping. If it returns PONG, Redis is running.

4. Running the Chat System
To test the distributed nature of the system (Problem 6), we will run two server instances on different ports and connect clients to each.

4.1. Start Server Instance 1 (Port 8000)
Open Terminal 1:

Expected Output: Secure Server listening on 0.0.0.0:8000 (TLS Enabled)

4.2. Start Server Instance 2 (Port 8081)
Open Terminal 2:

Expected Output: Secure Server listening on 0.0.0.0:8081 (TLS Enabled)

5. Connecting Clients
Now, connect clients to different server instances to verify they can communicate.

5.1. Client A (Connects to Server 1)
Open Terminal 3:

Port: Enter 8000

Username: Enter a

Password: Enter 1

5.2. Client B (Connects to Server 2)
Open Terminal 4:

Port: Enter 8081 (Note: Connecting to the second server)

Username: Enter b

Password: Enter 1

6. Testing Features
Once connected, try the following commands in the client terminals:

Global Chat: Type a message in Client A. Client B should receive it (even though they are on different ports).

Join Room:

Client A: /join room1

Client B: /join room1


Result: Both are now in room1 and can chat privately there.

List Rooms:

Command: /rooms

Result: Shows active rooms and user counts.

Subscribe (Pub/Sub):

Client A: /subscribe b

Client B: Type a message.


Result: Client A receives the message regardless of which room they are in.