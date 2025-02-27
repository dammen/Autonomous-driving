"""Main module for spatial training"""
#pylint: disable=superfluous-parens
import os
import numpy as np
from keras.callbacks import ModelCheckpoint, EarlyStopping
from Spatial.Networks.nvidia import load_network
from Spatial.batch_generator import BatchGenerator
from Spatial.data_configuration import Config

from Misc.misc import save_results
from Misc.misc import create_new_folder
from Misc.stop_training_on_request import StopTrainingOnInput

class Trainer(object):
    """ Main class for training a new model """
    def __init__(self):
        self.conf = Config()
        self.history = None
        self.train_generator = None
        self.validation_generator = None
        self.network_handler = None
        self.folder = None
        self.create_results_folder()
        self.checkpoint_path_loss = "Stored_models/" + \
            str(self.folder) + "/Checkpoints/train_loss-{epoch:02d}-{loss:.3f}.hdf5"
        self.checkpoint_path_val_loss = "Stored_models/" + \
            str(self.folder) + "/Checkpoints/val_loss-{epoch:02d}-{val_loss:.3f}.hdf5"


    def create_results_folder(self):
        """ Creates two folders:
        1. The folder that contains all results - defined by an integer
        2. The Checkoint folder used to store all checkpoints
        """
        self.folder = create_new_folder("../Spatial/Stored_models/")
        try:
            os.mkdir("Stored_models/" + str(self.folder) + "/Checkpoints")
            print("Created checpoints folder for " + str(self.folder))
        except OSError:
            print("Creation of the directory %s failed" % "Checkpoints")

    def initialise_generator_and_net(self):
        """ Creates a batch generator and a network handler"""
        self.train_generator = BatchGenerator(self.conf, data="Training_data")
        self.validation_generator = BatchGenerator(self.conf, data="Validation_data")
        self.network_handler = load_network(self.conf)

    def train(self):
        """ Trains the model """
        self.network_handler.model.compile(
            loss=self.conf.loss_functions,
            optimizer=self.conf.train_conf.optimizer,
            loss_weights=self.conf.loss_weights
        )
        self.history = self.network_handler.model.fit_generator(
            self.train_generator,
            validation_data=self.validation_generator,
            steps_per_epoch=self.conf.steps_per_epoch,
            validation_steps=self.conf.validation_steps,
            epochs=self.conf.train_conf.epochs,
            shuffle=True,
            callbacks=[
                ModelCheckpoint(self.checkpoint_path_loss, monitor='loss', save_best_only=True, period=int(np.floor(self.conf.train_conf.epochs/10))),
                ModelCheckpoint(self.checkpoint_path_val_loss, monitor='val_loss', save_best_only=True),
                EarlyStopping(monitor='val_loss', min_delta=0, patience=10, verbose=1, mode='auto', baseline=None, restore_best_weights=True),
                StopTrainingOnInput()
            ],
            use_multiprocessing=True,
            workers=12,
            verbose=1
        )

    def save(self, net="nvidia"):
        """ Saves Model(object, image and description), History and config """
        save_results(self, path="../Spatial/", net=net)
