import glob
import random
import json
import os

import cv2
import numpy as np
np.set_printoptions(threshold=np.inf)
from tqdm import tqdm
from tensorflow.keras.models import load_model

from ai_training.networks.segnet.train import find_latest_checkpoint
from ai_training.networks.segnet.data_utils.data_loader import get_image_array, get_segmentation_array, DATA_LOADER_SEED, class_colors, get_pairs_from_paths
from ai_training.networks.segnet.models.config import IMAGE_ORDERING
from . import metrics
import six

random.seed(DATA_LOADER_SEED)

def model_from_checkpoint_path(checkpoints_path):

    from .models.all_models import model_from_name
    assert (os.path.isfile(checkpoints_path+"_config.json")
            ), "Checkpoint not found."
    model_config = json.loads(
        open(checkpoints_path+"_config.json", "r").read())
    latest_weights = find_latest_checkpoint(checkpoints_path)
    assert (latest_weights is not None), "Checkpoint not found."
    model = model_from_name[model_config['model_class']](
        model_config['n_classes'], input_height=model_config['input_height'],
        input_width=model_config['input_width'])
    print("loaded weights ", latest_weights)
    model.load_weights(latest_weights)
    return model

def get_colored_segmentation_image(seg_arr, n_classes, colors=class_colors):
    output_height = seg_arr.shape[0]
    output_width = seg_arr.shape[1]
    seg_img = np.zeros((output_height, output_width, 3))
    for c in range(n_classes):
        seg_img[:, :, 0] += ((seg_arr[:, :] == c)*(colors[c][0])).astype('uint8')
        seg_img[:, :, 1] += ((seg_arr[:, :] == c)*(colors[c][1])).astype('uint8')
        seg_img[:, :, 2] += ((seg_arr[:, :] == c)*(colors[c][2])).astype('uint8')
    seg_img = seg_img.astype('uint8')
    return seg_img 

def get_legends(class_names,  colors=class_colors): 
    
    n_classes = len(class_names)
    legend = np.zeros(((len(class_names) * 25) + 25, 125, 3), dtype="uint8") + 255

    for (i, (class_name, color)) in enumerate(zip(class_names[:n_classes] , colors[:n_classes])):

        color = [int(c) for c in color]
        cv2.putText(legend, class_name, (5, (i * 25) + 17),
            cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 0), 1)
        cv2.rectangle(legend, (100, (i * 25)), (125, (i * 25) + 25),
            tuple(color), -1)
        
    return legend    

def overlay_seg_image(inp_img , seg_img):
    orininal_h = inp_img.shape[0]
    orininal_w = inp_img.shape[1]
    seg_img = cv2.resize(seg_img, (orininal_w, orininal_h))

    fused_img = (inp_img/2 + seg_img/2 ).astype('uint8')
    return fused_img 

def concat_lenends(  seg_img , legend_img  ):
    
    new_h = np.maximum( seg_img.shape[0] , legend_img.shape[0] )
    new_w = seg_img.shape[1] + legend_img.shape[1]

    out_img = np.zeros((new_h ,new_w , 3  )).astype('uint8') + legend_img[0 , 0 , 0 ]

    out_img[ :legend_img.shape[0] , :  legend_img.shape[1] ] = np.copy(legend_img)
    out_img[ :seg_img.shape[0] , legend_img.shape[1]: ] = np.copy(seg_img)

    return out_img

def visualize_segmentation(seg_arr, inp_img=None, n_classes=None, 
    colors=class_colors, class_names=None, overlay_img=False, show_legends=False, 
    prediction_width=None, prediction_height=None):
    
    print("Found the following classes in the segmentation image:", np.unique(seg_arr))

    if n_classes is None:
        n_classes = np.max(seg_arr)

    seg_img = get_colored_segmentation_image(seg_arr, n_classes , colors=colors)

    if not inp_img is None:
        orininal_h = inp_img.shape[0]
        orininal_w = inp_img.shape[1]
        seg_img = cv2.resize(seg_img, (orininal_w, orininal_h))

    if (not prediction_height is None) and (not prediction_width is None):
        seg_img = cv2.resize(seg_img, (prediction_width, prediction_height ))
        if not inp_img is None:
            inp_img = cv2.resize(inp_img, (prediction_width, prediction_height))
            
    if overlay_img:
        assert not inp_img is None
        seg_img = overlay_seg_image(inp_img, seg_img)

    if show_legends:
        assert not class_names is None
        legend_img = get_legends(class_names , colors=colors )

        seg_img = concat_lenends(seg_img, legend_img)

    return seg_img

def predict(model=None, inp=None, out_fname=None, image = None, overlay_img=False,
    class_names=None, show_legends=False, colors=class_colors, prediction_width=None, prediction_height=None):

    n_classes = model.n_classes

    pr = model.predict(inp)
    pr = np.squeeze(pr)

    #pr = pr.reshape((output_height,  output_width, n_classes)).argmax(axis=2)
    pr = pr.argmax(axis=2)

    seg_img = visualize_segmentation(pr, inp_img=image, n_classes=n_classes, overlay_img=True, colors=colors)

    if out_fname is not None:
        cv2.imwrite(out_fname, seg_img)

    return pr


def predict_multiple(model=None, inps=None, inp_dir=None, out_dir=None,
                     checkpoints_path=None ,overlay_img=False ,
    class_names=None , show_legends=False , colors=class_colors , prediction_width=None , prediction_height=None  ):

    if model is None and (checkpoints_path is not None):
        model = model_from_checkpoint_path(checkpoints_path)

    if inps is None and (inp_dir is not None):
        inps = glob.glob(os.path.join(inp_dir, "*.jpg")) + glob.glob(
            os.path.join(inp_dir, "*.png")) + \
            glob.glob(os.path.join(inp_dir, "*.jpeg"))

    assert type(inps) is list

    all_prs = []

    for i, inp in enumerate(tqdm(inps)):
        if out_dir is None:
            out_fname = None
        else:
            if isinstance(inp, six.string_types):
                out_fname = os.path.join(out_dir, os.path.basename(inp))
            else:
                out_fname = os.path.join(out_dir, str(i) + ".jpg")

        pr = predict(model, inp, out_fname ,
            overlay_img=overlay_img,class_names=class_names ,show_legends=show_legends , 
            colors=colors , prediction_width=prediction_width , prediction_height=prediction_height  )

        all_prs.append(pr)

    return all_prs

def evaluate(model=None, inp_images=None, annotations=None, inp_images_dir=None, annotations_dir=None, checkpoints_path=None):
    
    if model is None:
        assert (checkpoints_path is not None) , "Please provide the model or the checkpoints_path"
        model = model_from_checkpoint_path(checkpoints_path)
        
    if inp_images is None:
        assert (inp_images_dir is not None) , "Please provide inp_images or inp_images_dir"
        assert (annotations_dir is not None) , "Please provide inp_images or inp_images_dir"
        
        paths = get_pairs_from_paths(inp_images_dir, annotations_dir)
        paths = list(zip(*paths))
        inp_images = list(paths[0])
        annotations = list(paths[1])
        
    assert type(inp_images) is list
    assert type(annotations) is list
        
    tp = np.zeros(model.n_classes)
    fp = np.zeros(model.n_classes)
    fn = np.zeros(model.n_classes)
    n_pixels = np.zeros(model.n_classes)
    
    for inp, ann in tqdm(zip(inp_images , annotations)):
        pr = model.predict(inp)
        gt = get_segmentation_array(ann, model.n_classes, no_reshape=True)
        gt = gt.argmax(-1)
        #pr = pr.flatten()
        #gt = gt.flatten()
                
        for cl_i in range(model.n_classes):
            
            tp[ cl_i ] += np.sum( (pr == cl_i) * (gt == cl_i) )
            fp[ cl_i ] += np.sum( (pr == cl_i) * ((gt != cl_i)) )
            fn[ cl_i ] += np.sum( (pr != cl_i) * ((gt == cl_i)) )
            n_pixels[ cl_i ] += np.sum( gt == cl_i  )
            
    cl_wise_score = tp / ( tp + fp + fn + 0.000000000001 )
    n_pixels_norm = n_pixels /  np.sum(n_pixels)
    frequency_weighted_IU = np.sum(cl_wise_score*n_pixels_norm)
    mean_IU = np.mean(cl_wise_score)
    return {"frequency_weighted_IU":frequency_weighted_IU , "mean_IU":mean_IU , "class_wise_IU":cl_wise_score }
