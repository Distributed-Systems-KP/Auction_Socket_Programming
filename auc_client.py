import socket
import threading

HOST = '127.0.0.1'  # Server's hostname or IP address
PORT = 12345        # Port used by the server

def handle_server_messages(sock):
    """ Continuously listen for messages from the server """
    while True:
        try:
            message = sock.recv(1024).decode()
            if message:
                print(f"{message}")
        except Exception as e:
            print(f"Error receiving message from server: {e}")
            break

def seller_client(sock):
    # Input auction details from the seller in a single line
    auction_input = input("Enter auction type, minimum price, maximum number of bids, and item name (separated by spaces): ")
    auction_details = auction_input.split()


    auc_type, auc_min_price, max_bids, item_name = auction_details

    # Validate inputs

    # Send auction details to the server
    auction_request = f"{auc_type} {auc_min_price} {max_bids} {item_name}"
    sock.sendall(auction_request.encode())
    print("Auction request sent to server.")

    # Start a thread to handle incoming messages from the server
    threading.Thread(target=handle_server_messages, args=(sock,), daemon=True).start()

    # Keep the main thread alive to continue listening for server messages
    while True:
        pass

def buyer_client(sock):
    
    while True:
        try:
            message = sock.recv(1024).decode()
            if message:
                print(f"{message}")
            if "Please submit your bid" in message:
                bid_amount = input("Enter bid:")
                sock.sendall(bid_amount.encode())
        except Exception as e:
            print(f"Error receiving message from server: {e}")
            break

    
def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        print(f"Connecting to server at {HOST}:{PORT}...")
        sock.connect((HOST, PORT))
        
        # Receive initial role assignment from the server
        initial_message = sock.recv(1024).decode()
        print(f"Server: {initial_message}")
        
        if "[Seller]" in initial_message:
            seller_client(sock)
        elif "[Buyer]" in initial_message:
            buyer_client(sock)
        else:
            print("Unexpected role message from server.")

if __name__ == "__main__":
    main()