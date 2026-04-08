# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 11:54:18 2024

@author: Eva Broeders

"""
from psychopy import visual, core, parallel, event
from psychopy.constants import FINISHED
import os
import pyglet
from ParallelButtonBox import ButtonBox
import pandas as pd
import numpy as np
import subprocess
import time
import win32gui
import win32con

# Trigger settings
trig_port = parallel.ParallelPort(0xcFF8)
trigger_time = 0.005

# Buttonbox settings
btn_box = ButtonBox(address=0xdff8)

def set_display_mode(mode: str):
    """
    mode: 'internal', 'external', 'extend', or 'clone'
    """
    if mode not in ('internal', 'external', 'extend', 'clone'):
        raise ValueError("mode must be 'internal', 'external', 'extend', or 'clone'")
    subprocess.run(["DisplaySwitch.exe", f"/{mode}"], check=False)
    time.sleep(2)  # small pause to let Windows reconfigure displays


def create_img_list(img_path):
        img_files = [img_path + img for img in os.listdir(img_path) if img.endswith(('.bmp','.png', '.BMP', '.jpg'))]
        return sorted(img_files)

def create_staystill_screen(window):
    intro_screen = visual.TextStim(win=window, text="Please stay very still.", color='white',
                                   height=70, alignText='center', anchorHoriz='center',
                                   anchorVert='center')
    return intro_screen

def create_fixation_screen(window):
    fixation = visual.TextStim(win=window, text='+', color='white',
                            height=60, alignText='center', anchorHoriz='center',
                            anchorVert='center')
    return fixation

def get_window_size(screen_idx):
    display = pyglet.canvas.get_display()
    screens = display.get_screens()
    primary_screen = screens[screen_idx]  # Use the primary screen (or adjust index for others)
    win_size = primary_screen.width, primary_screen.height
    return win_size

def create_window(win_size, screen_idx):
    window = visual.Window(fullscr=True, size=win_size, screen=screen_idx, monitor="testMonitor", color="black", waitBlanking=True,
                           checkTiming=False, allowGUI=False, useFBO=False, units='pix')
    #fr = window.getActualFrameRate(nIdentical=60, nMaxFrames=240)
    #print('Refresh ~', fr, 'Hz')
    return window

def scale_imgs(images, scale_w, scale_h):
    for img in images:
        img_w = img.size[0]*scale_w
        img_h = img.size[1]*scale_h
        img.size = (img_w, img_h)
        
def send_trigger(code):
    trig_port.setData(code)
    core.wait(trigger_time)
    trig_port.setData(0)
    
def check_button_press_continuous(PortCodes, window, img_end_time, trial_list, n_trials_completed):
    # Return button_pressed (bool)
    button_pressed = False
    while core.getTime() < img_end_time:
        window.flip()
        keys = event.getKeys()
        jsbtns = btn_box.getAllButtons()[1:3]  # adjust indices to your device
        if any(jsbtns) or ('space' in keys):
            send_trigger(PortCodes.button)  #sends a trigger that button is pressed
            button_pressed = True        
        if 'escape' in keys:
            pd.DataFrame(trial_list[:n_trials_completed]).to_csv("trial_log.csv", index=False)
            intervals = np.array(window.frameIntervals)
            dropped = window.nDroppedFrames

            print("\n=== Frame Timing Diagnostics ===")
            print(f"Total flips:               {len(intervals)}")
            print(f"Dropped frames:            {dropped}")
            print(f"Median interval (s):       {np.median(intervals):.6f}")
            print(f"Mean interval (s):         {np.mean(intervals):.6f}")
            print(f"Std dev interval (s):      {np.std(intervals):.6f}")
            print(f"Estimated refresh (Hz):    {1.0 / np.median(intervals):.2f}")
            print("=================================\n")
            window.close()
            core.quit()
    return button_pressed


def play_attention_grabber(win, video, PortCodes):
    # Reset to start (if supported), set volume, and play
    video.seek(0.0)
    video.volume = 1.0
    video.play()
    
    clk = core.Clock()
    while True:
        video.draw()
        win.flip()
        
        keys = event.getKeys()
        jsbtns = btn_box.getAllButtons()[1:3]  # adjust indices to your device

        if 'escape' in keys:
            win.close(); core.quit()
        if video.status == FINISHED:
            break
        if any(jsbtns) or ('space' in keys):
            # Stop at second buttonpress
            send_trigger(PortCodes.button)  # sends a trigger that button is pressed
            video.stop()
            break            
    return clk.getTime()  # how long the attention video actually ran            

def check_button_press(PortCodes):
    btn_pressed = False
    jsbtns = btn_box.getAllButtons()[1:3]
    if any(jsbtns):
         print(jsbtns)
         send_trigger(PortCodes.button)  #sends a trigger that button is pressed
         btn_pressed = True        
    return btn_pressed
        
def img_playing(clock, img_end_time):
    current_time = clock.getTime()
    if current_time < img_end_time:
        return True
    else:
        return False
    
def print_frame_timing_diagnostics(window):
    intervals = np.array(window.frameIntervals)
    dropped = window.nDroppedFrames

    print("\n=== Frame Timing Diagnostics ===")
    print(f"Total flips:               {len(intervals)}")
    print(f"Dropped frames:            {dropped}")
    print(f"Median interval (s):       {np.median(intervals):.6f}")
    print(f"Mean interval (s):         {np.mean(intervals):.6f}")
    print(f"Std dev interval (s):      {np.std(intervals):.6f}")
    print(f"Estimated refresh (Hz):    {1.0 / np.median(intervals):.2f}")
    print("=================================\n")
    


def _is_normal_window(hwnd):
    """Return True if hwnd is a normal, visible, user-level window."""
    if not win32gui.IsWindowVisible(hwnd):
        return False

    # Skip tooltips, program managers, invisible system windows
    if win32gui.GetParent(hwnd) != 0:
        return False

    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    if not (style & win32con.WS_OVERLAPPEDWINDOW):
        return False

    title = win32gui.GetWindowText(hwnd)
    if not title.strip():
        return False

    return True


def save_window_positions():
    """Return a dict: {hwnd: (left, top, right, bottom)}."""
    positions = {}

    def enum_handler(hwnd, positions):
        if _is_normal_window(hwnd):
            rect = win32gui.GetWindowRect(hwnd)
            positions[hwnd] = rect

    win32gui.EnumWindows(enum_handler, positions)
    return positions


def restore_window_positions(positions):
    """Restore window positions from the saved dict."""
    for hwnd, rect in positions.items():
        if win32gui.IsWindow(hwnd):
            left, top, right, bottom = rect
            width = right - left
            height = bottom - top

            # Restore window without bringing it to front
            win32gui.SetWindowPos(
                hwnd,
                None,
                left, top, width, height,
                win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
            )

def ButtonStateMachine(buttonClock, keys, jsbtns, trig_code, prev_button_state, prev_button_time):
    """
    Debounced button state machine.
    - Only fires on new presses (edge: up -> down)
    - Enforces a minimum interval between triggers
    """
    now_time = buttonClock.getTime()
    
    button_now = any(jsbtns) or 'space' in keys
    is_new_press = button_now and not prev_button_state
    button_time_ok = (now_time - prev_button_time) > 0.2
    
    # Default: keep previous time if nothing happens
    new_button_time = prev_button_time
    
    # Fire trigger only for *new* presses, spaced in time
    if is_new_press and button_time_ok:
        send_trigger(trig_code)
        new_button_time = now_time
    
    new_button_state = button_now
    
    return new_button_state, new_button_time