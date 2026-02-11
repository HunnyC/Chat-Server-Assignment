import socket
import threading
import sys
import ssl

# Default to localhost/8000, can be changed
SERVER = "localhost"
PORT = 8000

def receive(sock):
    while True:
        try:
            buffer = ""
            while "\n" not in buffer:
                data = sock.recv(1024).decode()
                if not data: return
                buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", maxsplit=1)
                print(line)
        except:
            break

def main():
    # --- Part 7: SSL Context ---
   
 
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.check_hostname = False
    context.load_verify_locations("server.crt") # Expects the cert to exist locally

    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Wrap socket
    try:
        sock = context.wrap_socket(raw_sock, server_hostname=SERVER)
        # Ask user for port to demonstrate connecting to different docker instances
        port_in = input(f"Enter Port (default {PORT}): ")
        target_port = int(port_in) if port_in else PORT
        
        sock.connect((SERVER, target_port))
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    username = input("Enter username: ")
    password = input("Enter password: ")

    sock.sendall(f"LOGIN {username} {password}\n".encode())
    
    # Simple handshake wait
    response = sock.recv(1024).decode()
    print(response, end="")

    if "successful" not in response:
        sock.close()
        return

    t = threading.Thread(target=receive, args=(sock,), daemon=True)
    t.start()

    try:
        while True:
            msg = input()
            if msg == "/quit": break
            
            message = ""
            if msg.startswith("/join"):
                parts = msg.split()
                if len(parts) > 1:
                    message = f"{msg}\n"
            else:
                message = f"{msg}\n"
            
            sock.sendall(message.encode())
    except KeyboardInterrupt:
        pass
    finally:
        print("\nDisconnecting...")
        sock.close()
        sys.exit()

if __name__ == "__main__":
    main()