import matplotlib.pyplot as plt
import networkx as nx
import os
import pandas as pd
import configparser
from matplotlib.ticker import MaxNLocator
config = configparser.ConfigParser()
config.read('settings.ini')
# # Generate sample data for 9 graphs
# graphs = [nx.erdos_renyi_graph(100, 0.05) for _ in range(3)] + [nx.barabasi_albert_graph(100, 5) for _ in range(3)] + [
#     nx.watts_strogatz_graph(100, 6, 0.1) for _ in range(3)]
#
# fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(15, 15))
# axes = axes.flatten()
#
# for i, graph in enumerate(graphs):
#     degrees = [d for n, d in graph.degree()]
#     axes[i].hist(degrees, bins=range(min(degrees), max(degrees) + 1))
#     axes[i].set_title(f'Graph {i + 1}')
#     axes[i].set_xlim(left=0, right=max(degrees) + 1)
#     axes[i].set_ylim(bottom=0)
#
#     if i in [0, 1, 2, 6, 7, 8]:
#         # Remove unnecessary white space by setting appropriate limits
#         axes[i].set_xlim(left=0, right=10)
#         axes[i].set_ylim(bottom=0, top=15)
#
# plt.tight_layout()
# plt.show()

filepath = 'D:/Github/ECEN689Project/New Code/NDD/'
files = os.listdir(filepath)
case = config['DEFAULT']['case']

df_all = pd.DataFrame()

for file in files:
    df = pd.read_csv(os.path.join(filepath, file))
    if case in file:
        if 'radial' in file:
            df['Type'] = 'Radial'
        elif 'star' in file:
            df['Type'] = 'Star'
        elif 'statistics' in file:
            df['Type'] = 'Statistics'
        df_all = pd.concat([df_all, df], axis=0)

print(df_all.head())

# Define a list of colors
colors = {
    'Radial': '#013F5E',
    'Star': '#FFD700',
    'Statistics': '#D9534F'
}

# plot node degree distribution for all three radial, star and statistics in one graph
fig, ax = plt.subplots(figsize=(8, 6))
for name, group in df_all.groupby('Type'):
    print(name)
    print(group)
    ax.bar(group['Degree'], group[' Counts'], label=name, width=0.8, alpha=0.8, color=colors[name])
    ax.plot(group['Degree'], group[' Counts'], marker='o', color=colors[name])
ax.set_xlim(0, 15)
ax.xaxis.set_major_locator(MaxNLocator(integer=True))
ax.set_xlabel("Node Degree", fontsize=20)
ax.set_ylabel("Number of Nodes", fontsize=20)
ax.legend(fontsize=15)
fig.tight_layout()
plt.savefig(f'Node_Degree_Distribution_{case}.png', dpi=300)
plt.show()


