import os, sys
import dataset_functions as df
import copy

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
gcodedir = currentdir + "/gcode"

######################################### EINGABEN

dirname = "Macto_Run_Towers_stringing_missings"
makrodir = "%s/%s" %(gcodedir, dirname)

f = []
for (dirpath, dirnames, filenames) in os.walk(makrodir):
    f.extend(filenames)
    break

f = [x for x in f if x.endswith(".gcode")]

# sort f alphabetically
f.sort()


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

makro = []

for gcode in f:
    parameter = copy.deepcopy(parameter_)
    parameter["gcode"] = gcode
    makro.append(parameter)

savefile = makrodir + "/" + dirname + ".yaml"

df.dump_yaml(savefile, makro)