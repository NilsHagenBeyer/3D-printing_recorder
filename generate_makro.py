import os, sys
import dataset_functions as df
import copy

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
GCODE_DIR = SCRIPT_DIR + "/gcode"

'''     Use this script to generate a makro for scheduling a print job.
        
        - First create a directory in the gcode folder
        - Put all gcode files for printing in this folder
        - Enter the name of the directory in the Configuration section of the generate_makro script
        - Modify the printing parameters to be logged
        - Run the script
        - A makro.yaml file is created, which contains all relevant data to schedule the prints
'''

######################################### Configuration ####################################
# configure the makro directory, where the gcode files are stored
dirname = "Macto_Run_Towers_stringing_missings"

# modify the printing parameters to match your slicing settings
parameter_ = {  "gcode": None,
                "class": "STRINGING",
                "nozzle": 0.4,
                "filament": "PLA",
                "layer_height": 0.3,
                "filament_color": "gray",
                "ex_mul": 1,
                "retraction": 2,
                "shape": "complex",
                "recording": None,
                "printbed_color": "black",

}

#############################################################################################



makrodir = "%s/%s" %(GCODE_DIR, dirname)

# collect gcode files
f = []
for (dirpath, dirnames, filenames) in os.walk(makrodir):
    f.extend(filenames)
    break
f = [x for x in f if x.endswith(".gcode")]

# sort f alphabetically
f.sort()

# generate makro file
makro = []
for gcode in f:
    parameter = copy.deepcopy(parameter_)
    parameter["gcode"] = gcode
    makro.append(parameter)

savefile = makrodir + "/" + dirname + ".yaml"

# save makro file
df.dump_yaml(savefile, makro)