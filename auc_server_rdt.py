''' NAMES: KABIR SINGH BHATIA(kbhatia), PRABHUDATTA MISHRA (pmishra4)
    DATE: 20th November, 2024'''
import socket
import threading
import argparse

class AuctioneerServer:
    def __init__(self, host, port):
        """
        Initializes the Auctioneer server with the specified host and port.

        Parameters:
        - host (str): The IP address of the server
        - port (int): The port number for the server
        """
        self.host = host    # Server IP address
        self.port = port    # Server port number
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create TCP socket
        self.status = 0     # 0: Waiting for seller, 1: Waiting for buyer 
        self.seller_conn = None     # Connection object for seller
        self.buyers = []    # List to store connected buyers (conn, buyer_id)
        self.bids = {}      # Dictionary to store bids by buyer id  
        self.ongoing = False    # Flag that indicates whether the bidding is on-going
        self.auction_details = None     # Store auction details
        self.buyer_lock = threading.RLock()     # Reentrant lock for synchronizing access to buyers

    def start_server(self):
        
        """
        Starts the server to listen for incoming connections from
        seller and buyers

        Handles collection in separate threads for seller and buyers.
        """

        # Bind server socket and start listening for connections
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Auctioneer is ready for hosting auctions!")

        while True:
            conn, addr = self.server_socket.accept()
            if self.ongoing:
                conn.send(b"Server: Auction is ongoing. Please try again later\n")
                conn.close()
                continue
            if self.status == 0:    # Waiting for seller
                print(f"New Seller is connected from {addr[0]}:{addr[1]}")
                threading.Thread(target=self.handle_seller, args=(conn, addr)).start()      # Handling seller in a new thread
            elif self.status == 1:  # Waiting for buyers
                if not self.auction_details:    # If buyer connects when seller has not submitted auction request yet
                    conn.sendall(b"Server: Seller is busy. Try to connect again later\n")
                    conn.close()
                else:
                    threading.Thread(target=self.handle_buyer, args=(conn, addr)).start()   # Handle buyer in a new thread       

    def handle_seller(self, conn, addr):
        """
        Handles communication with the seller.

        Receives auction details from the seller and updates server status.


        Parameters:
        - conn: Connection object for the seller.
        - addr: Address of the seller.
        """
        
        print(">> New Seller Thread spawned")   # Server log
        self.seller_conn = conn
        conn.sendall(b"Server: Your role is: [Seller]\nPlease submit auction request:\n")   # Assigning role to the client
        self.status = 1     # Setting status to 1 so that the new clients can join as buyers

        while True:
            try:
                data = conn.recv(1024).decode() # Receive auction details from seller
                if not data:
                    break
                auction_details = data.split()
                if len(auction_details) != 4:   # Ensure exactly four components are received
                    raise Exception()
                
                auc_type, auc_min_price, max_bids, item_name = auction_details

                if (auc_type.isdigit() and auc_min_price.isdigit() and max_bids.isdigit() and (int(auc_type) in [1,2]) and len(str(item_name)) < 255):
                    # Store validated details in the dictionary
                    self.auction_details = {
                        'auc_type': int(auc_type),  # Type 1 or 2
                        'auc_min_price': int(auc_min_price),    # Minimum price for the auction
                        'max_bids': int(max_bids),      # Maximum number of bids allowed
                        'item_name': str(item_name)     # Name of the item being auctioned
                    }     
                    print("Action request received. Now waiting for Buyer")   
                    break
                else:
                    raise Exception()
                
            except Exception as e:
                conn.sendall(b"Server: Invalid auction request!\n")     # Notify seller of invalid request format
                continue
                


    def handle_buyer(self, conn, addr): 
        """
        Handles communication with a buyer.

        Manages buyer connections and starts bidding when enough buyers are connected.

        Parameters:
        - conn: Connection object for the buyers
        - addr: Address of the buyer
        """
        print(">> New Buyer Thread spawned")    # Server log
        conn.sendall(b"Server: Your role is: [Buyer]\n")    # Assigning role Buyer to client

        with self.buyer_lock:   # Acquire lock to safely modify buyers list
            if len(self.buyers) < self.auction_details['max_bids']:
                buyer_number = len(self.buyers) + 1
                buyer_id = f"Buyer {buyer_number}"
                self.buyers.append((conn, buyer_id))    # Add buyer connection and ID to list
                
                print(f"Buyer {buyer_id} is connected from {addr[0]}:{addr[1]}")    # Server log
            
                should_start_bidding = len(self.buyers) == self.auction_details['max_bids']     # Check if max buyers reached
                  
        if should_start_bidding:
            bidding_thread = threading.Thread(target=self.start_bidding)
            bidding_thread.start()  
        else:
            conn.sendall(b"Server: The Auctioneer is still waiting for other Buyer to connect...\n")    # Notify the buyer that the server is waiting for other buyers to connect


    def start_bidding(self):
        """
        Initiates the bidding process by launching separate threads 
        for each buyer to receive bids concurrently 
        """
        print(">> New Bidding Thread spawned")
        
        self.ongoing = True # Set the on-going flag to true so that main thread can reject new client connections
        for conn, _, in self.buyers:
            conn.sendall(b"Server: Requested number of bidders arrived. Let's start bidding!\n")    # Notify buyers that server has started bidding process
        self.seller_conn.sendall(b"Server: Requested number of bidders arrived. Let's start bidding!\n")    # Notify seller that server has started bidding process
        print("Requested number of bidders arrived. Let's start bidding!")
        
        threads = []
        for conn, buyer_id in self.buyers:
            thread = threading.Thread(target=self.receive_bid, args=(conn, buyer_id))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()   # Waiting for all bid-receiving threads to complete
        
        self.determine_winner() # Determine winner after all bids are received


    def receive_bid(self, conn, buyer_id):
        """
        Receives bids from a buyer.

            Validates bid amount and stores them in a dictionary

        Parameters:
        - conn: Connection object for the buyer
        - buyer_id: Identifier for the buyer
        """
        while True:
            conn.sendall(b"Server: Please submit your bid:")
            data = conn.recv(1024).decode()
            if data:
                try:
                    bid_amount = int(data)
                    if bid_amount < 0:
                        conn.sendall(b"Server: Invalid bid. Please submit a positive integer\n")
                        continue
                    with self.buyer_lock:   # Acquire lock to safely update bids dictionary
                        self.bids[buyer_id] = bid_amount
                        print(f"{buyer_id} bid ${bid_amount}")
                        conn.sendall(b"Server: Bid received. Please wait...\n")
                    break
                except ValueError:  # Handle non-integer inputs, notifying client of invalid bid format
                    conn.sendall(b"Server: Invalid bid. Try again.\n")
                    continue

    def determine_winner(self):
        """
        Determines the winner based on the type of auction and bids received

        Notifies the winner and other participants of the auction results
        
        """
        with self.buyer_lock:
            highest_bidder_id = max(self.bids, key=self.bids.get)   # Identify highest bidder based on bid amounts
            highest_bid = self.bids[highest_bidder_id]

            if highest_bid >= self.auction_details['auc_min_price']:    # Check if highest bid meets minimum price requirement
                if self.auction_details['auc_type'] == 1:   # First auction type
                    self.notify_winner(highest_bidder_id, highest_bid)
                elif self.auction_details['auc_type'] == 2: # Second auction type
                    self.bids['seller_min_price'] = self.auction_details['auc_min_price']
                    second_highest_bid = sorted(self.bids.values(), reverse=True)[1]
                    self.notify_winner(highest_bidder_id, second_highest_bid)
            else:
                self.notify_no_sale()

    def notify_winner(self, winner_id, price):
        """
        Notifies the winner of their successful bid and informs other buyers 
        of their loss

        Resets server state after notification

        Parameters:
        - winner_id: Identifier of the winning buyer
        - price: Winning bid amount
        
        """
        winner_conn = next(conn for conn, buyer_id in self.buyers if buyer_id == winner_id)
        seller_ip = self.seller_conn.getpeername()[0]
        buyer_ip = winner_conn.getpeername()[0]
        
        winner_conn.sendall(f"Auction Finished!\nYou won this item {self.auction_details['item_name']}. Your payment due is ${price}. Seller's IP: {seller_ip}\n".encode())    # Notify winner
        self.seller_conn.sendall(f"Auction Finished!\nSuccess! Your item {self.auction_details['item_name']} has been sold for ${price}. Winning Buyer's IP: {buyer_ip}\n".encode()) # Notify seller

        print(f"The item was sold to {winner_id} for ${price}")

        for conn, buyer_id in self.buyers:  # Notify losing bidders about their unsuccessful attempts
            if buyer_id != winner_id:
                conn.sendall(b"Server: Unfortunately, you did not win in the last round.\n")
        
        self.reset_server()     # Reset server state

    def notify_no_sale(self):
        """
        Notifies participants if no sale occured

        Resets server after notification
        """
        for conn, _ in self.buyers:
            conn.sendall(b"Server: The item was not sold.\n")
        
        print("The item was not sold")
        self.reset_server()
    

    def reset_server(self):
        """
        Resets server state after an auction concludes.
        
        Closes all connections and clears store data to prepare for a 
        new auction session.
        """
        self.status = 0     # Reset status to initial state (Waiting for seller)
        self.auction_details = None # Cleared stored auction details
        self.ongoing = False    # Reset ongoing flag

        if self.seller_conn:
            self.seller_conn.sendall(b"Disconnecting from auctioneer server. Auction is over")
            self.seller_conn.close()
            print("Connection closed with seller")
        self.seller_conn = None # Clearing stored seller connection object
        for conn, buyer_id in self.buyers:
            conn.sendall(b"Disconnecting from auctioneer server. Auction is over")  # Closing connections with all buyers
            conn.close()
            print(f"Connection closed with {buyer_id}")
        with self.buyer_lock:   # Clear buyers list and bids dictionary safely with the lock
            self.buyers.clear() 
            self.bids.clear()
        


if __name__ == "__main__":

    try:
        # Parsing user input (host IP address and port)
        parser = argparse.ArgumentParser(description="Add host IP address and host port")
        parser.add_argument('host', type=str, help="The host IP address")
        parser.add_argument('port', type=int, help="The host port")

        args = parser.parse_args()

        host = args.host
        port = args.port

        server = AuctioneerServer(host, port)  # Creating instance of the Auctioneer Server
        server.start_server()   # Starting the server
    except Exception as e:
        print(f"Error: {e}")
