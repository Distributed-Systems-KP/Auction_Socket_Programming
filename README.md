
# BidMaster: A Simple Auction System

## Authors
- **Kabir Singh Bhatia (kbhatia@ncsu.edu)**
- **Prabhudatta Mishra (pmishra4@ncsu.edu)**

## Project Overview
This project implements a sealed-bid auction system using socket programming in Python. It includes two main components:
1. **Auctioneer Server**: Hosts auctions, handles seller and buyer connections, and coordinates the auction process.
2. **Seller/Buyer Client**: Allows users to participate as either a seller or a buyer in the auction.

The system also incorporates a reliable data transfer (RDT) mechanism for file transfer between the winning buyer and the seller, simulating packet loss scenarios.

---

## Features
- **Auction Types**:
  - First-price sealed-bid auction.
  - Second-price (Vickrey) sealed-bid auction.
- **Client Roles**:
  - Seller: Submits auction details.
  - Buyer: Submits bids during the auction.
- **Reliable Data Transfer**:
  - Implements Stop-and-Wait protocol.
  - Simulates packet loss with configurable rates.

---

## Requirements
- Python 3.x
- Required libraries can be installed using:
  ```
  pip3 install -r requirements.txt
  ```

---

## How to Run

### Step 0: Network Setup Requirements
#### To run this application, you must meet the following network setup requirements:

- Multiple Machines: The application requires at least two separate virtual machines (VMs) or physical computers.
- Same Network: All machines must be connected to the same local network to enable communication between them.
- IP Configuration: Ensure that each machine has a unique IP address within the network.

#### Steps to Configure the Network
- Connect all required VMs or computers to the same local network.
- Verify connectivity between the machines by using commands like `ping <IP_address>` from one machine to another.
- Ensure that firewall settings or network policies allow communication between the machines on required ports.


If deploying on VMs:
- Assign each VM an IP address within the same subnet.
Start the application on each VM, ensuring they are configured to recognize each other's IP addresses.

If deploying on physical computers:
- Connect all computers to the same router or switch.
- Follow similar steps to configure and verify connectivity.


### Step 1: Start the Auctioneer Server
Run the server in one terminal:
```
python3 server_rdt.py <host> <port>
```
- `<host>`: IP address of the server.
- `<port>`: Port number for the server.

Example:
```
python3 server_rdt.py 127.0.0.1 3000
```

### Step 2: Start Clients (Seller/Buyers)
Run clients in separate machine.

<b>The rdtport must be same in all clients.</b>

#### Seller Client:
```
python3 client_rdt.py <host> <port> <rdtport> <packet_loss_rate>
```
- `<rdtport>`: UDP port for file transfer.
- `<packet_loss_rate>`: Packet loss rate (range [0,1], optional, default=0).

Example:
```
python3 client_rdt.py 127.0.0.1 3000 3001 0.2
```

#### Buyer Clients:
Similar to the seller client, but buyers connect after the seller has submitted an auction request.

Example:
```
python3 client_rdt.py 127.0.0.1 3000 3001 0.2
```

---

## Example Workflow

### Seller's Process:
1. Connects to the server and submits auction details in the format:
   ```
   <auction_type> <minimum_price> <max_bids> <item_name>
   ```
   Example input:
   ```
   1 100 3 WolfPackSword
   ```

2. Waits for buyers to join and receives auction results.

### Buyer's Process:
1. Connects to the server and waits for bidding to start.
2. Submits a bid when prompted.
3. Receives auction results indicating whether they won or lost.

---

## Reliable Data Transfer (RDT)
After the auction concludes, the seller transfers a file to the winning buyer using a Stop-and-Wait protocol with simulated packet loss.

### File Transfer Steps:
1. The seller sends a start message with file metadata (size, checksum).
2. The file is sent in chunks, with each chunk requiring an acknowledgment (ACK) from the buyer.
3. The process handles packet loss by retransmitting lost packets until acknowledged.
4. The transfer concludes with a "fin" message.

---

## Performance Analysis

### Metrics:
1. **Total Completion Time (TCT)**: Time taken to complete file transfer.
2. **Average Throughput (AT)**: Data transfer rate in bytes per second.

### Observations:
- TCT increases non-linearly with higher packet loss rates due to retransmissions.
- AT decreases as packet loss increases, with sharp drops at lower loss rates.

### Sample Results:
| Packet Loss Rate | TCT (seconds) | AT (Bps)       |
|------------------|---------------|----------------|
| 0.10             | 3.32          | 631055.81      |
| 0.20             | 7.34          | 285486.76      |
| 0.30             | 8.57          | 244739.24      |
| 0.40             | 39.16         | 53545.89       |
| 0.50             | 44.58         | 47043.10       |

---

## Testing and Validation

### Normal Case (No Packet Loss):
- File transfer completes successfully without retransmissions.
- Seller and buyer exchange acknowledgments correctly.

### Simulated Packet Loss (e.g., `packet_loss_rate = 0.2`):
- Lost packets are retransmitted until acknowledged.
- File integrity is verified using checksums after transfer.

---

## Screenshots and Logs

![Alt text](./image.png)

![Alt text](./image2.png)