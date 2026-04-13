# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 15:41:02 2026

@author: Eva Broeders, based on the Converge visual gamma paradigm

CaptainCortex paradigm. 
Trials consist of still and moving circles to elicit visual gamma oscillations. 
After presentation of the circles, the participant is shown an image. 
If the image is that of an astronaut (Captain Cortex), they are instructed to
press the red button.

Controls:
    - red button:   button press (linked to trigger)
    - space:        enter trial loop after showing instruction screen / button press during trial loop (linked to trigger)
    - Escape:       quits the experiment completely. Also works while paused
    - p:            pauses the experiment
    - r:            resumes the experiment after pause
"""

import CaptainCortexUtils as utils
import numpy as np
from enum import IntFlag
from ParallelButtonBox import ButtonBox
from psychopy import visual, event, core
import os

os.chdir(os.path.dirname(os.path.abspath(__file__))) 

#%% Parameters

# Timing parameters
num_trials = 80 # number of trials
stimulus_duration = 2 # duration of still and moving circles in s
image_duration = 0.5 # duration of image presentation in s
fixation_duration = 1.8 # average duration of fixation
max_jitter = 0.2; # jitter duration in s, effective fixation duration will be between [fixation_duration - max_jitter, fixation_duration + max_jitter]
framerate = 60; # Hz, System-dependent
circle_speed = 7 # How many circle files are skipped to generate a 'movie', analogous to Presentation
ready_duration = 3 # duration of ready set go sequence
end_duration = 2 # duration of the final message in s


# File paths
circles_folder = "./circles_enlarged/"
nontarget_folder = './nontarget_images/'
target_image = './captain_image/astronaut1.png'
instruction = './instructions/Instruction_black.PNG'

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

# Image sizes
img_size = 300 # Pixels
circle_size = 500 # pixels
fixation_radius = 10 # pixels
#%% Logistics

# Apply jitter to isi interval
jitters = np.random.uniform(-max_jitter, max_jitter, num_trials)
fixation_durations = fixation_duration + jitters

# Convert timings to number of frames 
num_circle_frames = np.round(stimulus_duration*framerate).astype(int)
num_fixation_frames = np.round(fixation_durations*framerate).astype(int)
num_image_frames = np.round(image_duration*framerate).astype(int)

# Get images
circle_files = utils.create_img_list(circles_folder)
nontarget_files = utils.create_img_list(nontarget_folder)

#%% Set up window and button box

# Create buttonbox    
btn_box = ButtonBox(address=0xdff8)

# Create a window
win_size = utils.get_window_size(screen_idx) 
window = utils.create_window(win_size, screen_idx)

#%% Create screens
intro_screen = visual.ImageStim(window, pos=(0,0), image=instruction, size=win_size)

ready_screen = visual.TextStim(win=window, text="Ready", color='white',
                               height=70, alignText='center', anchorHoriz='center',
                               anchorVert='center')

set_screen = visual.TextStim(win=window, text="Set", color='white',
                               height=70, alignText='center', anchorHoriz='center',
                               anchorVert='center')

go_screen = visual.TextStim(win=window, text="Go!", color='white',
                               height=70, alignText='center', anchorHoriz='center',
                               anchorVert='center')

fixation = visual.Circle(window, radius=fixation_radius)

end_screen = visual.TextStim(win=window, text="The end.\nThank you for playing!", color='white',
                               height=70, alignText='center', anchorHoriz='center',
                               anchorVert='center')

#%% Display instructions
intro_screen.draw()
window.flip()

#%% Meanwhile, load the stimuli and randomize their order

# Sort circles first, make sure they are sorted naturally instead of alphabetically
circle_files.sort(key=lambda f: int("".join(c for c in f if c.isdigit()))) 
circles = [ visual.ImageStim(window, pos=(0,0), image=circle, size=circle_size) for circle in circle_files]

# Randomize nontarget stimuli
is_target = np.random.choice([0, 1], size=(num_trials,), p=(1-p_target, p_target))
is_target[0:init_nontargets] = 0
is_target[init_nontargets] = 1

num_nontarget = num_trials - np.sum(is_target)

if num_nontarget > len(nontarget_files):
    # There are more nontarget trials than images available
    full_repeats = num_nontarget//len(nontarget_files)
    num_extra = num_nontarget%len(nontarget_files)
    
    # Create bulk
    nontarget_list = full_repeats*nontarget_files
    
    # Select extras
    extra = np.random.choice(nontarget_files, size=(num_extra,), replace=False)
    nontarget_list.extend(extra)
    
    # Shuffle
    np.random.shuffle(nontarget_list)

else:
    nontarget_list = np.random.choice(nontarget_files, size=(num_nontarget,), replace=False)


# Now fill up the list
stim_images = np.empty(num_trials, dtype=object)
stim_images[is_target.astype(bool)] = visual.ImageStim(window, pos=(0,0), image=target_image, size=img_size)
stim_images[~is_target.astype(bool)] = [visual.ImageStim(window, pos=(0,0), image=img, size=img_size) for img in nontarget_list]

#%% Wait a bit longer if needed, until ready
event.clearEvents() # Clear the keyboard events buffer to make sure previous button presses are ignored
print('All images loaded. Press space when ready.')
ready = False
while not ready:
    keys = event.getKeys()
    if 'escape' in keys:
        window.close()
        core.quit()
    if 'space' in keys:
        ready = True
ready_screen.draw()
window.flip()
core.wait(ready_duration/3)

set_screen.draw()
window.flip()
core.wait(ready_duration/3)

go_screen.draw()
window.flip()
core.wait(ready_duration/3)

#%% Trial loop
circle_idx = 0
window.setRecordFrameIntervals(True) # Enable frame timing diagnostics
for trial_idx in range(num_trials):
    
    # Present still circle
    for frame_idx in range(num_circle_frames):
        circles[circle_idx].draw()
        window.callOnFlip(utils.send_trigger, PortCodes.still_circle)
        window.flip()
        utils.check_keys(window, PortCodes)
    
    # Present moving circle
    for frame_idx in range(num_circle_frames):
        circles[circle_idx].draw()
        window.callOnFlip(utils.send_trigger, PortCodes.moving_circle)
        window.flip()
        circle_idx += circle_speed # Loop through circles by updating the circle index
        circle_idx = circle_idx%len(circle_files) # Make sure index doesn't go out of range
        utils.check_keys(window, PortCodes)
    
    # Present image
    for frame_idx in range(num_image_frames):
        stim_images[trial_idx].draw()
        if is_target[trial_idx]:
            window.callOnFlip(utils.send_trigger, PortCodes.target_image)
        else:
            window.callOnFlip(utils.send_trigger, PortCodes.nontarget_image)        
        window.flip()
        utils.check_keys(window, PortCodes)
            
    # Present fixation
    for frame_idx in range(num_fixation_frames[trial_idx]):
        fixation.draw()
        window.flip()
        utils.check_keys(window, PortCodes)

# Draw end screen
end_screen.draw()
window.flip()
core.wait(end_duration)

window.close()
core.quit()
        




