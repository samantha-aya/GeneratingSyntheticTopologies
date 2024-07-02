import json
import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import os
import configparser
#import time

#start_graph = time.time()
config = configparser.ConfigParser()
config.read('settings.ini')
configuration = config['DEFAULT']['topology_configuration']
case = config['DEFAULT']['case']

print("configuration is: ", configuration)

cwd = os.getcwd()

#### Create Hierarchical Graph of Substation Elements ####
def create_hierarchical_substation_graph_no_crossings(substation_data):
    G = nx.DiGraph()

    # Define levels for different types of nodes in the hierarchy
    levels = {
        "RC": 1,
        "Relay": 0,
        "Switch": 2,
        "Router": 4,
        "Host": 1,
        "Firewall": 3,
        "LocalDatabase": 1,
        "LocalWebServer": 1
    }
    node_positions = {}
    y_level_dist = 1.0  # Vertical distance between levels
    x_level_width = 1.0  # Horizontal distance between nodes in the same level

    # Initialize x positions for nodes in each level to avoid crossings
    x_positions = {level: 0.0 for level in levels.values()}


    # Add nodes with positions based on their hierarchical level
    i=1
    for node in substation_data['nodes']:
        node_id = node['label']
        words = node['label'].split('.')
        node_type = words[3].split(' ')[0]  # Extract node type from label
        print(node_type)
        level = levels.get(node_type, 6)  # Default level for unrecognized types
        x_pos = x_positions[level]
        y_pos = level * y_level_dist
        node_positions[node_id] = (x_pos, y_pos)
        x_positions[level] += x_level_width  # Increment x position for the next node in the same level
        print(node['label'])
        print(x_positions[level], y_pos)
        G.add_node(node_id, label=node_type)#node['label'])

    # Add links based on the connections specified in 'links'
    for link in substation_data['links']:
        G.add_edge(link['source'], link['destination'])

    return G, node_positions

def create_hierarchical_utility_graph_no_crossings(utility_data):
    G = nx.DiGraph()

    # Define levels for different types of nodes in the hierarchy
    levels = {
        "RC": 2,
        "EMS": 1,
        "Switch": 3,
        "Router": 4,
        "DMZ": 1,
        "Host": 1,
        "Firewall": 5,
        "Bus": 0
    }
    node_positions = {}
    y_level_dist = 1.0  # Vertical distance between levels
    x_level_width = 1.0  # Horizontal distance between nodes in the same level

    # Initialize x positions for nodes in each level to avoid crossings
    x_positions = {level: 0.0 for level in levels.values()}

    # Add nodes with positions based on their hierarchical level
    for node in utility_data['nodes']:
        node_id = node['label']
        words = node['label'].split('.')
        if len(words) < 4:
            continue # Extract node type from label
        else:
            node_type = words[3].split(' ')[0]  # Extract node type from label
        level = levels.get(node_type, 6)  # Default level for unrecognized types
        x_pos = x_positions[level]
        y_pos = level * y_level_dist
        node_positions[node_id] = (x_pos, y_pos)
        x_positions[level] += x_level_width  # Increment x position for the next node in the same level
        G.add_node(node_id, label=node['label'])

    # Add links based on the connections specified in 'links'
    for link in utility_data['links']:
        if 'Bus' in link['destination']:
            continue
        else:
            G.add_edge(link['source'], link['destination'])

    return G, node_positions

def create_hierarchical_region_graph_no_crossings(region_data):
    G = nx.DiGraph()

    # Define levels for different types of nodes in the hierarchy
    levels = {
        "Controller": 1,
        "EMS": 0,
        "Switch": 2,
        "Router": 3,
        "DMZ": 0,
        "Firewall": 4
    }
    node_positions = {}
    y_level_dist = 1.0  # Vertical distance between levels
    x_level_width = 2.0  # Horizontal distance between nodes in the same level

    # Initialize x positions for nodes in each level to avoid crossings
    x_positions = {level: 0.0 for level in levels.values()}

    # Add nodes with positions based on their hierarchical level
    for node in region_data['nodes']:
        node_id = node['id']
        node_type = node['label'].split('0')[0]  # Extract node type from label
        level = levels.get(node_type, 6)  # Default level for unrecognized types
        x_pos = x_positions[level]
        y_pos = level * y_level_dist
        node_positions[node_id] = (x_pos, y_pos)
        x_positions[level] += x_level_width  # Increment x position for the next node in the same level
        G.add_node(node_id, label=node['label'])

    # Add links based on the connections specified in 'links'
    for link in region_data['links']:
        G.add_edge(link['source'], link['destination'])

    return G, node_positions

def create_utilities_graph_with_color(data, configuration):
    G = nx.Graph()
    if 'star' in configuration:
        for utility in data['utilities']:
            utility_id = utility['label']
            G.add_node(utility_id, pos=(utility['longitude'], utility['latitude']), label='Util', color='red')

            for substation in utility['substations']:
                if substation['type'] == 'generation':
                    G.add_node(substation['substation'], pos=(substation['longitude'], substation['latitude']), label='Sub',
                           color='green')
                else:
                    G.add_node(substation['substation'], pos=(substation['longitude'], substation['latitude']), label='Sub',
                           color='lightblue')
                # print(utility_id)
                # print(substation['substation'])
                G.add_edge(utility_id, substation['substation'])
    elif 'radial' in configuration or 'statistics' in configuration:
        for reg in data['region']:
            for utility in data['utilities']:
                #add substation nodes
                for substation in utility['substations']:
                    #if substation type is generation, color it green
                    if substation['type'] == 'generation':
                        G.add_node(substation['substation'], pos=(substation['longitude'], substation['latitude']), label='Sub', color='green')
                    elif substation['type'] == 'transmission':
                        G.add_node(substation['substation'], pos=(substation['longitude'], substation['latitude']), label='Sub', color='lightblue')
                #add edge only if there is a link between utility and substation
                #add edges between substations
                for link in utility['links']:
                    print(link['source'], link['destination'])
                    if f"{utility['label']}.{utility['utility']}" not in link['destination'] or f"{utility['label']}.{utility['utility']}" not in link['source']:
                        #get substation id from link
                        source_id = link['source'].split(".")[1]
                        print(source_id)
                        dest_id = link['destination'].split(".")[1]
                        print(dest_id)
                        G.add_edge(source_id, dest_id)

                utility_id = utility['label']
                G.add_node(utility_id, pos=(utility['longitude'], utility['latitude']), label='Util', color="red")

    else:
        print("Configuration is neither radial, statistics based nor star.")

    return G

def main(code_to_run, data):
    if code_to_run==1:
        # Select a specific substation to visualize
        selected_substation_data = data['utilities'][3]['substations'][40]
        # print("###############")
        # print(data['utilities'][0])
        # print("###############")
        # print(selected_substation_data)
        # print("###############")
        substation_graph, substation_positions = create_hierarchical_substation_graph_no_crossings(selected_substation_data)

        # Plotting the substation graph
        plt.figure(figsize=(12, 10))
        labels = nx.get_node_attributes(substation_graph, 'label')
        nx.draw(substation_graph, substation_positions, with_labels=True, labels=labels, node_size=500,
                node_color='lightgreen', font_size=12, arrows=True)
        plt.title(
            f'Graph of Substation: {selected_substation_data["substation"]} with Hierarchical Structure and No Crossings')
        plt.show()
    elif code_to_run==2:
        ##### Code to generate utility data #####
        # Load the shapefile
        if '500' in case:
            gdf = gpd.read_file('Nc.shp')
        elif '2k' in case:
            gdf = gpd.read_file('Tx.shp')
        elif '10k' in case:
            gdf = gpd.read_file('WECC.shp')

        # Create the utilities graph
        utilities_graph_with_color = create_utilities_graph_with_color(data, configuration)

        # Plotting
        fig, ax = plt.subplots(figsize=(15, 15))
        gdf.plot(ax=ax, color='white', edgecolor='black', alpha=0.1)  # Plot the shapefile

        # Adjusting the node size
        small_node_size = 10  # Smaller size for nodes

        # Plot the utilities and substations
        pos = nx.get_node_attributes(utilities_graph_with_color, 'pos')
        labels = nx.get_node_attributes(utilities_graph_with_color, 'label')
        colors = [utilities_graph_with_color.nodes[node]['color'] for node in utilities_graph_with_color.nodes]

        nx.draw(utilities_graph_with_color, pos, with_labels=False, labels=labels, node_size=small_node_size, node_color=colors, width=0.2,font_size=5)
        plt.savefig('Output\\Regulatory\\Utilities_statistics.pdf')
        plt.show()
    elif code_to_run==3:
        # Select a specific utility to visualize
        selected_utility_data = data['utilities'][0]
        utility_graph, utility_positions = create_hierarchical_utility_graph_no_crossings(
            selected_utility_data)

        # Plotting the substation graph
        plt.figure(figsize=(12, 10))
        labels = nx.get_node_attributes(utility_graph, 'label')
        nx.draw(utility_graph, utility_positions, with_labels=True, labels=labels, node_size=500,
                node_color='lightgreen', font_size=12, arrows=True)
        plt.title(
            f'Graph of Utility: {selected_utility_data["utility"]} with Hierarchical Structure and No Crossings')
        plt.show()
    elif code_to_run==4:
        # Select a specific substation to visualize
        selected_region_data = data['region'][0]
        region_graph, region_positions = create_hierarchical_region_graph_no_crossings(
            selected_region_data)

        # Plotting the substation graph
        plt.figure(figsize=(12, 10))
        labels = nx.get_node_attributes(region_graph, 'label')
        nx.draw(region_graph, region_positions, with_labels=True, labels=labels, node_size=500,
                node_color='lightgreen', font_size=12, arrows=True)
        plt.title(
            f'Graph of Substation: {selected_region_data["region"]} with Hierarchical Structure and No Crossings')
        plt.show()


if __name__ == "__main__":
    code_to_run = 2
    #1-Generate substation internal layout
    #2-Generate substation-utility graph on a map -- Modify this part to use maps (some fancy python packages)
    #3-Generate utility internal layout
    #4-Generate regulatory/region internal layout
    file_path = os.path.join(cwd, 'Output\\Regulatory\\Regulatory.json')

    # Load the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)
    main(code_to_run, data)

#end_graph = time.time()
#total_time_graph = end_graph - start_graph
#print(total_time_graph)