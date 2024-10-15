import socket
import threading

HOST = '127.0.0.1'
PORT = 12345
MAX_BUYERS = 10

class AuctioneerServer:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.status = 0
        self.seller_conn = None
        self.buyers = []
        self.bids = {}
        self.auction_details = None
        self.buyer_lock = threading.Lock()

    def start_server(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Auctioneer is ready for hosting auctions!")

        while True:
            conn, addr = self.server_socket.accept()
            if self.status == 0:
                if not self.auction_details:
                    print(f"New Seller is connected from {addr[0]}:{addr[1]}")
                    threading.Thread(target=self.handle_seller, args=(conn, addr)).start()
                else:
                    conn.sendall(b"Server is busy. Try to connect again later.\n")
                    conn.close()
            elif self.status == 1:
                if not self.auction_details:
                    conn.sendall(b"Server is busy. Try to connect again later.\n")
                    conn.close()
                else:
                    print(f"New Buyer is connected from {addr[0]}:{addr[1]}")
                    threading.Thread(target=self.handle_buyer, args=(conn, addr)).start()              

    def handle_seller(self, conn, addr):
        
        print(">> New Seller Thread spawned")
        self.seller_conn = conn
        conn.sendall(b"Your role is: [Seller]\nPlease submit auction request:\n")
        self.status = 1

        while True:
            try:
                data = conn.recv(1024).decode()
                if not data:
                    break
                auction_details = data.split()
                if len(auction_details) != 4:
                    raise Exception()
                
                auc_type, auc_min_price, max_bids, item_name = auction_details

                if (auc_type.isdigit() and auc_min_price.isdigit() and max_bids.isdigit() and int(auc_type) <= 2 and int(auc_type) >= 0):
                    self.auction_details = {
                        'auc_type': int(auc_type),
                        'auc_min_price': int(auc_min_price),
                        'max_bids': int(max_bids),
                        'item_name': str(item_name)
                    }     
                    print(self.auction_details) 
                    print("Action request received. Now waiting for Buyer")
                                  
                    break
                else:
                    raise Exception()
                
            except Exception as e:
                conn.sendall(b"Server: Invalid auction request!\n")
                continue
        
                


    def handle_buyer(self, conn, addr):
        print(">> New Buyer Thread spawned")
        conn.sendall(b"Your role is: [Buyer]\n")

        with self.buyer_lock:
            if len(self.buyers) < self.auction_details['max_bids']:
                buyer_number = len(self.buyers) + 1
                buyer_id = f"Buyer {buyer_number}"
                self.buyers.append((conn, buyer_id))
                print(self.buyers)
            
                if len(self.buyers) == self.auction_details['max_bids']:
                    for conn, _, in self.buyers:
                        conn.sendall(b"Requested number of bidders arrived. Let's start bidding!\n")
                    print("Requested number of bidders arrived. Let's start bidding!")
                    self.start_bidding()
                else:
                    conn.sendall(b"The Auctioneer is still waiting for other Buyer to connect...\n")
                    print(f"Buyer len = {len(self.buyers)}")
            else:
                conn.sendall(b"Server is busy. Try to connect again later.\n")
                print(f"Buyer len = {len(self.buyers)}")
                conn.close()


    def start_bidding(self):

        threads = []
        for conn, buyer_id in self.buyers:
            thread = threading.Thread(target=self.receive_bid, args=(conn, buyer_id))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        self.determine_winner()
    

    def receive_bid(self, conn, buyer_id):
        while True:
            conn.sendall(b"Please submit your bid:")
            data = conn.recv(1024).decode()
            if data:
                try:
                    bid_amount = int(data)
                    print(f"bid: {bid_amount}")
                    with self.buyer_lock:
                        print("Lock acquired")
                        self.bids[buyer_id] = bid_amount
                        print(f"{buyer_id} bid ${bid_amount}")
                        conn.sendall(b"Bid receive. Please wait...\n")
                        break
                except ValueError:
                    conn.sendall(b"Invalid bid.\n")


    def determine_winner(self):
        with self.buyer_lock:
            highest_bidder_id = max(self.bids, key=self.bids.get)
            highest_bid = self.bids[highest_bidder_id]

            if highest_bid >= self.auction_details['auc_min_price']:
                if self.auction_details['auc_type'] == 1:
                    self.notify_winner(highest_bidder_id, highest_bid)
                elif self.auction_details['auc_type'] == 2:
                    second_highest_bid = sorted(self.bids.values(), reverse=True)[1]
                    self.notify_winner(highest_bidder_id, second_highest_bid)
            else:
                self.notify_no_sale()

    def notify_winner(self, winner_id, price):
        winner_conn = next(conn for conn, buyer_id in self.buyers if buyer_id == winner_id)

        winner_conn.sendall(f"You won this item {self.auction_details['item_name']}. Your payment due is ${price}".encode())
        self.seller_conn.sendall(f"Success! Your item {self.auction_details['item_name']} has been sold for ${price}".encode())

        for conn, buyer_id in self.buyers:
            if buyer_id != winner_id:
                conn.sendall(b"Unfortunately, you did not win in the last round.\n")
        
        self.reset_server()

    def notify_no_sale(self):
        for conn, _ in self.buyers:
            conn.sendall(b"The item was not sold.\n")
        
        print("The item was not sold")
        self.reset_server()
    

    def reset_server(self):
        self.status = 0
        self.auction_details = None

        if self.seller_conn:
            self.seller_conn.close()
        self.seller_conn = None
        for conn, _ in self.buyers:
            conn.close()
        with self.buyer_lock:
            self.buyers.clear()
            self.bids.clear()


if __name__ == "__main__":
    server = AuctioneerServer()
    server.start_server()
