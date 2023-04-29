import os, sys
import dataset_functions as df
import shutil


currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
gcodedir = currentdir + "/gcode"


######################################### EINGABEN

dirname = "modifier_test"
makrodir = "%s/%s" %(gcodedir, dirname)

# the layer between the indices will be modified
modify_layers_between = [4,8]

# the extrusion will be multiplied by this value
modify_extrusion = 0.2

# sets the filename ending of the modified gcode file
modified_file_ending = "_modified.gcode"


######################################### START SCRIPT
# find all gcode files in makrodir
f = []
for (dirpath, dirnames, filenames) in os.walk(makrodir):
    f.extend(filenames)
    break
f = [x for x in f if x.endswith(".gcode")] 
f = [x for x in f if not x.endswith(modified_file_ending)]
# sort f alphabetically
f.sort()

########################################## iterate over all gcode files
for gcode in f:
    # generat full filepath
    filepath = "%s/%s" %(makrodir, gcode)    
    # get layerjumps in the file
    layerjumps = df.get_layerjump(filepath)
    layerjumps_lines = layerjumps["lines"]
    total_lines = layerjumps["total"]["lines"]
    # invert keys and values of layerjumps_lines
    layerjumps_lines = {v: k for k, v in layerjumps_lines.items()}
    # calculate layerjump lines from 2
    modify_lines_between = [layerjumps_lines[x] for x in modify_layers_between]
    #print(modify_lines)
 

    ###################################### open file and iterate over lines, also open second file to write modified gcode
    # copy file and rename
    modify_file = filepath[:-6] + modified_file_ending
    shutil.copy(filepath, modify_file)

    with open(filepath, "r") as file, open(modify_file, "w") as mod_file:
        line_counter = 0
        prev_extrusion = 0
        make_changes = False
        mod_extrusion = 0
        for line in file:
            line_counter += 1
            # set mod_line to line as default to copy unchanged lines
            mod_line = line
            
            ### layerwise conditions
            # check if line is in modify_lines
            if line_counter >= modify_lines_between[0] and line_counter <= modify_lines_between[1]:
                
                ### line context conditions
                # check if line is perimeter and set make_changes marker to True
                if line.startswith(";TYPE:Internal perimeter") or line.startswith(";TYPE:External perimeter"):
                    make_changes = True
                # stop making changes if perimeter ends
                if line.startswith(";WIPE_START"):
                    make_changes = False
                


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
                                mod_extrusion_length = extrusion_length * modify_extrusion
                                # round mod_extrusion_length to 5 decimal places
                                mod_extrusion_length = round(mod_extrusion_length, 5)


                                # calculate modified extrusion value from previous modified extrusion value and modified extrusion length
                                mod_extrusion = prev_mod_extrusion + mod_extrusion_length


                                #mod_line = "%s %s %s E%f --------------\n" %(components[0], components[1], components[2], mod_extrusion)
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
            
    print("File: %s\nLines: %i\nLayers: %i" %(gcode, line_counter, layerjumps["total"]["layers"]))
                    
