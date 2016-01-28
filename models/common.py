import numpy as np
import tensorflow as tf


def leaky_relu(x):
    """leaky ReLU"""
    return tf.maximum(0.01*x, x)


def xavier_init(fan_in, fan_out, const=1): 
    """xavier initialization for weights"""
    min = -const*np.sqrt(6./(fan_in+fan_out))
    max = const*np.sqrt(6./(fan_in+fan_out))
    return tf.random_uniform((fan_in, fan_out), minval=min, maxval=max)


def minibatches(input_data, batch_size):
    """splits data into minibatches"""
    n_examples, n_input = input_data.shape
    n_batches = int(n_examples/batch_size)
    shuffled_idx = np.random.permutation(n_examples)
    return np.split(input_data[shuffled_idx], n_batches)


def minibatch(input_data, batch_size):
    """samples a single minibatch from data"""
    n_examples, n_input = input_data.shape
    shuffled_idx = np.random.permutation(n_examples)
    return input_data[shuffled_idx][:batch_size]
