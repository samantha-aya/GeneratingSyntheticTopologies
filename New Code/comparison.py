import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from statistics_based import generate_nwk

# Set global figure settings for high-quality publication-style visuals
plt.rcParams.update({
    "font.family": "serif",  # Use serif fonts for a professional look
    "font.size": 14,         # Increase font size for readability
    "axes.titlesize": 16,    # Title size
    "axes.labelsize": 14,    # Axis label size
    "xtick.labelsize": 12,   # Tick label size
    "ytick.labelsize": 12,   # Tick label size
    "figure.figsize": (15, 5),  # Wider figure
    "axes.grid": False,      # No grid for a clean aesthetic
    "legend.fontsize": 12,   # Legend font size
    "figure.dpi": 300,       # High resolution for publication
})

def generate_connected_graphs(n):
    """
    Generate a connected Chung-Lu network and a connected Havel-Hakimi network.

    Parameters:
        n (int): Number of nodes

    Returns:
        G_chunglu (networkx.Graph): Connected Chung-Lu network
        G_havelhakimi (networkx.Graph): Connected Havel-Hakimi network
    """
    if n < 2:
        raise ValueError("Number of nodes must be at least 2.")

    # Generate expected degrees from a power-law distribution
    degree_sequence = np.random.zipf(2.5, size=n)

    # Ensure no zero-degree nodes (for connectivity)
    degree_sequence[degree_sequence == 0] = 1

    # Ensure even degree sum for Havel-Hakimi
    if sum(degree_sequence) % 2 == 1:
        degree_sequence[np.argmax(degree_sequence)] += 1

    # **Ensure the degree sequence is graphical**
    while not nx.is_graphical(sorted(degree_sequence, reverse=True)):
        degree_sequence[np.argmax(degree_sequence)] -= 1  # Adjust the highest degree downward

    # Chung-Lu network
    G_chunglu = nx.expected_degree_graph(degree_sequence, selfloops=False)
    if not nx.is_connected(G_chunglu):
        components = list(nx.connected_components(G_chunglu))
        for i in range(len(components) - 1):
            node1 = next(iter(components[i]))
            node2 = next(iter(components[i + 1]))
            G_chunglu.add_edge(node1, node2)

    # Havel-Hakimi network (guaranteed to be valid now)
    G_havelhakimi = nx.havel_hakimi_graph(sorted(degree_sequence, reverse=True))
    if not nx.is_connected(G_havelhakimi):
        components = list(nx.connected_components(G_havelhakimi))
        for i in range(len(components) - 1):
            node1 = next(iter(components[i]))
            node2 = next(iter(components[i + 1]))
            G_havelhakimi.add_edge(node1, node2)

    return G_chunglu, G_havelhakimi

n_nodes = 50
chunglu_graph, havelhakimi_graph = generate_connected_graphs(n_nodes)
stat_based, _, _ = generate_nwk(n_nodes, 0)

# Create high-quality plots
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Define a consistent layout for better visualization
layout_chunglu = nx.spring_layout(chunglu_graph, seed=42)
layout_havelhakimi = nx.spring_layout(havelhakimi_graph, seed=42)
layout_stat_based = nx.spring_layout(stat_based, seed=42)

# Chung-Lu Network (Connected)
nx.draw(
    chunglu_graph, layout_chunglu, ax=axes[0],
    node_size=80, edge_color="black", alpha=0.7, linewidths=0.5, width=0.5
)
axes[0].set_title("Chung-Lu Network", fontsize=16)

# Havel-Hakimi Network (Connected)
nx.draw(
    havelhakimi_graph, layout_havelhakimi, ax=axes[1],
    node_size=80, edge_color="black", alpha=0.7, linewidths=0.5, width=0.5
)
axes[1].set_title("Havel-Hakimi Network", fontsize=16)

# Stat-based Network (Connected)
nx.draw(
    stat_based, layout_stat_based, ax=axes[2],
    node_size=80, edge_color="black", alpha=0.7, linewidths=0.5, width=0.5
)
axes[2].set_title("Stat-Based Network", fontsize=16)

# Remove axis ticks for clean presentation
for ax in axes:
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_frame_on(False)

# Adjust layout for better spacing
plt.tight_layout()
plt.show()

def generate_multi_subgraphs_no_stat(n_nodes, util):
    """
    Generate multiple subgraphs (Chung-Lu and Havel-Hakimi) and connect them via a utility node.

    Parameters:
        n_nodes (int): Total number of nodes across all subgraphs.
        util (int): Number of subgraphs to generate.

    Returns:
        G_final (networkx.Graph): Final graph with connected subgraphs.
    """
    if n_nodes < util or util < 1:
        raise ValueError("Number of nodes must be greater than the number of subgraphs.")

    graph_nodes = n_nodes // util  # Nodes per subgraph
    G_finalC = nx.Graph()
    G_finalH = nx.Graph()
    G_finalS = nx.Graph()
    util_node = n_nodes  # Utility node ID (last node)

    for ut in range(util):
        # Generate subgraphs
        chunglu_graph, havelhakimi_graph = generate_connected_graphs(graph_nodes)
        stat_based, _, _ = generate_nwk(graph_nodes, 0)

        # Merge graphs into the final graph
        offset = ut * graph_nodes  # Offset for node IDs

        # Relabel nodes to keep unique node IDs across subgraphs
        chunglu_graph = nx.relabel_nodes(chunglu_graph, {node: node + offset for node in chunglu_graph.nodes()})
        havelhakimi_graph = nx.relabel_nodes(havelhakimi_graph, {node: node + offset for node in havelhakimi_graph.nodes()})
        statbased_graph = nx.relabel_nodes(stat_based, {node: node + offset for node in stat_based.nodes()})

        # Add subgraphs to the final graph
        G_finalC.add_edges_from(chunglu_graph.edges())
        G_finalH.add_edges_from(havelhakimi_graph.edges())
        G_finalS.add_edges_from(statbased_graph.edges())

        # Connect a random node from each subgraph to the utility node
        random_node = np.random.choice(list(chunglu_graph.nodes()))
        G_finalC.add_edge(random_node, util_node)

        random_node = np.random.choice(list(havelhakimi_graph.nodes()))
        G_finalH.add_edge(random_node, util_node)

        random_node = np.random.choice(list(statbased_graph.nodes()))
        G_finalS.add_edge(random_node, util_node)

    return G_finalC, G_finalH, G_finalS

# Generate and plot the final multi-subgraph network
n_nodes = 500
util = 4
final_graphC, final_graphH, final_graphS = generate_multi_subgraphs_no_stat(n_nodes, util)

# Plot the final network with a professional aesthetic
plt.figure(figsize=(8, 10))
layout = nx.spring_layout(final_graphC, seed=42)
nx.draw(final_graphC, layout, node_size=60, edge_color="black", alpha=0.7, linewidths=0.5, width=0.5)
plt.scatter(*layout[n_nodes], color='red', s=120, label="Utility Node")  # Highlight utility node
plt.title("Chung Lu Network", fontsize=26)
plt.legend()
plt.show()

# Plot the final network with a professional aesthetic
plt.figure(figsize=(8, 10))
layout = nx.spring_layout(final_graphH, seed=42)
nx.draw(final_graphH, layout, node_size=60, edge_color="black", alpha=0.7, linewidths=0.5, width=0.5)
plt.scatter(*layout[n_nodes], color='red', s=120, label="Utility Node")  # Highlight utility node
plt.title("Havel Hakimi Network", fontsize=26)
plt.legend()
plt.show()

# Plot the final network with a professional aesthetic
plt.figure(figsize=(8, 10))
layout = nx.spring_layout(final_graphS, seed=42)
nx.draw(final_graphS, layout, node_size=60, edge_color="black", alpha=0.7, linewidths=0.5, width=0.5)
plt.scatter(*layout[n_nodes], color='red', s=120, label="Utility Node")  # Highlight utility node
plt.title("Statistics based Network", fontsize=26)
plt.legend()
plt.show()

