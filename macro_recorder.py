import os, sys
import time
import octorest
import dataset_functions as df
import copy
import cv2
from datetime import datetime
import csv

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
GCODE_DIR = SCRIPT_DIR + "/gcode"

''' This script allows to take layerwise images from a 3D printer connected via octoprint
    
    - Connect the cam and fill out the octoprint url and API key in the Congifurations section
    - Create a folder for your makro in the gcode folder, and put your gcode files there
    - Generate a makro yaml with the generate_matkro script
    - Set the makro in the Configurations section
    - Configure the image path in necessary in the Configurations section
    
    - the script prints all gcodes, but waits for the user to remove the prints
'''

############################################################ Configuration
### SAVE IMAGES HERE
#recording_base_path = "/home/ltb/USB_DATASET/"
recording_base_path = "/home/ltb/recordings_dump"       # <---- recorded images go here

### OCTOPRINT CONFIGURATION                             # <---- configure your octopi api
url = "http://0.0.0.0:90"
key = "4A2E82FAB7254214A8710FD1BF8D4E4B"

### CAMERA CONFIGURATION
cam_data = (("ELP_12MP", 0, (2592, 1944), 110), )       # <---- Configure: Cam Name, Cam Port, Resolution, Focus

images_per_layer = 2                                    # <---- number of images taker per layer
boundingbox = [0.25, 0.26, 0.25, 0.3]                   # <---- crop image at these relative coordinates

### DEFINE MAKRO SOURCE HERE
makro_name = "Macto_Run_Towers_stringing_missings"          # <----- Put the name of the makro here, put the makro .yaml to your gcode in the same named folder
makro_path = "%s/%s" %(GCODE_DIR, makro_name)
makro_yaml_path = "%s/%s.yaml" %(makro_path, makro_name)

############################################################# Initialize
# make octoprint client and connect
print("making octoprint client")
client = df.make_client(url, key)
print("client created")
print(client.connect())

# create cameras
cams = []
for name, port, res, focus in cam_data:
    print("Initializing Camera %s" %name)
    cam = df.camera(name, port, res, focus=focus, crop=boundingbox)
    if cam.initialize_cam():
        cams.append(cam)

# run through all gcode files in the makro folder
for info in df.extract_yaml(makro_yaml_path):
    # create folder
    base_path = SCRIPT_DIR + "/Recordings"
    now = datetime.now()
    recording_name = "Recording_" + now.strftime("%d.%m.%Y_%H_%M_%S")
    recording_path = "%s/%s" %(recording_base_path, recording_name)

    if not os.path.exists(recording_path):
        os.mkdir(recording_path)

    ### CSV CONFIGURATION
    # create csv
    csv_filename = "%s.csv" %recording_name
    csv_path = "%s/%s" %(recording_path, csv_filename)

    # CSV HEADER
    extend_csv_header = ["image", "layer",]
    # extract header from yaml
    static_header = df.extract_keys_from_yaml(makro_yaml_path, excluded_keys=["gcode"])
    # extend header with image name and layer
    extend_csv_header.extend(static_header)
    csv_header = extend_csv_header
    # write recording name to content
    info["recording"] = recording_name
    static_content = [info[key] for key in static_header]
    #write header
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f, delimiter=";")
        # write a row to the csv file
        writer.writerow(csv_header)

    # upload and select gcode file on octoporint server
    gcode = "%s/%s" %(makro_path, info["gcode"])
    print(gcode)
    client.upload(gcode)
    df.file_names(client)
    client.select(info["gcode"])

    # starting print
    print("Upcoming Print: %s" %info["gcode"])
    input("press key to start print")
    client.start()
    print("starting")

    ############################################################## Recording Loop
    
    # get byte positions of layerjumps    
    layerjumps_bytes = list(df.get_layerjump(gcode)["bytes"].keys()) 
    #layerjumps = df.get_layerjump(gcode)  <- does not work with current get_layerjump function (return layserjump_bytes instead)
    trigger = layerjumps_bytes.pop(0)
    layer = 0
        
    while client.printer()["state"]["flags"]["printing"]:
        job_info = client.job_info()    
        current_filepos = job_info["progress"]["filepos"]

        if current_filepos == None:
            client.cancel()
            break
        
        # check for new layer
        if current_filepos >= trigger:
            print("New Layer detected")
            # ignore zero layer
            if not trigger == 0:
                layer = layer + 1
            # take next linejump trigger from list
            if layerjumps_bytes:
                trigger = layerjumps_bytes.pop(0)
            # take image and save
            for i in range(images_per_layer):
                for cam in cams:
                    image = cam.make_image()
                    filename = df.generate_unique_name(name=cam.get_name())
                    file = "%s/%s" %(recording_path, filename)
                    print("saving image %s" %filename)
                    cv2.imwrite(file, image)

                    recording_class = info["class"]

                    with open(csv_path, 'a', newline='') as f:
                        # create the csv writer
                        writer = csv.writer(f, delimiter=";")
                        # write a row to the csv file
                        content = [filename, layer]
                        content = content + static_content
                        writer.writerow(content)

    ############################################################## End of print
