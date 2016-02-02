import unittest
import numpy as np
from world import social

np.random.seed(0)


class Person():
    def __init__(self, sex, race, age, education):
        self.sex = sex
        self.race = race
        self.age = age
        self.education = education


class WorldTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_friendships(self):
        people = [
            Person(0, 1, 25, 10),
            Person(0, 1, 25, 10),
            Person(1, 4, 45, 16),
            Person(1, 4, 80, 8),
        ]
        expected_adj_mat = np.array([[0., 1., 0., 0.],
                                     [1., 0., 0., 0.],
                                     [0., 0., 0., 0.],
                                     [0., 0., 0., 0.]])
        adj_mat = social.friendship_matrix(people, base_prob=0.5)
        np.testing.assert_array_equal(adj_mat, expected_adj_mat)
