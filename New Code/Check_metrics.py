import networkx as nx
import json
import statistics
from geopy.distance import geodesic
import time

start_metrics = time.time()
filename = 'D:/Github/ECEN689Project/New Code/Output/Regulatory/Regulatory.json'
#filename = 'C:/GitHubProjects/ECEN689Project/New Code/Output/Regulatory/Regulatory.json'
# Open the JSON file and load its contents into a Python variable
with open(filename, 'r') as file:
    json_data = json.load(file)

G = nx.Graph()
# Parse the JSON data to populate the graph
# for utility in json_data["utilities"]:
#     # add a node for each utility
#     G.add_node(utility['label'])
#     for substation in utility["substations"]:
#         # add a node for each substation firewall? or router?
#         G.add_node(substation['label'])
#         for node in substation["nodes"]:
#             G.add_node(node["label"])
#         for link in substation["links"]:
#             G.add_edge(link["source"], link["destination"])
#         G.add_node(node["label"])
coordinates = {}
for node in json_data["nodes"]:
#    label = node["label"]
#    lat = node["latitude"]
#    lon = node["longitude"]
#    coordinates[label] = (lat, lon)
    G.add_node(node["label"])

for link in json_data["links"]:
#    source = link["source"]
#    destination = link["destination"]
#    source_coords = coordinates[source]
#    destination_coords = coordinates[destination]
#    weight = geodesic(source_coords, destination_coords).kilometers
    G.add_edge(link["source"], link["destination"])

# Calculating metrics
average_path_length = nx.average_shortest_path_length(G) if nx.is_connected(G) else "Graph is not connected"
# average_path_length & degree & diameter for routers only?
node_degree = dict(G.degree())
diameter = nx.diameter(G) if nx.is_connected(G) else "Graph is not connected"
worst_case_connectivity = len(min(nx.connectivity.cuts.minimum_node_cut(G), key=len)) if nx.is_connected(G) else "Graph is not connected"
algebraic_connectivity = nx.algebraic_connectivity(G)
number_of_links = G.number_of_edges()
number_of_nodes = G.number_of_nodes()
network_density = nx.density(G)

#average shortest path length TRUE distance
#if nx.is_connected(G):
#    avg_path_length_km = nx.average_shortest_path_length(G, weight='weight')
#    avg_path_length_miles = avg_path_length_km * 0.621371  # Convert km to miles
#else:
#    avg_path_length_km = "Graph is not connected"
#    avg_path_length_miles = "Graph is not connected"

end_metrics = time.time()
total_time_metrics = end_metrics - start_metrics
#total_time = (adding all three times, json, graph, and metrics)

max_degree = max(node_degree.values())
min_degree = min(node_degree.values())
avg_degree = statistics.mean(node_degree.values())

#print(average_path_length, node_degree, diameter, worst_case_connectivity, algebraic_connectivity, number_of_links, network_density)
print("Average path length:  ", average_path_length)
#print("Average shortest path length (km): ", avg_path_length_km)
#print("Average shortest path length (miles): ", avg_path_length_miles)
print("Diameter:  ", diameter)
print("Minimum Degree: ", min_degree)
print("Maximum Degree: ", max_degree)
print("Average Degree: ", avg_degree)
print("Worst Case Connectivity:  ", worst_case_connectivity)
print("Algebraic connectivity:  ", algebraic_connectivity)
print("Number of links:  ", number_of_links)
print("Total number of nodes:  ", number_of_nodes)
print("Network Density:  ", network_density)
print("Total Generation Time", total_time_metrics)
