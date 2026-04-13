# -*- coding: utf-8 -*-
"""
Created on Mon Apr 13 10:35:21 2026

@author: MEG Stim
"""

from PIL import Image
import os

os.chdir(os.path.dirname(os.path.abspath(__file__))) 



input_folder = "./circles_original/"
output_folder = "./circles_enlarged/"


for img_file in os.listdir(input_folder):
    print(input_folder + img_file)
    img = Image.open(input_folder + img_file)
    img_resized = img.resize((500, 500), Image.LANCZOS)  # highest quality
    output_path = os.path.join(output_folder, img_file)
    img_resized.save(output_path)
