import json
import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import os
import configparser

import time


start_graph = time.time()
config = configparser.ConfigParser()
config.read('settings.ini')
configuration = config['DEFAULT']['topology_configuration']
case = config['DEFAULT']['case']

print("configuration is: ", configuration)

cwd = os.getcwd()

#### Create Hierarchical Graph of Substation Elements ####
def oldcreate_hierarchical_substation_graph_no_crossings(substation_data):
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

def create_hierarchical_substation_graph_no_crossings(substation_data):
    G = nx.Graph()
    # Define levels for different types of nodes in the hierarchy
    levels = {
        "Router": 4,
        "Outstation": 3.5,
        "HMI": 3.5,
        "Firewall": 3,
        "OT.Switch": 3,
        "Corporate.Switch": 3,
        "LocalWebServer": 1,
        "LocalDatabase": 1,
        "Host": 1,
        "RC": 1,
        "Relay": 0,
    }
    node_positions = {}

    # Add nodes with positions based on their hierarchical level
    switch_count = 0
    shift = 0
    rcount = 0
    for node in substation_data['nodes']:
        words = node['label'].split('.')
        node_id = node['label']
        print(node_id)
        if len(words) < 4:
            continue
        else:
            node_type = words[3].split(' ')[0]  # Extract node type from label
            extra_node_type = words[2]
            relay_num = words[3].split(' ')[1]
        level = levels.get(node_type, 9) if node_type != 'Switch' else levels.get(f"{extra_node_type}.{node_type}", 9)# Default level for unrecognized types
        # x_pos = x_positions[level]

        print(node_type)
        print(f"{extra_node_type}.{node_type}")
        print(level)

        # x_positions[level] += x_level_width  # Increment x position for the next node in the same level
        if node_type == 'Router':
            n_color = '#f2809f'
            x_pos = 0
            y_pos = level
        elif node_type == 'Firewall':
            n_color = '#faa673'
            x_pos = 0
            y_pos = level
        elif f"{extra_node_type}.{node_type}" == 'OT.Switch':
            n_color = '#472f80'
            x_pos = -0.2
            y_pos = level
            node_type = 'OT.Switch'
        elif f"{extra_node_type}.{node_type}" == "Corporate.Switch":
            n_color = '#472f80'
            x_pos = 0.2
            y_pos = level
            node_type = 'Corporate.Switch'
        elif node_type == 'HMI':
            n_color = '#2E6A57'
            x_pos = 0.2
            y_pos = level
        elif node_type == 'Outstation':
            n_color = '#2E6A57'
            x_pos = -0.2
            y_pos = level
        elif node_type == 'RC':
            n_color = '#9f80f2'
            x_pos = -0.2
            y_pos = level
        elif node_type == 'Relay':
            n_color = '#2E6A57'
            x_pos = -0.2 + shift
            y_pos = level
            shift = shift + 0.1
            node_type = f'Relay{rcount}'
            rcount += 1
        elif node_type == "LocalWebServer" or node_type == "LocalDatabase" or node_type == "Host":
            n_color = '#2E6A57'
            x_pos = -0.15 + shift
            y_pos = level
            shift = shift + 0.1

        print(n_color)
        print(node_id)
        node_positions[node_id] = (x_pos, y_pos)
        G.add_node(node_id, label=node_type, color=n_color, pos=(x_pos, y_pos))

    # Add links based on the connections specified in 'links'
    for link in substation_data['links']:
        # label2 = link['destination'].split('.')
        # if substation_data['substation'] not in label2[1]:
        #     continue
        #     # G.add_edge(link['source'], f'{label2[0]}.{label2[1]}')
        # else:
        G.add_edge(link['source'], link['destination'])

    return G, node_positions

def create_hierarchical_utility_graph_no_crossings():
    file_path = os.path.join(cwd, 'Output\\Utilities\\Region.Utility 0.json')
    with open(file_path, 'r') as file:
        utility_data = json.load(file)
    G = nx.Graph()

    levels={}

    # Define levels for different types of nodes in the hierarchy
    levels = {
        "SubstationRouter": 0,
        "SubstationFirewall": 1,
        "Switch": 2,
        "EMS": 1.5,
        "HMI": 2.5,
        "UtilityFirewall": 3,
        "DMZFirewall": 4,
        "UtilityRouter": 4,
        "ICCPServer": 3,
    }
    node_positions = {}
    # x_level_width = 1.0  # Horizontal distance between nodes in the same level

    # # Initialize x positions for nodes in each level to avoid crossings
    # x_positions = {level: level for level in levels.values()}

    # Add nodes with positions based on their hierarchical level
    switch_count=0
    for node in utility_data['nodes']:
        words = node['label'].split('.')
        node_id = node['label']
        if len(words) < 4:
            continue
        else:
            node_type = words[3].split(' ')[0]  # Extract node type from label
        level = levels.get(node_type, 9)  # Default level for unrecognized types
        # x_pos = x_positions[level]

        # x_positions[level] += x_level_width  # Increment x position for the next node in the same level
        if node_type == 'SubstationRouter' or node_type == 'UtilityRouter':
            n_color = '#f2809f'
            x_pos = 0.1
            y_pos = level
        elif node_type == 'SubstationFirewall' or node_type == 'UtilityFirewall':
            n_color = '#faa673'
            x_pos = 0.1
            y_pos = level
        elif node_type == 'Switch':
            switch_count+=1
            n_color = '#472f80'
            if switch_count>1:
                x_pos=-0.15
                y_pos=level+1.5
            else:
                x_pos=0.1
                y_pos=level
        elif node_type == 'EMS' or node_type == 'HMI':
            n_color = '#2E6A57'
            x_pos = 0
            y_pos = level
        elif node_type == 'DMZFirewall':
            n_color = '#faa673'
            x_pos = -0.15
            y_pos = level
        elif node_type == 'ICCPServer':
            n_color = '#2E6A57'
            x_pos = -0.15
            y_pos = level


        print(node_id)
        print(node_type)
        print(x_pos,y_pos)
        node_positions[node_id] = (x_pos, y_pos)
        G.add_node(node_id, label=node_type, color=n_color, pos=(x_pos, y_pos))

    # Add links based on the connections specified in 'links'
    for link in utility_data['links']:
        if 'Bus' in link['destination']:
            continue
        else:
            label2 = link['destination'].split('.')
            if 'Utility 0' not in label2[1]:
                continue
                # G.add_edge(link['source'], f'{label2[0]}.{label2[1]}')
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

def create_utilities_graph_with_color(data, configuration, G):

    if 'star' in configuration:
        for utility in data['utilities']:
            utility_id = utility['label']
            G.add_node(utility_id, pos=(utility['longitude'], utility['latitude']), label='Util', color='#FFA500', size=0.5)

            for substation in utility['substations']:
                if substation['type'] == 'generation':
                    G.add_node(substation['substation'], pos=(substation['longitude'], substation['latitude']), label='Sub',
                           color='#00FF00', size=0.1)
                else:
                    G.add_node(substation['substation'], pos=(substation['longitude'], substation['latitude']), label='Sub',
                           color='#00008B', size=0.1)
                # print(utility_id)
                # print(substation['substation'])
                G.add_edge(utility_id, substation['substation'])
    elif 'radial' in configuration or 'statistics' in configuration:
        for utility in data['utilities']:
            #add substation nodes
            for substation in utility['substations']:
                #if substation type is generation, color it green
                if substation['type'] == 'generation':
                    G.add_node(substation['substation'], pos=(substation['longitude'], substation['latitude']), label='Sub', color='#00FF00', size=0.1)
                elif substation['type'] == 'transmission':
                    G.add_node(substation['substation'], pos=(substation['longitude'], substation['latitude']), label='Sub', color='#00008B', size=0.1)
            #add edge only if there is a link between utility and substation
            #add edges between substations
            for link in utility['links']:
                # print(link['source'], link['destination'])
                if f"{utility['label']}.{utility['utility']}" not in link['destination'] or f"{utility['label']}.{utility['utility']}" not in link['source']:
                    #get substation id from link
                    source_id = link['source'].split(".")[1]
                    # print(source_id)
                    dest_id = link['destination'].split(".")[1]
                    # print(dest_id)
                    G.add_edge(source_id, dest_id)

            utility_id = utility['label']
            G.add_node(utility_id, pos=(utility['longitude'], utility['latitude']), label='Util', color='#FFA500', size=0.5)

    else:
        print("Configuration is neither radial, statistics based nor star.")

    return G

def add_regulatory_nodes(path):
    G = nx.Graph()

    files = os.listdir(path)
    for file in files:
        filepath = os.path.join(path, file)
        print(filepath)
        with open(filepath,'r', encoding='utf-8') as file:
            data = json.load(file)

        utilities_graph_with_color = create_utilities_graph_with_color(data, configuration, G)

        utilities_graph_with_color.add_node(data['label'], pos=(data['longitude'], data['latitude']), label='Reg', color='#DC143C', size=0.8)
        #add edge between utility and region
        for utility in data['utilities']:
            utilities_graph_with_color.add_edge(utility['label'], data['label'])

    return utilities_graph_with_color


def main(code_to_run, file_path):
    if code_to_run==1:
        file = "Output/Substations/"
        files = os.listdir(file)

        file_path = os.path.join(file, files[0])
        # Load the JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)
        # Select a specific substation to visualize
        selected_substation_data = data
        substation_graph, substation_positions = create_hierarchical_substation_graph_no_crossings(selected_substation_data)
        colors = [substation_graph.nodes[node]['color'] for node in substation_graph.nodes]
        labels = nx.get_node_attributes(substation_graph, 'label')

        # Plotting the graph
        plt.figure(figsize=(9, 5))
        nx.draw(substation_graph, pos=substation_positions, with_labels=False, labels=labels, node_size=300,
                node_color=colors, font_size=12, font_weight='bold')
        y_off = 0.3
        substation_positions_higher = {}
        for k, v in substation_positions.items():
            substation_positions_higher[k] = (v[0], v[1] + y_off)
        nx.draw_networkx_labels(substation_graph, substation_positions_higher, labels, font_size=10, font_weight='bold')
        plt.savefig('Output/Substations/Substation_Internal.png')
        plt.show()
    if code_to_run==2:
        ##### Code to generate utility data #####
        # Load the shapefile
        if '500' in case:
            gdf = gpd.read_file('Nc.shp')
        elif '2k' in case:
            gdf = gpd.read_file('Tx.shp')
        elif '10k' in case:
            gdf = gpd.read_file('WECC.shp')

        # Create the utilities graph

        graph_with_reg = add_regulatory_nodes('Output\\Regulatory')

        print("Number of edges in the graph: ", graph_with_reg.number_of_edges())
        print("Graph is connected: ", nx.is_connected(graph_with_reg))

        components = list(nx.connected_components(graph_with_reg))
        print(f"The graph has {len(components)} connected components.")
        for i, component in enumerate(components, 1):
            print(f"Component {i}: {component}")

        # Plotting
        fig, ax = plt.subplots(figsize=(15, 15))
        gdf.plot(ax=ax, color='white', edgecolor='black', alpha=0.2)  # Plot the shapefile


        # Plot the utilities and substations
        pos = nx.get_node_attributes(graph_with_reg, 'pos')
        labels = nx.get_node_attributes(graph_with_reg, 'label')
        colors = [graph_with_reg.nodes[node]['color'] for node in graph_with_reg.nodes]
        node_sizes = [graph_with_reg.nodes[node]['size'] for node in graph_with_reg.nodes()]
        print(colors)

        nx.draw(graph_with_reg, pos, with_labels=False, labels=labels, node_size=node_sizes, node_color=colors, width=0.2)
        plt.savefig('Output\\Regulatory\\radial.pdf')
        # plt.show()
    elif code_to_run==3:
        # Select a specific utility to visualize
        # selected_utility_data = data['utilities'][0]
        utility_graph, utility_positions = create_hierarchical_utility_graph_no_crossings()
        colors = [utility_graph.nodes[node]['color'] for node in utility_graph.nodes]
        labels = nx.get_node_attributes(utility_graph, 'label')

        print(utility_positions)

        # Plotting the graph
        plt.figure(figsize=(9, 5))
        labels = nx.get_node_attributes(utility_graph, 'label')
        # layout = nx.spring_layout(utility_graph, iterations=300, k=15, pos=utility_positions)
        nx.draw(utility_graph, pos=utility_positions, with_labels=False, labels=labels, node_size=300, node_color=colors, font_size=8, font_weight='bold')
        y_off = 0.3
        utility_positions_higher = {}
        for k, v in utility_positions.items():
            utility_positions_higher[k] = (v[0], v[1]+y_off)
        nx.draw_networkx_labels(utility_graph, utility_positions_higher, labels, font_size=10, font_weight='bold')
        # nx.draw(utility_graph, utility_positions, with_labels=True, labels=labels, node_size=500,
        #         node_color='lightgreen', font_size=12, arrows=True)
        plt.title(
            f'Graph of Utility: with Hierarchical Structure and No Crossings')
        plt.savefig('Output\\Utilities\\Utility_Internal.png')
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
                node_color='lightgreen', font_size=12)
        plt.title(
            f'Graph of Substation: {selected_region_data["region"]} with Hierarchical Structure and No Crossings')
        # plt.show()


if __name__ == "__main__":
    code_to_run = 2
    #1-Generate substation internal layout
    #2-Generate substation-utility graph on a map
    #3-Generate utility internal layout
    #4-Generate regulatory/region internal layout
    # file_path = os.path.join(cwd, 'Output\\Regulatory\\Regulatory.json')
    #
    # # Load the JSON file
    # with open(file_path, 'r') as file:
    #     data = json.load(file)
    # main(code_to_run, data)
    main(code_to_run, [])

end_graph = time.time()
total_time_graph = end_graph - start_graph
print(f"{total_time_graph:.2f} seconds")  #output time with 2 decimal places