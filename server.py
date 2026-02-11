import socket
import threading
import bcrypt
import ssl
import os
import redis
import json
import time

# --- CONFIGURATION ---
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
DEFAULT_ROOM = "lobby"

# --- REDIS SETUP ---
r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
PUB_SUB_CHANNEL = "global_chat_events"

# --- LOCAL STATE ---
local_sock2user = {}  # socket -> username
local_user2sock = {}  # username -> socket
local_room2socks = {} # room_name -> set(sockets)

users_db = {
    u: bcrypt.hashpw("1".encode(), bcrypt.gensalt()) 
    for u in ["a", "b", "c", "d", "e", "f", "g", "h"]
}

lock = threading.Lock()

def get_redis_room_members(room):
    return r.smembers(f"room:{room}")

def get_redis_subscribers(target_user):
    return r.smembers(f"subs:{target_user}")

def handle_redis_messages():
    """
    Thread function: Listens for messages from other servers (or self) via Redis
    and routes them to local connected clients.
    """
    pubsub = r.pubsub()
    pubsub.subscribe(PUB_SUB_CHANNEL)
    
    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            event_type = data.get('type')
            
            # 1. ROOM BROADCAST
            if event_type == 'room_msg':
                target_room = data['room']
                msg_content = data['content']
                sender = data.get('sender')
                exclude_sender = data.get('exclude_sender', False)
                
                # Send to all LOCAL sockets currently in this room
                with lock:
                    if target_room in local_room2socks:
                        for sock in local_room2socks[target_room]:
                            
                            # LOGIC: If exclude_sender is True, skip the sender's own socket
                            if exclude_sender and sender:
                                sock_user = local_sock2user.get(sock)
                                if sock_user == sender:
                                    continue 

                            try:
                                sock.sendall(msg_content.encode())
                            except:
                                pass

            # 2. DIRECT/SUBSCRIPTION BROADCAST
            elif event_type == 'direct_msg':
                target_user = data['target_user']
                msg_content = data['content']
                
                with lock:
                    if target_user in local_user2sock:
                        try:
                            local_user2sock[target_user].sendall(msg_content.encode())
                        except:
                            pass

def broadcast_global_room(room, message, sender=None, exclude_sender=False):
    """Publish a message to Redis so ALL servers can deliver it."""
    payload = {
        'type': 'room_msg',
        'room': room,
        'sender': sender,
        'content': message,
        'exclude_sender': exclude_sender 
    }
    r.publish(PUB_SUB_CHANNEL, json.dumps(payload))

def notify_subscribers(publisher, message):
    subscribers = get_redis_subscribers(publisher)
    for sub in subscribers:
        payload = {
            'type': 'direct_msg',
            'target_user': sub,
            'content': f"[Sub] {publisher}: {message}"
        }
        r.publish(PUB_SUB_CHANNEL, json.dumps(payload))

def handle_command(conn, username, line):
    current_room = r.hget("user:room", username)
    if not current_room: 
        current_room = DEFAULT_ROOM

    if line.startswith("/join "):
        new_room = line.split(maxsplit=1)[1]
        
        # 1. Update Redis State
        r.srem(f"room:{current_room}", username)
        r.sadd(f"room:{new_room}", username)
        r.hset("user:room", username, new_room)
        
        # 2. Update Local State (for routing)
        with lock:
            if conn in local_room2socks.get(current_room, set()):
                local_room2socks[current_room].remove(conn)
            if new_room not in local_room2socks:
                local_room2socks[new_room] = set()
            local_room2socks[new_room].add(conn)

        # 3. Notify (Global)
        conn.sendall(f"🟢 You joined {new_room}\n".encode())
        
        # Exclude sender from seeing "User joined" since they got "You joined"
        broadcast_global_room(current_room, f"🔴 {username} left {current_room}\n", sender=username, exclude_sender=True)
        broadcast_global_room(new_room, f"🟢 {username} joined {new_room}\n", sender=username, exclude_sender=True)

    elif line == "/leave":
        r.srem(f"room:{current_room}", username)
        r.sadd(f"room:{DEFAULT_ROOM}", username)
        r.hset("user:room", username, DEFAULT_ROOM)

        with lock:
            if conn in local_room2socks.get(current_room, set()):
                local_room2socks[current_room].remove(conn)
            if DEFAULT_ROOM not in local_room2socks:
                local_room2socks[DEFAULT_ROOM] = set()
            local_room2socks[DEFAULT_ROOM].add(conn)

        conn.sendall(f"🟢 You returned to {DEFAULT_ROOM}\n".encode())
        
        # Exclude sender
        broadcast_global_room(current_room, f"🔴 {username} left {current_room}\n", sender=username, exclude_sender=True)
        broadcast_global_room(DEFAULT_ROOM, f"🟢 {username} joined {DEFAULT_ROOM}\n", sender=username, exclude_sender=True)

    elif line == "/rooms":
        keys = r.keys("room:*")
        room_list = []
        for k in keys:
            r_name = k.replace("room:", "")
            count = r.scard(k)
            room_list.append(f"{r_name}({count})")
        conn.sendall(f"Rooms: {', '.join(room_list)}\n".encode())

    elif line.startswith("/subscribe "):
        parts = line.split(maxsplit=1)
        if len(parts) < 2:
            conn.sendall("Usage: /subscribe <username>\n".encode())
            return
        target = parts[1]
        if target not in users_db:
            conn.sendall(f"🔴 User {target} does not exist\n".encode())
        elif target == username:
            conn.sendall("🔴 Cannot subscribe to self\n".encode())
        else:
            r.sadd(f"subs:{target}", username)
            conn.sendall(f"🟢 Subscribed to {target}\n".encode())

    elif line.startswith("/unsubscribe "):
        parts = line.split(maxsplit=1)
        target = parts[1]
        if r.sismember(f"subs:{target}", username):
            r.srem(f"subs:{target}", username)
            conn.sendall(f"🟢 Unsubscribed from {target}\n".encode())
        else:
            conn.sendall(f"🟡 Not subscribed to {target}\n".encode())

    else:
        # Standard Message - CHANGED: exclude_sender is now True
        # The sender will NOT get their own message echoed back.
        broadcast_global_room(current_room, f"{username}: {line}\n", sender=username, exclude_sender=True)
        
        # Notify Subscribers (This should still go out)
        notify_subscribers(username, f"{line}\n")

def handle_login(conn):
    try:
        data = conn.recv(1024).decode().strip()
        if not data.startswith("LOGIN "):
            conn.sendall("Invalid protocol\n".encode())
            return False, ""
        
        _, user, pwd = data.split(maxsplit=2)
        
        if user not in users_db or not bcrypt.checkpw(pwd.encode(), users_db[user]):
            conn.sendall("Invalid credentials\n".encode())
            return False, ""

        if r.hexists("sessions", user):
            conn.sendall("User already logged in (Duplicate)\n".encode())
            return False, ""
        
        r.hset("sessions", user, "active")
        conn.sendall(f"Login successful. Welcome {user}!\n".encode())
        return True, user
    except Exception as e:
        print(f"Login error: {e}")
        return False, ""

def handle_client(conn, addr):
    success, username = handle_login(conn)
    if not success:
        conn.close()
        return

    with lock:
        local_sock2user[conn] = username
        local_user2sock[username] = conn
        if DEFAULT_ROOM not in local_room2socks:
            local_room2socks[DEFAULT_ROOM] = set()
        local_room2socks[DEFAULT_ROOM].add(conn)

    r.hset("user:room", username, DEFAULT_ROOM)
    r.sadd(f"room:{DEFAULT_ROOM}", username)
    
    # Exclude sender for initial join
    broadcast_global_room(DEFAULT_ROOM, f"🟢 {username} joined {DEFAULT_ROOM}\n", sender=username, exclude_sender=True)
    
    # Send direct welcome
    conn.sendall(f"🟢 You joined {DEFAULT_ROOM}\n".encode())

    try:
        buffer = ""
        while True:
            data = conn.recv(1024).decode()
            if not data: break
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                handle_command(conn, username, line.strip())
    except Exception as e:
        print(f"Error {addr}: {e}")
    finally:
        current_room = r.hget("user:room", username)
        
        r.hdel("sessions", username)
        if current_room:
            r.srem(f"room:{current_room}", username)
            r.hdel("user:room", username)
            broadcast_global_room(current_room, f"🔴 {username} left\n", sender=username, exclude_sender=True)

        with lock:
            if conn in local_sock2user: del local_sock2user[conn]
            if username in local_user2sock: del local_user2sock[username]
            if current_room and current_room in local_room2socks:
                if conn in local_room2socks[current_room]:
                    local_room2socks[current_room].remove(conn)
        
        conn.close()

def main():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    if os.path.exists("server.crt") and os.path.exists("server.key"):
        context.load_cert_chain(certfile="server.crt", keyfile="server.key")
    else:
        print("Warning: Keys not found. SSL will fail. Run gen_cert.py first.")
        return

    t_redis = threading.Thread(target=handle_redis_messages, daemon=True)
    t_redis.start()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Secure Server listening on {HOST}:{PORT} (TLS Enabled)")

    while True:
        try:
            raw_conn, addr = server.accept()
            conn = context.wrap_socket(raw_conn, server_side=True)
            print(f"Secure connection from {addr}")
            
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
        except ssl.SSLError as e:
            print(f"SSL Error: {e}")
        except Exception as e:
            print(f"Accept Error: {e}")

if __name__ == "__main__":
    main()