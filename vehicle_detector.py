
import matplotlib.image as mpimg
import numpy as np
import cv2
from skimage.feature import hog
from scipy.ndimage.measurements import label
import time

## constants
QUEUE_SIZE = 5

def convert_color(img, conv='RGB2YCrCb'):
    if conv == 'RGB2YCrCb':
        return cv2.cvtColor(img, cv2.COLOR_RGB2YCrCb)
    if conv == 'BGR2YCrCb':
        return cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    if conv == 'RGB2LUV':
        return cv2.cvtColor(img, cv2.COLOR_RGB2LUV)

# Define a function to return HOG features and visualization
def get_hog_features(img, orient, pix_per_cell, cell_per_block, 
                        vis=False, feature_vec=True):
    # Call with two outputs if vis==True
    if vis == True:
        features, hog_image = hog(img, orientations=orient, 
                                  pixels_per_cell=(pix_per_cell, pix_per_cell),
                                  cells_per_block=(cell_per_block, cell_per_block), 
                                  transform_sqrt=True, 
                                  visualise=vis, feature_vector=feature_vec)
        return features, hog_image
    # Otherwise call with one output
    else:      
        features = hog(img, orientations=orient, 
                       pixels_per_cell=(pix_per_cell, pix_per_cell),
                       cells_per_block=(cell_per_block, cell_per_block), 
                       transform_sqrt=True, 
                       visualise=vis, feature_vector=feature_vec)
        return features

"""
# Define a function to compute binned color features  
def bin_spatial(img, size=(32, 32)):
    # Use cv2.resize().ravel() to create the feature vector
    features = cv2.resize(img, size).ravel() 
    # Return the feature vector
    return features
"""

### - from Hog Sub Sampling Window - 
def bin_spatial(img, size=(32, 32)):
    color1 = cv2.resize(img[:,:,0], size).ravel()
    color2 = cv2.resize(img[:,:,1], size).ravel()
    color3 = cv2.resize(img[:,:,2], size).ravel()
    return np.hstack((color1, color2, color3))

"""
# Define a function to compute color histogram features 
# NEED TO CHANGE bins_range if reading .png files with mpimg!
def color_hist(img, nbins=32, bins_range=(0, 256)):
    # Compute the histogram of the color channels separately
    channel1_hist = np.histogram(img[:,:,0], bins=nbins, range=bins_range)
    channel2_hist = np.histogram(img[:,:,1], bins=nbins, range=bins_range)
    channel3_hist = np.histogram(img[:,:,2], bins=nbins, range=bins_range)
    # Concatenate the histograms into a single feature vector
    hist_features = np.concatenate((channel1_hist[0], channel2_hist[0], channel3_hist[0]))
    # Return the individual histograms, bin_centers and feature vector
    return hist_features
"""

## Compute color histogram features
def color_hist(img, nbins=32):    #bins_range=(0, 256)
    # Compute the histogram of the color channels separately
    channel1_hist = np.histogram(img[:,:,0], bins=nbins)
    channel2_hist = np.histogram(img[:,:,1], bins=nbins)
    channel3_hist = np.histogram(img[:,:,2], bins=nbins)
    # Concatenate the histograms into a single feature vector
    hist_features = np.concatenate((channel1_hist[0], channel2_hist[0], channel3_hist[0]))
    # Return the individual histograms, bin_centers and feature vector
    return hist_features


# Extract features from a list of images
# Have this function call bin_spatial() and color_hist()
def extract_features(imgs, color_space='RGB', spatial_size=(32, 32),
                        hist_bins=32, orient=9, 
                        pix_per_cell=8, cell_per_block=2, hog_channel=0,
                        spatial_feat=True, hist_feat=True, hog_feat=True):
    # Create a list to append feature vectors to
    features = []
    # Iterate through the list of images
    for file in imgs:
        file_features = []
        # Read in each one by one
        image = mpimg.imread(file)
        # apply color conversion if other than 'RGB'
        if color_space != 'RGB':
            if color_space == 'HSV':
                feature_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            elif color_space == 'LUV':
                feature_image = cv2.cvtColor(image, cv2.COLOR_RGB2LUV)
            elif color_space == 'HLS':
                feature_image = cv2.cvtColor(image, cv2.COLOR_RGB2HLS)
            elif color_space == 'YUV':
                feature_image = cv2.cvtColor(image, cv2.COLOR_RGB2YUV)
            elif color_space == 'YCrCb':
                feature_image = cv2.cvtColor(image, cv2.COLOR_RGB2YCrCb)
        else: feature_image = np.copy(image)      

        if spatial_feat == True:
            spatial_features = bin_spatial(feature_image, size=spatial_size)
            file_features.append(spatial_features)
        if hist_feat == True:
            # Apply color_hist()
            hist_features = color_hist(feature_image, nbins=hist_bins)
            file_features.append(hist_features)
        if hog_feat == True:
        # Call get_hog_features() with vis=False, feature_vec=True
            if hog_channel == 'ALL':
                hog_features = []
                for channel in range(feature_image.shape[2]):
                    hog_features.append(get_hog_features(feature_image[:,:,channel], 
                                        orient, pix_per_cell, cell_per_block, 
                                        vis=False, feature_vec=True))
                hog_features = np.ravel(hog_features)        
            else:
                hog_features = get_hog_features(feature_image[:,:,hog_channel], orient, 
                            pix_per_cell, cell_per_block, vis=False, feature_vec=True)
            # Append the new feature vector to the features list
            file_features.append(hog_features)
        features.append(np.concatenate(file_features))
    # Return list of feature vectors
    return features
    
# Define a function that takes an image,
# start and stop positions in both x and y, 
# window size (x and y dimensions),  
# and overlap fraction (for both x and y)
def slide_window(img, x_start_stop=[None, None], y_start_stop=[None, None], 
                    xy_window=(64, 64), xy_overlap=(0.5, 0.5)):
    ''' Given an image img, this method returns coordinates of all possible sliding windows
    '''
    # If x and/or y start/stop positions not defined, set to image size
    if x_start_stop[0] is None:
        x_start_stop[0] = 0
    if x_start_stop[1] is None:
        x_start_stop[1] = img.shape[1]
    if y_start_stop[0] is None:
        y_start_stop[0] = 0
    if y_start_stop[1] is None:
        y_start_stop[1] = img.shape[0]
    # Compute the span of the region to be searched    
    xspan = x_start_stop[1] - x_start_stop[0]
    yspan = y_start_stop[1] - y_start_stop[0]
    # Compute the number of pixels per step in x/y
    nx_pix_per_step = np.int(xy_window[0]*(1 - xy_overlap[0]))
    ny_pix_per_step = np.int(xy_window[1]*(1 - xy_overlap[1]))
    # Compute the number of windows in x/y
    nx_buffer   = np.int(xy_window[0]*(xy_overlap[0]))
    ny_buffer   = np.int(xy_window[1]*(xy_overlap[1]))
    nx_windows  = np.int((xspan-nx_buffer)/nx_pix_per_step) 
    ny_windows  = np.int((yspan-ny_buffer)/ny_pix_per_step) 
    # Initialize a list to append window positions to
    window_list = []
    # Loop through finding x and y window positions
    # Note: you could vectorize this step, but in practice
    # you'll be considering windows one by one with your
    # classifier, so looping makes sense
    for ys in range(ny_windows):
        for xs in range(nx_windows):
            # Calculate window position
            startx  = xs*nx_pix_per_step + x_start_stop[0]
            endx    = startx + xy_window[0]
            starty  = ys*ny_pix_per_step + y_start_stop[0]
            endy    = starty + xy_window[1]
            
            # Append window position to list
            window_list.append(((startx, starty), (endx, endy)))
    # Return the list of windows
    return window_list


# Define a function to extract features from a single image window
# This function is very similar to extract_features()
# just for a single image rather than list of images
def single_img_features(img, color_space='RGB', spatial_size=(32, 32),
                        hist_bins=32, orient=9, 
                        pix_per_cell=8, cell_per_block=2, hog_channel=0,
                        spatial_feat=True, hist_feat=True, hog_feat=True):    
    #1) Define an empty list to receive features
    img_features = []
    #2) Apply color conversion if other than 'RGB'
    if color_space != 'RGB':
        if color_space == 'HSV':
            feature_image = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        elif color_space == 'LUV':
            feature_image = cv2.cvtColor(img, cv2.COLOR_RGB2LUV)
        elif color_space == 'HLS':
            feature_image = cv2.cvtColor(img, cv2.COLOR_RGB2HLS)
        elif color_space == 'YUV':
            feature_image = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
        elif color_space == 'YCrCb':
            feature_image = cv2.cvtColor(img, cv2.COLOR_RGB2YCrCb)
    else: feature_image = np.copy(img)      
    #3) Compute spatial features if flag is set
    if spatial_feat == True:
        spatial_features = bin_spatial(feature_image, size=spatial_size)
        #4) Append features to list
        img_features.append(spatial_features)
    #5) Compute histogram features if flag is set
    if hist_feat == True:
        hist_features = color_hist(feature_image, nbins=hist_bins)
        #6) Append features to list
        img_features.append(hist_features)
    #7) Compute HOG features if flag is set
    if hog_feat == True:
        if hog_channel == 'ALL':
            hog_features = []
            for channel in range(feature_image.shape[2]):
                hog_features.extend(get_hog_features(feature_image[:,:,channel], 
                                    orient, pix_per_cell, cell_per_block, 
                                    vis=False, feature_vec=True))      
        else:
            hog_features = get_hog_features(feature_image[:,:,hog_channel], orient, 
                        pix_per_cell, cell_per_block, vis=False, feature_vec=True)
        #8) Append features to list
        img_features.append(hog_features)

    #9) Return concatenated array of features
    return np.concatenate(img_features)

# Define a function you will pass an image 
# and the list of windows to be searched (output of slide_windows())
def search_windows(img, windows, clf, scaler, color_space='RGB', 
                    spatial_size=(32, 32), hist_bins=32, 
                    hist_range=(0, 256), orient=9, 
                    pix_per_cell=8, cell_per_block=2, 
                    hog_channel=0, spatial_feat=True, 
                    hist_feat=True, hog_feat=True):
    ''' Given an image img, and list of windows to search for, this function 
        returns a list of hot_windows where there might be a vehicle

        :param img - the image within which to search
        :param windows - list of windows to search for (output of slide_windows())
        :param clf - the trained classifier that predicts if a vehicle exists in the image
        :param scaler - the scaler transformer

        :return hot_windows - a list of windows (bounding boxes) that possibly contain a vehicle
    '''

    #1) Create an empty list to receive positive detection windows
    on_windows = []
    #2) Iterate over all windows in the list
    for window in windows:
        #3) Extract the test window from original image
        test_img = cv2.resize(img[window[0][1]:window[1][1], window[0][0]:window[1][0]], (64, 64))      
        #4) Extract features for that window using single_img_features()
        features = single_img_features(test_img, color_space=color_space, 
                            spatial_size=spatial_size, hist_bins=hist_bins, 
                            orient=orient, pix_per_cell=pix_per_cell, 
                            cell_per_block=cell_per_block, 
                            hog_channel=hog_channel, spatial_feat=spatial_feat, 
                            hist_feat=hist_feat, hog_feat=hog_feat)
        #5) Scale extracted features to be fed to classifier
        test_features = scaler.transform(np.array(features).reshape(1, -1))
        #6) Predict using your classifier
        prediction = clf.predict(test_features)
        #7) If positive (prediction == 1) then save the window
        if prediction == 1:
            on_windows.append(window)
    #8) Return windows for positive detections
    return on_windows


# Define a function to draw bounding boxes
def draw_boxes(img, bboxes, color=(0, 0, 255), thick=6):
    # Make a copy of the image
    imcopy = np.copy(img)
    # Iterate through the bounding boxes
    for bbox in bboxes:
        # Draw a rectangle given bbox coordinates
        cv2.rectangle(imcopy, bbox[0], bbox[1], color, thick)
    # Return the image copy with boxes drawn
    return imcopy


# Heatmap -- add heat in given bounding boxes
def add_heat(heatmap, bbox_list):
    # Iterate through list of bboxes
    for box in bbox_list:
        # Add += 1 for all pixels inside each bbox
        # Assuming each "box" takes the form ((x1, y1), (x2, y2))
        heatmap[box[0][1]:box[1][1], box[0][0]:box[1][0]] += 1

    # Return updated heatmap
    return heatmap

# Apply threshold to given heatmap: filter out bits that do not cross the threshold 
def apply_threshold(heatmap, threshold):
    # Zero out pixels below the threshold
    heatmap[heatmap <= threshold] = 0
    # Return thresholded map
    return heatmap

def draw_labeled_bboxes(img, labels):
    # Iterate through all detected cars
    for car_number in range(1, labels[1]+1):
        # Find pixels with each car_number label value
        nonzero = (labels[0] == car_number).nonzero()
        # Identify x and y values of those pixels
        nonzeroy = np.array(nonzero[0])
        nonzerox = np.array(nonzero[1])
        # Define a bounding box based on min/max x and y
        bbox = ((np.min(nonzerox), np.min(nonzeroy)), (np.max(nonzerox), np.max(nonzeroy)))
        # Draw the box on the image
        cv2.rectangle(img, bbox[0], bbox[1], (0,0,255), 6)
    # Return the image
    return img


'''
color_space     = 'YCrCb' # Can be RGB, HSV, LUV, HLS, YUV, YCrCb
orient          = 9  # HOG orientations
pix_per_cell    = 8 # HOG pixels per cell
cell_per_block  = 2 # HOG cells per block
hog_channel     = 'ALL' # Can be 0, 1, 2, or "ALL"
spatial_size    = (16, 16) # Spatial binning dimensions
hist_bins       = 32    # Number of histogram bins
spatial_feat    = True # Spatial features on or off
hist_feat       = True # Histogram features on or off
hog_feat        = True # HOG features on or off
y_start_stop = [400, 680] # Min and max in y to search in slide_window()

'''

class VehicleDetector:
    '''  Class that detects vehicles in a frame
    '''
    def __init__(self, 
                color_space, 
                orient, 
                pix_per_cell, 
                cell_per_block,
                hog_channel,
                spatial_size,
                hist_bins,
                spatial_feat,
                hist_feat,
                hog_feat,
                x_start_stop,
                y_start_stop,
                xy_window,
                xy_overlap,
                heat_threshold,
                clf,        # trained classifier
                scaler     # scaler for transforming inputs
        ):
        self.color_space     = color_space   # Can be RGB, HSV, LUV, HLS, YUV, YCrCb
        self.orient          = orient       # HOG orientations
        self.pix_per_cell    = pix_per_cell8 # HOG pixels per cell
        self.cell_per_block  = cell_per_block2 # HOG cells per block
        self.hog_channel     = hog_channel   # 0, 1, 2, 'ALL'
        self.spatial_size    = spatial_size # Spatial binning dimensions
        self.hist_bins       = hist_bins    # Number of histogram bins
        self.spatial_feat    = spatial_feat # Spatial features on or off
        self.hist_feat       = hist_feat # Histogram features on or off
        self.hog_feat        = hog_feat  # HOG features on or off
        self.y_start_stop    = y_start_stop # Min and max in y to search in slide_window()
        self.x_start_stop    = x_start_stop
        self.xy_window       = xy_window
        self.xy_overlap      = xy_overlap
        self.heat_threshold  = heat_threshold
        self.clf             = clf 
        self.scaler          = scaler

        self.process_time   = []   # saves seconds required to process each frame

    
    
    def process_frame(self, frame):
        '''  Process each frame to detect a vehicle in it, and return a bounded box on it 
        '''
        img_copy = np.copy(frame)
        img_copy = img_copy.astype(np.float32) / 255.

        t0 = time.time()   # for processing

        # 1 - find sliding windows in frame
        sliding_windows = slide_window(img_copy, 
                                    x_start_stop=self.x_start_stop,
                                    y_start_stop=self.y_start_stop, 
                                    xy_window=self.xy_window,
                                    xy_overlap=self.xy_overlap
                            )
        # 2 - search for hot windows within these sliding_windows
        hot_windows = search_windows(img_copy, 
                                    sliding_windows,
                                    clf=self.clf,
                                    scaler=self.scaler,
                                    color_space=self.color_space,
                                    spatial_size=self.spatial_size,
                                    hist_bins=self.hist_bins,
                                    orient=self.orient,
                                    pix_per_cell=self.pix_per_cell,
                                    cell_per_block=self.cell_per_block,
                                    hog_channel=self.hog_channel,
                                    spatial_feat=self.spatial_feat,
                                    hist_feat=self.hist_feat,
                                    hog_feat=self.hog_feat
                        )
        # 3a - heat map init
        heatmap = np.zeros_like(img_copy[:,:,0]).astype(np.float)
        # 3b - add heat
        heatmap = add_heat(heatmap, hot_windows)
        # 3c - TODO Buffer frame

        # 3d - apply heatmap threshold to excl false positives
        heatmap = apply_threshold(heatmap, self.heat_threshold)

        # 4 - get labels
        labels = label(heatmap)

        # 5 - draw bboxes
        processed_img = draw_labeled_bboxes(frame, labels)

        # for debug - time reqd to process
        t2 = time.time()
        process_time = t2-t0
        self.process_time.append(process_time)

        return processed_img

    def process_info(self):
        ''' Show total processing info
        '''
        frames = len(self.process_time)
        avg_time    = np.mean(self.process_time) # secs
        total_time  = np.sum(self.process_time)  # secs

        msg = '[Total {0} frames, time: {1} s, avg:{2} sec/frame]'.format(
                frames, round(total_time, 2), round(avg_time, 2)
        )
        print(msg)
