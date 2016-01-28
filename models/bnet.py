"""
for using probabilistic graphical models (bayes' nets in particular).
"""

import pandas as pd
import networkx as nx
from util import random_choice


class BNet():
    def __init__(self, nodes, edges, data, bins):
        """creates the graphical model (bayes net)"""
        self.g = nx.DiGraph()
        self.g.add_nodes_from(nodes)
        self.g.add_edges_from(edges)
        self.bins = bins
        self.df = data

    def groups(self, n):
        """get user-specified grouping criteria (bins) if it exists,
        otherwise just group by the variable"""
        bins = self.bins.get(n)
        if bins is not None:
            grouper = pd.cut(self.df[n.value], bins)
        else:
            grouper = n.value
        return self.df.groupby(grouper)

    def probs_given(self, n, given={}):
        """computes distribution across groups
        given other variable values, assuming given
        variables are independent. that is, it computes
        prod(p(g|x_i) for x_i in given)/Z"""
        probs = {}
        groups = self.groups(n)

        # compute conditional probabilities for each group
        for group in groups.groups:
            df_g = groups.get_group(group)
            group_size = len(df_g)
            prior_prob = group_size/len(self.df)

            likelihood = 1.
            for key, val in given.items():
                bins = self.bins.get(key)
                if bins is None:
                    likelihood *= len(df_g[df_g[key.value] == val])/group_size
                else:
                    # bin this group accordingly
                    # and count the corresponding bin
                    grouper = pd.cut(df_g[key.value], bins)
                    subgroup = df_g.groupby(grouper)
                    likelihood *= len(subgroup.get_group(val))/group_size

            probs[group] = prior_prob * likelihood

        # normalize to a distribution
        total = sum(probs.values())
        for group in probs.keys():
            probs[group] /= total
        return probs

    def sample_node(self, n, sampled):
        """sample an individual node,
        samples from parents as necessary"""
        parents = self.g.predecessors(n)

        if not parents:
            # if no parents, use p(n)
            prob_dist = (self.groups(n).size()/len(self.df)).to_dict()
        else:
            # if parents, use prod(p(n|x_i) for x_i in parents)
            for parent in parents:
                if parent not in sampled:
                    sampled = self.sample_node(parent, sampled)
            prob_dist = self.probs_given(n, given=sampled)
        sampled[n] = random_choice(prob_dist)
        return sampled

    def sample(self, sampled=None):
        """sample from the complete PGM"""
        sampled = sampled or {}
        for n in self.g.nodes():
            if n in sampled:
                continue
            sampled = self.sample_node(n, sampled)
        return sampled
