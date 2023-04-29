#from imp import is_frozen_package
import os, sys
import time
import octorest
import dataset_functions as df
import keyboard
import cv2
from datetime import datetime
import csv

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
PATH_LIB = currentdir + "//src"
sys.path.append(PATH_LIB)

recording_base_path = "/home/ltb/USB_DATASET/"

url = "http://0.0.0.0:90"
key = "4A2E82FAB7254214A8710FD1BF8D4E4B"

gcode_file = "3_D2_23m_0,20mm_200C_PLA_ENDER3BLTOUCH.gcode"

csv_header = ["image", "layer", "class", "nozzle", "filament", "ex_mul", "retraction", "color", "shape"]

recording_class = "good"
nozzle = 0.4
filament = "PLA"
filament_color = "dark_green"
extrusion_multiplier = 1
retraction = 5
shape = "spherelike_shape"

cam_data = (("ELP_12MP", 0, (2592, 1944)), ("ELP_2MP", 2 ,(1920, 1080)) )


######################## Initialize
# make octoprint client and connect
print("making octoprint client")
client = df.make_client(url, key)
print("client created")
print(client.connect())

# create cameras
cams = []
for name, port, res in cam_data:
    print("Initializing Camera %s" %name)
    cam = df.camera(name, port, res)
    if cam.initialize_cam():
        cams.append(cam)

# create folder
base_path = currentdir + "/Recordings"
now = datetime.now()
recording_name = "Recording_" + now.strftime("%d.%m.%Y_%H_%M_%S")
recording_path = "%s/%s" %(recording_base_path, recording_name)

if not os.path.exists(base_path):
    os.mkdir(base_path)
if not os.path.exists(recording_path):
    os.mkdir(recording_path)

# create csv
csv_filename = "%s.csv" %recording_name
csv_path = "%s/%s" %(recording_path, csv_filename)


# upload and select gcode file on octoporint server
gcode = currentdir + "/gcode/" + gcode_file
client.upload(gcode)
df.file_names(client)
client.select(gcode_file)

# starting print
input("press key to start print")
client.start()
print("starting")

for cam in cams:
    image = cam.make_image()
    filename = df.generate_unique_name(name=cam.get_name())
    file = "%s/%s" %(recording_path, filename)
    print("saving image %s" %file)
    cv2.imwrite(file, image)


################################# Recording Loop
layerjumps = df.get_layerjump(gcode)
trigger = layerjumps.pop(0)
layer = 0

    
while client.printer()["state"]["flags"]["printing"]:
    job_info = client.job_info()    
    current_filepos = job_info["progress"]["filepos"]

    if current_filepos == None:
        client.cancel()
        break

    if current_filepos >= trigger:
        print("New Layer detected")
        # ignore zero layer
        if not trigger == 0:
            layer = layer + 1
        # take next linejump trigger from list
        if layerjumps:
            trigger = layerjumps.pop(0)
        # take image and save
        for i in range(2):
            for cam in cams:
                image = cam.make_image()
                filename = df.generate_unique_name(name=cam.get_name())
                file = "%s/%s" %(recording_path, filename)
                print("savin image %s" %filename)
                cv2.imwrite(file, image)

                with open(csv_path, 'a', newline='') as f:
                    # create the csv writer
                    writer = csv.writer(f, delimiter=";")
                    # write a row to the csv file
                    writer.writerow(csv_header)
                    writer.writerow([filename, layer, recording_class, nozzle, filament, extrusion_multiplier, retraction, filament_color, shape])

for i in range(5):
    time.sleep(1)
    for cam in cams:
        image = cam.make_image()
        filename = df.generate_unique_name(name=cam.get_name())
        file = "%s/%s" %(recording_path, filename)
        print("savin image %s" %filename)
        cv2.imwrite(file, image)

        with open(csv_path, 'a', newline='') as f:
            # create the csv writer
            writer = csv.writer(f, delimiter=";")
            # write a row to the csv file
            writer.writerow(csv_header)
            writer.writerow([filename, layer, recording_class, nozzle, filament, extrusion_multiplier, retraction, filament_color, shape])


#client.cancel()