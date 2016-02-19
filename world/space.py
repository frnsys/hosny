import networkx as nx


class Space():
    def __init__(self, nodes, edges):
        """the geography of the city"""
        self.geo = nx.Graph()
        self.geo.add_nodes_from([(n, {'agents':[]}) for n in nodes])
        self.geo.add_edges_from(edges)

        # keep track of agent positions
        self.agent_pos = {}

    def place_agent(self, agent, node):
        """place an agent at a node,
        removes them from their current node, if there is one"""
        current_node = self.agent_pos.get(agent.id)
        if current_node is not None:
            self.geo.node[current_node]['agents'].remove(agent)
        self.geo.node[node]['agents'].append(agent)
        self.agent_pos[agent.id] = node
