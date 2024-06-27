import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from scipy.optimize import linear_sum_assignment
import logging
logger = logging.getLogger('progress.log')


def calculate_centroid(pos):
    x_coords, y_coords = zip(*pos.values())
    centroid = (np.mean(x_coords), np.mean(y_coords))
    return centroid


def translate_positions(pos, translation):
    return {node: (pos[node][0] + translation[0], pos[node][1] + translation[1]) for node in pos}


def rotate_positions(pos, angle, centroid):
    rot_matrix = np.array([
        [np.cos(angle), -np.sin(angle)],
        [np.sin(angle), np.cos(angle)]
    ])
    return {
        node: rot_matrix.dot(np.array([pos[node][0] - centroid[0], pos[node][1] - centroid[1]])).tolist() + np.array(
            centroid) for node in pos}

# Function to find the closest node in pos1 for each node in pos2
def find_closest(pos, reference):
    closest = {}
    for key, value in pos.items():
        closest_node = None
        min_dist = float('inf')
        for ref_key, ref_value in reference.items():
            dist = np.linalg.norm(np.array(value) - np.array(ref_value))
            if dist < min_dist:
                min_dist = dist
                closest_node = ref_key
        closest[key] = closest_node
    return closest

def optimize_alignment(pos1, pos2, centroid1, steps=360):
    best_score = float('inf')
    best_pos = {}

    # Mapping pos2 nodes to pos1 based on spatial proximity
    node_mapping = find_closest(pos2, pos1)

    for angle_deg in np.linspace(0, 360, steps, endpoint=False):
        angle_rad = np.radians(angle_deg)
        pos2_rotated = rotate_positions(pos2, angle_rad, centroid1)

        score = 0
        for node2, pos2_val in pos2_rotated.items():
            if node2 in node_mapping:
                node1 = node_mapping[node2]
                # Calculate score using the mapped nodes
                score += np.linalg.norm(np.array(pos1[node1]) - np.array(pos2_val))

        if score < best_score:
            best_score = score
            best_pos = pos2_rotated

    return best_pos, best_score

def map_labels_and_geo(G1, pos1, G2, optimized_pos):
    label_mapping = {}
    for node2 in G2.nodes():
        # if node2 not in optimized_pos: NO SKIPPING NODES
        #     continue  # Skip if no corresponding position exists
        # Find the closest node in G1 for each node in G2 based on the optimized positions
        closest_node1 = min(G1.nodes(), key=lambda n: np.linalg.norm(np.array(pos1[n]) - np.array(optimized_pos[node2])))
        label_mapping[node2] = G1.nodes[closest_node1]['label']
        # Transfer geographic coordinates
        G2.nodes[node2]['pos'] = pos1[closest_node1]
    return label_mapping

def map_labels_and_geo_unique(G1, pos1, G2, optimized_pos):
    # Create a cost matrix based on distances between nodes in G1 and optimized_pos (G2's nodes)
    size_G1 = len(G1.nodes())
    size_G2 = len(G2.nodes())
    cost_matrix = np.zeros((size_G2, size_G1))

    G1_nodes = list(G1.nodes())
    G2_nodes = list(G2.nodes())

    logger.info('Optimized Positions: %s', optimized_pos)

    for i, node2 in enumerate(G2_nodes):
        for j, node1 in enumerate(G1_nodes):
            cost_matrix[i, j] = np.linalg.norm(np.array(pos1[node1]) - np.array(optimized_pos[node2]))

    # Solve the assignment problem to find the minimum cost matches
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    # Create label mapping and set positions based on the assignment
    label_mapping = {}
    for idx, node2 in enumerate(G2_nodes):
        node1 = G1_nodes[col_ind[idx]]
        label_mapping[node2] = G1.nodes[node1]['label']
        G2.nodes[node2]['pos'] = pos1[node1]  # Transfer geographic coordinates
        #also add labels to G2
        labels = {node: str(node) for node in G2.nodes()}
        nx.set_node_attributes(G2, labels, 'label')

    return label_mapping

def main(cyber_nwk, power_nwk, util_id):
    # Assuming G1 and G2 are passed correctly and have node attributes 'Latitude' and 'Longitude'
    G1 = power_nwk
    G2 = cyber_nwk

    pos1 = {node: (attrs['Latitude'], attrs['Longitude']) for node, attrs in G1.nodes(data=True)}
    pos2 = nx.spring_layout(G2)  # This gives G2 initial positions that are arbitrary

    labels = {node: str(node) for node in G1.nodes()}  # Labels are now just the node indices
    print('Labels:', labels)
    nx.set_node_attributes(G1, labels, 'label')

    # Optimally, you would align these positions first before mapping
    centroid1 = calculate_centroid(pos1)
    centroid2 = calculate_centroid(pos2)
    translation = (centroid1[0] - centroid2[0], centroid1[1] - centroid2[1])
    pos2_translated = translate_positions(pos2, translation)

    optimized_pos2, _ = optimize_alignment(pos1, pos2_translated, centroid1)
    logging.info('Optimized positions for G2: %s', optimized_pos2)

    # Mapping labels and geographic information with unique assignment
    mapping_test = map_labels_and_geo_unique(G1, pos1, G2, optimized_pos2)

    # Plotting
    plt.figure(figsize=(12, 6))
    ax1 = plt.subplot(121)
    nx.draw(G1, pos1, node_color='red', with_labels=True, node_size=50)
    plt.title('Network G1 (Original)')

    ax2 = plt.subplot(122)
    nx.draw(G2, nx.get_node_attributes(G2, 'pos'), labels=nx.get_node_attributes(G2, 'label'), node_color='blue',
            with_labels=True, node_size=50)
    plt.title('Network G2 (Aligned with Labels)')

    plt.savefig(f'power_cyber_for_{util_id}.png')

    return mapping_test

if __name__ == "__main__":
    main(cyber_nwk, power_nwk, util_id)

