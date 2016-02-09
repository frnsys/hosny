"""
parameters for this logistic regression were pulled from Table 3, Model 3 of:

    Social Distance in the United States: Sex, Race, Religion, Age, and Education Homophily among Confidants, 1985 to 2004. Jeffrey A. Smith, Miller McPherson, Lynn Smith-Lovin. University of Nebraska - Lincoln. 2014.
    http://digitalcommons.unl.edu/cgi/viewcontent.cgi?article=1254&context=sociologyfacpub

Note that these parameters are for "confidants", i.e. a more intimate friendship,
rather than friendships in general, e.g. acquaintances
"""

import math
import numpy as np
import networkx as nx


def friendship_matrix(people, base_prob):
    """friendship matrix :)
    takes a list of agents, returns an adjacency matrix of friendships
    `base_prob` is the probability that two individuals would be friends
    if they are exactly the same.
    """
    mat = np.array([[p.race, p.sex, p.age, p.education] for p in people])
    adj_mat = np.zeros((mat.shape[0], mat.shape[0]))

    for idx, row in enumerate(mat):
        # only build lower triangle
        if idx >= math.ceil(len(mat)/2):
            break

        # compute diffs
        diffs = np.abs(row - mat)

        # for race, we only care that they are different,
        # not the actual difference in value
        # end result is: [diff_race, diff_sex, age_diff, educ_diff]
        diffs[np.where(diffs[:,0] != 0), 0] = 1

        # intercept is generate according to user-specified
        # base friendship probability
        intercept = -math.log((1-base_prob)/base_prob)

        # see above for from where these params were retrieved
        params = np.array([-1.468, -1.088, -0.114, -0.208])
        out = np.dot(diffs, params) + intercept
        probs = 1/(1+np.exp(-out))

        # rolls for friendship
        rolls = np.random.uniform(size=len(diffs))

        # indices where true
        friend_idx = np.where(rolls < probs)[0]

        # define relationships
        adj_mat[idx, friend_idx] = 1

    # can't be friends with yourself
    np.fill_diagonal(adj_mat, 0)

    # copy lower triangle to upper triangle (the matrix is symmetric)
    adj_mat = adj_mat + adj_mat.T - np.diag(adj_mat.diagonal())
    return adj_mat


def social_network(people, base_prob=0.5):
    """generate a social network for a list of people"""
    friendship_mat = friendship_matrix(people, base_prob)
    return nx.from_numpy_matrix(friendship_mat)