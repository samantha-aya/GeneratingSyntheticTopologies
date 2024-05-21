import cvxpy as cp
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

from ortools.sat.python import cp_model
import math

import igraph as ig
import matplotlib.pyplot as plt
from numpy.linalg import norm

def lognormal(x, a, b):
    # numpy.random.lognormal
    return 1/(a*x*np.sqrt(2*np.pi))*np.exp(-np.power(np.log(x) - b, 2)/(2*np.power(a, 2)))

def statistics_based(subs, gens):

    probability = lognormal(np.array(range(1,11)), 0.57627298, 0.56637515 )
    # add 0.003 to each value in probablity
    # probability = np.add(probability, 0.003)


    # generate n integers from the probablity distribution
    num_sub = subs
    # sub_ratio = 200/333
    # n = round(num_sub/sub_ratio)
    n = subs
    print("Num of vertices:", n)

    expected = (probability * n).astype(int)
    sum_degree = round(n*1.0777)*2
    # sum_degree = n*(n-1)*nx.density(BC)
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
    # for i in range(n_degree):
    #     seq += [degrees[i] for _ in range(solver.Value(nodes[i]))]
    temp = [45,37,16,7,3,4 , 0 , 0 , 0 , 0]
    for i in range(10):
        seq += [degrees[i] for _ in range(temp[i])]
    seq = np.array(seq)
    print("seq", seq)
    print(len(seq))

    target = np.array([-0.0728, 0.023, -0.355])
    best = None
    best_dist = float('inf')
    for i in range(10000):
        g = ig.Graph.Degree_Sequence(seq.tolist(), method="vl")

        A = g.get_edgelist()
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
    plt.show()

    #node type assignments
    candidates = len(subbase.nodes())
    num_gen = gens
    degree_list = [d for n, d in subbase.degree()]
    order = [n for n, d in subbase.degree()]
    bc_list = [d for n, d in nx.betweenness_centrality(subbase).items()]
    hop_list = [nx.shortest_path_length(subbase, (subs-1), i) for i in order]
    import picos as pc

    x = pc.BinaryVariable('x', candidates)
    y = pc.RealVariable('y', 3)
    z = pc.RealVariable('z', 3)

    avg_degree = 1.7407407407407407 #derived from real utility
    avg_bc = 0.03630284995660414 #derived from real utility
    avg_hop = 6.296296296296296 #derived from real utility

    P = pc.Problem()
    P.minimize = pc.sum(z)
    P += pc.sum(x) == gens
    P += y[0] == pc.sum(degree_list*x) - num_gen*avg_degree
    P += y[1] == pc.sum(bc_list*x) - num_gen*avg_bc
    P += y[2] == pc.sum(hop_list*x) - num_gen*avg_hop
    P += z[0] >= y[0]
    P += z[0] >= -y[0]
    P += z[1] >= y[1]
    P += z[1] >= -y[1]
    P += z[2] >= y[2]
    P += z[2] >= -y[2]
    P.options.timelimit = 300
    P.solve(solver="gurobi")
    results = np.nonzero(x.np)[0]
    for n in subbase.nodes():
        subbase.nodes[n]['color'] = 'b'

    for i in results:
        subbase.nodes[order[i]]['color'] = 'r'

    subbase.nodes[111]['color'] = 'black'

    plt.figure(figsize=(16,16))
    colors = [node[1]['color'] for node in subbase.nodes(data=True)]
    nx.draw_networkx(subbase, pos, with_labels=False, node_size=90, node_color=colors)
    plt.show()

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

subs = 112
gens = 17
statistics_based(subs, gens)