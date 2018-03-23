#!/usr/bin/env python3

import os, sys, logging
import numpy as np

# Silence import message
stderr = sys.stderr
sys.stderr = open('/dev/null', 'w')
import keras
sys.stderr = stderr


import utility

logger = logging.getLogger("cil_project.models.cnn_lr_d")

class Model:
    """CNN model implementing a classifier using leaky ReLU and dropouts."""

    def __init__(self, train_path, patch_size=16, context_padding=28):
        """Initialise the model.

        Args:
            train_path (str): path to training data.
            patch_size (int): default=16 - the size of the patch to analyse.
            context_padding (int): default=28 - padding on each side of the analysed patch.
        """
        logger.info("Generating CNN model with leaky ReLU and dropouts ...")

        # Seed the RNG to ensure the results are reproducible.
        np.random.seed(0)

        self.train_path = train_path
        self.patch_size = patch_size
        self.context_padding = context_padding
        self.window_size = patch_size + 2 * context_padding

        # The following can be set using a config file in ~/.keras/keras.json
        if keras.backend.image_dim_ordering() == "tf":
            # Keras is using Tensorflow as backend
            input_dim = (self.window_size, self.window_size, 3)
        else:
            # Keras is using Theano as backend
            input_dim = (3, self.window_size, self.window_size)

        # Define the model
        self.model = keras.models.Sequential()

        # Define the first wave of layers
        self.model.add(keras.layers.Convolution2D(filters=64,
                                                  kernel_size=(5, 5),
                                                  padding="same",
                                                  input_shape=input_dim))
        self.model.add(keras.layers.LeakyReLU(alpha=0.1))
        self.model.add(keras.layers.MaxPooling2D(pool_size=(2,2),
                                                 padding="same"))
        self.model.add(keras.layers.Dropout(rate=0.25))

        # Define the second wave of layers
        self.model.add(keras.layers.Convolution2D(filters=128,
                                                  kernel_size=(3, 3),
                                                  padding="same"))
        self.model.add(keras.layers.LeakyReLU(alpha=0.1))
        self.model.add(keras.layers.MaxPooling2D(pool_size=(2,2),
                                                 padding="same"))
        self.model.add(keras.layers.Dropout(rate=0.25))

        # Define the third wave of layers
        self.model.add(keras.layers.Convolution2D(filters=256,
                                                  kernel_size=(3, 3),
                                                  padding="same"))
        self.model.add(keras.layers.LeakyReLU(alpha=0.1))
        self.model.add(keras.layers.MaxPooling2D(pool_size=(2,2),
                                                 padding="same"))
        self.model.add(keras.layers.Dropout(rate=0.25))

        # Define the fourth wave of layers
        self.model.add(keras.layers.Convolution2D(filters=256,
                                                  kernel_size=(3, 3),
                                                  padding="same"))
        self.model.add(keras.layers.LeakyReLU(alpha=0.1))
        self.model.add(keras.layers.MaxPooling2D(pool_size=(2,2),
                                                 padding="same"))
        self.model.add(keras.layers.Dropout(rate=0.25))

        # Define the fifth wave of layers
        self.model.add(keras.layers.Flatten())
        self.model.add(keras.layers.Dense(units=128,
                                          kernel_regularizer=keras.regularizers.l2(1e-6)))
        self.model.add(keras.layers.LeakyReLU(alpha=0.1))
        self.model.add(keras.layers.Dropout(rate=0.5))

        self.model.add(keras.layers.Dense(units=2,
                                          kernel_regularizer=keras.regularizers.l2(1e-6),
                                          activation="softmax"))

        logger.info("Done")

    def train(self, data, verifier):
        """Train the model.

        Args:
            data (numpy.ndarray): input data to the model.
            verifier (numpy.ndarray): verifier data for the model.
        """
        logger.info("Preparing training ...")

        self.model.compile(loss=keras.losses.categorical_crossentropy,
                           optimizer=keras.optimizers.Adam,
                           metrics=["accuracy"])

        # TODO finish



    def _create_batch(self, batch_size, data, verifier):
        """Create a batch to feed to the neural network for training.

        Args:
            batch_size (int): size of each batch.
            data (numpy.ndarray): input data to create batch.
            verifier (numpy.ndarray): verifier data to create batch.
        """
        while True:
            batch_data = np.empty((batch_size, self.window_size, self.window_size, 3))
            batch_verifier = np.empty((batch_size))

            for idx in range(batch_size):
                data_patch, verifier_patch = utility.get_random_image_patch(self.train_path,
                                                                            self.patch_size,
                                                                            self.patch_size,
                                                                            self.context_padding)
                label = (np.mean(verifier_patch) > 0.25) * 1
                batch_data[idx] = data_patch
                batch_verifier[idx] = label

            if keras.backend.image_dim_ordering() == "th":
                batch_data = np.rollaxis(batch_data, 3, 1)

            yield (batch_data, verifier_data)


