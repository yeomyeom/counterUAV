import librosa
import pickle
import sys
import glob as g
import os
from os.path import isfile, isdir
import numpy as np

# For augmenting .wav data

SAMPLE_RATE=5682
FILE_EXT='*.wav'
DATA_PATH='../raw_data/'  # path of raw file
PATH='../raw_data/data_process'  # path for visualize.py
sys.path.insert(0, PATH)
from visualize import LoadPlot

"""
This class contains data augmentation methods that increase the size and variance of our dataset.
Data augmentation methods include:

    1) Frequency shifting
    2) Add random noise
    3) Time stretching
    4) Shifting frequency (use np.roll())

All methods should return the following two values:
    1) Y (augmented frequency values)
    2) sr (sampling rate)
"""
class DataAugmentor():
    def __init__(self, file_ext=FILE_EXT):
        opt = {}
        opt['file_ext'] = file_ext
    '''
    This method shifts the signal by n half-steps (n: # of steps)
    '''
    def freq_shifting(self, raw_freq, num_steps=4, sr=SAMPLE_RATE):
    # Shifting frequency values of the signal by <num_setps> * half-steps
        Ys, fs = [], []

        for fr in raw_freq: 
            # Shift up by a major third (four half-steps)
            Y_shifted = librosa.effects.pitch_shift(fr, sr, num_steps)
            Ys.append(Y_shifted)
            fs.append(sr)

        return Ys, sr

    '''
    This method adds random noise to the signal
    '''
    def add_noise(self, data, scale = 0.005, sr=SAMPLE_RATE):
    # Generate random noise to augment the data
        Yn = []
        
        max_len_idx = max((len(l), i) for i, l in enumerate(data))[1] #Get index of longest subarray
        max_len = len(data[max_len_idx])
        noise = np.random.uniform(low=2, high=5, size=1) # Generate a random number within a range [low, high] with the length of the longest subarray
        print('Noise value:', noise)
        noise_val = np.full(max_len, noise)
        for e in data:
            Y = e + (noise_val[:len(e)] * scale)
            Yn.append(Y)

        return Yn, sr

    '''
    This method streches the data on time axis.
    Parameter raw_freq is a list of data amplitude values (5682 samples * time in seconds)
    It returns a list with time-stretched elements
    '''
    def time_stretching(self, raw_freq, rate=2.0):
        Ys = []
        for fr in raw_freq:  # raw_freq has many data files.
            Y_stretched = librosa.effects.time_stretch(fr, rate)
            Ys.append(Y_stretched)
        return Ys

#    def visualize

def main():
    # Frequency shift and visualize in log-spectrogram
    loader = LoadPlot()
    paths = []

    file_paths = g.glob(os.path.join(DATA_PATH, FILE_EXT))
    print('File path:', g.glob(os.path.join(DATA_PATH, FILE_EXT)))

    # Pickling data file to reduce the size and speed up load time of the *.wav files
    try:
        if not isfile('radar_dataset.pickle'):
            print('radar_dataset.pickle not found: Pickling...')
            loader = LoadPlot()
            raw_freq = loader.load_sound_files(file_paths)

            lbl = []
            for p in file_paths:
                path, filename = os.path.split(p)
                freq_labels = filename.split('_')[1]    # extract labels from the file name
                lbl.append(freq_labels)

            freq_data = {'raw_freq': raw_freq,
                    'labels': lbl}

            with open('radar_dataset.pickle', 'wb') as handle:
                print('Pickling data object...')
                pickle.dump(freq_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

        else:
            print('Loading data from radar_dataset.pickle')
            with open('radar_dataset.pickle', 'rb') as handle:
                freq_data = pickle.load(handle)

    except IOError:
        print('IOError: Could not find file path')

    da = DataAugmentor()
    #freq_data['ps_freq'], sr = da.freq_shifting(freq_data['raw_freq'])
    freq_data['noise_freq'], sr = da.add_noise(freq_data['raw_freq'])

    print('Value of original frequency:', freq_data['raw_freq'][0])
    print('Value of noise added frequency:', freq_data['noise_freq'][0])

    loader.plot_log_specgram(freq_data['labels'][:2], freq_data['raw_freq'][:2]) #visualize in log_spectrogram
    loader.plot_log_specgram(freq_data['labels'][:2], freq_data['noise_freq'][:2]) 

if __name__ == "__main__":
    main()
