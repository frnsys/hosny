"""
a generative adversarial network, as described in:

    I. Goodfellow, J. Pouget-Abadie, M. Mirza, B. Xu, D. Warde-
    Farley, S. Ozair, A. Courville, and Y. Bengio.  Generative
    Adversarial Nets. <http://arxiv.org/abs/1406.2661>

"""

import numpy as np
import tensorflow as tf
from .common import xavier_init, leaky_relu, minibatch, minibatches
from sklearn.preprocessing import MinMaxScaler


def binary_cross_entropy(target, output, eps=1e-12):
    """eps is to avoid log(0)"""
    return tf.reduce_mean(-(target * tf.log(output + eps) + (1 - target) * tf.log(1 - output + eps)))


def sample_noise(input_dim, batch_size):
    """sample a noise vector using a uniform prior"""
    return np.random.uniform(-1, 1, [batch_size, input_dim])


class GAN():
    def __init__(self, input_dim, g_dims, d_dims, learning_rate=0.001, drop_prob=0.5):
        # hyperparameters
        self.learning_rate = learning_rate
        self.drop_prob = drop_prob

        # keep probability for dropout
        self.keep_prob = tf.placeholder('float')

        # architecture
        self.input_dim = input_dim
        output_dim = input_dim

        # None means that dimension of the matrix has unspecified length
        # i.e. we can have as many samples as we want
        self.z = tf.placeholder('float', [None, input_dim])
        self.X = tf.placeholder('float', [None, input_dim])
        self.y = tf.placeholder('float', [None, output_dim])

        # keep these variables here so they can be shared,
        # e.g. amongst the real & fake discriminators
        self.weights_g = {
            'h1': tf.Variable(xavier_init(input_dim, g_dims[0])),
            'h2': tf.Variable(xavier_init(g_dims[0], g_dims[1])),
            'out': tf.Variable(xavier_init(g_dims[1], output_dim))
        }
        self.biases_g = {
            'b1': tf.Variable(tf.random_normal([g_dims[0]])),
            'b2': tf.Variable(tf.random_normal([g_dims[1]])),
        }

        self.weights_d = {
            'h1': tf.Variable(xavier_init(input_dim, d_dims[0])),
            'h2': tf.Variable(xavier_init(d_dims[0], d_dims[1])),
            'out': tf.Variable(xavier_init(d_dims[1], output_dim))
        }
        self.biases_d = {
            'b1': tf.Variable(tf.random_normal([d_dims[0]])),
            'b2': tf.Variable(tf.random_normal([d_dims[1]])),
        }

        # build the networks
        self.G = self._generator(self.z, self.weights_g, self.biases_g)
        self.D_real = self._discriminator(self.X, self.weights_d, self.biases_d) # for "real" examples
        self.D_fake = self._discriminator(self.G, self.weights_d, self.biases_d) # for counterfeit examples

        # cost functions
        self.cost_d_real = binary_cross_entropy(tf.ones_like(self.D_real), self.D_real)
        self.cost_d_fake = binary_cross_entropy(tf.zeros_like(self.D_fake), self.D_fake)
        self.cost_d = self.cost_d_real + self.cost_d_fake

        # refer to paper for this justification.
        # basically, when D is very good, G has a stronger gradient with this loss function
        self.cost_g = tf.reduce_mean(tf.log(1 - self.D_fake + 1e-12))

        vars_d = list(self.weights_d.values()) + list(self.biases_d.values())
        vars_g = list(self.weights_g.values()) + list(self.biases_g.values())
        self.optimizer_d = tf.train.AdamOptimizer(learning_rate=tf.Variable(learning_rate)).minimize(self.cost_d, var_list=vars_d)
        self.optimizer_g = tf.train.AdamOptimizer(learning_rate=tf.Variable(learning_rate)).minimize(self.cost_g, var_list=vars_g)

        # initialize
        init = tf.initialize_all_variables()
        self.sess = tf.Session()
        self.sess.run(init)

    def _generator(self, z, w, b):
        """defines the generator network"""
        hidden_1 = leaky_relu(tf.add(tf.matmul(z, w['h1']), b['b1']))
        hidden_2 = leaky_relu(tf.add(tf.matmul(hidden_1, w['h2']), b['b2']))
        #return tf.matmul(hidden_2, w['out'])
        return tf.nn.sigmoid(tf.matmul(hidden_2, w['out']))

    def _discriminator(self, X, w, b):
        """defines the discriminator network"""
        hidden_1 = leaky_relu(tf.add(tf.matmul(X, w['h1']), b['b1']))
        hidden_1_drop = tf.nn.dropout(hidden_1, self.keep_prob)
        hidden_2 = leaky_relu(tf.add(tf.matmul(hidden_1_drop, w['h2']), b['b2']))
        return tf.nn.sigmoid(tf.matmul(hidden_2, w['out']))

    def train(self, input_data, epochs=1000, batch_size=250, pretrain_epochs=10, k_d=2, k_g=1, verbose=True):
        """train the networks.
        note that a maximally-confused discriminator will output 0.5 for both real and
        fake samples, i.e. it can't tell the difference. thus its loss will be log(0.5) + log(0.5)
        this also means the generator's best loss will be log(0.5) because the discriminator is
        maximally confused on fake samples."""
        n_examples, input_dim = input_data.shape
        assert input_dim == self.input_dim

        if not hasattr(self, 'scaler'):
            self.scaler = MinMaxScaler()
            input_data = self.scaler.fit_transform(input_data)
        else:
            input_data = self.scaler.transform(input_data)

        if verbose:
            X_compare = minibatch(input_data, batch_size)
            z_compare = sample_noise(input_dim, batch_size)

        # pretrain the discriminator
        for _ in range(pretrain_epochs):
            for X_batch in minibatches(input_data, batch_size):
                # sample noise samples from the noise prior
                z_batch = sample_noise(input_dim, batch_size)

                self.sess.run(self.optimizer_d, {self.X: X_batch,
                                            self.z: z_batch,
                                            self.keep_prob: 1-self.drop_prob})

        for epoch in range(epochs):
            for i in range(k_d):
                for X_batch in minibatches(input_data, batch_size):
                    # sample noise samples from the noise prior
                    z_batch = sample_noise(input_dim, batch_size)

                    self.sess.run(self.optimizer_d,
                                  {self.X: X_batch,
                                   self.z: z_batch,
                                   self.keep_prob: 1-self.drop_prob})

            for i in range(k_g):
                for _ in minibatches(input_data, batch_size):
                    # sample noise samples from the noise prior
                    z_batch = sample_noise(input_dim, batch_size)
                    self.sess.run(self.optimizer_g, {self.z: z_batch,
                                                self.keep_prob: 1.})

            #if verbose and epoch % 50 == 0:
            if verbose and epoch % 950 == 0:
                print('EPOCH:', epoch)
                samples, d_loss_real, d_loss_fake, g_loss = self.sess.run(
                    [self.G, self.cost_d_real, self.cost_d_fake, self.cost_g],
                    {self.X: X_compare,
                     self.z: z_compare,
                     self.keep_prob: 1-self.drop_prob})
                print('D loss real', d_loss_real)
                print('D loss fake', d_loss_fake)
                print('G loss', g_loss)
                yield self.scaler.inverse_transform(samples)

    def generate(self, n):
        """generate n samples from the generator"""
        z_batch = sample_noise(self.input_dim, n)
        samples = self.sess.run(self.G, {self.z: z_batch})
        samples = self.scaler.inverse_transform(samples)
        return samples


if __name__ == '__main__':
    means = [0,0]
    covariance = [[1,0], [0, 10]]
    input_data = np.random.multivariate_normal(means, covariance, (100000,))
    _, input_dim = input_data.shape

    gan = GAN(input_dim, [10, 10], [10, 10])
    gan.train(input_data)
    samples = gan.generate(100)
    print(samples)
