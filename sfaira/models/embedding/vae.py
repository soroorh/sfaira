import numpy as np
import tensorflow as tf
from typing import List, Union, Tuple

from sfaira.models.embedding.output_layers import NegBinOutput, NegBinSharedDispOutput
from sfaira.models.embedding.external import BasicModel
from sfaira.models.embedding.external import PreprocInput
from sfaira.models.embedding.external import Topologies


class Sampling(tf.keras.layers.Layer):
    """Uses (z_mean, z_log_var) to sample z."""

    def call(self, inputs, **kwargs):
        z_mean, z_log_var = inputs
        batch = tf.shape(z_mean)[0]
        dim = tf.shape(z_mean)[1]
        epsilon = tf.keras.backend.random_normal(shape=(batch, dim))
        return z_mean + tf.exp(0.5 * z_log_var) * epsilon


class Encoder(tf.keras.layers.Layer):
    """Maps input to embedding space"""

    def __init__(
            self,
            latent_dim: Tuple,
            dropout_rate,
            l1_coef: float,
            l2_coef: float,
            batchnorm: bool,
            activation: str,
            kernel_initializer: str,
            name='encoder',
            **kwargs
    ):
        super().__init__(name=name, **kwargs)

        self.fwd_pass = []
        for i, hid_size in enumerate(latent_dim[:-1]):
            self.fwd_pass.append(
                tf.keras.layers.Dense(
                    units=hid_size,
                    activation=activation,
                    kernel_initializer=kernel_initializer,
                    kernel_regularizer=tf.keras.regularizers.l1_l2(l1=l1_coef, l2=l2_coef),
                    name='enc%s' % i
                )
            )
            # At the bottleneck layer:
            # 1. a linear activation function is used to not restrict the support of the hidden units
            # 2. no batch normalisation is used to not scale the variance of inactive units up and the activity of
            # active units down.
            # 3. no dropout is used to not confound the required bottleneck dimension with dropout rate.
            if batchnorm and i < (len(latent_dim) - 1):
                self.fwd_pass.append(
                    tf.keras.layers.BatchNormalization(
                        center=True,
                        scale=True
                    )
                )
            if i < (len(latent_dim) - 1):
                self.fwd_pass.append(
                    tf.keras.layers.Dropout(
                        dropout_rate,
                        noise_shape=None,
                        seed=None
                    )
                )

        # final layer
        self.dense_mean = tf.keras.layers.Dense(
            units=latent_dim[-1],
            activation="linear"
        )
        self.dense_log_var = tf.keras.layers.Dense(
            units=latent_dim[-1],
            activation="linear"
        )
        self.sampling = Sampling()

    def call(self, inputs, **kwargs):
        x = inputs
        for layer in self.fwd_pass:
            x = layer(x)
        # final layer
        z_mean = self.dense_mean(x)
        z_log_var = self.dense_log_var(x)
        z = self.sampling((z_mean, z_log_var))
        return z, z_mean, z_log_var


class Decoder(tf.keras.layers.Layer):
    """Maps latent space sample back to output"""

    def __init__(
            self,
            latent_dim: Tuple,
            dropout_rate,
            l1_coef: float,
            l2_coef: float,
            batchnorm: bool,
            activation: str,
            kernel_initializer: str,
            name='decoder',
            **kwargs
    ):
        super().__init__(name=name, **kwargs)

        self.fwd_pass = []
        for i, hid_size in enumerate(latent_dim):
            self.fwd_pass.append(
                tf.keras.layers.Dense(
                    units=hid_size,
                    activation=activation,
                    kernel_initializer=kernel_initializer,
                    kernel_regularizer=tf.keras.regularizers.l1_l2(l1=l1_coef, l2=l2_coef),
                    name='dec%s' % i
                )
            )
            if batchnorm:
                self.fwd_pass.append(
                    tf.keras.layers.BatchNormalization(
                        center=True,
                        scale=True
                    )
                )
            self.fwd_pass.append(
                tf.keras.layers.Dropout(
                    dropout_rate,
                    noise_shape=None,
                    seed=None
                )
            )

    def call(self, inputs, **kwargs):
        x = inputs
        for layer in self.fwd_pass:
            x = layer(x)
        return x


class ModelVae(BasicModel):

    def predict_reconstructed(self, x: np.ndarray):
        return np.split(self.training_model.predict(x)[0], indices_or_sections=2, axis=1)[0]

    def __init__(
            self,
            in_dim,
            latent_dim=(128, 64, 2, 64, 128),
            dropout_rate=0.1,
            l1_coef: float = 0.,
            l2_coef: float = 0.,
            batchnorm: bool = False,
            activation='tanh',
            init='glorot_uniform',
            output_layer="nb"
    ):
        super(ModelVae, self).__init__()
        # Check length of latent dim to divide encoder-decoder stack:
        if len(latent_dim) % 2 == 1:
            n_layers_enc = len(latent_dim) // 2 + 1
        else:
            raise ValueError("len(latent_dim)=%i should be uneven to provide a defined bottleneck" % len(latent_dim))


        inputs_encoder = tf.keras.Input(shape=(in_dim,), name='counts')
        inputs_sf = tf.keras.Input(shape=(1,), name='size_factors')
        inputs_encoder_pp = PreprocInput()(inputs_encoder)
        output_encoder = Encoder(
            latent_dim=latent_dim[:n_layers_enc],
            dropout_rate=dropout_rate,
            l1_coef=l1_coef,
            l2_coef=l2_coef,
            batchnorm=batchnorm,
            activation=activation,
            kernel_initializer=init
        )(inputs_encoder_pp)

        z, z_mean, z_log_var = output_encoder
        expected_logqz_x = -0.5 * tf.reduce_sum(1 + z_log_var, axis=1)
        expected_logpz = -0.5 * tf.reduce_sum(tf.square(z_mean) + tf.exp(z_log_var), axis=1)

        expected_densities = tf.keras.layers.Concatenate(axis=1, name='kl')([
            tf.expand_dims(expected_logqz_x, axis=1),
            tf.expand_dims(expected_logpz, axis=1)])

        output_decoder = Decoder(
            latent_dim=latent_dim[n_layers_enc:],
            dropout_rate=dropout_rate,
            l1_coef=l1_coef,
            l2_coef=l2_coef,
            batchnorm=batchnorm,
            activation=activation,
            kernel_initializer=init
        )(z)

        if output_layer == 'nb':
            output_decoder_nb = NegBinOutput(original_dim=in_dim)((output_decoder, inputs_sf))
        elif output_layer == 'nb_shared_disp':
            output_decoder_nb = NegBinSharedDispOutput(original_dim=in_dim)((output_decoder, inputs_sf))
        else:
            raise ValueError("tried to access a non-supported output layer %s" % output_layer)
        output_decoder_nb_concat = tf.keras.layers.Concatenate(axis=1, name="neg_ll")(output_decoder_nb)

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


class ModelVaeVersioned(ModelVae):
    def __init__(
            self,
            topology_container: Topologies,
            override_hyperpar: Union[dict, None] = None
    ):
        hyperpar = topology_container.topology["hyper_parameters"]
        if override_hyperpar is not None:
            for k in list(override_hyperpar.keys()):
                hyperpar[k] = override_hyperpar[k]
        ModelVae.__init__(
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
