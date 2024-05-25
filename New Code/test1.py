import networkx as nx

power_nwk = nx.Graph()
power_nwk.add_nodes_from([1, 2, 3, 4])
power_nwk.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1)])

print(power_nwk.nodes[1])
print(power_nwk.nodes.data())
print(power_nwk.nodes.items())