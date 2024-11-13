''' NAMES: KABIR SINGH BHATIA(kbhatia), PRABHUDATTA MISHRA (pmishra4)
    DATE: 16th October, 2024'''
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

def validate_auction_request(auction_details):
    '''
    This function validates the auction details sent by seller
    '''

    auc_type, auc_min_price, max_bids, item_name = auction_details
    # Checking if auction details except the item name are integers
    if not auc_type.isdigit() or not auc_min_price.isdigit() or not max_bids.isdigit():
        print("Error: auc_type, min_price and max_bids should be integers")
        return False

    # Validating auction type input
    if int(auc_type) not in [1,2]:
        print("Error: Action type can be either 1 or 2")
        return False
    
    # Validating item name length
    if len(item_name) > 255:
        print("Error: Item name should be within 255 characters")

    return True


def send_auction_request(sock):
    '''Collects auction details from the seller and send them to server.
    This function handles the seller's interaction to input
    auction details and validates the input formart before sending it to the server'''
     
    # Input auction details from the seller in a single line

    while True:
        auction_input = input("Enter auction type, minimum price, maximum number of bids, and item name (separated by spaces): ")
        auction_details = auction_input.split()

        if len(auction_details) != 4:
            print("You must provide exactly 4 details:<auction type> <min_price> <max_bids> <item_name>")
        
            # validating the input before sending to server
        if validate_auction_request(auction_details): 
            try:
                #Unpacking the details
                auc_type, auc_min_price, max_bids, item_name = auction_details
                # Creating the auction request string
                auction_request = f"{auc_type} {auc_min_price} {max_bids} {item_name}"
                #send the auction details to the server
                sock.sendall(auction_request.encode())
                print("Auction request sent to server.")
                break
            except Exception as e:
                print(f"Error: {e}. Invalid input format, please try again.")
        else:
            print("Invalid Request, Please try again!")


def seller_client(sock, rdtport):
    '''This handles seller side logic. The seller sends
    auction details and waits for the further messages from
    the server'''

    send_auction_request(sock)
    while True:
        try:
            # Receive messages from the server
            message = sock.recv(1024).decode()
            if message:
                print(f"{message}")
            # If the server requests a bid, the buyer submits one    
            if "Server: Invalid auction request!" in message:
                send_auction_request(sock)
                continue
            if "Buyer's IP:" in message:
                buyer_ip = message.split(':')[1]
                handle_file_send(buyer_ip, rdtport) 
                break
        except Exception as e:
            print(f"Error receiving message from server: {e}")
            break

    # Starting a thread to handle incoming messages from the server
    #threading.Thread(target=handle_server_messages, args=(sock,), daemon=True).start()

    # Keeping the main thread alive to continue listening for server messages
    
def buyer_client(sock, rdtport):
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
            if "Seller's IP:" in message:
                seller_ip = message.split(':')[1]
                handle_file_receive(seller_ip, rdtport)
        except Exception as e:
            print(f"Error receiving message from server: {e}")
            break

def open_udp_socket(rdtport):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('eth0', rdtport))
    print("UDP socket opened for RDT")
    return udp_socket


def handle_file_send(seller_ip, rdtport):
    udp_socket = open_udp_socket(rdtport) ## creating the UDP socket
    udp_socket.settimeout(2) ## setting 2 seconds for retransmission

    seq_num = 0 ## initiated with 0 for stop and wait protocol to be followed
    file_path = ''
    print("UDP socket created...")

    try:
        with open(file_path, 'rb') as file:
            file_size = len(file.read()) # to get total file size by reading through the file and reaches EOF
            file.seek(0) # reset file pointer to start position

            start_messaging = f"start {file_size}".encode()
            udp_socket.sendto(bytes([seq_num, 0]) + start_messaging, (buyer_ip, rdtport)) # setting seq 0 and type 0 and along with that sending the size of the file 
            ## basifcally this initialtes the transmission to be done by the seller
            print("Sent transmission start message: { start_message.decode()}")

            ## waiting for ack to start message 
            ## the ack value should be same as the seq no. and also checking for the address of the sender( buyer)

            try:
                ack, addr = udp_socket.recvfrom(2)
                ack_seq, ack_type = ack
                if ack_seq == seq_num and ack_type == 0 and addr[0] == buyer_ip:
                    print("Start message acknowledged from winning buyer")
                else:
                    print("Unexpected ACK or from unknown IP. Discarding.")
                    return
            except socket.timeout:
                print("Timeout waiting for start message acknowledgement. Exiting")
                return
            
            ## So we send the data packets if the conditions passes
            while True:
                data = file.read(2000) ## reading as a chunk of 2000 bytes at a time
                if not data :
                    print("End of file reached.")
                    break

                # Preparing the packet
                meta_header = bytes ([seq_num, 1]) ## keeping the TYPE=1 and the seq_num as 0
                packet = meta_header + data
                sent = False

                while not sent:
                    # send the packet
                    udp_socket.sendto(packet,(buyer_ip, rdtport))
                    print(f"Sending packets with sequence numbers {seq_num}")

                    try:
                        ## Waiting for the acknowledgement 
                        ack, addr = udp_socket.recvfrom(2)
                        ack_seq, ack_type = ack
                        if addr[0] == buyer_ip and ack_seq == seq_num and ack_type == 0:
                            print(f"Received valid ACK for sequence {seq_num}")
                            seq_num = {seq_num + 1} % 256 ## incrementing the sequence number
                            sent = True
                        else:
                            print(f" Received invalid ACK or from unknown IP. Resending packet ")
                    except socket.timeout:
                        print(f"Timeout waiting for ACK. Resending packet with sequence {seq_num} ")
        
        udp_socket.sendto(bytes([seq_num, 0]) + b"fin", (buyer_ip, rdtport))
        print("End-of-transmission signal sent")
        print("File transmission completed")

    except FileNotFoundError:
        print(" File 'tosend.file' not found")
    except Exception as e:
        print(f"Unexpected error during file transfer: {e}")
    finally:
        udp_socket.close()dde
        print("UDP socket closed.")




    print('Handle file receive function called')
    
def handle_file_receive(buyer_ip, rdtport):
    # udp_socket = open_udp_socket(rdtport)
    # data, client_address = udp_socket.recvfrom(2000)
    print('Handle file send function called')
        
def connect_to_server(host, port, rdtport):
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
            seller_client(sock, rdtport)
        elif "[Buyer]" in initial_message:
            buyer_client(sock, rdtport)
        else:
            print("Unexpected role message from server.")
    
    
def main():
    '''This establishes a connection to the auction server.
    Parses the CLI args for the host IP and port, then it 
    initiates the connection to the server.'''

    # Parses command line args for port and host
    parser = argparse.ArgumentParser(description="Add server IP address and server port")
    parser.add_argument('host', type=str, help="The server IP address")
    parser.add_argument('port', type=int, help="The server port")
    parser.add_argument('rdtport', type=int, help="The host rdtport")

    args = parser.parse_args()

    # Connect to the auction server with the provided host and port
    connect_to_server(args.host, args.port, args.rdtport)


if __name__ == "__main__":
    main()