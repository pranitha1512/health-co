# chat_server.py
import socket
import threading
import sys

# --- Configuration ---
HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
# You can change the HOST to '0.0.0.0' to allow connections from other computers on your network
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)
MAX_CLIENTS = 10    # Maximum number of clients allowed

# --- Global Variables ---
clients = {} # Dictionary to store connected client sockets and their names {conn: name}
client_lock = threading.Lock() # Lock for thread-safe access to the clients dictionary

# --- Functions ---

def broadcast(message, sender_socket=None):
    """Sends a message to all connected clients, optionally excluding the sender."""
    with client_lock: # Acquire lock before accessing shared clients list
        # Create a list of sockets to iterate over to avoid issues if clients disconnect during broadcast
        current_client_sockets = list(clients.keys())
        for client_socket in current_client_sockets:
            # Don't send the message back to the sender if specified
            if sender_socket is None or client_socket != sender_socket:
                try:
                    client_socket.sendall(message)
                except socket.error as e:
                    # Handle potential errors if a client disconnects abruptly
                    print(f"[ERROR] Failed to send message to a client: {e}")
                    # Remove the problematic client if it's still in the main dict
                    # Use .pop() which safely removes and returns the value or None
                    removed_client_name = clients.pop(client_socket, None)
                    if removed_client_name:
                         print(f"[CLEANUP] Removing disconnected client during broadcast: {removed_client_name}")
                         # No need to broadcast departure here, handled by remove_client

def remove_client(conn):
     """Removes a client from the dictionary and closes the connection."""
     with client_lock:
         # Use pop to safely remove and get the name
         client_name = clients.pop(conn, None)
         if client_name:
             print(f"[DISCONNECTED] {client_name} disconnected.")
             # Announce departure only if client was successfully removed
             broadcast(f"[SERVER] {client_name} has left the chat.\n".encode('utf-8'))
         else:
             # This might happen if broadcast already removed the client
             print("[CLEANUP] Attempted to remove a client that was already removed or not found.")
     try:
         # Shutdown signals intent to close, helps unblock threads
         conn.shutdown(socket.SHUT_RDWR)
         conn.close()
     except socket.error as e:
         # Ignore errors like 'socket not connected' if already closed
         if e.errno != 107 and e.errno != 9: # 107: Transport endpoint not connected, 9: Bad file descriptor
            print(f"[ERROR] Error shutting/closing socket: {e}")
     except Exception as e: # Catch other potential errors during close
         print(f"[ERROR] Unexpected error closing socket: {e}")


def handle_client(conn, addr):
    """Handles connection for a single client."""
    print(f"[NEW CONNECTION] {addr} connected.")
    client_name = None # Name will be set after receiving it

    try:
        # Request and receive the client's name
        conn.sendall(b"Welcome! Please enter your name: ")
        # Set a timeout for receiving the name to prevent hanging
        conn.settimeout(60.0) # 60 seconds timeout
        name_data = conn.recv(1024)
        conn.settimeout(None) # Reset timeout to blocking

        if not name_data:
            raise socket.error("Client disconnected before sending name") # Handle empty name data

        client_name = name_data.decode('utf-8').strip()
        if not client_name: # Handle empty name string
            client_name = f"User_{addr[1]}" # Assign default if name is empty
            print(f"[INFO] Client {addr} provided empty name, assigned default: {client_name}")

        # Add the new client to the dictionary (thread-safe)
        with client_lock:
            # Check if name already exists (optional feature)
            # if client_name in clients.values():
            #     conn.sendall(f"[SERVER] Name '{client_name}' is taken. Please reconnect with a different name.\n".encode('utf-8'))
            #     raise ValueError("Username already taken")
            clients[conn] = client_name
            print(f"[NAME SET] {addr} is now known as {client_name}.")

        # Announce new user to others
        broadcast(f"[SERVER] {client_name} has joined the chat.\n".encode('utf-8'), conn)
        conn.sendall(f"You have joined the chat as {client_name}.\nType 'exit' to leave.\n".encode('utf-8')) # Send confirmation

        # Main loop to receive messages from this client
        while True:
            data = conn.recv(1024) # Buffer size 1024 bytes
            if not data:
                # Empty data means client disconnected gracefully
                break # Exit loop to handle disconnection
            else:
                # Decode message and prepare for broadcast
                message = data.decode('utf-8')
                # Basic check for excessively long messages (optional)
                if len(message) > 4096:
                     print(f"[WARNING] Received overly long message from {client_name}. Truncating.")
                     message = message[:4096] + "... (truncated)"

                print(f"[{client_name}] {message.strip()}") # Log message on server console
                broadcast_message = f"[{client_name}] {message}".encode('utf-8')
                # Broadcast the message to other clients
                broadcast(broadcast_message, conn)

    except socket.timeout:
         print(f"[TIMEOUT] Client {addr} timed out waiting for name. Disconnecting.")
    except socket.error as e:
        # Handle socket errors (e.g., connection reset) only if name was set
        if client_name:
            print(f"[SOCKET ERROR] Error with {client_name} ({addr}): {e}")
        else:
            print(f"[SOCKET ERROR] Error with connection {addr} before name set: {e}")
    except UnicodeDecodeError:
         print(f"[ERROR] Received non-UTF-8 data from {client_name or addr}. Disconnecting.")
    except ValueError as e: # Catch specific errors like username taken
         print(f"[INFO] Client {addr} disconnected due to input error: {e}")
         # No need to broadcast departure if they never fully joined
         client_name = None # Prevent broadcast in finally block
    except Exception as e:
        # Handle other unexpected errors
        print(f"[UNEXPECTED ERROR] Error with {client_name or addr}: {e}")
    finally:
        # --- Cleanup when client loop ends (disconnect or error) ---
        # remove_client handles closing conn and broadcasting departure if name was set
        remove_client(conn)


def start_server():
    """Starts the chat server."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((HOST, PORT))
        print(f"[INFO] Server bound to {HOST}:{PORT}")
    except socket.error as e:
        print(f"[FATAL ERROR] Binding failed: {e}")
        sys.exit(1)

    server_socket.listen(MAX_CLIENTS)
    print(f"[LISTENING] Server is listening for up to {MAX_CLIENTS} clients...")
    active_threads = [] # Keep track of threads

    try:
        while True:
            # Accept a new connection - this blocks until a client connects
            try:
                conn, addr = server_socket.accept()
            except OSError as e:
                 # Handle potential error if server socket is closed while accepting
                 print(f"[INFO] Server socket closed, stopping accept loop ({e}).")
                 break # Exit the accept loop

            # Create a new thread to handle the client communication
            client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            client_thread.start()
            active_threads.append(client_thread) # Add thread to list (optional tracking)

            # Optional: Clean up finished threads from the list periodically
            # active_threads = [t for t in active_threads if t.is_alive()]

    except KeyboardInterrupt:
        print("\n[SHUTTING DOWN] Keyboard interrupt received. Server is shutting down.")
    except Exception as e:
        print(f"[ERROR] Error accepting connections: {e}")
    finally:
        # --- Server Shutdown Cleanup ---
        print("[CLEANUP] Closing server socket...")
        server_socket.close() # Close the main server socket first

        print("[CLEANUP] Closing all client connections...")
        with client_lock:
            client_sockets = list(clients.keys())
            for client_socket in client_sockets:
                try:
                    client_socket.sendall(b"[SERVER] Server is shutting down. Disconnecting.\n")
                    # remove_client handles closing and broadcasting
                    remove_client(client_socket)
                except socket.error as e:
                    print(f"[ERROR] Error notifying client during shutdown: {e}")
                    # Ensure removal even if send fails
                    clients.pop(client_socket, None)
                    try:
                        client_socket.close()
                    except socket.error: pass

        print("[SERVER] Server shutdown complete.")

# --- Main Execution ---
if __name__ == "__main__":
    start_server()
