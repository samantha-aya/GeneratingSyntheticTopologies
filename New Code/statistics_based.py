
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import random


from ortools.sat.python import cp_model
import math

import igraph as ig
import matplotlib.pyplot as plt
from numpy.linalg import norm
import logging
import os

cwd = os.getcwd()
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(filename=os.path.join(cwd, 'progress_stats.log'), filemode='w', level=logging.INFO)
#logging.basicConfig(filename='C:/ECEN689Project/New Code/progress.log', filemode='w', level=logging.INFO)
loggerstat = logging.getLogger()

def lognormal(x, a, b):
    # numpy.random.lognormal
    return 1/(a*x*np.sqrt(2*np.pi))*np.exp(-np.power(np.log(x) - b, 2)/(2*np.power(a, 2)))

def havel_hakimi(seq):
    # if seq is empty or only contains zeros,
    # degree sequence is valid
    if len(seq) < 1 or all(deg == 0 for deg in seq):
        print("Finished! Graph IS constructable with Havel Hakimi algorithm.")
        return True

    seq.sort()

    last = seq[len(seq)-1]
    if last > len(seq)-1:
        print("Failed! Graph IS NOT constructable with Havel Hakimi algorithm.")
        return False

    # remove last element
    seq.remove(last)

    # iterate seq backwards
    for num in range(len(seq)-1, len(seq)-last-1, -1):
        if seq[num] > 0:
            seq[num] -= 1
        else:
            print("\nFailed! Graph is not constructable with Havel Hakimi algorithm")
            return False

    # print(" --alg-->", end="")
    # print(seq)

    # recursive call
    return havel_hakimi(seq)

def find_random_edge(g, exclude_edges=set()):
    edges = list(g.edges())
    random.shuffle(edges)
    for edge in edges:
        if edge not in exclude_edges and (edge[1], edge[0]) not in exclude_edges:
            return edge
    return None

def double_edge_swap(g, u1, v1, u2, v2):
    # Ensure no parallel edges, self-loops, and edges exist in the graph
    if (g.has_edge(u1, v2) or g.has_edge(u2, v1) or
            u1 == v2 or u2 == v1 or
            not g.has_edge(u1, v1) or not g.has_edge(u2, v2)):
        return False

    # Remove the old edges
    g.remove_edge(u1, v1)
    g.remove_edge(u2, v2)

    # Add the new edges
    g.add_edge(u1, v2)
    g.add_edge(u2, v1)
    return True

def reduce_nodes_to_n(g, n):
    nodes_to_remove = [node for node in g.nodes() if g.degree(node) == 1]
    while len(g.nodes()) > n and nodes_to_remove:
        node = nodes_to_remove.pop()
        g.remove_node(node)
        print(f"Removed node {node} with degree 1 to reduce the number of nodes")

        # Update the list of nodes to remove
        nodes_to_remove = [node for node in g.nodes() if g.degree(node) == 1]

    if len(g.nodes()) > n:
        print(f"Unable to reduce the number of nodes to {n} by removing only nodes with degree 1")

def generate_nwk(subs, gens):
    metrics_dict = {}
    probability = lognormal(np.array(range(1,11)), 0.57627298, 0.56637515 )
    # add 0.003 to each value in probablity
    # probability = np.add(probability, 0.003)
    # generate n integers from the probablity distribution
    num_sub = subs
    n = subs
    print("Num of vertices:", n)

    expected = (probability * n).astype(int)
    sum_degree = round(n*1.0777)*2
    #sum_degree = n*(n-1)*nx.density(BC)
    print(expected, sum_degree)
    n_degree = len(expected)
    print(sum(expected))

    # Creates the model.
    model = cp_model.CpModel()

    # Creates the variables.
    nodes = []
    residues = []
    degrees = list(range(1, n_degree+1))
    for i in range(10):
        nodes.append(model.NewIntVar(0, n, 'nodes[%i]' % i))
        residues.append(model.NewIntVar(0, n, 'residues[%i]' % i))

    # Creates the constraints.
    model.Add(sum([node*degree for node, degree in zip(nodes, degrees)]) == sum_degree)
    for i in range(n_degree):
        model.AddAbsEquality(residues[i], (expected[i] - nodes[i])*degrees[i])

    # Create the Havel-Hakimi constraint
    allowable_max_degree = math.floor(np.sqrt(n)*2) - 2
    if allowable_max_degree < max(degrees):
        for i in range(allowable_max_degree+1, max(degrees)):
            model.Add(nodes[i-1] == 0)

    # Creates the objective
    model.Minimize(sum([res for res in residues]))

    # Creates a solver and solves the model.
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f'Maximum of objective function: {solver.ObjectiveValue()}\n')
        for i in range(n_degree):
            print(f'x[{degrees[i]}] = {solver.Value(nodes[i])}')
    else:
        print('No solution found.')

    # Statistics.
    print('\nStatistics')
    print(f'  status   : {solver.StatusName(status)}')
    print(f'  conflicts: {solver.NumConflicts()}')
    print(f'  branches : {solver.NumBranches()}')
    print(f'  wall time: {solver.WallTime()} s')

    seq = []
    for i in range(n_degree):
        seq += [degrees[i] for _ in range(solver.Value(nodes[i]))]
    # temp = expected #[45,37,16,7,3,4 , 0 , 0 , 0 , 0]
    # for i in range(10):
    #     seq += [degrees[i] for _ in range(temp[i])]
    seq = np.array(seq)
    print("seq", seq)
    print(len(seq))

    havel_hakimi(seq.tolist())

    target = np.array([-0.0728, 0.023, -0.355])
    best = None
    best_dist = float('inf')
    for i in range(10000):
        #print('iteration:', i)
        g = ig.Graph.Degree_Sequence(seq.tolist(), method="simple") #nx.havel_hakimi_graph(seq.tolist()) #
        g = ig.Graph.to_networkx(g)

        if len(g.nodes()) < n:
            u = random.choice(list(g.nodes()))
            g.add_node(len(g.nodes())+1)
            g.add_edge(u, len(g.nodes())+1)

        loggerstat.info(f"Graph generated with {len(g.nodes())} nodes and {len(g.edges())} edges")

        #if the graph is not connected then get all the isolated components and add edges between them
        if not nx.is_connected(g):
           # print("Graph is not connected")
            isolated_components = list(nx.connected_components(g))

            # Connect isolated components
            for i in range(len(isolated_components) - 1):
                component1 = isolated_components[i]
                component2 = isolated_components[i + 1]

                # Select random nodes from each component to connect
                node1 = random.choice(list(component1))
                node2 = random.choice(list(component2))

                # Ensure no self-loops
                while node1 == node2:
                    node2 = random.choice(list(component2))

                # Perform a double-edge swap
                random_edge1 = find_random_edge(g)
                random_edge2 = find_random_edge(g, {random_edge1})

                if random_edge1 and random_edge2:
                    u1, v1 = random_edge1
                    u2, v2 = random_edge2

                    # Swap edges to maintain the degree of nodes
                    if double_edge_swap(g, u1, v1, node1, node2):
                        print(f"Connected node {node1} from component {i} to node {node2} from component {i + 1}")
                    else:
                        # If swap was not successful, connect directly and adjust later
                        g.add_edge(node1, node2)
                        #print(
                            #f"Directly connected node {node1} from component {i} to node {node2} from component {i + 1}")
                else:
                    # If not enough edges to swap, connect directly and adjust later
                    g.add_edge(node1, node2)
                    #print(f"Directly connected node {node1} from component {i} to node {node2} from component {i + 1}")

        # Ensure no vertex has degree 0 by adding edges if necessary
        for node in g.nodes():
            if g.degree(node) == 0:
                other_node = random.choice(list(g.nodes()))
                while other_node == node or g.has_edge(node, other_node):
                    other_node = random.choice(list(g.nodes()))

                g.add_edge(node, other_node)
                #print(f"Added edge between node {node} and node {other_node} to ensure no vertex has degree 0")

        # Reduce the number of nodes to the desired number
        reduce_nodes_to_n(g, subs)

        # Verify the graph is now connected
        if nx.is_connected(g):
            print("Graph is now connected")
        else:
            print("Graph is still not connected")

        A = g.edges()
        subbase = nx.Graph(A)
        eigens = nx.adjacency_spectrum(subbase)
        atts = np.array([abs(eigens[0]) - abs(eigens[1]), nx.average_clustering(subbase), nx.degree_assortativity_coefficient(subbase)])
        dist = norm(atts - target)
        if dist < best_dist:
            best_dist = dist
            best = subbase


    plt.figure(figsize=(16,16))
    # largest_component = []
    # for i, c in enumerate(nx.connected_components(base)):
    #     if len(c) > len(largest_component):
    #         largest_component = c
    # subbase = base.subgraph(largest_component)
    subbase = best

    #remove self loops from subbase
    subbase.remove_edges_from(nx.selfloop_edges(subbase))
    print('Num of nodes:', len(subbase.nodes()))
    density = len(subbase.edges())/len(subbase.nodes())
    print('Density:', len(subbase.edges())/len(subbase.nodes()))
    # print('Density:', nx.density(subbase))
    diameter = nx.diameter(subbase)
    print('Diameter:',diameter)
    print("Average diameter", nx.average_shortest_path_length(subbase))
    eigens = nx.adjacency_spectrum(subbase)
    print("Spectral gap:", abs(eigens[0]) - abs(eigens[1]))
    print("Clustering coefficient:", nx.average_clustering(subbase))
    print("Assortativity:", nx.degree_assortativity_coefficient(subbase))
    pos = nx.kamada_kawai_layout(subbase)
    nx.draw_networkx(subbase,pos=pos,node_color='blue',node_size=90,with_labels=False)

    metrics_dict['Nodes'] = len(subbase.nodes())
    metrics_dict['Density'] = density
    metrics_dict['Diameter'] = diameter
    metrics_dict['Average Diameter'] = nx.average_shortest_path_length(subbase)
    metrics_dict['Spectral Gap'] = abs(eigens[0]) - abs(eigens[1])
    metrics_dict['Clustering Coefficient'] = nx.average_clustering(subbase)
    metrics_dict['Assortativity'] = nx.degree_assortativity_coefficient(subbase)
    metrics_dict['Utility'] = ''


    #find the node with highest degree
    max_degree = 0
    max_node = 0
    for node in subbase.nodes():
        if subbase.degree(node) > max_degree:
            max_degree = subbase.degree(node)
            max_node = node




    # #node type assignments
    # candidates = len(subbase.nodes())
    # num_gen = gens
    # degree_list = [d for n, d in subbase.degree()]
    # order = [n for n, d in subbase.degree()]
    # bc_list = [d for n, d in nx.betweenness_centrality(subbase).items()]
    # hop_list = [nx.shortest_path_length(subbase, (subs-1), i) for i in order]
    # import picos as pc
    #
    # x = pc.BinaryVariable('x', candidates)
    # y = pc.RealVariable('y', 3)
    # z = pc.RealVariable('z', 3)
    #
    # avg_degree = 1.7407407407407407 #derived from real utility
    # avg_bc = 0.03630284995660414 #derived from real utility
    # avg_hop = 6.296296296296296 #derived from real utility
    #
    # P = pc.Problem()
    # P.minimize = pc.sum(z)
    # P += pc.sum(x) == gens
    # P += y[0] == pc.sum(degree_list*x) - num_gen*avg_degree
    # P += y[1] == pc.sum(bc_list*x) - num_gen*avg_bc
    # P += y[2] == pc.sum(hop_list*x) - num_gen*avg_hop
    # P += z[0] >= y[0]
    # P += z[0] >= -y[0]
    # P += z[1] >= y[1]
    # P += z[1] >= -y[1]
    # P += z[2] >= y[2]
    # P += z[2] >= -y[2]
    # P.options.timelimit = 300
    # P.solve(solver="gurobi")
    # results = np.nonzero(x.np)[0]
    # for n in subbase.nodes():
    #     subbase.nodes[n]['color'] = 'b'
    #
    # for i in results:
    #     subbase.nodes[order[i]]['color'] = 'r'
    #
    # subbase.nodes[subs-1]['color'] = 'black'
    #
    #
    #
    # plt.figure(figsize=(16,16))
    # colors = [node[1]['color'] for node in subbase.nodes(data=True)]
    # nx.draw_networkx(subbase, pos, with_labels=True, node_size=90, node_color=colors)
    # plt.show()
    return subbase, max_node, metrics_dict

    # avg_ebc_mw = 0.125
    # avg_ebc_plc = 0.0198
    # avg_ebc_fiber = 0.0390
    # avg_ebc_leased = 0.0222
    # avg_ebc_low_cap = 0.0751
    # avg_distance_mw = 5.0
    # avg_distance_plc = 5.5
    # avg_distance_fiber = 6.6
    # avg_distance_leased = 6.14
    # avg_distance_low_cap = 5.27
    #
    # color_map1 = []
    # num_link = len(subbase.edges())
    # LINK_ARRAY = np.ones(num_link)
    #
    # num_mw = round(num_link*0.32)
    # num_plc = round(num_link*0.22)
    # num_leased = round(num_link*0.25)
    # num_fibre = round(num_link*0.18)
    # num_radio = num_link - num_mw - num_plc - num_leased - num_fibre
    #
    # weight_list = np.array([1, 1, 1, 1, 1]) #  10 2 5 2 1
    #
    # # ebc
    # ebc_list = [d for n, d in nx.edge_betweenness_centrality(subbase).items()]
    # link_order = [n for n, d in nx.edge_betweenness_centrality(subbase).items()]
    #
    # # distance
    # distance_dict = nx.shortest_path_length(subbase, 103)
    # distance_list = []
    # for e in list(subbase.edges()):
    #     distance_list.append(min(distance_dict[e[0]], distance_dict[e[1]]))  # same order as link_order
    #
    # # Construct the problem.
    # mw = cp.Variable(num_link, name='mw', boolean=True)
    # plc = cp.Variable(num_link, name='plc', boolean=True)
    # leased = cp.Variable(num_link, name='leased', boolean=True)
    # fibre = cp.Variable(num_link, name='fibre', boolean=True)
    # radio = cp.Variable(num_link, name='radio', boolean=True)
    # y = cp.Variable(5, name='y')
    # z = cp.Variable(1, name='z', nonneg=True)
    # p = cp.Variable(5, name='p')
    # q = cp.Variable(1, name='q', nonneg=True)
    #
    # objective = cp.Minimize(z + q)
    #
    # constraints = []
    # constraints += [cp.sum(mw) == num_mw]
    # constraints += [cp.sum(plc) == num_plc]
    # constraints += [cp.sum(leased) == num_leased]
    # constraints += [cp.sum(fibre) == num_fibre]
    # constraints += [cp.sum(radio) == num_radio]
    # constraints += [mw + plc + leased + fibre + radio == LINK_ARRAY]
    # constraints += [y[0] == cp.sum(cp.multiply(ebc_list, mw))/num_mw - avg_ebc_mw]
    # constraints += [y[1] == cp.sum(cp.multiply(ebc_list, plc))/num_plc - avg_ebc_plc]
    # constraints += [y[2] == cp.sum(cp.multiply(ebc_list, leased))/num_leased - avg_ebc_leased]
    # constraints += [y[3] == cp.sum(cp.multiply(ebc_list, fibre))/num_fibre - avg_ebc_fiber]
    # constraints += [y[4] == cp.sum(cp.multiply(ebc_list, radio))/num_radio - avg_ebc_low_cap]
    # constraints += [p[0] == cp.sum(cp.multiply(distance_list, mw))/num_mw - avg_distance_mw]
    # constraints += [p[1] == cp.sum(cp.multiply(distance_list, plc))/num_plc - avg_distance_plc]
    # constraints += [p[2] == cp.sum(cp.multiply(distance_list, leased))/num_leased - avg_distance_leased]
    # constraints += [p[3] == cp.sum(cp.multiply(distance_list, fibre))/num_fibre - avg_distance_fiber]
    # constraints += [p[4] == cp.sum(cp.multiply(distance_list, radio))/num_radio - avg_distance_low_cap]
    #
    # constraints += [z >= cp.sum_squares(cp.multiply(y, weight_list))]
    # constraints += [q >= cp.sum_squares(cp.multiply(p, weight_list))]
    #
    #
    # prob = cp.Problem(objective, constraints)
    #
    # # The optimal objective value is returned by `prob.solve()`.
    # # result = prob.solve(solver=cp.SCIP, verbose=True, scip_params={'limits/time': 300})
    # result = prob.solve(solver=cp.GUROBI, verbose=True, TimeLimit=500)
    # # The optimal value for x is stored in `x.value`.
    # if prob.status not in ["infeasible", "unbounded"]:
    #     # Otherwise, problem.value is inf or -inf, respectively.
    #     print("Optimal value: %s" % prob.value)
    #     for variable in prob.variables():
    #         print("Variable %s: value %s" % (variable.name(), variable.value))
    #
    # from SecretColors import Palette
    #
    # p = Palette('ibm')
    #
    # mw_link = np.nonzero(mw.value)[0]
    # plc_link = np.nonzero(plc.value)[0]
    # leased_link = np.nonzero(leased.value)[0]
    # fibre_link = np.nonzero(fibre.value)[0]
    # radio_link = np.nonzero(radio.value)[0]
    #
    # for i in mw_link:
    #     subbase.edges[link_order[i]]['color'] = p.black()
    # for i in plc_link:
    #     subbase.edges[link_order[i]]['color'] = p.blue()
    # for i in fibre_link:
    #     subbase.edges[link_order[i]]['color'] = p.red()
    # for i in leased_link:
    #     subbase.edges[link_order[i]]['color'] = p.orange()
    # for i in radio_link:
    #     subbase.edges[link_order[i]]['color'] = p.green()
    #
    # plt.figure(figsize=(16,16))
    # colors = [edge[2]['color'] for edge in subbase.edges(data=True)]  # edge[2] is the attribute dict
    # pos = nx.kamada_kawai_layout(subbase)
    # nx.draw_networkx_edges(subbase,pos=pos,edge_color=p.black(),width=2, label='Microwave Link')
    # nx.draw_networkx_edges(subbase,pos=pos,edge_color=p.blue(),width=2, label='PLC Link')
    # nx.draw_networkx_edges(subbase,pos=pos,edge_color=p.red(),width=2, label='Fiber Link')
    # nx.draw_networkx_edges(subbase,pos=pos,edge_color=p.orange(),width=2, label='Leased Link')
    # nx.draw_networkx_edges(subbase,pos=pos,edge_color=p.green(),width=2, label='Low-Capacity Radio')
    # nx.draw_networkx(subbase, pos, node_color=p.white(),edge_color=colors, with_labels=False, edgecolors=p.gray(), node_size=40, width=3, font_size=6)
    # plt.legend(loc=8, ncol=5, fontsize=14, frameon=False)
    # plt.show()


if __name__ == "__main__":
   # stuff only to run when not called via 'import' here
   subs=50
   gens=2
   cyber_nwk = generate_nwk(subs, gens)