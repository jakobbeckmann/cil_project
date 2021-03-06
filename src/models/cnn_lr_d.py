#!/usr/bin/env python3

import keras

from models.base_model import BaseModel
from utils.commons import *

file_path = os.path.dirname(os.path.abspath(__file__))


class CnnLrD(BaseModel):
    """CNN model implementing a classifier using leaky ReLU and dropouts. Used as baseline in our project. Code based on
       https://github.com/dariopavllo/road-segmentation."""

    def __init__(self, train_generator, path=None):
        """Initialise the model.

        If `path` is given, the model is loaded from memory instead of compiled.
        """
        super().__init__(train_generator)

        if path:
            print("Loading existing model from {}".format(path))
            self.load(path)
            print("Finished loading model")
            return

        print("Generating CNN model with leaky ReLU and dropouts ...")

        # Define the model
        self.model = keras.models.Sequential()

        # Define the first wave of layers
        self.model.add(keras.layers.Convolution2D(filters=64,
                                                  kernel_size=(5, 5),
                                                  padding="same",
                                                  input_shape=train_generator.input_dim()))
        self.model.add(keras.layers.LeakyReLU(alpha=0.1))
        self.model.add(keras.layers.MaxPooling2D(pool_size=(2, 2),
                                                 padding="same"))
        self.model.add(keras.layers.Dropout(rate=0.25))

        # Define the second wave of layers
        self.model.add(keras.layers.Convolution2D(filters=128,
                                                  kernel_size=(3, 3),
                                                  padding="same"))
        self.model.add(keras.layers.LeakyReLU(alpha=0.1))
        self.model.add(keras.layers.MaxPooling2D(pool_size=(2, 2),
                                                 padding="same"))
        self.model.add(keras.layers.Dropout(rate=0.25))

        # Define the third wave of layers
        self.model.add(keras.layers.Convolution2D(filters=256,
                                                  kernel_size=(3, 3),
                                                  padding="same"))
        self.model.add(keras.layers.LeakyReLU(alpha=0.1))
        self.model.add(keras.layers.MaxPooling2D(pool_size=(2, 2),
                                                 padding="same"))
        self.model.add(keras.layers.Dropout(rate=0.25))

        # Define the fourth wave of layers
        self.model.add(keras.layers.Convolution2D(filters=256,
                                                  kernel_size=(3, 3),
                                                  padding="same"))
        self.model.add(keras.layers.LeakyReLU(alpha=0.1))
        self.model.add(keras.layers.MaxPooling2D(pool_size=(2, 2),
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

        print("Compiling model ...")

        optimiser = keras.optimizers.Adam()
        self.model.compile(loss=keras.losses.categorical_crossentropy,
                           optimizer=optimiser,
                           metrics=["accuracy"])
        print(self.model.summary())

        print("Done")

    def train(self, epochs=150, steps=5000, train_split=0.66):
        """Train the model.

        Args:
            epochs (int): default: 150 - epochs to train.
            steps (int): default: 5000 - batches per epoch to train.
        """

        print("Starting training ...")

        lr_callback = keras.callbacks.ReduceLROnPlateau(monitor="acc",
                                                        factor=0.5,
                                                        patience=0.5,
                                                        verbose=0,
                                                        cooldown=0,
                                                        min_lr=0)
        stop_callback = keras.callbacks.EarlyStopping(monitor="acc",
                                                      min_delta=0.0001,
                                                      patience=11,
                                                      verbose=0,
                                                      mode="auto")

        tensorboard_callback = keras.callbacks.TensorBoard(log_dir=properties["LOG_DIR"], histogram_freq=0,
                                                           batch_size=128,
                                                           write_graph=True,
                                                           write_grads=False, write_images=False, embeddings_freq=0,
                                                           embeddings_layer_names=None, embeddings_metadata=None)

        checkpoint_callback = keras.callbacks.ModelCheckpoint(
            os.path.join(properties["OUTPUT_DIR"], 'weights.h5'),
            monitor='val_loss', verbose=0, save_best_only=True,
            save_weights_only=False, mode='auto', period=1)

        self.model.fit_generator(self.train_generator.generate_patch(type="train", train_split=train_split),
                                 steps_per_epoch=steps,
                                 epochs=epochs,
                                 callbacks=[lr_callback, stop_callback, tensorboard_callback,
                                            checkpoint_callback],
                                 validation_data=self.train_generator.generate_patch(type="valid", train_split=train_split),
                                 validation_steps=100)

    def save(self, path):
        """Save the model of the trained model.

        Args:
            path (path): path for the model file.
        """
        self.model.save(path)
        print("Model saved to {}".format(path))
