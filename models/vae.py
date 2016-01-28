"""
variational autoencoder
http://arxiv.org/pdf/1312.6114v10.pdf

also referred to:
- <https://jmetzen.github.io/2015-11-27/vae.html#Illustrating-reconstruction-quality>
- <https://github.com/ikostrikov/TensorFlow-VAE-GANs/blob/master/main-vae.py>
- <http://vdumoulin.github.io/morphing_faces/>

NOTE: this is not working at the moment, the cost is always nan?
"""

import tensorflow as tf
from .common import xavier_init, minibatches


class VAE():
    def __init__(self, input_dim, n_z=10, n_hidden=10, learning_rate=0.001):
        """
        `n_z` is the number of units in the latent layer (i.e. latent variables),
        `n_hidden` is the number of units for hidden layers
        """

        # hyperparameters
        self.learning_rate = learning_rate

        # architecture
        self.input_dim = input_dim
        self.n_z = n_z

        # input/observed data
        self.X = tf.placeholder('float', [None, input_dim])

        self.weights_d = {
            'h': tf.Variable(xavier_init(n_z, n_hidden)),
            'out': tf.Variable(xavier_init(n_hidden, input_dim))
        }
        self.biases_d = {
            'b': tf.Variable(tf.zeros([n_hidden])),
            'out': tf.Variable(tf.zeros([input_dim]))
        }
        self.weights_e = {
            'h': tf.Variable(xavier_init(input_dim, n_hidden)),
            'out_mean': tf.Variable(xavier_init(n_hidden, n_z)),
            'out_log_stddev_sq': tf.Variable(xavier_init(n_hidden, n_z))
        }
        self.biases_e = {
            'b': tf.Variable(tf.zeros([n_hidden])),
            'out_mean': tf.Variable(tf.zeros([n_z])),
            'out_log_stddev_sq': tf.Variable(tf.zeros([n_z]))
        }

        mean, stddev = self._encoder(self.X, self.weights_e, self.biases_e)
        self.decoder = self._decoder(mean, stddev, self.weights_d, self.biases_d)

        # reconstruction error for a Bernoulli decoder (see C.1 in the paper)
        eps=1e-10
        self.rec_loss = -tf.reduce_sum(self.X * tf.log(self.decoder + eps) + (1.0 - self.X) * tf.log(1.0 - self.decoder + eps))

        # negative variational lower bound for when the prior p(z) and the
        # posterior approximation q(z|x) are both Gaussian (see B in the paper)
        self.var_loss = -0.5 * tf.reduce_sum(1 + tf.log(tf.square(stddev)) - tf.square(mean) - tf.square(stddev))

        vars = list(self.weights_e.values()) + list(self.biases_e.values()) \
            + list(self.weights_d.values()) + list(self.biases_d.values())

        self.loss = tf.reduce_mean(self.rec_loss + self.var_loss)
        self.optimizer = tf.train.AdamOptimizer(self.learning_rate).minimize(self.loss, var_list=vars)

        # initialize
        init = tf.initialize_all_variables()
        self.sess = tf.Session()
        self.sess.run(init)

    def _encoder(self, X, w, b):
        """constructs the encoder network (the recognition model),
        which learns p(z|x), i.e. it yields latent z from an observed x.
        as implemented, this is a Gaussian encoder. See C.2 in the paper."""
        hidden = tf.nn.tanh(tf.add(tf.matmul(X, w['h']), b['b']))
        mean = tf.add(tf.matmul(hidden, w['out_mean']), b['out_mean'])
        log_stddev_sq = tf.add(tf.matmul(hidden, w['out_log_stddev_sq']), b['out_log_stddev_sq'])
        stddev = tf.exp(tf.sqrt(log_stddev_sq))
        return mean, stddev

    def _decoder(self, mean, stddev, w, b):
        """constructs the decoder network (the generation model),
        which learns p(x|z), i.e. it (re)constructs a datapoint x from z.
        as implemented, this is a Bernoulli decoder and assumes
        the encoder is a Gaussian encoder. See 2.4 and C.1 in the paper."""

        # here we use a standard Gaussian distribution for p(eps)
        batch_size, _ = mean.shape
        epsilon = tf.random_normal((batch_size, self.n_z), 0, 1)

        # reparameterized z, given that p(z|x)
        # is a Gaussian paramterized by mean, stddev
        z_re = mean + epsilon * stddev

        hidden = tf.nn.tanh(tf.add(tf.matmul(z_re, w['h']), b['b']))

        # use sigmoid for a Bernoulli decoder
        return tf.nn.sigmoid(tf.add(tf.matmul(hidden, w['out']), b['out']))

    def train(self, input_data, epochs=1000, batch_size=250, verbose=True):
        """train the networks"""
        n_examples, input_dim = input_data.shape
        assert input_dim == self.input_dim

        for epoch in range(epochs):
            avg_cost = 0
            for batch in minibatches(input_data, batch_size):
                # debugging
                opt, cst, rl, vl, mean, stdev = self.sess.run([self.optimizer, self.loss,
                                                               self.rec_loss, self.var_loss,
                                                               self.mean, self.stddev],
                                                              {self.X: batch})
                avg_cost += cst / n_examples * batch_size

                # debugging
                import math
                if math.isnan(rl) or math.isnan(vl):
                    raise Exception('nan!!!!')

            if verbose and epoch % 10 == 0:
                print('EPOCH:', epoch)
                print('avg cost:', avg_cost)

    def reconstruct(self, input_data):
        """try reconstructing some input"""
        return self.sess.run(self.decoder, {self.X: input_data})
