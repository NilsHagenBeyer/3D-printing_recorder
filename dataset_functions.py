import os
import octorest
import cv2
from datetime import datetime
import time
import matplotlib.pyplot as plt
import csv
import yaml

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)

def extract_yaml(file, print_info=False):
    with open(file, "r") as stream:
        try:
            content = yaml.safe_load(stream)
            if print_info:
                print("LOADED: %s" %file)
            return content
        except yaml.YAMLError as exc:
            print("Yaml file not readable: %s" %file)
            print(exc)

def dump_yaml(file, content):
    with open(file, 'w') as f:
        yaml.dump(content, f,  explicit_start=True, default_flow_style=False)

def extend_yaml(yaml_file, data):
    try:
        with open(yaml_file, 'r') as f:
            yaml_data = yaml.safe_load(f)
    except FileNotFoundError:
        yaml_data = []

    yaml_data.append(data)

    with open(yaml_file, 'w') as f:
        yaml.dump(yaml_data, f)

def extract_keys_from_yaml(yaml_file, excluded_keys=[]):
    # Open the YAML file and read the contents
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)

    # Extract the dictionary keys from the list of dictionaries
    keys = [list(d.keys()) for d in data][0]
    #merged_keys = set().union(*keys)
    
    # Exclude certain keys from the merged list
    #filtered_keys = keys.difference(excluded_keys)
    # exclude excluded_keys from keys
    filtered_keys = [x for x in keys if x not in excluded_keys]

    return filtered_keys

def get_layerjump(filepath):
    total_size = os.path.getsize(filepath)
    line_counter = 0
    byte_counter = 0
    layer_counter = 0

    layerjump_bytes = []

    layerjumps = {"total":{}, "bytes":{}, "lines":{}}
    
    with open(filepath, "r") as file:        
        for line in file:
            line_counter = line_counter + 1
            byte_counter = byte_counter + len(line.encode('utf-8'))
            
            # find layerjump line in gcode and save bytelength marker of that line
            if line.startswith("G1 Z"):
                layerjump_bytes.append(byte_counter)
                # increase layercounter for next jump
                layer_counter = layer_counter + 1
                layerjumps["bytes"][byte_counter] = layer_counter
                layerjumps["lines"][line_counter] = layer_counter
            
            # if ";start" marker is in gcode, reset layerjumps up to here and begin counting
            if line.startswith(";start"):
                layerjump_bytes = []
                layerjumps = {"total":{}, "bytes":{}, "lines":{}}
                layer_counter = 0

            # break if "diable Motors" command signals end of executable gcode file
            #if line.startswith("M84"):
            #    break

    layerjumps["total"]["lines"] = line_counter
    layerjumps["total"]["bytes"] = byte_counter
    layerjumps["total"]["layers"] = layer_counter
    
    return layerjumps

def make_client(url, apikey):
     """Creates and returns an instance of the OctoRest client.

     Args:
         url - the url to the OctoPrint server
         apikey - the apikey from the OctoPrint server found in settings
     """
     try:
         client = octorest.OctoRest(url=url, apikey=apikey)
         return client
     except ConnectionError as ex:
         # Handle exception as you wish
         print(ex)

def file_names(client):
     """Retrieves the G-code file names from the
     OctoPrint server and returns a string message listing the
     file names.

     Args:
         client - the OctoRest client
     """
     message = "The GCODE files currently on the printer are:\n\n"
     for k in client.files()['files']:
         message += k['name'] + "\n"
     print(message)

def toggle_home(client):
     """Toggles the current print (if printing it pauses and
     if paused it starts printing) and then homes all of
     the printers axes.

     Args:
         client - the OctoRest client
     """
     print("toggling the print!")
     #client.toggle()
     print("Homing your 3d printer...")
     client.home()

def generate_unique_name(name="", ftype="png"):
    now = datetime.now()
    datestring = now.strftime("%d.%m.%Y")
    unix_timestamp = str(time.mktime(now.timetuple()) * 1000 + now.microsecond/1000)
    unix_timestamp = unix_timestamp.split(".")[0][:-1]

    generated_name = "%s_%s_%s.%s" %(name, datestring, unix_timestamp, ftype)
    return generated_name

class camera():
    def __init__(self, name, port, resolution, focus=110, crop=None ):
        self.name = name
        self.port = port
        self.res_width, self.res_height = resolution
        self.focus = focus
        self.crop = crop

    def initialize_cam(self):        
        self.cam = cv2.VideoCapture(self.port)
        self.cam.set(3, self.res_width)
        self.cam.set(4, self.res_height)
        #self.cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)
        #self.cam.set(15, -13)
        #self.cam.set(21, -13)

        #self.cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
        self.cam.set(cv2.CAP_PROP_EXPOSURE, 2000)
        self.cam.set(cv2.CAP_PROP_FOCUS, self.focus)
        
        #self.cam.set(cv2.CAP_PROP_FPS, 15)
        #print(self.cam.get(cv2.CAP_PROP_EXPOSURE))
        
        time.sleep(2)
        if self.cam:
            return True
        else:
            return False

    def make_image(self):   
        result, image = self.cam.read()

        if self.crop:
            image = self.crop_image(image, self.crop)

        return image

    def get_name(self):
        return self.name

    def crop_image(self, image, boundingbox):
        img_height, img_width, img_channels = image.shape
        y_factor, x_factor, height_factor, width_factor = boundingbox
        # rows
        y = int(img_height * y_factor)
        h = int(y + img_height * height_factor)
        # columns
        x = int(img_width * x_factor)
        w = h
        #w = int(x + img_width * width_factor)

        crop_img = image[y:y+h, x:x+w]

        return crop_img



if __name__ == "__main__":

    boundingbox = [0.25, 0.26, 0.25, 0.3]

    #print(cv2.getBuildInformation())
    cam = camera("cam", 0, (2592, 1944))
    #print("Initializin cam")
    #print(cam.initialize_cam())
    #print("Wait...")
    #print("Making image")
    #image = cam.make_image()
    #print("saving")

    read_file = currentdir + "/fullsize.png"
    image = cv2.imread(read_file)
    crop_img = cam.crop_image(image, boundingbox)
    print(crop_img.shape)

    file = "image2.png"
    save_file = currentdir + "/croped.png"
    cv2.imwrite(save_file, crop_img)
    print("done")



    '''# open the file in the write mode
    header = ["image", "layer", "class"]

    with open('data.csv', 'w') as f:
        # create the csv writer
        writer = csv.writer(f, delimiter=";")

        # write a row to the csv file
        writer.writerow(header)
        writer.writerow([file, "1", "good"])'''