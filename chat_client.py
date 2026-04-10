# chat_client.py
import socket
import threading
import sys
import time

# --- Configuration ---
# Should match the server's HOST and PORT
SERVER_HOST = '127.0.0.1' # Change if server is on a different machine
SERVER_PORT = 65432

# Flag to signal threads to stop
stop_event = threading.Event()

# --- Functions ---

def receive_messages(client_socket):
    """Receives messages from the server and prints them."""
    while not stop_event.is_set():
        try:
            message = client_socket.recv(1024) # Buffer size 1024 bytes
            if not message:
                # Server likely closed the connection gracefully
                print("\n[DISCONNECTED] Server closed the connection.")
                stop_event.set() # Signal other threads to stop
                break

            # Decode and print the message
            # Use sys.stdout.write and flush for better handling with input()
            sys.stdout.write(message.decode('utf-8'))
            sys.stdout.flush()

        except ConnectionResetError:
             print("\n[ERROR] Connection to the server was lost.")
             stop_event.set()
             break
        except ConnectionAbortedError:
             print("\n[INFO] You have disconnected from the server.")
             stop_event.set() # Ensure stop if connection is aborted locally
             break
        except socket.error as e:
            # Handle other socket errors only if not stopping
            if not stop_event.is_set():
                print(f"\n[ERROR] Socket error during receive: {e}")
            stop_event.set()
            break
        except Exception as e:
             # Handle other unexpected errors only if not stopping
            if not stop_event.is_set():
                print(f"\n[UNEXPECTED ERROR] Error receiving message: {e}")
            stop_event.set()
            break

    print("Receive thread finished.")
    # Attempt to close socket from this thread as well, in case send thread hangs
    try:
        client_socket.shutdown(socket.SHUT_RDWR) # Signal no more reads/writes
        client_socket.close()
    except socket.error:
        pass # Ignore if already closed


def send_messages(client_socket):
    """Sends messages typed by the user to the server."""
    try:
        # Get username from user
        username = input("Enter your username: ")
        client_socket.sendall(username.encode('utf-8'))
        print(f"Username '{username}' sent. You can now start chatting (type 'exit' to quit).")
        time.sleep(0.1) # Small delay to allow receive thread to print welcome messages

    except (socket.error, EOFError, KeyboardInterrupt) as e:
        print(f"\n[ERROR] Could not send username or initial setup failed: {e}")
        stop_event.set() # Signal receive thread to stop
        return # Exit send thread

    while not stop_event.is_set():
        try:
            # Use input() which blocks, allowing receive thread to print
            message = input()
            if stop_event.is_set(): # Check again after input returns
                 break
            if message.lower() == 'exit': # Allow user to exit cleanly
                 print("[EXITING] Closing connection...")
                 stop_event.set() # Signal receive thread to stop
                 break
            if message: # Only send non-empty messages
                client_socket.sendall(message.encode('utf-8'))

        except EOFError: # Handle Ctrl+D
             print("\n[EXITING] EOF detected. Closing connection...")
             stop_event.set()
             break
        except KeyboardInterrupt: # Handle Ctrl+C
             print("\n[EXITING] Keyboard interrupt detected. Closing connection...")
             stop_event.set()
             break
        except (socket.error, BrokenPipeError) as e:
            if not stop_event.is_set(): # Avoid double message if already exiting
                print(f"\n[ERROR] Failed to send message. Connection lost? {e}")
            stop_event.set()
            break
        except Exception as e:
            if not stop_event.is_set():
                print(f"\n[UNEXPECTED ERROR] Error sending message: {e}")
            stop_event.set()
            break

    print("Send thread finished.")
    # Attempt to close socket from this thread
    try:
        # Ensure socket is properly closed if send thread initiates exit
        client_socket.shutdown(socket.SHUT_RDWR)
        client_socket.close()
    except socket.error:
        pass # Ignore if already closed by receive thread


# --- Main Execution ---
if __name__ == "__main__":
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        print(f"Attempting to connect to {SERVER_HOST}:{SERVER_PORT}...")
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        print("[CONNECTED] Successfully connected to the server.")
    except socket.error as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(1) # Exit if connection fails

    # Create and start the receiving thread
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,), daemon=True)
    receive_thread.start()

    # Start the sending loop in the main thread
    send_messages(client_socket)

    # Wait for the receive thread to finish if needed (optional, helps ensure cleanup messages are printed)
    receive_thread.join(timeout=1.0)

    print("[CLIENT] Client application finished.")

