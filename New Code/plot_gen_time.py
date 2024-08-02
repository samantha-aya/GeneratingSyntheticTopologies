import pandas as pd
import matplotlib.pyplot as plt

# Creating the DataFrame with the given values
data = {
    "Buses": [500, 2000, 10000],
    "Star": [3.25, 21.22, 77.06],
    "Radial": [3.35, 20.54, 76.62],
    "Statistics": [147.48, 1347.20, 6012.70]
}

df = pd.DataFrame(data)

plt.figure(figsize=(12, 8))

# Main plot
plt.plot(df['Buses'], df['Radial'], marker='o', label='Radial', color='red', linewidth=4)
plt.plot(df['Buses'], df['Statistics'], marker='s', label='Statistics', color='orange', linewidth=6)
plt.plot(df['Buses'], df['Star'], marker='^', label='Star', color='blue', linewidth=2)

plt.xlabel('Number of Buses', fontsize=20)
plt.ylabel('Generation Time (s)', fontsize=20)
plt.title('Star vs. Radial vs. Statistics', fontsize=20)
plt.legend(fontsize=25)
plt.grid(True)
plt.tick_params(axis='both', which='major', labelsize=20)

# Inset plot (graph inside graph)
inset_axes = plt.axes([0.55, 0.2, 0.32, 0.32])  # [left, bottom, width, height]
inset_axes.plot(df['Buses'], df['Radial'], marker='o', label='Radial', color='red')
inset_axes.plot(df['Buses'], df['Star'], marker='^', label='Star', color='blue')
inset_axes.set_title('Star vs. Radial (Zoomed)', fontsize=20)
inset_axes.grid(True)

plt.savefig('BusNumVSGenTime.pdf')

plt.show()


