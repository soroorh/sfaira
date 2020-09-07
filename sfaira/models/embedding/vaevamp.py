import numpy as np
import tensorflow as tf
from typing import List, Union, Tuple

from sfaira.models.embedding.output_layers import NegBinOutput, NegBinSharedDispOutput
from sfaira.models.embedding.external import BasicModel
from sfaira.models.embedding.external import PreprocInput
from sfaira.models.embedding.external import Topologies

def log_sum_of_exponentials(x, axis):
    x_max = tf.math.reduce_max(x, axis=axis)
    x_max_expanded = tf.expand_dims(x_max, axis=axis)
    return x_max + tf.math.log(tf.reduce_sum(tf.exp(x - x_max_expanded), axis=axis))

def log_normal_diag(x, mean, log_var, average=False, axis=None):
    log2pi = np.log(2 * np.pi)
    log_normal = -0.5 * (log_var + tf.square(x - mean) / tf.exp(log_var) + log2pi)
    if average:
        return tf.mean(log_normal, axis=axis)
    else:
        return tf.reduce_sum(log_normal, axis=axis)

class Sampling(tf.keras.layers.Layer):
    """Uses (z_mean, z_log_var) to sample z."""

    def call(self, inputs, **kwargs):
        z_mean, z_log_var = inputs
        batch = tf.shape(z_mean)[0]
        dim = tf.shape(z_mean)[1]
        epsilon = tf.keras.backend.random_normal(shape=(batch, dim))
        return z_mean + tf.exp(0.5 * z_log_var) * epsilon


class DensityBlock(tf.keras.layers.Layer):
    def __init__(
            self,
            latent_dim
    ):
        super(DensityBlock, self).__init__(name='density_block')

        self.sampling = Sampling()

        self.dense_mean = tf.keras.layers.Dense(
            units=latent_dim,
            activation="linear"
        )
        self.dense_log_var = tf.keras.layers.Dense(
            units=latent_dim,
            activation="linear"
        )

    def call(self, input_tensor):
        mean = self.dense_mean(input_tensor)
        log_var = tf.clip_by_value(
            self.dense_log_var(input_tensor),
            clip_value_min=np.log(0.001),  # variance larger 0.001
            clip_value_max=np.log(100.0)  # variance smaller 100.0
        )
        x = self.sampling((mean, log_var))
        return x, mean, log_var


class DenseBlock(tf.keras.layers.Layer):
    def __init__(
            self,
            config
    ):
        super(DenseBlock, self).__init__(name='dense_block')
        _, hidden_dim, l1_coef, l2_coef, dropout_rate, self.batchnorm, activation, kernel_initializer = config

        self.dense = tf.keras.layers.Dense(
            units=hidden_dim,
            activation=activation,
            kernel_initializer=kernel_initializer,
            kernel_regularizer=tf.keras.regularizers.l1_l2(l1=l1_coef, l2=l2_coef),
        )
        self.bn = tf.keras.layers.BatchNormalization(
            center=True,
            scale=True
        )
        self.dropout = tf.keras.layers.Dropout(
            dropout_rate,
            noise_shape=None,
            seed=None
        )

    def call(self, input_tensor, training=False):
        x = self.dense(input_tensor)
        if self.batchnorm:
            x = self.bn(x, training=training)
        x = self.dropout(x)
        return x


class TrainablePseudoInputs(tf.keras.layers.Layer):
    def __init__(self, out_shape, activation="hard_sigmoid", **kwargs):
        self.out_shape = out_shape
        self.pseudo_inputs = None
        super().__init__(**kwargs)
        self.activation = tf.keras.activations.get(activation)

    def build(self, input_shape):
        self.pseudo_inputs = self.add_weight(
            shape=self.out_shape,
            initializer=tf.random_normal_initializer(mean=-0.05, stddev=0.01),
            dtype=tf.float32,
            name='u'
        )
        super().build(input_shape)

    def call(self, inputs, **kwargs):
        return self.activation(self.pseudo_inputs)

    def compute_output_shape(self, input_shape):
        return self.out_shape


class Encoder(tf.keras.layers.Layer):
    """Maps input to embedding space"""

    def __init__(
            self,
            config,
            name='encoder',
            **kwargs
    ):
        super().__init__(name=name, **kwargs)
        z1_dim, z2_dim = config[0]

        self.enc_dense1 = DenseBlock(config)
        self.enc_dense2 = DenseBlock(config)
        self.q_z2 = DensityBlock(z2_dim)

        self.enc_dense3a = DenseBlock(config)
        self.enc_dense3b = DenseBlock(config)
        self.enc_dense4 = DenseBlock(config)
        self.q_z1 = DensityBlock(z1_dim)

    def call(self, inputs, **kwargs):                                                    # (batch_size, in_dim)
        x = self.enc_dense1(inputs)                                          # (batch_size, 300)
        x = self.enc_dense2(x)                                          # (batch_size, 300)
        z2, q_z2_mean, q_z2_log_var = self.q_z2(x)                      # (batch_size, z2_dim)

        x = tf.concat([self.enc_dense3a(z2), self.enc_dense3b(inputs)], axis=1)
        x = self.enc_dense4(x)
        z1, q_z1_mean, q_z1_log_var = self.q_z1(x)
        return (z1, q_z1_mean, q_z1_log_var), (z2, q_z2_mean, q_z2_log_var)


class Decoder(Encoder):
    """Maps latent space sample back to output"""

    def __init__(
            self,
            in_dim,
            batch_size_u,
            config,
            name='decoder',
            **kwargs
    ):
        super().__init__(config=config, name=name, **kwargs)
        z1_dim, z2_dim = config[0]

        self.dec_dense1 = DenseBlock(config)
        self.dec_dense2 = DenseBlock(config)
        self.p_z1 = DensityBlock(z1_dim)

        self.dec_dense3a = DenseBlock(config)
        self.dec_dense3b = DenseBlock(config)

        self.dec_dense4 = DenseBlock(config)

        self.pseudo_inputs_layer = TrainablePseudoInputs(out_shape=(batch_size_u, in_dim))

    def call(self, inputs, **kwargs):
        z1, z2, data_input = inputs                                     # (batch_size, z1_dim/z2_dim/in_dim)

        # p(z_1|z_2)
        x = self.dec_dense1(z2)                                         # (batch_size, 300)
        x = self.dec_dense2(x)                                          # (batch_size, 300)
        _, p_z1_mean, p_z1_log_var = self.p_z1(x)                       # (batch_size, z1_dim)

        # the prior p(z_2)
        u = self.pseudo_inputs_layer(data_input)                        # (batch_size_u, in_dim)
        x = self.enc_dense1(u)                                          # (batch_size_u, 300)
        x = self.enc_dense2(x)                                          # (batch_size_u, 300)
        _, p_z2_mean, p_z2_log_var = self.q_z2(x)                       # (batch_size_u, z2_dim)

        x = tf.concat([self.dec_dense3a(z1), self.dec_dense3b(z2)], axis=1)
        out = self.dec_dense4(x)

        return (p_z1_mean, p_z1_log_var), (p_z2_mean, p_z2_log_var), out


class ModelVaeVamp(tf.keras.Model):

    def predict_reconstructed(self, x: np.ndarray):
        return np.split(self.training_model.predict(x)[0], indices_or_sections=2, axis=1)[0]

    def __init__(
            self,
            in_dim,
            latent_dim=(64, 64),
            hidden_dim=300,
            dropout_rate=0.1,
            l1_coef: float = 0.,
            l2_coef: float = 0.,
            batch_size_u: int = 500,
            batchnorm: bool = False,
            activation='tanh',
            init='glorot_uniform',
            output_layer="nb"
    ):
        super(ModelVaeVamp, self).__init__()
        config = (
            latent_dim,
            hidden_dim,
            l1_coef,
            l2_coef,
            dropout_rate,
            batchnorm,
            activation,
            init
        )
        inputs_encoder = tf.keras.Input(shape=(in_dim,), name='counts')
        inputs_sf = tf.keras.Input(shape=(1,), name='size_factors')
        inputs_encoder_pp = PreprocInput()(inputs_encoder)
        encoder = Encoder(config)
        decoder = Decoder(in_dim, batch_size_u, config)

        (z1, q_z1_mean, q_z1_log_var), (z2, q_z2_mean, q_z2_log_var) = encoder(inputs_encoder_pp)
        (p_z1_mean, p_z1_log_var), (p_z2_mean, p_z2_log_var), out = decoder((z1, z2, inputs_encoder_pp))

        z2_expanded = tf.expand_dims(z2, axis=1)  # (batch_size, 1, dim_z2)
        p_z2_mean_expanded = tf.expand_dims(p_z2_mean, axis=0)  # (1, batch_size_u, dim_z2)
        p_z2_log_var_expanded = tf.expand_dims(p_z2_log_var, axis=0)  # (1, batch_size_u, dim_z2)

        log_p_z1 = log_normal_diag(z1, p_z1_mean, p_z1_log_var, axis=1)
        log_q_z1 = log_normal_diag(z1, q_z1_mean, q_z1_log_var, axis=1)
        # the prior log_p_z2
        log_p_z2 = log_normal_diag(z2_expanded, p_z2_mean_expanded, p_z2_log_var_expanded, axis=2)
        log_p_z2 = log_sum_of_exponentials(log_p_z2, axis=1)  # marginalize over batch_size_u
        log_q_z2 = log_normal_diag(z2, q_z2_mean, q_z2_log_var, axis=1)

        logqz_x = tf.expand_dims(log_q_z1 + log_q_z2, axis=1)
        logpz = tf.expand_dims(log_p_z1 + log_p_z2, axis=1)

        expected_densities = tf.keras.layers.Concatenate(axis=1, name="kl")([logqz_x, logpz])

        if output_layer == 'nb':
            output_decoder_nb = NegBinOutput(original_dim=in_dim)((out, inputs_sf))
        elif output_layer == 'nb_shared_disp':
            output_decoder_nb = NegBinSharedDispOutput(original_dim=in_dim)((out, inputs_sf))
        else:
            raise ValueError("tried to access a non-supported output layer %s" % output_layer)
        output_decoder_nb_concat = tf.keras.layers.Concatenate(axis=1, name="neg_ll")(output_decoder_nb)

        z = tf.keras.layers.Concatenate(axis=1, name="z")([z1, z2])
        z_mean = tf.keras.layers.Concatenate(axis=1, name="z_mean")([q_z1_mean, q_z2_mean])
        z_log_var = tf.keras.layers.Concatenate(axis=1, name="z_log_var")([q_z1_log_var, q_z2_log_var])

        self.encoder_model = tf.keras.Model(
            inputs=inputs_encoder,
            outputs=[z, z_mean, z_log_var],
            name="encoder_model"
        )
        self.training_model = tf.keras.Model(
            inputs=[inputs_encoder, inputs_sf],
            outputs=[output_decoder_nb_concat, expected_densities],
            name="autoencoder"
        )

    def predict_embedding(self, x: np.ndarray):
        return self.encoder_model.predict(x)


class ModelVaeVampVersioned(ModelVaeVamp):
    def __init__(
            self,
            topology_container: Topologies,
            override_hyperpar: Union[dict, None] = None
    ):
        hyperpar = topology_container.topology["hyper_parameters"]
        if override_hyperpar is not None:
            for k in list(override_hyperpar.keys()):
                hyperpar[k] = override_hyperpar[k]
        ModelVaeVamp.__init__(
            self=self,
            in_dim=topology_container.ngenes,
            **hyperpar
        )

        print('passed hyperpar: \n', hyperpar)
        self._topology_id = topology_container.topology_id
        self.genome_size = topology_container.ngenes
        self.model_class = topology_container.model_class
        self.model_type = topology_container.model_type
        self.hyperparam = dict(
            list(hyperpar.items()) +
            [
                ("topology_id", self._topology_id),
                ("genome_size", self.genome_size),
                ("model_class", self.model_class),
                ("model_type", self.model_type)
            ]
        )
