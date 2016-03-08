"""
for using probabilistic graphical models (bayes' nets in particular).
"""

import logging
import pandas as pd
import networkx as nx
from cess.util import random_choice

logger = logging.getLogger(__name__)

class BNet():
    def __init__(self, nodes, edges, data, bins, precompute=True):
        """creates the graphical model (bayes net)"""
        self.g = nx.DiGraph()
        self.g.add_nodes_from(nodes)
        self.g.add_edges_from(edges)
        self.bins = bins
        self.df = data

        if precompute:
            self._cache = self._precompute_dists()
        else:
            self._cache = {}

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

        # used cached distributions, if available
        if self._cache:
            dist = self._cache[n.name]
            prior_probs = dist['_']

            for group, prior_prob in prior_probs.items():
                likelihood = 1.
                for key, val in given.items():
                    try:
                        likelihood *= dist[key.name][val]
                    except KeyError:
                        likelihood = 1e-20 # non-zero likelihood
                probs[group] = prior_prob * likelihood

        else:
            groups = self.groups(n)
            prior_probs = (groups.size()/len(self.df)).to_dict()

            # compute conditional probabilities for each group
            for group, prior_prob in prior_probs.items():
                df_g = groups.get_group(group)
                group_size = len(df_g)

                likelihood = 1.
                for key, val in given.items():
                    bins = self.bins.get(key)
                    if bins is None:
                        # smoothing
                        likelihood *= max(len(df_g[df_g[key.value] == val])/group_size, 1e-20)
                    else:
                        # bin this group accordingly
                        # and count the corresponding bin
                        grouper = pd.cut(df_g[key.value], bins)
                        subgroup = df_g.groupby(grouper)
                        try:
                            likelihood *= len(subgroup.get_group(val))/group_size
                        except KeyError:
                            likelihood = 0

                probs[group] = prior_prob * likelihood

        # normalize to a distribution
        total = sum(probs.values())

        # we have encoutered a sample not present in the data
        # fallback to a uniform distribution
        if total == 0:
            logger.warn('Not enough data to learn a conditional distribution for {} given {}; falling back to unconditional distribution'.format(n, given))
            total = sum(prior_probs.values())
            probs = prior_probs

        for group in probs.keys():
            probs[group] /= total

        return probs

    def sample_node(self, n, sampled):
        """sample an individual node,
        samples from parents as necessary"""
        parents = self.g.predecessors(n)

        if not parents:
            # if no parents, use p(n)
            try:
                prob_dist = self._cache[n.name]['_']
            except KeyError:
                prob_dist = self.p_n(n)
        else:
            # if parents, use prod(p(n|x_i) for x_i in parents)
            for parent in parents:
                if parent not in sampled:
                    sampled = self.sample_node(parent, sampled)
            given = {k:v for k,v in sampled.items() if k in parents}
            prob_dist = self.probs_given(n, given=given)
        sampled[n] = random_choice(prob_dist.items())
        return sampled

    def _precompute_dists(self):
        """precompute pgm distributions in advance"""
        dists = {}
        for n in self.g.nodes():
            name = n.name
            dists[name] = {}
            dists[name]['_'] = self.p_n(n)
            parents = self.g.predecessors(n)
            for parent in parents:
                dists[name][parent.name] = self.p_p_n(n, parent)
        return dists

    def p_n(self, n):
        """p(n) for a node"""
        return (self.groups(n).size()/len(self.df)).to_dict()

    def p_p_n(self, n, parent):
        """p(parent|n) for a node"""
        dist = {}
        groups = self.groups(n)
        bins = self.bins.get(parent)
        for group, df_g in groups:
            group_size = len(df_g)
            if bins is None:
                grouper = parent.value
            else:
                grouper = pd.cut(df_g[parent.value], bins)
            subgroups = df_g.groupby(grouper)
            dist = (subgroups.size()/group_size).to_dict()
        return dist

    def sample(self, sampled=None):
        """sample from the complete PGM"""
        sampled = sampled or {}
        for n in self.g.nodes():
            if n in sampled:
                continue
            sampled = self.sample_node(n, sampled)
        return sampled
