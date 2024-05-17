# 3D-printing_recorder

This repository is used to record image data of a 3D printing process.
It's purpose is to create an image dataset to explore visual error detection in 3D-printing with machine learning.
The dataset created with this tool, can be found at the bottom of this page.


Furthermore it is possible to inflict Under-Extrusion synthetically on gcode-files, to create this error in a determined manner.
The printer should be connected to a Octoprint server: https://github.com/OctoPrint/octoprint-docker

## How to record

### Make a makro

To log metadata and to schedule prints use the *generate_makro* script:

  - First create a directory in the gcode folder
  - Put all gcode files for printing in this folder
  - Enter the name of the directory in the Configuration section of the generate_makro script
  - Modify the printing parameters to be logged
  - Run the script
  - A makro.yaml file is created, which contains all relevant data to schedule the prints
  
  
### Record the images

To record images use the *makro_recorder*:
  
  In the script:
  - Specify a base path for the images to be saved
  - Configure url and API-key of your octoprint server
  - Configure the cam port, resolution, and focus to utilize any usb-camera. Multiple cameras possible.
  - You can specify a boundingbox to which the images are cropped
  - Enter the path of the directory with your gcode and makro.yaml
  - Connect the cameras and the 3D printer
  - Run the script to start printing, the script will wait for user to press a key to start the next scheduled print
  
  
  ## Create Under-Extrusion
    
 To create the Under-Extrusion error, use the *gcode_modifier* script:
    
  In the Script:
  - Specify directory with gcode files to be modified
  - Set the printing parameter to be logged
  - Set the under extrusion parameter to specify the error properties
  - Run the script to modify your gcode files; The script automatically creates a makro.yaml for print scheduling
 
  
## Videostreaming

To check and adjust your camera, use the main.py in the Videostreaming directory. You have to adjust cam port and the focus.

## Dataset

https://www.kaggle.com/nimbus200
