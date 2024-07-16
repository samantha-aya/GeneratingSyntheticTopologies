import networkx as nx
import json
import statistics
import numpy as np
import time
import os
import geopandas as gpd
import matplotlib.pyplot as plt
import configparser
import re
config = configparser.ConfigParser()
config.read('settings.ini')

start_metrics = time.time()
G = nx.Graph()
utils_path = 'Output\\Utilities'
utils_files = os.listdir(utils_path)
added_routers = set()
util_routers = 0
sub_routers = 0
i=0

for file in utils_files:
    filepath = os.path.join(utils_path, file)
    print(filepath)
    with open(filepath, 'r', encoding='utf-8') as file:
        utility = json.load(file)
        # print(utility['substationsRouter'][0])
        utilLabel = utility['substationsRouter'][0]['label']
        for nodes in utility['nodes']:
            if 'Router' in nodes['label'] and nodes['label'] not in added_routers:
                #print(nodes['label'])
                G.add_node(nodes['label'], pos=(utility['longitude'], utility['latitude']), label=nodes['label'], color='#FFA500')
                added_routers.add(nodes['label'])
                util_routers += 1

        for substation in utility['substations']:
           for nodes in substation['nodes']:
               if 'Router' in nodes['label']:
                   router_info = nodes['label']
                   if nodes['label'] not in added_routers:
                       G.add_node(nodes['label'], pos=(substation['longitude'], substation['latitude']), label=nodes['label'], color='#00FF00')
                       added_routers.add(router_info)
                       sub_routers += 1

        for link in utility['links']:
            if ('Router' in link["source"]) and ('Router' in link["destination"]) and link['source'] in added_routers and link['destination'] in added_routers:
                n1 = [n for n, d in G.nodes(data=True) if d['label'] == link["source"]][0]
                n2 = [n for n, d in G.nodes(data=True) if d['label'] == link["destination"]][0]
                G.add_edge(n1, n2)
            elif 'Router' in link["source"] and 'Router' not in link["destination"]:
                G.add_edge(link["source"], utilLabel)

# # add the utility edges
reg_path = 'Output/Regulatory/'
reg_files = os.listdir(reg_path)
for file in reg_files:
    filepath = os.path.join(reg_path, file)
    print(filepath)
    with open(filepath, 'r') as file:
       reg_data = json.load(file)
       # adding regulatory node to the graph
       G.add_node(reg_data['regulatoryRouter'][0]['label'], pos=(reg_data['longitude'], reg_data['latitude']), label=reg_data['regulatoryRouter'][0]['label'], color='#DC143C')
       added_routers.add(reg_data['regulatoryRouter'][0]['label'])

       print(reg_data['links'])
       for link in reg_data['links']:
           if ('Router' in link["source"]) and ('Router' in link["destination"]) and link['source'] in added_routers and link['destination'] in added_routers:
               # find node with label link["source"] and link["destination"]
               n1 = [n for n, d in G.nodes(data=True) if d['label'] == link["source"]][0]
               n2 = [n for n, d in G.nodes(data=True) if d['label'] == link["destination"]][0]
               G.add_edge(n1, n2)
case = config['DEFAULT']['case']
if '500' in case:
    gdf = gpd.read_file('Nc.shp')
elif '2k' in case:
    gdf = gpd.read_file('Tx.shp')
elif '10k' in case:
    gdf = gpd.read_file('WECC.shp')

gdf = gpd.read_file('Nc.shp')
fig, ax = plt.subplots(figsize=(15, 15))
pos = nx.get_node_attributes(G, 'pos')
colors = [G.nodes[node]['color'] for node in G.nodes]
gdf.plot(ax=ax, color='white', edgecolor='black', alpha=0.1)  # Plot the shapefile
nx.draw(G, pos, with_labels=False, node_size=20, width=0.2, node_color=colors)
#plt.show()

# Calculating metrics
average_path_length = nx.average_shortest_path_length(G) if nx.is_connected(G) else "Graph is not connected"
# average_path_length & degree & diameter for routers only?

# gets node degree max and min and also plots the node degree distribution
fig, ax = plt.subplots(figsize=(8, 6))
degree_sequence = sorted((d for n, d in G.degree()), reverse=True)
max_degree = max(degree_sequence)
min_degree = min(degree_sequence)
degrees, counts = np.unique(degree_sequence, return_counts=True)
ax.bar(degrees, counts)
ax.plot(degrees, counts, color='red', marker='o')
ax.set_title("Node Degree Distribution", fontsize=16)
ax.set_xlabel("Node Degree", fontsize=16)
ax.set_ylabel("Number of Nodes", fontsize=16)
fig.tight_layout()
#plt.show()

diameter = nx.diameter(G) if nx.is_connected(G) else "Graph is not connected"
worst_case_connectivity = len(min(nx.connectivity.cuts.minimum_node_cut(G), key=len)) if nx.is_connected(G) else "Graph is not connected"
algebraic_connectivity = nx.algebraic_connectivity(G)
number_of_links = G.number_of_edges()
number_of_nodes = G.number_of_nodes()
network_density = nx.density(G)

#Calculating total ACL count
utilTotalACLs = 0
subTotalACLs = 0
regTotalACLs = 0

# Loop through all files in the specified directory
for file in reg_files:
    filepath = os.path.join(reg_path, file)
    with open(filepath, 'r') as file:
        data = json.load(file)
        for utility in data['utilities']:
            for node in utility['nodes']:
                if 'Firewall' in node['label']:
                    keysList = list(node['acls'].keys())
                    aclCount = len(keysList)
                    utilTotalACLs +=aclCount
                    print(keysList)
                    #print(aclCount)
            node = ""
            for substation in utility['substations']:
                for node in substation['nodes']:
                    if '.Firewall' in node['label']:
                        keysList = list(node['acls'].keys())
                        aclCount = len(keysList)
                        subTotalACLs += aclCount
                        #print()
                        print(keysList)
                        #print(aclCount)

totalACLs = utilTotalACLs + subTotalACLs + regTotalACLs
print(f"Regulatory ACLs: ", regTotalACLs)
print(f"Utility ACLs: ", utilTotalACLs)
print(f"Substation ACLs: ", subTotalACLs)
print(f"Number of ACLs: ", totalACLs)
#        for substation in utility['substations']:
#            for nodes in substation['nodes']:
#                if 'acl' in nodes['acls']:
#                    acl_count += 1
#                    print(acl_count)
#print(f"The string 'acl' appears {acl_count} times in the JSON files.")


#average shortest path length TRUE distance
#if nx.is_connected(G):
#    avg_path_length_km = nx.average_shortest_path_length(G, weight='weight')
#    avg_path_length_miles = avg_path_length_km * 0.621371  # Convert km to miles
#else:
#    avg_path_length_km = "Graph is not connected"
#    avg_path_length_miles = "Graph is not connected"

end_metrics = time.time()
total_time_metrics = end_metrics - start_metrics
# total_time = (adding all three times, json, graph, and metrics)



#print(average_path_length, node_degree, diameter, worst_case_connectivity, algebraic_connectivity, number_of_links, network_density)
print("Average path length:  ", average_path_length)
# print("Average shortest path length (km): ", avg_path_length_km)
# print("Average shortest path length (miles): ", avg_path_length_miles)
print("Diameter:  ", diameter)
print("Minimum Degree: ", min_degree)
print("Maximum Degree: ", max_degree)
# print("Average Degree: ", avg_degree)
# print("Worst Case Connectivity:  ", worst_case_connectivity)
# print("Algebraic connectivity:  ", algebraic_connectivity)
print("Number of links:  ", number_of_links)
print("Total number of nodes:  ", number_of_nodes)
print(f"{sub_routers} substations, {util_routers} utilities, and 1 regulatory")
print(f"{len(added_routers)}")
print("Network Density:  ", network_density)
print("Total Generation Time", total_time_metrics)


components = list(nx.connected_components(G))
print(f"The graph has {len(components)} connected components.")
for i, component in enumerate(components, 1):
    print(f"Component {i}: {component}")