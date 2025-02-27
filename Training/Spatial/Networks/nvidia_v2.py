"""NETWORK HANDLER AND CREATER"""
#pylint: disable=invalid-name
#pylint: disable=superfluous-parens

from keras.models import Model
from keras.layers import Input, concatenate
from keras.layers.core import Dense, Activation, Flatten, Lambda, Dropout
from keras.layers.convolutional import Conv2D
from keras.layers.pooling import MaxPooling2D
from keras.layers.normalization import BatchNormalization

class NetworkHandler(object):
    """ Class that holds the network in use"""
    def __init__(self):
        self.conv_layers = 0
        self.pool_layers = 0
        self.batch_norm_layers = 0
        self.activation_layers = 0
        self.dropout_layers = 0
        self.dense_layers = 0
        self.model = None

    def conv_block(self, x, filters, kernel_size, stride, padding='valid'):
        """ Creates a full conv block """
        x = self.conv(x, filters, kernel_size, stride, padding)
        x = self.batch_norm(x)
        x = self.dropout(x, rate=0.0)
        x = self.activation(x)
        return x


    def conv(self, x, filters, kernel_size, stride, padding='valid', activation=None):
        """ Adds a convolutional layer """
        self.conv_layers += 1
        x = Conv2D(
            filters=filters,
            kernel_size=kernel_size,
            strides=stride,
            padding=padding,
            activation=activation,
            name="conv_" + str(self.conv_layers)
        )(x)
        return x

    def max_pool(self, x, pool_size=(2, 2)):
        """ Adds a max pooling layer """
        self.pool_layers += 1
        x = MaxPooling2D(pool_size=pool_size, name="max_pool_" + str(self.conv_layers))(x)
        return x

    def batch_norm(self, x, chanDim=-1):
        """
        Adds a batch normalisation layer
        NB: after a Conv2D layer with data_format="channels_first",
        set axis=1 in BatchNormalization
        """
        self.batch_norm_layers += 1
        x = BatchNormalization(axis=chanDim, name="batch_norm_" + str(self.batch_norm_layers))(x)
        return x

    def activation(self, x, function="relu"):
        """ Adds an activation-layer """
        self.activation_layers += 1
        x = Activation(function, name="activation_" + str(self.activation_layers))(x)
        return x

    def dropout(self, x, rate=0.0):
        """ Adds a dropout layer """
        self.dropout_layers += 1
        x = Dropout(rate, name="dropout_" + str(self.dropout_layers))(x)
        return x

    def dense(self, x, output_size, function=None, name=None):
        """ Adds a dense layer """
        if not name:
            name="dense_" + str(self.dense_layers)
        self.dense_layers += 1
        x = Dense(output_size, activation=function, name=name)(x)
        return x

def hsv_convert(x):
    """ Converts input from rgb to hsv in the range 0-1 """
    import tensorflow as tf
    return tf.image.rgb_to_hsv(x)

def load_network(conf):
    """ Creates and returns a model using the class network handler """
    input_measures = [key for key in conf.available_columns if conf.input_data[key]]
    output_measures = [key for key in conf.available_columns if conf.output_data[key]]
    input_size_data = conf.input_size_data

    inputs = []
    x = Input(shape=input_size_data["Image"], name="input_Image")
    inputs.append(x)
    net = NetworkHandler()

    # RGB TO HSV
    x = Lambda(hsv_convert)(x)

    # CONV 1
    x = net.conv(x, 24, 5, 2, activation="elu")

    # CONV 2
    x = net.conv(x, 36, 5, 2, activation="elu")

    # CONV 3
    x = net.conv(x, 48, 5, 2, activation="elu")

    # CONV 4
    x = net.conv(x, 64, 3, 1, activation="elu")

    # CONV 4
    x = net.conv(x, 64, 3, 1, activation="elu")

    #x = net.dropout(x, rate=0.5)
    
    # FLATTEN
    x = Flatten()(x)
    #x = net.dense(x, 100)
    #x = net.dense(x, 50)
    #x = net.dense(x, 10)

    #x = net.dropout(x, rate=0.3)
    


    #######     INPUT DATA     #######
    #for measure in input_measures:
    #    input_layer = Input(input_size_data[measure], name="input_" + measure)
    #    inputs.append(input_layer)
    #    x = concatenate([x, input_layer], 1)

    
    #######     OUTPUT DATA     #######
    outputs = []
    for measure in output_measures:
        function = None
        if measure != "Steer":
            function = "relu"
        x_branched = net.dense(x, 100, function=function)
        #x_branched = net.dropout(x_branched, rate=0.3)
        x_branched = net.dense(x_branched, 50, function=function)
        x_branched = net.dense(x_branched, 10, function=function)
        output_layer = net.dense(
            x_branched,
            conf.output_size_data[measure],
            function=conf.activation_functions["output_" + measure],
            name="output_" + measure
            )
        outputs.append(output_layer)

    net.model = Model(inputs=inputs, outputs=outputs)

    return net
