# -*- coding: utf-8 -*-
"""LSTM (1).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1XgygDaF2ErBnQ_7ETYSx4Z5ffG0JJu41
"""

## IMPORTS 
import numpy as np 
import pandas as pd
import scipy
from scipy import signal
from scipy.io import loadmat
from sklearn import preprocessing 
from sklearn.preprocessing import MinMaxScaler
from sklearn.utils import shuffle 
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
from keras.utils import to_categorical
import matplotlib.pyplot as plt

# Load in full data set from MATLAB
data = loadmat('cis519project_data.mat')

# Store data into arrays 
full_dg_p1 = data['full_dg_p1']; full_dg_p2 = data['full_dg_p2']; full_dg_p3 = data['full_dg_p3']
full_ecog_p1 = data['full_ecog_p1']; full_ecog_p2 = data['full_ecog_p2']; full_ecog_p3 = data['full_ecog_p3']

"""Prepare Labels """

# make individual finger flexion arrays 
dg_finger1 = []; dg_finger2 = []; dg_finger3 = []; dg_finger4 = []; dg_finger5 = [] 
for array in full_dg_p1: 
    dg_finger1.append(array[0])
    dg_finger2.append(array[1])
    dg_finger3.append(array[2])
    dg_finger4.append(array[3])
    dg_finger5.append(array[4])

# make arrays of 500 samples (500 ms) long with 250 sample (250 ms) sliding window 
# time windows should be: (xLen/fs - winLen + winDisp)/winDisp --> (300000/1000 - 0.5 + 0.25)/0.25 = 1199 
pop1 = dg_finger1; pop2 = dg_finger2; pop3 = dg_finger3; pop4 = dg_finger4; pop5 = dg_finger5
windows1 = []; windows2 = []; windows3 = []; windows4 = []; windows5 = []
while len(pop1) >= 500: 
    temp1 = pop1[0:500]; temp2 = pop2[0:500]; temp3 = pop3[0:500]
    temp4 = pop4[0:500]; temp5 = pop5[0:500]
    windows1.append(temp1); windows2.append(temp2); windows3.append(temp3) 
    windows4.append(temp4); windows5.append(temp5)
    for pop_amount in range(250):
        pop1.pop(0); pop2.pop(0); pop3.pop(0); pop4.pop(0); pop5.pop(0)

# make arrays to track how much each finger changes in each time window 
change1 = []; change2 = []; change3 =[]; change4 = []; change5 =[]

for window in windows1:
    temp_change = 0 
    for i in range(len(window)-1):
        temp_change+= abs(window[i+1] - window[i])
    change1.append(temp_change)

for window in windows2:
    temp_change = 0 
    for i in range(len(window)-1):
        temp_change+= abs(window[i+1] - window[i])
    change2.append(temp_change)

for window in windows3:
    temp_change = 0 
    for i in range(len(window)-1):
        temp_change+= abs(window[i+1] - window[i])
    change3.append(temp_change)

for window in windows4:
    temp_change = 0 
    for i in range(len(window)-1):
        temp_change+= abs(window[i+1] - window[i])
    change4.append(temp_change)
    
for window in windows5:
    temp_change = 0 
    for i in range(len(window)-1):
        temp_change+= abs(window[i+1] - window[i])
    change5.append(temp_change)

# find where there are changes over a time frame for at least one of the fingers 
nonzero_indicies = []
for index in range(len(change1)): 
    if (change1[index] + change2[index] + change3[index] + change4[index] + change5[index]) != 0:
        nonzero_indicies.append(index)

# every time interval has some change in at least one finger --> no need to reduce

# make labels by finding highest change in each interval

list_of_changes = []
for i in range(len(change1)):
    temp = []
    temp.append(change1[i])
    temp.append(change2[i])
    temp.append(change3[i])
    temp.append(change4[i])
    temp.append(change5[i])
    list_of_changes.append(temp)

labels_list = []
for five_set in list_of_changes: 
    labels_list.append(five_set.index(max(five_set)))

# one hot encode these labels 
labels_df = pd.DataFrame(data = labels_list)
labels = np.array(labels_df)
labels = labels.reshape(len(labels_list),)
labels_one_hot = to_categorical(labels)

"""Prepare Inputs"""

# find which channels are the most variant over the entire time scale
full_ecog_p1_list = full_ecog_p1.tolist()
ecog_df = pd.DataFrame(full_ecog_p1_list)

big_list_of_channels = []
for i in range(ecog_df.shape[1]): 
    big_list_of_channels.append(ecog_df[i].tolist())

channel_changes = []
for channel in big_list_of_channels:
    temp = 0
    for i in range(len(channel)-1): 
        temp += abs(channel[i+1] - channel[i])
    channel_changes.append(temp)
# all channels have similar change over entire time scale

# filter the data 
numerator, denominator = scipy.signal.butter(5,(2*200)/1000)
for i in range(62): 
    ecog_df[i] = scipy.signal.lfilter(numerator,denominator,ecog_df[i].tolist())

# # min max scale the data # messed everything up horribly 
# scaler = MinMaxScaler()
# scaled_ecog = scaler.fit_transform(ecog_df)
# ecog_df = pd.DataFrame(scaled_ecog)

# get into arrays consistent with outputs 
for i in range(len(ecog_df)):
    full_ecog_p1_list[i] = ecog_df.loc[i].tolist()

np.shape(full_ecog_p1_list)

ECOG_windows = np.zeros((len(labels_one_hot),500,62))
count = 0
while len(full_ecog_p1_list) >= 500: 
    ECOG_windows[count,:,:] = full_ecog_p1_list[0:500]
    for pop_amount in range(250):
        full_ecog_p1_list.pop(0)
    count += 1

np.shape(ECOG_windows)

## CALCULATE FEATURES

def bandpower(x, fmin, fmax):
    f, Pxx = scipy.signal.periodogram(x, fs=1000)
    ind_min = np.argmax(f > fmin) - 1
    ind_max = np.argmax(f > fmax) - 1
    return np.trapz(Pxx[ind_min: ind_max], f[ind_min: ind_max])
def line_length(x):
    return(sum(abs(np.diff(x))))
def area(x):
    return(sum(abs(x)))
def energy(x):
    return(sum(np.square(x)))
def dc_gain(x):
    return(np.mean(x))
def zero_crossings(x):
    return(sum(x > np.mean(x)))
def peak_volt(x):
    return(np.max(x))
def variance(x):
    return(np.std(x)**2)

feat_names = ['BP 8-12', 'BP 18-24', 'BP 75-115', 'BP 125-159', 'BP 160-180', 'Line Length', 'Area', 'Energy', 'DC Gain', 'Zero Crossings', 'Peak Voltage', 'Variance']
n_feats = 12
n_channels = 62
batch_ct = len(change1);
features = np.zeros((batch_ct, n_channels, n_feats))
for chan in range(n_channels):
    for idx in range(batch_ct):
        x = ECOG_windows[idx,:,chan]
        features[idx,chan,0] = bandpower(x, 8, 12)
        features[idx,chan,1] = bandpower(x, 18, 24)
        features[idx,chan,2] = bandpower(x, 75, 115)
        features[idx,chan,3] = bandpower(x, 125, 159)
        features[idx,chan,4] = bandpower(x, 160, 180)
        features[idx,chan,5] = line_length(x)
        features[idx,chan,6] = area(x)
        features[idx,chan,7] = energy(x)
        features[idx,chan,8] = dc_gain(x)
        features[idx,chan,9] = zero_crossings(x)
        features[idx,chan,10] = peak_volt(x)
        features[idx,chan,11] = variance(x)
    #pd.DataFrame(features[:,chan,:],columns=feat_names).to_csv('Features/feats_500ms_'+str(chan),index=False)

# reduce dimensionality of feature matrix
features_2d = np.zeros((batch_ct, n_channels*n_feats))
for idx in range(batch_ct):
    for chan in range(n_channels):
        for feat in range(n_feats):
            features_2d[idx, chan + feat*n_channels] = features[idx,chan,feat]

"""Final Preprocessing and Train Test Split """

features_2d = features_2d.reshape(1199,744,1)

X_train = features_2d[0:960]
Y_train = labels_list[0:960]

X_test = features_2d[960:]
Y_test = labels_list[960:]

# have to one hot encode outputs 
Y_train_oh = to_categorical(Y_train)
Y_test_oh = to_categorical(Y_test)

# # shuffle data 
# X_train_shuff, Y_train_shuff = shuffle(X_train,Y_train)
# X_test_shuff, Y_test_shuff = shuffle(X_test,Y_test)

print(np.shape(X_train))
print(np.shape(Y_train))
print(np.shape(X_test))
print(np.shape(Y_test))

"""Train Model

"""

#imports 
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout
from keras.layers import Activation 
from keras.utils import to_categorical
from keras import optimizers

# have to shuffle arrays 
from sklearn.utils import shuffle 
X_train_shuff, Y_train_shuff = shuffle(X_train,Y_train_oh)
X_test_shuff, Y_test_shuff = shuffle(X_test, Y_test_oh)

model = Sequential()
model.add(LSTM(40,return_sequences = False, input_shape = (n_feats*n_channels,1)))
model.add(Dropout(0.2))
model.add(Dense(5,activation = 'softmax'))

opt = optimizers.SGD(lr=0.5)
model.compile(loss='categorical_crossentropy', optimizer=opt, metrics=['accuracy'])

history = model.fit(X_train_shuff,Y_train_shuff,batch_size = batch_ct,epochs = 100,validation_data = (X_test_shuff,Y_test_shuff))



