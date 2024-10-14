import socket
import sys

# Constants for client roles
SELLER = "seller"
BUYER = "buyer"

# Client class to handle both seller and buyer modes
class AuctionClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = None
    
    # Connect to the server
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            print(f"Connected to server at {self.server_ip}:{self.server_port}")
        except Exception as e:
            print(f"Failed to connect to the server: {e}")
            sys.exit()

    # Seller logic to submit auction request
    def seller_mode(self):
        try:
            # Read auction request details from user
            auction_type = input("Enter auction type (1 for first-price, 2 for second-price): ")
            lowest_price = input("Enter lowest price: ")
            number_of_bids = input("Enter number of bids (max 10): ")
            item_name = input("Enter item name: ")

            # Format the request and send to server
            auction_request = f"{auction_type} {lowest_price} {number_of_bids} {item_name}"
            self.socket.sendall(auction_request.encode())
            print(f"Sent auction request: {auction_request}")

            # Receive server response
            server_response = self.socket.recv(1024).decode()
            print(f"Server response: {server_response}")

            # Wait for auction result
            while True:
                result = self.socket.recv(1024).decode()
                if result:
                    print(f"Auction result: {result}")
                    break
        except Exception as e:
            print(f"Error in seller mode: {e}")
        finally:
            self.socket.close()

    # Buyer logic to submit a bid
    def buyer_mode(self):
        try:
            print("Waiting for the server to start the bidding...")

            # Wait for bidding start signal
            while True:
                bidding_start_msg = self.socket.recv(1024).decode()
                if bidding_start_msg == "Bidding start!":
                    print("Bidding has started!")
                    break
            
            # Submit the bid
            bid = input("Enter your bid (positive integer): ")
            self.socket.sendall(bid.encode())
            print(f"Sent bid: {bid}")

            # Receive bid confirmation
            server_response = self.socket.recv(1024).decode()
            print(f"Server response: {server_response}")

            # Wait for auction result
            while True:
                result = self.socket.recv(1024).decode()
                if result:
                    print(f"Auction result: {result}")
                    break
        except Exception as e:
            print(f"Error in buyer mode: {e}")
        finally:
            self.socket.close()

# Main client function
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python auc_client.py <server_ip> <server_port> <role (seller/buyer)>")
        sys.exit()

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    role = sys.argv[3].lower()

    # Create client instance and connect to server
    client = AuctionClient(server_ip, server_port)
    client.connect()

    # Based on the role, execute seller or buyer mode
    if role == SELLER:
        client.seller_mode()
    elif role == BUYER:
        client.buyer_mode()
    else:
        print("Invalid role! Use 'seller' or 'buyer'.")
