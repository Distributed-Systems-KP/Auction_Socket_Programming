''' NAMES: KABIR SINGH BHATIA(kbhatia), PRABHUDATTA MISHRA (pmishra4)
    DATE: 20th November, 2024'''
import socket
import argparse
import json
import numpy as np
import base64
import hashlib
import time
import os

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
            continue
        
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

def cal_check_sum(file_path):
    hash_obj= hashlib.sha256()
    with open(file_path, 'rb') as f:
        for x in iter(lambda: f.read(4096), b""):
            hash_obj.update(x)
    return hash_obj.hexdigest()

def seller_client(sock, rdtport, packet_loss_rate):
    '''This handles seller side logic. The seller sends
    auction details and waits for the further messages from
    the server'''

    send_auction_request(sock)
    buyer_ip = None
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
                buyer_ip = message.split("Buyer's IP: ")[1].strip()
                print(buyer_ip) 
                break
        except Exception as e:
            print(f"Error receiving message from server: {e}")
            break
    handle_file_send(buyer_ip, rdtport, packet_loss_rate)

    # Starting a thread to handle incoming messages from the server
    #threading.Thread(target=handle_server_messages, args=(sock,), daemon=True).start()

    # Keeping the main thread alive to continue listening for server messages
    
def buyer_client(sock, rdtport, packet_loss_rate):
    '''Handles buyer side logic.
    The buyer receives info from server and 
    submits bids when prompted.'''
    
    seller_ip = None

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
                seller_ip = message.split("Seller's IP: ")[1].strip()
                print(seller_ip)
                break
            if "Unfortunately" in message:
                return
        except Exception as e:
            print(f"Error receiving message from server: {e}")
            break
    
    handle_file_receive(seller_ip, rdtport, packet_loss_rate)

def open_udp_socket(rdtport):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('0.0.0.0', rdtport))
    # print("UDP socket opened for RDT")
    return udp_socket


def handle_file_send(buyer_ip, rdtport, packet_loss_rate=0.0):
    # Create a UDP socket and set a timeout for retransmissions
    # rdtport=8081
    udp_socket = open_udp_socket(rdtport)
    udp_socket.settimeout(2)  # Set a 2-second timeout for retransmissions
    seq_num = 0  # Initialize sequence number for Stop-and-Wait protocol
    file_path = 'tosend.file'  # Specify the file path

    print("UDP socket opened for RDT")
    print("Start sending file")

    try:
        with open(file_path, 'rb') as file:
            # Calculate total file size
            file_data = file.read()
            file_size = os.path.getsize(file_path)

            #Creating checksum for the data
            original_checksum = cal_check_sum(file_path)

            # Send a start message with the total file size (control message with TYPE=0)
            start_message = {
                'TYPE': 0,               # Control message type (0 indicates a control message)
                'SEQ/ACK': seq_num,      # Initial sequence number
                'DATA': f'start {file_size} {original_checksum}'  # Start message data
            }
            udp_socket.sendto(json.dumps(start_message).encode(), (buyer_ip, rdtport))
            print(f"Sending control seq 0: start {file_size}")

            # Wait for acknowledgment for the start message
            while True:
                try:
                    message, addr = udp_socket.recvfrom(1024)
                    ## simulating the packet loss
                    if np.random.binomial(1, packet_loss_rate) == 1:
                        print(f"Msg re-sent: {seq_num}")
                        print(f"Ack dropped: {seq_num}")
                        continue 
                    message = json.loads(message.decode())
                    if message['SEQ/ACK'] == seq_num and message['TYPE'] == 0 and addr[0] == buyer_ip:
                        print(f"Ack received: {seq_num}")
                        seq_num = 1
                        break
                    else:
                        print("Unexpected ACK or from unknown IP. Discarding.")
                        continue
                except socket.timeout:
                    print("Timeout waiting for start message acknowledgment. Retrying.")
                    udp_socket.sendto(json.dumps(start_message).encode(), (buyer_ip, rdtport))
                    print(f"Sending control seq 0: start {file_size}")
                    continue

            # Send file data in chunks
            for i in range(0, file_size, 2000):
                chunk_data = base64.b64encode(file_data[i:i + 2000]).decode('utf-8')

                # Prepare the data packet (TYPE=1 indicates a data packet)
                message = {
                    'TYPE': 1,                 # Data packet type
                    'SEQ/ACK': seq_num,        # Sequence number for Stop-and-Wait protocol
                    'DATA': chunk_data  # Convert binary data to string for JSON serialization
                }
                print(f"Sending data seq {seq_num}: {i+2000} / {file_size}")
                sent = False
                while not sent:
                    # Send the message as JSON
                    udp_socket.sendto(json.dumps(message).encode(), (buyer_ip, rdtport))
                    # print(f"Sent packet with sequence number {seq_num}")

                    try:
                        # Wait for an acknowledgment
                        response, addr = udp_socket.recvfrom(1024)
                        if np.random.binomial(1, packet_loss_rate) == 1:
                            print("Simulated packet loss for data packet acknowledgment.")
                            continue  ## skipping the further processing
                        response_message = json.loads(response.decode())
                        if addr[0] == buyer_ip and response_message['SEQ/ACK'] == seq_num and response_message['TYPE'] == 0:
                            print(f"ACK received: {seq_num}")
                            # Toggle sequence number for Stop-and-Wait (0 -> 1 or 1 -> 0)
                            seq_num = 1 - seq_num
                            sent = True
                        else:
                            print("Received invalid ACK or from unknown IP. Resending packet.")
                    except socket.timeout:
                        print(f"Timeout waiting for ACK. Resending packet with sequence {seq_num}.")

        # Send end-of-transmission control message (TYPE=0)
        end_message = {
            'TYPE': 0,
            'SEQ/ACK': seq_num,
            'DATA': 'fin'
        }

        udp_socket.settimeout(5)
        try:
            while True:
                udp_socket.sendto(json.dumps(end_message).encode(), (buyer_ip, rdtport))
                print(f"Sending control seq: {seq_num} : fin")
                response, addr = udp_socket.recvfrom(1024)
                if np.random.binomial(1, packet_loss_rate) == 1:
                    print("Simulated packet loss for data packet acknowledgment.")
                    continue  ## skipping the further processing
                response_message = json.loads(response.decode())
                # print(message)
                if addr[0] == buyer_ip and response_message['SEQ/ACK'] == seq_num and response_message['TYPE'] == 0 and 'fin/ack' in response_message['DATA']:
                    print(f"Ack Received: {seq_num}")
                    break
        except socket.timeout:
            print("Timeout occured.")
        except Exception as e:
            print(f"Error: {e}")

        # print("End-of-transmission signal sent.")
        print("File transmission completed.")

    except FileNotFoundError:
        print("File 'tosend.file' not found.")
    except Exception as e:
        print(f"Unexpected error during file transfer: {e}")
    finally:
        udp_socket.close()
        print("UDP socket closed.")

    
def handle_file_receive(seller_ip, rdtport, packet_loss_rate=0.0):
    # seller_ip='127.0.0.1'
    # rdtport=8082
    udp_socket = open_udp_socket(rdtport)
    expected_seq_num = 0
    file_data = b''
    ack_message = {}
    start_time = None
    end_time = None
    total_file_size=0
    current_size =0
    print("UDP socket opened for RDT")
    print("Start receiving file")


    try:
        while True:

            if np.random.binomial(1, packet_loss_rate) == 1:
                print("Pkt dropped: 0")
                continue  # Simulate packet loss by discarding the message

            response, addr = udp_socket.recvfrom(4096)

            response_message = json.loads(response.decode())

            if addr[0] != seller_ip:
                continue

            if response_message['TYPE'] == 0:
                if 'start' in response_message['DATA']:
                    seq_num = response_message.get('SEQ/ACK', None)  # Assuming 'SEQ_NUM' is the key holding the sequence number
                    if seq_num is None:
                        print("Error: sequence number is missing")
                    else:
                        print(f"Msg received: {seq_num}")
                        split_data = response_message['DATA'].split()
                        if len(split_data) == 3:
                            total_file_size = int(split_data[1])
                            original_checksum = split_data[2]
                        
                        else:
                            print("Invalid start message format received.")
                            return

                    ack_message = {
                        'TYPE': 0,
                        'SEQ/ACK': expected_seq_num,
                        'DATA': None
                    }
                    udp_socket.sendto(json.dumps(ack_message).encode(), addr)

                    print(f"Ack sent: {expected_seq_num}")
                    expected_seq_num = 1
                    start_time = time.time()
                expected_seq_num = 1
                elif 'fin' in response_message['DATA']:
                    ack_message = {
                        'TYPE': 0,
                        'SEQ/ACK': expected_seq_num,
                        'DATA': "fin/ack"
                    }
                    udp_socket.sendto(json.dumps(ack_message).encode(), addr)
                    # print("Received end of transmission signal. Sent fin/ack")
                    print(f"Msg received: {seq_num}")
                    print(f"Ack sent: { expected_seq_num}")
                    end_time = time.time()
                    break

            if response_message['TYPE'] == 1:
                
                seq_num = response_message['SEQ/ACK']
                if seq_num == expected_seq_num:
                    print(f"Msg received: {seq_num}")
                    
                    chunk_data = base64.b64decode(response_message['DATA'].encode('utf-8'))

                    file_data += chunk_data
                    current_size = len(file_data)
                    print(f"Ack sent: {seq_num}")
                    print(f"Received Data seq {seq_num} : {current_size}/{total_file_size}")

                    ack_message = {
                        'TYPE': 0,
                        'SEQ/ACK': seq_num,
                        'DATA': None
                    }
                    

                    udp_socket.sendto(json.dumps(ack_message).encode(), addr)
                    

                    expected_seq_num = 1 - expected_seq_num
                
                else:
                    print(f"Msg received with mismatched sequence number {seq_num}. Expecting {expected_seq_num}")
                    udp_socket.sendto(json.dumps(ack_message).encode(), addr)
                    print(f"Ack re-sent: {seq_num}")
        
        transfer_completion_time = round(end_time - start_time, 6)
        # print(f"Test tct timer: {transfer_completion_time}")
        with open('received.file', 'wb') as file:
            file.write(file_data)
        # print("File received and saved as 'received.file'")
        ## creating checksum for the received data
        received_checksum = cal_check_sum('received.file')

        if received_checksum == original_checksum :
            print("All data received! Exiting.....")
            throughput = get_average_throughput(current_size, transfer_completion_time)
            print(f"Transmission finished: {current_size} / {transfer_completion_time} = {throughput} bps")
        else:
            print("File transfer is complete and the file is corrupted")
    
    except Exception as e:
        print(f"Unexpected error during file reception: {e}")
    finally:
        udp_socket.close()
        print("UDP socket closed.")

def get_average_throughput(bytes, seconds):
    return round(bytes / seconds, 6)
        
def connect_to_server(host, port, rdtport, packet_loss_rate):
    '''Establishes a connection to the auction server.
    Based on the role assigned by the server (Seller or Buyer),
    it calls the appropriate client logic.'''

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        print(f"Connecting to server at {host}:{port}...")
        sock.connect((host, port))
        
        # Receive initial role assignment from the server
        initial_message = sock.recv(1024).decode()
        print(f"{initial_message}")
        
        # decides the role based on the initial message from the server and invokes the logic
        if "[Seller]" in initial_message:
            seller_client(sock, rdtport, packet_loss_rate)
        elif "[Buyer]" in initial_message:
            buyer_client(sock, rdtport, packet_loss_rate)
        

def validate_float(value):
    fvalue = float(value)
    if fvalue < 0 or fvalue > 1:
        raise argparse.ArgumentTypeError(f"{value} must be between 0 and 1")
    return fvalue
        
def main():
    '''This establishes a connection to the auction server.
    Parses the CLI args for the host IP and port, then it 
    initiates the connection to the server.'''

    # Parses command line args for port and host
    parser = argparse.ArgumentParser(description="Add server IP address and server port")
    parser.add_argument('host', type=str, help="The server IP address")
    parser.add_argument('port', type=int, help="The server port")
    parser.add_argument('rdtport', type=int, help="The host rdtport")
    parser.add_argument('packet_loss_rate', type=validate_float, help="Set packet loss rate, must range between 0 and 1")
    
    args = parser.parse_args()

    
    connect_to_server(args.host, args.port, args.rdtport, args.packet_loss_rate)


if __name__ == "__main__":
    main()
