import os, sys
import dataset_functions as df
import shutil
import numpy as np
import copy

def is_between_key_pairs(d, i):
    for key, value in d.items():
        if key <= i <= value:
            return True
    return False

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
GCODE_DIR = SCRIPT_DIR + "/gcode"

''' This script can be used to modify gcode files to simulate underextrusion

    - Specify directory with gcode files to be modified
    - Set the printing parameter to be logged
    - Set the under extrusion parameter to specify the error properties
    - Run the script to modify your gcode files; The script automatically creates a makro.yaml for print scheduling

'''

######################################### Configuration ####################################
# configure the makro directory, where the gcode files are stored
dirname = "complex_shapes_2_underex"


##### PRINTING PARAMETERS #####
# modify the printing parameters to match your slicing settings
recording_class = "underextrusion"
nozzle = 0.4
filament = "PLA"
layer_height = 0.3
filament_color = "gray"
retraction = 8.5
shape = "complex"
printbed_color = "black"

##### UNDEREXTRUSION PARAMETERS #####

modify_layers_between = [5,200]         # the layers and in between can be be modified
min_modified_layers = 8                 # minimum layers to be modified
modify_layer_chance = 0.25              # possibility of a layer to be modified
top_layer_cap = 10                      # top layer cap, to prevent the top layers from being modified
modify_line_chance = 0.9                # possibility of a layer subsection (line) to be modified

modify_extrusion_mean = 0.6             # extrusion factor mean and std
modify_extursion_std = 0.2

# sets the filename ending of the modified gcode file
modified_file_ending = "_modified.gcode"

##### SCRIPT  #####
generate_macro = True
delete_unmodified_gcode = True
debug_mode = False


######################################### START ############################################
makrodir = "%s/%s" %(GCODE_DIR, dirname)
# find all gcode files in makrodir
f = []
for (dirpath, dirnames, filenames) in os.walk(makrodir):
    f.extend(filenames)
    break
f = [x for x in f if x.endswith(".gcode")]
f = [x for x in f if not x.endswith(modified_file_ending)]
# sort f alphabetically
f.sort()

# iterate over all gcode files
for gcode in f: 
    # generat full filepath
    filepath = "%s/%s" %(makrodir, gcode)
    # get layerjumps from the file
    layerjumps = df.get_layerjump(filepath)
    layerjumps_lines = layerjumps["lines"]
    total_lines = layerjumps["total"]["lines"]
    total_layers = layerjumps["total"]["layers"]
    # invert keys and values of layerjumps_lines
    layerjumps_lines = {v: k for k, v in layerjumps_lines.items()}

    # hinder modify_layers_between to be higher than total_layers
    if modify_layers_between[1] > total_layers - top_layer_cap:
        modify_layers_between[1] = total_layers - top_layer_cap
    

    ##################################### generate line modifier, it determines which lines will be modified based on layer modifier
    # generate list of possible indices for layers to be modified
    possible_layers = np.arange(modify_layers_between[0], modify_layers_between[1]+1)
    # list to save layers that will be modified
    modify_layers = []
    
    ### SELCT BY CHANCE
    # select layers to be modified based on modify_layer_chance
    for layer in possible_layers:
        # check if layer will be modified based on modify_layer_chance
        if np.random.random() <= modify_layer_chance:
            # add layer to modify_layers
            modify_layers.append(layer)
            # delete value at index from possible_indices
            possible_layers = np.delete(possible_layers, np.where(possible_layers==layer))

    # amount of layers that will be modified
    amount_of_modified_layers = len(modify_layers)
    # calculate amount of layers missing to reach min_modified_layers
    missing_layers = min_modified_layers - amount_of_modified_layers

    ### SELECT BY MINIMUM
    # select layers to guarantee minimum number of modified layers
    for m in range(missing_layers):
        # check if possible_indices is not empty
        if len(possible_layers) > 0:            
            # pop random index from possible_indices
            choice_layer = np.random.choice(possible_layers)
            # add layer to modify_layers
            modify_layers.append(choice_layer)
            # delete value at index from possible_indices
            possible_layers = np.delete(possible_layers, np.where(possible_layers==choice_layer))            
        else:
            print("Min layers exeeds layer range...all layers between layer range will be modified")
            break

    # sort modify_layers
    modify_layers.sort()
    #print(possible_layers, modify_layers)

    # calculate line boundaries for each layer to be modifid
    modify_lines_between = {layerjumps_lines[x]:layerjumps_lines[x+1] for x in modify_layers}
    #print(modify_lines_between)

    # set -1 as marker for lines NOT to be modified
    line_modifier = [-1] * total_lines
    # initilize counters
    total_modified_lines = 0
    modified_layers = []
    # iterage through file
    for i in range(total_lines):
        # modify lines only between modify_lines
        if is_between_key_pairs(modify_lines_between, i):
            # check line will be modified based on modify_chance
            # calculate extrusion factor and save it in line_modifier
            if np.random.random() <= modify_line_chance:
                # calculate random gaussian value from modify_extrusion_mean and modify_extrusion_std
                extrusion_factor = np.random.normal(modify_extrusion_mean, modify_extursion_std)
                # make modify_extrusion absolute value
                extrusion_factor = abs(extrusion_factor)
                # hinde overextrusion
                if extrusion_factor >= 1:
                    extrusion_factor = 1
                line_modifier[i] = extrusion_factor
                # increase total_modified_lines counter
                total_modified_lines += 1
            # if line will not be modified set line_modifier to 1 meaning original extrusion
            else:
                line_modifier[i] = 1


    ###################################### open file and iterate over lines, also open second file to write modified gcode
    # copy file and rename
    modify_file = gcode[:-6] + modified_file_ending
    modify_filepath = filepath[:-6] + modified_file_ending
    shutil.copy(filepath, modify_filepath)

    with open(filepath, "r") as file, open(modify_filepath, "w") as mod_file:
        line_counter = 0
        prev_extrusion = 0
        make_changes = False
        mod_extrusion = 0
        for line in file:
            line_counter += 1
            # set mod_line to line as default to copy unchanged lines
            mod_line = line
            

            ### line context conditions
            # check if line is perimeter and set make_changes marker to True
            if line.startswith(";TYPE:Internal perimeter") or line.startswith(";TYPE:External perimeter"):
                make_changes = True
            # stop making changes if perimeter ends
            if line.startswith(";WIPE_START"):
                make_changes = False

            ### layerwise conditions
            # check if line to be modified based on line_modifier value
            # (-1 means line will not be modified, other values represent the lines extursion multiplier)
            if line_modifier[line_counter-1] != -1:

                ############################# make changes if make_changes is True
                if make_changes:
                    components = line.split(" ")
                    # check length of components and skip if not long enough (hinder index out of range error for next condition check)
                    if len(components) >= 4:
                        ### contentwise plausibility check
                        # check if line is a G1 command with X, Y and E values
                        if components[0].startswith("G1") and components[1].startswith("X") and components[2].startswith("Y") and components[3].startswith("E"):                    
                            
                            # extract extrusion value
                            extrusion_value = float(components[3].split("E")[1][:-1])
                            # check if next extrusion value is higher than previous and if previous_extrusion is not 0 (first iteration)
                            if extrusion_value > prev_extrusion and prev_extrusion != 0:
                                # calculate extrusion length
                                extrusion_length = extrusion_value - prev_extrusion
                                # round extrusion_length to 5 decimal places
                                extrusion_length = round(extrusion_length, 5)
                                # calculate modified extrusion length
                                mod_extrusion_length = extrusion_length * line_modifier[line_counter]
                                # round mod_extrusion_length to 5 decimal places
                                mod_extrusion_length = round(mod_extrusion_length, 5)


                                # calculate modified extrusion value from previous modified extrusion value and modified extrusion length
                                mod_extrusion = prev_mod_extrusion + mod_extrusion_length

                                # check if debug mode is enabled
                                if debug_mode:
                                    mod_line = "%s %s %s E%f -----Mod rel %f ---- Umod rel %f  abs %f \n" %(components[0], components[1], components[2], mod_extrusion, mod_extrusion_length, extrusion_length, extrusion_value)
                                    
                                else:
                                    # write modified line to mod_line
                                    mod_line = "%s %s %s E%.5f\n" %(components[0], components[1], components[2], mod_extrusion)
                                
                                # set previous extrusion value to current extrusion value for next iteration
                                prev_extrusion = extrusion_value
                                prev_mod_extrusion = mod_extrusion

                            
                            
                            else:
                                # set previous extrusion value to current extrusion value in case of first iteration
                                prev_extrusion = extrusion_value
                                # set previous modified extrusion to real extrusion value in case of first iteration
                                prev_mod_extrusion = extrusion_value



            # write line to modified file
            mod_file.write(mod_line)
            
    print("File: {}\nLayers: {}\nLines: {}\n\nModified Layers: {}\nTotal modified Layers: {}\n\nModified Lines: {}\nTotal modified Lines: {}\n".format(
    gcode, 
    total_layers, 
    line_counter,
    modify_layers,
    len(modify_layers), 
    modify_lines_between,
    total_modified_lines,))

    # save parameters to yaml file
    if generate_macro:
        parameter_ = {  "gcode": modify_file,
                        "class": recording_class,
                        "nozzle": nozzle,
                        "filament": filament,
                        "layer_height": layer_height,
                        "filament_color": filament_color,
                        "ex_mul": modify_extrusion_mean,
                        "extrusion_std": modify_extursion_std,
                        "retraction": 8.5,
                        "shape": "complex",
                        "modified_layers":str(modify_layers),
                        "recording": None,
                        "printbed_color": printbed_color,
                    }

        savefile = makrodir + "/" + dirname + ".yaml"
        df.extend_yaml(savefile, parameter_)

    # delete original file
    if delete_unmodified_gcode:
        os.remove(filepath)
                        
