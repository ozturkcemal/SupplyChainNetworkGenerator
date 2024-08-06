import random
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import json
import sys

class BOM:
    def __init__(self, n, num_roots, max_depth, max_parents, min_demand, max_demand, seed=None):
        self.n = n
        self.num_roots = num_roots
        self.max_depth = max_depth
        self.max_parents = max_parents
        self.min_demand = min_demand
        self.max_demand = max_demand
        self.seed = seed
        self.G = None
        self.leaf_nodes = []
        self.depth = {}  # Initialize depth dictionary

        if seed is not None:
            random.seed(seed)

        self.create_connected_dag_with_multiple_parents()
        self.ensure_graph_connected()
        self.calculate_node_depths()  # Compute node depths after graph is fully constructed

    def update_leaf_nodes(self):
        """Update the list of leaf nodes based on the current graph structure."""
        if self.G is not None:  # Ensure that self.G is initialized
            self.leaf_nodes = [node for node in self.G.nodes if self.G.out_degree(node) == 0]

    def create_connected_dag_with_multiple_parents(self):
        G = nx.DiGraph()

        # Add multiple root nodes
        for i in range(self.num_roots):
            G.add_node(i)

        # Add nodes ensuring the graph remains connected
        for i in range(self.num_roots, self.n):
            possible_parents = list(G.nodes)  # Include all nodes as possible parents
            num_parents = min(len(possible_parents), self.max_parents)
            if num_parents == 0:
                continue

            parents = random.sample(possible_parents, num_parents)
            G.add_node(i)
            for parent in parents:
                G.add_edge(parent, i, weight=random.randint(1, 10))

        # Initialize the graph and update the leaf_nodes list
        self.G = G
        self.update_leaf_nodes()

        # Ensure the graph is connected
        for node in G.nodes:
            if G.in_degree(node) == 0 and node >= self.num_roots:  # Non-root node with no incoming edges
                parent = random.choice(list(G.nodes))
                if parent != node:
                    G.add_edge(parent, node, weight=random.randint(1, 10))

        self.update_leaf_nodes()
        demand = {node: (random.randint(self.min_demand, self.max_demand) if node in self.leaf_nodes else 0) for node in
                  G.nodes}
        nx.set_node_attributes(G, demand, 'demand')
        self.G = G

    def ensure_graph_connected(self):
        """Ensure that the graph is a single connected component."""
        if not nx.is_weakly_connected(self.G):
            # Find all the weakly connected components
            components = list(nx.weakly_connected_components(self.G))
            if len(components) > 1:
                # Add edges to connect all components
                for i in range(len(components) - 1):
                    # Connect the last node of the first component to the first node of the next component
                    src = list(components[i])[-1]
                    dest = list(components[i + 1])[0]
                    self.G.add_edge(src, dest, weight=random.randint(1, 10))
                    # Optionally, add more edges to make it more connected
                    self.add_edges_between_components(components[i], components[i + 1])

    def add_edges_between_components(self, comp1, comp2):
        """Add edges between two components."""
        node1 = random.choice(list(comp1))
        node2 = random.choice(list(comp2))
        self.G.add_edge(node1, node2, weight=random.randint(1, 10))
        # Optionally, add more edges to enhance connectivity
        if len(comp1) > 1 and len(comp2) > 1:
            node1 = random.choice(list(comp1))
            node2 = random.choice(list(comp2))
            self.G.add_edge(node1, node2, weight=random.randint(1, 10))

    def calculate_node_depths(self):
        """Compute and update the depth of each node."""
        # Initialize depth for root nodes
        self.depth = {node: 0 for node in self.G.nodes if self.G.in_degree(node) == 0}

        # Perform a breadth-first search to determine the depth of each node
        queue = list(self.depth.keys())
        while queue:
            node = queue.pop(0)
            current_depth = self.depth[node]
            for successor in self.G.successors(node):
                if successor not in self.depth:  # Node not yet visited
                    self.depth[successor] = current_depth + 1
                    queue.append(successor)

    def find_longest_path(self):
        # Use topological sorting to find the longest path in a DAG
        topo_order = list(nx.topological_sort(self.G))
        dist = {node: float('-inf') for node in self.G.nodes}
        prev = {node: None for node in self.G.nodes}

        # Initialize distances for root nodes
        for node in self.depth:
            dist[node] = 0

        for node in topo_order:
            for succ in self.G.successors(node):
                if dist[node] + 1 > dist[succ]:  # Update based on the number of nodes
                    dist[succ] = dist[node] + 1
                    prev[succ] = node

        # Find the end node with the maximum distance
        end_node = max(dist, key=dist.get)
        longest_path_length = dist[end_node]

        # Backtrack to find the path
        path = []
        while end_node is not None:
            path.append(end_node)
            end_node = prev[end_node]
        path.reverse()

        return longest_path_length, path

    def visualize_graph(self, filename):
        # Define scaling factors based on the number of nodes
        num_nodes = len(self.G.nodes)
        node_size = max(500, 2000 / num_nodes)  # Ensure nodes are large enough to see, but scale down with more nodes
        font_size = max(8, 20 / (
                num_nodes / 10))  # Adjust font size to avoid overlap; smaller graphs have larger font size
        fig_size = (max(8, num_nodes / 5), max(6, num_nodes / 10))  # Adjust figure size based on number of nodes

        # Generate layout positions
        pos = nx.drawing.nx_agraph.graphviz_layout(self.G, prog='dot')

        # Check if pos contains the correct type of values
        for node, (x, y) in pos.items():
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                raise ValueError(f"Invalid position value for node {node}: ({x}, {y})")

        # Rotate 180 degrees by flipping y-coordinates
        y_coords = {node: -y for node, (x, y) in pos.items()}
        pos = {node: (x, y_coords[node]) for node, (x, y) in pos.items()}

        # Update leaf nodes and labels
        leaf_nodes = [node for node in self.G.nodes if self.G.out_degree(node) == 0]
        node_colors = ['red' if node in leaf_nodes else 'skyblue' for node in self.G.nodes]
        labels = {node: f"{node}\n(demand={self.G.nodes[node]['demand']})" if node in leaf_nodes else str(node) for node
                  in self.G.nodes}

        # Create figure and plot the graph
        plt.figure(figsize=fig_size)  # Set figure size dynamically
        nx.draw(self.G, pos, with_labels=True, labels=labels, node_size=node_size, node_color=node_colors,
                font_size=font_size,
                font_color="black", arrows=True)
        edge_labels = nx.get_edge_attributes(self.G, 'weight')
        nx.draw_networkx_edge_labels(self.G, pos, edge_labels=edge_labels)

        # Save and show the plot
        plt.savefig(filename)
        plt.show(block=False)
        plt.pause(2)
        plt.close()

    def create_bom_matrix(self):
        # Initialize BOM matrix with zeros
        bom_matrix = np.zeros((self.n, self.n + 1), dtype=int)

        # Populate BOM matrix with edge weights
        for (u, v, wt) in self.G.edges(data='weight'):
            bom_matrix[u][v] = wt

        # Create a list of demands based on the current nodes
        demands = np.array([self.G.nodes[node]['demand'] if node in self.G.nodes else 0 for node in self.G.nodes])

        # Ensure demands array matches the size of BOM matrix
        if len(demands) < self.n:
            demands = np.pad(demands, (0, self.n - len(demands)), 'constant')
        elif len(demands) > self.n:
            demands = demands[:self.n]

        # Add the demands as the last column in the BOM matrix
        bom_matrix[:, -1] = demands

        return bom_matrix

    def run(self):
        # Open a file to write the print statements
        with open('output/BOM_output.txt', 'w') as f:
            # Redirect stdout to the file
            original_stdout = sys.stdout
            sys.stdout = f

            # Print the edges with weights
            print("Edges with weights:")
            for (u, v, wt) in self.G.edges(data='weight'):
                print(f"Edge ({u}, {v}) has weight {wt}")

            # Print the nodes with their demands
            print("\nNodes with demands:")
            for node, demand in nx.get_node_attributes(self.G, 'demand').items():
                print(f"Node {node} has demand {demand}")

            # Print the depth of each node
            print("\nDepth of each node:")
            for node, depth in self.depth.items():
                print(f"Node {node} is at depth {depth}")

            # Find and print the longest path
            longest_path_length, longest_path = self.find_longest_path()
            print(
                f"\nLongest path length (height) or the number of levels in BOM (in terms of number of nodes): {longest_path_length}")
            print(f"Longest path: {' -> '.join(map(str, longest_path))}")

            # Visualize the tree and save the figure
            self.visualize_graph('output/BOM_visualization.png')

            # Create and print the BOM matrix
            bom_matrix = self.create_bom_matrix()
            print("\nBOM matrix:")
            print(bom_matrix)

            # Define labels
            labels = {
                "nodes": [f"Node {i}" for i in range(self.n)],
                "demand": "Demand"
            }

            # Export BOM matrix to JSON
            self.export_bom_matrix_to_json(bom_matrix, 'output/bom_matrix.json', labels)

            # Restore stdout
            sys.stdout = original_stdout

    def export_bom_matrix_to_json(self, bom_matrix, filename, labels):
        bom_matrix_list = bom_matrix.tolist()
        data = {
            "labels": labels,
            "matrix": bom_matrix_list
        }
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)