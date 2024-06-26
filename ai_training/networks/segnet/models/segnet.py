import os

from tensorflow.keras.models import *
from tensorflow.keras.layers import *

from .config import IMAGE_ORDERING
from .model_utils import get_segmentation_model
from ai_training.networks.common_utils.feature import create_feature_extractor

mobilenet = {1:10,2:23,3:36,4:73,5:86}
densenet121 = {1:8,2:50,3:138,4:310,5:426}
nasnetmobile = {1:7,2:64,3:295,4:537,5:768}
squeezenet = {1:2,2:17,3:32,4:47,5:61}
full_yolo = {1:14,2:27,3:40,4:53,5:73}
tiny_yolo = {1:7,2:15,3:23,4:27,5:30}
resnet50 = {1:2,2:37,3:80,4:142,5:174}

def chopper(model, model_name, f):
    outputs = model.layers[model_name[f]].output

def segnet_decoder(f, n_classes, n_up=3):

    assert n_up >= 2

    o = f
    o = (ZeroPadding2D((1, 1), data_format=IMAGE_ORDERING))(o)
    o = (Conv2D(256, (3, 3), padding='valid', data_format=IMAGE_ORDERING))(o)
    o = (BatchNormalization())(o)

    o = (UpSampling2D((2, 2), data_format=IMAGE_ORDERING))(o)
    o = (ZeroPadding2D((1, 1), data_format=IMAGE_ORDERING))(o)
    o = (Conv2D(128, (3, 3), padding='valid', data_format=IMAGE_ORDERING))(o)
    o = (BatchNormalization())(o)

    for _ in range(n_up-2):
        o = (UpSampling2D((2, 2), data_format=IMAGE_ORDERING))(o)
        o = (ZeroPadding2D((1, 1), data_format=IMAGE_ORDERING))(o)
        o = (Conv2D(64, (3, 3), padding='valid',
             data_format=IMAGE_ORDERING))(o)
        o = (BatchNormalization())(o)

    o = (UpSampling2D((2, 2), data_format=IMAGE_ORDERING))(o)
    o = (ZeroPadding2D((1, 1), data_format=IMAGE_ORDERING))(o)
    o = (Conv2D(32, (3, 3), padding='valid', data_format=IMAGE_ORDERING))(o)
    o = (BatchNormalization())(o)

    o = Conv2D(n_classes, (3, 3), padding='same',
               data_format=IMAGE_ORDERING)(o)

    return o


def _segnet(n_classes, encoder_input, encoder_output,  input_height=416, input_width=608, encoder_level=3):

    o = segnet_decoder(f=encoder_output, n_classes=n_classes, n_up=encoder_level-1)
    model = get_segmentation_model(encoder_input, o)

    return model

def full_yolo_segnet(n_classes, input_size, encoder_level, weights):

    encoder = create_feature_extractor('Full Yolo',input_size, weights)
    encoder_output = encoder.feature_extractor.layers[full_yolo[encoder_level]].output
    print(encoder_output)
    encoder_input = encoder.feature_extractor.inputs[0]
    encoder_level += 1
    model = _segnet(n_classes, encoder_input, encoder_output, input_size, encoder_level=encoder_level)
    model.model_name = "full_yolo_segnet"
    model.normalize = encoder.normalize
    return model

def tiny_yolo_segnet(n_classes, input_size, encoder_level, weights):

    encoder = create_feature_extractor('Tiny Yolo',input_size, weights)
    encoder_output = encoder.feature_extractor.layers[tiny_yolo[encoder_level]].output
    print(encoder_output)
    encoder_input = encoder.feature_extractor.inputs[0]
    encoder_level += 1
    model = _segnet(n_classes, encoder_input, encoder_output, input_size, encoder_level=encoder_level)
    model.model_name = "tiny_yolo_segnet"
    model.normalize = encoder.normalize
    return model

def squeezenet_segnet(n_classes, input_size, encoder_level, weights):

    encoder = create_feature_extractor('SqueezeNet',input_size, weights)
    encoder_output = encoder.feature_extractor.layers[squeezenet[encoder_level]].output
    encoder_input = encoder.feature_extractor.inputs[0]

    model = _segnet(n_classes, encoder_input, encoder_output, input_size, encoder_level=encoder_level)
    model.model_name = "squeezenet_segnet"
    model.normalize = encoder.normalize
    return model

def densenet121_segnet(n_classes, input_size, encoder_level, weights):

    encoder = create_feature_extractor('DenseNet121', input_size, weights)
    encoder_output = encoder.feature_extractor.layers[densenet121[encoder_level]].output
    encoder_input = encoder.feature_extractor.inputs[0]

    model = _segnet(n_classes, encoder_input, encoder_output, input_size, encoder_level=encoder_level)
    model.model_name = "densenet121_segnet"
    model.normalize = encoder.normalize
    return model

def nasnetmobile_segnet(n_classes, input_size, encoder_level, weights):

    encoder = create_feature_extractor('NASNetMobile', input_size, weights)
    encoder_output = encoder.feature_extractor.layers[nasnetmobile[encoder_level]].output
    encoder_input = encoder.feature_extractor.inputs[0]

    model = _segnet(n_classes, encoder_input, encoder_output, input_size, encoder_level=encoder_level)
    model.model_name = "nasnetmobile_segnet"
    model.normalize = encoder.normalize
    return model

def resnet50_segnet(n_classes, input_size, encoder_level, weights):

    encoder = create_feature_extractor('ResNet50',input_size, weights)
    encoder_output = encoder.feature_extractor.layers[resnet50[encoder_level]].output
    encoder_input = encoder.feature_extractor.inputs[0]

    model = _segnet(n_classes, encoder_input, encoder_output, input_size, encoder_level=encoder_level)
    model.model_name = "resnet50_segnet"
    model.normalize = encoder.normalize
    return model


def mobilenet_segnet(n_classes, input_size, encoder_level, weights, architecture = 'MobileNet2_5'):
    
    encoder = create_feature_extractor(architecture, input_size, weights)
    encoder_output = encoder.feature_extractor.layers[mobilenet[encoder_level]].output
    encoder_input = encoder.feature_extractor.inputs[0]
    
    model = _segnet(n_classes, encoder_input, encoder_output, input_size, encoder_level=encoder_level)
    model.model_name = "mobilenet_segnet"
    model.normalize = encoder.normalize
    return model

