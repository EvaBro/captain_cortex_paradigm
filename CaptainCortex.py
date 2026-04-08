# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 15:41:02 2026

@author: Eva Broeders

"""

import CaptainCortexUtils as utils
import numpy as np
from enum import IntFlag
from ParallelButtonBox import ButtonBox
from psychopy import visual, event, core



#%% Parameters

# Timing parameters
num_trials = 80 # number of trials
stimulus_duration = 2 # duration of still and moving circles in s
presentation_duration = 0.5 # duration of image presentation in s
fixation_duration = 1.8 # average duration of fixation
max_jitter = 0.2; # jitter duration in s, effective fixation duration will be between [fixation_duration - max_jitter, fixation_duration + max_jitter]

# File paths
circles_folder = "./circles/"
nontarget_folder = './nontarget_images/'
target_image = './captain_image/astronaut1.png'

# Triggers
class PortCodes(IntFlag):
    reset = 0         # Reset all ports
    still_circle = 1  # Trigger 1 for still circle start
    optitrack = 2     # Trigger 2 reserved for Optitrack
    moving_circle = 4 # Trigger 3 for moving circle start
    nontarget_image = 8 # Trigger 4 for nontarget image
    target_image = 16   # Trigger 5 for Captain Cortex
    button = 32         # Trigger 6 for button press
    all = 255         # Send trigger to all ports


# Screen on which video is displayed
screen_idx=0 # Should be 0 for stim PC

# Target proportion and settings
p_target = 0.25 # Proportion of trials with Captain Cortex
init_nontargets = 3 # How many nontarget trials come at the start

#%% Logistics

# Apply jitter to isi interval
jitters = np.random.uniform(-max_jitter, max_jitter, num_trials)
fixation_durations = fixation_duration + jitters

# Get images
circle_files = utils.create_img_list(circles_folder)
nontarget_files = utils.create_img_list(nontarget_folder)



#%% Set up screen and button box

# Create buttonbox    
btn_box = ButtonBox(address=0xdff8)

# Create a window
win_size = utils.get_window_size(screen_idx)
window = utils.create_window(win_size, screen_idx)

#%% Create screens
intro_screen = utils.create_staystill_screen(window)
end_screen = utils.create_staystill_screen(window)
fixation = utils.create_fixation_screen(window)

#%% Display instructions

#%% Load the stimuli

# Sort circles first, make sure they are sorted naturally instead of alphabetically
circle_files.sort(key=lambda f: int("".join(c for c in f if c.isdigit()))) 
circles = [ visual.ImageStim(window, pos=(0,0), image=circle) for circle in circle_files]

# Randomize nontarget stimuli
is_target = np.random.choice([0, 1], size=(num_trials,), p=(1-p_target, p_target))
is_target[0:init_nontargets] = 0
is_target[init_nontargets] = 1 

#%%



