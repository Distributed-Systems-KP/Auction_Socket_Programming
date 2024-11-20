import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set a modern style for plots
sns.set_theme(style="whitegrid")

# Load the CSV file
data = pd.read_csv('performance.csv')

# Extract the relevant data
pkt_loss_rate = data['pkt_loss_rate']
tct = data['TCT']
at = data['AT']

# Plot Fig. 1: pkt_loss_rate vs TCT
plt.figure(figsize=(10, 6))
plt.plot(pkt_loss_rate, tct, marker='o', linestyle='-', linewidth=2, color='blue', label='TCT')
plt.title('Fig. 1: Packet Loss Rate vs Total Completion Time (TCT)', fontsize=16, fontweight='bold')
plt.xlabel('Packet Loss Rate', fontsize=14)
plt.ylabel('Total Completion Time (TCT)', fontsize=14)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.grid(visible=True, linestyle='--', alpha=0.7)
plt.legend(fontsize=12)
plt.tight_layout()
plt.savefig('fig1_tct_vs_pkt_loss_rate.png', dpi=300)  # Save the figure with high resolution
plt.show()

# Plot Fig. 2: pkt_loss_rate vs AT
plt.figure(figsize=(10, 6))
plt.plot(pkt_loss_rate, at, marker='s', linestyle='-', linewidth=2, color='darkorange', label='AT')
plt.title('Fig. 2: Packet Loss Rate vs Average Throughput (AT)', fontsize=16, fontweight='bold')
plt.xlabel('Packet Loss Rate', fontsize=14)
plt.ylabel('Average Throughput (AT)', fontsize=14)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.grid(visible=True, linestyle='--', alpha=0.7)
plt.legend(fontsize=12)
plt.tight_layout()
plt.savefig('fig2_at_vs_pkt_loss_rate.png', dpi=300)  # Save the figure with high resolution
plt.show()