# -*- coding: utf-8 -*-
"""
Created on Sun Aug 19 21:38:08 2018

@author: z3439910
"""

import numpy as np
import xarray as xr
import pandas as pd
import os
import cv2
import matplotlib.pyplot as plt
import time
import h5py

from scipy import ndimage
from matplotlib import colors
from skimage.morphology import watershed
from skimage import measure
from skimage.feature import peak_local_max
from skimage.morphology import reconstruction
from scipy.spatial.distance import cdist

WORKPLACE = r"C:\Users\z3439910\Documents\Kien\1_Projects\2_Msc\1_E1\5_GIS_project"
IRDIR = WORKPLACE + r"\IRimages2012"
BTDIR = WORKPLACE + r"\2_IBTrACSfiles"
os.chdir(IRDIR)
#%
CHOSEN_YEAR = "2012"
BASIN = "SI"
IMAG_RES = 4 #km
r = 500
DEG_TO_KM = 111 #ratio

if BASIN == "WP":
    LAT_BOUND = [-20,60] #WP Basin
    LON_BOUND = [60,180] #WP Basin
    B_tracks = xr.open_dataset(BTDIR+"\\"+"IBTrACS.WP.v04r00.nc")
elif BASIN == "EP": 
    LAT_BOUND = [-20,60] #WP Basin
    LON_BOUND = [-180,-60] #WP Basin
    B_tracks = xr.open_dataset(BTDIR+"\\"+"IBTrACS.EP.v04r00.nc")
elif BASIN == "NI": 
    LAT_BOUND = [-20,60] #WP Basin
    LON_BOUND = [0,120] #WP Basin
    B_tracks = xr.open_dataset(BTDIR+"\\"+"IBTrACS.NI.v04r00.nc")
elif BASIN == "SI": 
    LAT_BOUND = [-60,20] #WP Basin
    LON_BOUND = [0,150] #WP Basin
    B_tracks = xr.open_dataset(BTDIR+"\\"+"IBTrACS.SI.v04r00.nc")

B_TC_serials_decode = [x.decode("utf-8") for x in B_tracks['sid'].values]

TC_indices = [i for i,x in enumerate(B_TC_serials_decode) if x.startswith(CHOSEN_YEAR)==True]
TC_serials = [x for i,x in enumerate(B_TC_serials_decode) if x.startswith(CHOSEN_YEAR)==True]
#%
#% Functions
def calcdistance_km(latA,lonA,latB,lonB):
    dist = np.sqrt(np.square(latA-latB)+np.square(lonA-lonB))*111
    return np.int(dist)
#    return True\
    
#%
def time_to_string_with_min(iyear, imonth, iday, ihour, iminute):   
    str_iyear = str(iyear)
    if imonth < 10:
        str_imonth = "0" + str(imonth)
    else:
        str_imonth = str(imonth)
    
    if iday < 10:
        str_iday = "0" + str(iday)
    else:
        str_iday = str(iday)      
    
    if ihour < 10:
        str_ihour = "0" + str(ihour)
    else:
        str_ihour = str(ihour) 
        
    if iminute < 10:
        str_iminute = "0" + str(iminute)
    else:
        str_iminute = str(iminute)
    
    str_itime = str_iyear + str_imonth + str_iday + str_ihour + str_iminute
    return str_itime

#%
def time_to_string_without_min(iyear, imonth, iday, ihour):   
    str_iyear = str(iyear)
    if imonth < 10:
        str_imonth = "0" + str(imonth)
    else:
        str_imonth = str(imonth)
    
    if iday < 10:
        str_iday = "0" + str(iday)
    else:
        str_iday = str(iday)      
    
    if ihour < 10:
        str_ihour = "0" + str(ihour)
    else:
        str_ihour = str(ihour) 
    
    str_itime = str_iyear + str_imonth + str_iday + str_ihour
    return str_itime

def get_coord_to_idx(lat_y,lon_x):
    idx_x = np.int(np.round((lat_y - LAT_BOUND[0])*111/4))
    idx_y = np.int(np.round((lon_x - LON_BOUND[0])*111/4))
    return [idx_x,idx_y]

def get_idx_to_coord(idx_x,idx_y): 
    lat_y = idx_x*4/111 + LAT_BOUND[0]
    lon_x = idx_y*4/111 + LON_BOUND[0]
    return [lat_y,lon_x]

#%
def get_BTempimage_bound(latmin,latmax,lonmin,lonmax):
    BTempimage = xr.open_dataset(WORKPLACE+ "\IRimages2012\merg_2012080100_4km-pixel.nc4")
    BTemp_lat = BTempimage['lat'].values[:]
    BTemp_lon = BTempimage['lon'].values
    lat_bound = [i for i,val in enumerate(BTemp_lat) if (val>latmin and val<latmax)]   
    lat_val_bound = [val for i,val in enumerate(BTemp_lat) if (val>latmin and val<latmax)] 
    lon_bound = [i for i,val in enumerate(BTemp_lon) if (val>lonmin and val<lonmax)]   
    lon_val_bound = [val for i,val in enumerate(BTemp_lon) if (val>lonmin and val<lonmax)] 
    return[lat_bound[0],lat_bound[-1],lon_bound[0],lon_bound[-1]]
#% Get idices in accordance with brightness temperature images

DIM_BOUND = get_BTempimage_bound(LAT_BOUND[0],LAT_BOUND[1],LON_BOUND[0],LON_BOUND[1])#incices from BT images

##%%
#latmin =LAT_BOUND[0]
#latmax = LAT_BOUND[1]
#lonmin = LON_BOUND[0]
#lonmax =LON_BOUND[1]
#BTempimage = xr.open_dataset(WORKPLACE+ "\IRimages2012\merg_2012080100_4km-pixel.nc4")
#BTemp_lat = BTempimage['lat'].values[:]
#BTemp_lon = BTempimage['lon'].values
#lat_bound = [i for i,val in enumerate(BTemp_lat) if (val>latmin and val<latmax)]   
#lat_val_bound = [val for i,val in enumerate(BTemp_lat) if (val>latmin and val<latmax)] 
#lon_bound = [i for i,val in enumerate(BTemp_lon) if (val>lonmin and val<lonmax)]   
#lon_val_bound = [val for i,val in enumerate(BTemp_lon) if (val>lonmin and val<lonmax)] 

#%%
i = 18

TC_serial = TC_serials[i]
TC_index = TC_indices[i]
#%
B_TC_names = [x.decode("utf-8") for x in B_tracks['name'].values]
I_name = B_TC_names[TC_index]
I_name = I_name.replace(r":",r"_")
#%
#I_name = "UNNAMED"
I_TC_time = B_tracks['time'][TC_index,:]
I_TC_time =  I_TC_time.dropna('date_time').values


#%

I_lat = B_tracks['lat'].values[TC_index,:]
I_lat = pd.DataFrame(I_lat).dropna().values[:,0]
I_lon = B_tracks['lon'].values[TC_index,:]
I_lon = pd.DataFrame(I_lon).dropna().values[:,0]


#%
# interpolate best track lat long to 0.5-hour intervals
df = pd.DataFrame({'time':I_TC_time,'lat':I_lat,'lon':I_lon})
df = df.set_index('time')
df_reindexed = df.reindex(pd.date_range(start=I_TC_time[0],end=I_TC_time[len(I_TC_time)-1],freq='0.5H'))
I_time_interpolate = df_reindexed.interpolate(method='time')
I_time_interpolate.index.name = 'time'
I_time_interpolate.reset_index(inplace = True)
I_year = pd.to_datetime(I_time_interpolate['time'].values).year
I_month = pd.to_datetime(I_time_interpolate['time'].values).month
I_day = pd.to_datetime(I_time_interpolate['time'].values).day
I_hour = pd.to_datetime(I_time_interpolate['time'].values).hour
I_minute = pd.to_datetime(I_time_interpolate['time'].values).minute
I_lat = I_time_interpolate['lat']
I_lon = I_time_interpolate['lon']

#%
SAVDIR = r"K:\THEJUDGEMENT\BASINS_RESULTS_2012" + "\\"+ BASIN + "\\" + TC_serial + "_" + I_name
os.mkdir(SAVDIR)

#% Create an HDF5 file to store label for the current storm
DIM_LAT = DIM_BOUND[1]-DIM_BOUND[0] + 1
DIM_LON = DIM_BOUND[3]-DIM_BOUND[2] + 1
DIM_TIME = np.shape(I_time_interpolate['time'])[0]
#%
HFILE_DIR = SAVDIR + r"\\" + TC_serial + r"_" + I_name + r'_labels.h5'
Hfile_label = h5py.File(HFILE_DIR,'w')
Hfile_label.close()

Hfile_label = h5py.File(HFILE_DIR,'r+')
Hfile_label.create_dataset('label_TC', shape = (DIM_TIME,DIM_LAT,DIM_LON),chunks=True,dtype='uint8')


Hfile_label.close()

#% Start spreading 
# open the label HDF5 file
Hfile_label = h5py.File(HFILE_DIR,'r+')  
C_label_TC = Hfile_label['label_TC']

# define some variables
TB_THRES = 280
start_time_overall = time.time()
# define search boundry
S_BOUND_KM = 300 #km
S_BOUND_DEG = S_BOUND_KM/111 #convert km to deg
S_NO_PX = np.round(S_BOUND_KM/IMAG_RES)

S_BOUND_TOT_KM = 1110 #km
S_BOUND_TOT_DEG = S_BOUND_TOT_KM/111 #convert km to deg
S_NO_TOT_PX = np.round(S_BOUND_TOT_KM/IMAG_RES)


#%% FIRST FRAME
C_i_start = 0
for C_i in range(C_i_start,C_i_start+1):
    
    #% Acquire BT images
    C_label_TC[C_i,:,:] = np.zeros([DIM_LAT,DIM_LON])
    BTemp_filename = r"merg_"+ time_to_string_without_min(I_year[C_i],I_month[C_i],I_day[C_i],I_hour[C_i]) + r"_4km-pixel.nc4"
    
    if I_minute[C_i] == 0:
        #slice out BT images for the current basin
        C_BTemp = xr.open_dataset(IRDIR+ "\\" + BTemp_filename)['Tb'].values[0][DIM_BOUND[0]:DIM_BOUND[1]+1,DIM_BOUND[2]:DIM_BOUND[3]+1]
        C_lat = xr.open_dataset(IRDIR+ "\\" + BTemp_filename)['lat'].values[DIM_BOUND[0]:DIM_BOUND[1]+1]
        C_lon = xr.open_dataset(IRDIR+ "\\" + BTemp_filename)['lon'].values[DIM_BOUND[2]:DIM_BOUND[3]+1]
        #interpolate NaN values in BT images
        mask = np.isnan(C_BTemp)
        C_BTemp[mask] = np.interp(np.flatnonzero(mask), np.flatnonzero(~mask), C_BTemp[~mask])
      
    elif I_minute[C_i] == 30:
        #slice out BT images for the current basin
        C_BTemp = xr.open_dataset(IRDIR+ "\\" + BTemp_filename)['Tb'].values[1][DIM_BOUND[0]:DIM_BOUND[1]+1,DIM_BOUND[2]:DIM_BOUND[3]+1]
        C_lat = xr.open_dataset(IRDIR+ "\\" + BTemp_filename)['lat'].values[DIM_BOUND[0]:DIM_BOUND[1]+1]
        C_lon = xr.open_dataset(IRDIR+ "\\" + BTemp_filename)['lon'].values[DIM_BOUND[2]:DIM_BOUND[3]+1]
        #interpolate NaN values in BT images
        mask = np.isnan(C_BTemp)
        C_BTemp[mask] = np.interp(np.flatnonzero(mask), np.flatnonzero(~mask), C_BTemp[~mask])

    #% Initilize core for spreading
    C_flag = C_label_TC[C_i,:,:][:]
    C_flag = np.zeros([DIM_LAT,DIM_LON])
    # first image
#    if C_i == 0:    
        
    box_i_w = [i_w for i_w,x_w in enumerate(C_lon) if abs(I_lon[C_i]-x_w) < S_BOUND_DEG]
    box_i_h = [i_h for i_h,x_h in enumerate(C_lat) if abs(I_lat[C_i]-x_h) < S_BOUND_DEG]
    
    #
    for i_w in box_i_w:
        for i_h in box_i_h:
            t_lat = C_lat[i_h]
            t_lon = C_lon[i_w]
            t_btemp = C_BTemp[i_h,i_w]
            if (calcdistance_km(I_lat[C_i], I_lon[C_i], t_lat, t_lon) <S_BOUND_KM) and (np.int(t_btemp)) < 230:
                C_flag[i_h,i_w] = 1
                print ('found at ' + str(i_w) + ' and ' + str(i_h))
    C_Core = C_flag[:]     
#    
##%
    fig = plt.figure()
    lat_max = np.round(np.max(C_lat),1)
    lat_min = np.round(np.min(C_lat),1)
    lon_max = np.round(np.max(C_lon),1)
    lon_min = np.round(np.min(C_lon),1)
    im = plt.imshow(C_BTemp, extent = (lon_min, lon_max, lat_min, lat_max), cmap='Greys',origin='lower')
    plt.plot(I_lon[C_i],I_lat[C_i],'or', markersize = 2) 
    plt.show()
    #%% Start spreading
    BOUNDADRY_R = 500 #Default: 500
    NO_MAXIMA = 16 #Default: 16
    C_BTEMP_MAX = 270 #Default: 270
    
    I_idx = get_coord_to_idx(I_lat[C_i],I_lon[C_i])
    C_binary = np.where(C_BTemp>C_BTEMP_MAX,0,C_BTemp)
    C_binary = np.where(C_binary>1,1,C_binary)
    C_binary_cut = np.zeros([DIM_LAT,DIM_LON])
    r = BOUNDADRY_R #the bounding box side = 2r
    C_binary_cut[I_idx[0]-r:I_idx[0]+r,I_idx[1]-r:I_idx[1]+r] = C_binary[I_idx[0]-r:I_idx[0]+r,I_idx[1]-r:I_idx[1]+r] 
    C_binary8 = C_binary_cut.astype(np.uint8)
    
    kernel = np.ones((3,3),np.uint8)
    opening = cv2.morphologyEx(C_binary8,cv2.MORPH_OPEN,kernel, iterations = 2)
    dist_transform = cv2.distanceTransform(opening,cv2.DIST_L2,0)
    ret, sure_fg = cv2.threshold(dist_transform,0.04*dist_transform.max(),255,0)

    labels_ws = watershed(-dist_transform, C_Core, mask=C_binary8)
    C_binary8_second = np.where(labels_ws>0, C_binary8, 0)
    C_flag = np.where(labels_ws == 0, 0,labels_ws)
    #%
    #% Second round - divide the previous mask into 2 blobs
    ##################################################################
    seed = np.copy(C_binary8_second)
    seed[1:-1, 1:-1] = C_binary8_second.max()
    mask = C_binary8_second
    
    # fill all holes the do distance transform
    C_binary8_filled = reconstruction(seed, mask, method='erosion')
    C_binary8_filled8 = C_binary8_filled.astype(np.uint8)
    dist_transform_second = cv2.distanceTransform(C_binary8_filled8,cv2.DIST_L2,0)  
   
    # Maximum them find maxima
    maximum_fil_result = ndimage.maximum_filter(dist_transform_second, size=1)
    
    min_distance_val = 1
    flag = 0
#    maximum_fil_result = maximum_fil_result[I_idx[0]-200:I_idx[0]+200,I_idx[1]-200:I_idx[1]+200]
    while flag == 0: 
        maximum_coordinates = peak_local_max(maximum_fil_result,min_distance = min_distance_val, indices = True)
        min_distance_val +=1
        if np.int(np.shape(maximum_coordinates)[0]) < NO_MAXIMA:
            flag = 1
            
    markers_two = np.zeros([DIM_LAT,DIM_LON])
    for i in range(0,np.shape(maximum_coordinates)[0]-1):
        markers_two[maximum_coordinates[i,0],maximum_coordinates[i,1]] = dist_transform_second[maximum_coordinates[i,0],maximum_coordinates[i,1]]
    
    labels_ws_second = watershed(-dist_transform_second, markers_two, mask=C_binary8_second,watershed_line=False)
    blobs_labels = measure.label(labels_ws_second,neighbors=4, background=0)
    
    #%%
    box_from_BTcenter = dist_transform_second[I_idx[0]-100:I_idx[0]+100,I_idx[1]-100:I_idx[1]+100]
    max_idx_from_box = np.unravel_index(np.argmax(box_from_BTcenter, axis=None), box_from_BTcenter.shape) #idx within box
    max_idx  = [I_idx[0]-100 + max_idx_from_box[0],I_idx[1] - 100 + max_idx_from_box[1]] #idx in the image
    max_blob_value = blobs_labels[max_idx[0],max_idx[1]]
    
    C_flag = np.where(blobs_labels == max_blob_value,2,0)
#    C_flag = np.where(blobs_labels == 7,2,C_flag)
#    C_flag = np.where(blobs_labels == 1,2,C_flag)
#    C_flag = np.where(blobs_labels == 3,2,C_flag)
#    C_flag = np.where(blobs_labels == 5,2,C_flag)
    
     #%
    C_label_TC[C_i,:,:] = C_flag.astype(np.uint8)    
    #%
    # % PLOT RESULTS
    # Prepare masks with NaN values
    C_mask_TC = np.where(C_flag == 0, np.NaN , C_flag)
    C_mask_Core = np.where(C_Core == 0, np.NaN , C_Core)
    
    #%% Plot
    fig = plt.figure()
    lat_max = np.round(np.max(C_lat),1)
    lat_min = np.round(np.min(C_lat),1)
    lon_max = np.round(np.max(C_lon),1)
    lon_min = np.round(np.min(C_lon),1)
    filename = TC_serial+ "_" + I_name + "_" + time_to_string_with_min(I_year[C_i], I_month[C_i], I_day[C_i], I_hour[C_i], I_minute[C_i])
    #%
    
    plt.subplot(221)
    #% Plot BT image with 3 labels
#    im = plt.imshow(dist_transform_second, extent = (lon_min, lon_max, lat_min, lat_max),  cmap='Greys_r',origin='lower')
    im = plt.imshow(labels_ws_second, extent = (lon_min, lon_max, lat_min, lat_max),  cmap=plt.cm.nipy_spectral,origin='lower')
    # Best track center
    plt.plot(I_lon[C_i],I_lat[C_i],'or', markersize = 2) 
    
    plt.subplot(222)
    #% Plot BT image with 3 labels
#    im = plt.imshow(dist_transform, extent = (lon_min, lon_max, lat_min, lat_max),  cmap='Greys_r',origin='lower')
    im = plt.imshow(blobs_labels, extent = (lon_min, lon_max, lat_min, lat_max),  cmap=plt.cm.nipy_spectral,interpolation='nearest',origin='lower')

    plt.subplot(223)
    im = plt.imshow(maximum_fil_result,cmap='Greys_r',origin='lower')
    plt.plot(maximum_coordinates[:, 1], maximum_coordinates[:, 0], 'r.')
    plt.subplot(224)

    im = plt.imshow(C_BTemp, extent = (lon_min, lon_max, lat_min, lat_max),  cmap='Greys',origin='lower')
    im2 = plt.imshow(C_mask_TC, extent = (lon_min, lon_max, lat_min, lat_max), cmap=colors.ListedColormap(['yellow']),origin='lower',alpha=0.3)
    im2 = plt.imshow(C_mask_Core, extent = (lon_min, lon_max, lat_min, lat_max), cmap=colors.ListedColormap(['green']),origin='lower',alpha=0.3)
    # Best track center
    plt.plot(I_lon[C_i],I_lat[C_i],'or', markersize = 2) 
    plt.show()    
#%
#        C_flag_prev = C_label_TC[C_i,:,:][:] 
#        fig = plt.figure()
#        im = plt.imshow(C_flag_prev,  cmap='Greys',origin='lower')
#        plt.show()
#%% CLOSE HDF5 FILES
Hfile_label.close()
