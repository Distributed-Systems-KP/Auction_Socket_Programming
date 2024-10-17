import socket
import threading
import argparse


def handle_server_messages(sock):
    """ Continuously listen for messages from the server.
    This function runs on a separate thread and is responsible for receiving and displaying 
    messages from the server. """

    while True:
        try:
            message = sock.recv(1024).decode()
            if message:
                print(f"{message}")
        except Exception as e:
            print(f"Error receiving message from server: {e}")
            break

def send_auction_request(sock):
    '''Collects auction details from the seller and send them to server.
    This function handles the seller's interaction to input
    auction details and validates the input formart before sending it to the server'''
    
    # Input auction details from the seller in a single line
    auction_input = input("Enter auction type, minimum price, maximum number of bids, and item name (separated by spaces): ")
    auction_details = auction_input.split()

    # Unpacking the details
    auc_type, auc_min_price, max_bids, item_name = auction_details

    # Creating the auction request string
    auction_request = f"{auc_type} {auc_min_price} {max_bids} {item_name}"

    #send the auction details to the server
    sock.sendall(auction_request.encode())
    print("Auction request sent to server.")

def seller_client(sock):
    '''This handles seller side logic. The seller sends
    auction details and waits for the further messages from
    the server'''

    send_auction_request(sock)

    # Starting a thread to handle incoming messages from the server
    threading.Thread(target=handle_server_messages, args=(sock,), daemon=True).start()

    # Keeping the main thread alive to continue listening for server messages
    while True:
        pass

def buyer_client(sock):
    '''Handles buyer side logic.
    The buyer receives info from server and 
    submits bids when prompted.'''
   
    while True:
        try:
            # Receive messages from the server
            message = sock.recv(1024).decode()
            if message:
                print(f"{message}")

            # If the server requests a bid, the buyer submits one    
            if "Please submit your bid" in message:
                bid_amount = input("Enter bid:")
                sock.sendall(bid_amount.encode())
        except Exception as e:
            print(f"Error receiving message from server: {e}")
            break

def connect_to_server(host, port):
    '''Establishes a connection to the auction server.
    Based on the role assigned by the server (Seller or Buyer),
    it calls the appropriate client logic.'''

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        print(f"Connecting to server at {host}:{port}...")
        sock.connect((host, port))
        
        # Receive initial role assignment from the server
        initial_message = sock.recv(1024).decode()
        print(f"Server: {initial_message}")
        
        # decides the role based on the initial message from the server and invokes the logic
        if "[Seller]" in initial_message:
            seller_client(sock)
        elif "[Buyer]" in initial_message:
            buyer_client(sock)
        else:
            print("Unexpected role message from server.")
    
    
def main():
    '''This establishes a connection to the auction server.
    Parses the CLI args for the host IP and port, then it 
    initiates the connection to the server.'''

    # Parses command line args for port and host
    parser = argparse.ArgumentParser(description="Add host IP address and host port")
    parser.add_argument('host', type=str, help="The host IP address")
    parser.add_argument('port', type=int, help="The host IP address")

    args = parser.parse_args()

    # Connect to the auction server with the provided host and port
    connect_to_server(args.host, args.port)

if __name__ == "__main__":
    main() 