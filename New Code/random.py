# function to multiply two numbers
def multiply(a, b):
    return a * b

# function to generate a graph network with normal degree distribution and display it
def generate_graph():
    import networkx as nx
    import matplotlib.pyplot as plt
    G = nx.gnp_random_graph(100, 0.02)
    nx.draw(G)
    plt.show()
    return G

