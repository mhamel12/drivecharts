# ========================================================================
#
# dc.py
#
# Drive chart generator for Python
#
# Creative Commons license: http://creativecommons.org/licenses/by-nc-sa/4.0/
# Attribution-NonCommercial-ShareAlike 4.0 International
#
# 11/09/2022  Rev 1.6  Changes to work with matplotlib 3.6.2 and Python 3.10.8
# 04/09/2022  Rev 1.5  Fix how negative drives are drawn.
# 04/04/2022  Rev 1.4  Move drive box text for drives starting inside the team's 10 yard line. Also enlarge end zone text.
# 04/03/2022  Rev 1.3  Cleanup and support for custom strings in drive input files
# 03/31/2022  Rev 1.2  Text in drive box now includes (plays-yds time), added color codes for all teams
# 03/30/2022  Rev 1.1  Added triangles to indicate drive direction
# 03/28/2022  Rev 1.0  Initial version
#
# ========================================================================

import argparse
from collections import defaultdict
import re

# https://matplotlib.org/stable/users/getting_started/
# Note that I had to upgrade pyparsing on my PC in order for matplotlib to install: pip install pyparsing==2.4.7
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np # added for drawing triangles

# ========================================================================
# Text-based drive chart functions, useful for comparison/debugging of the 
# graphical charts.
#

DC_PREFIX = " Q TM      P-YD TIME [START] "
DC_PREFIX_WIDTH = len(DC_PREFIX)
FIELD_HEADER = "....'....|....'....|....'....|....'....|....'....|....'....|....'....|....'....|....'....|....'...."
FIELD_HEADER_WIDTH = len(FIELD_HEADER)
YDMRK_HEADER = "        1 0       2 0       3 0       4 0       5 0       4 0       3 0       2 0       1 0        "

def get_header_field_string(r_abbrev,h_abbrev):
    field="%s%s%s%s" % (DC_PREFIX,h_abbrev,FIELD_HEADER,r_abbrev)
    return (field)    

def get_yard_marker_field_string(h_abbrev):
    field="%s%s" % (" " * (DC_PREFIX_WIDTH + len(h_abbrev)),YDMRK_HEADER)
    return (field) 
    
def get_result_abbrev(result):
    if result == "Field Goal": # F would conflict with Fumble
        return "G"
    elif result == "End of Half": # E would conflict with End of Game (in OT games, the end of the 4th Quarter is also listed as "End of Half")
        return "H"
    return(result[:1]) # by default, return first letter of the result string
    
def get_net_yards_as_string(net_yards_as_int):
    if net_yards_as_int >= 0:
        net_yards_as_string = str(net_yards_as_int)
    else:
        net_yards_as_string = "(" + str(abs(net_yards_as_int)) + ")"    
    return(net_yards_as_string)
    
def get_dc_string(offensive_team_abbrev,home_team_abbrev,plays,net_yards_as_int,quarter,drive_length_in_time,start_time_of_drive,starting_yard_line,ending_yard_line,result):

    #print(offensive_team_abbrev)
    #print(home_team_abbrev)
    #print(plays)
    #print(net_yards_as_int)
    #print(quarter)
    #print(drive_length_in_time)
    #print(start_time_of_drive)
    #print(starting_yard_line)
    #print(ending_yard_line)
    #print(result)

    net_yards_as_string = get_net_yards_as_string(net_yards_as_int)
        
    # PP: ##-#### ##:## [##:## - ##:##] 
    summary = plays + "-" + net_yards_as_string

    prefix_width = DC_PREFIX_WIDTH + len(home_team_abbrev) - 1 # assume this abbrev was also passed to get_header_field_string()
    raw_field = "%2s %2s: %7s %4s [%4s]" % (quarter,offensive_team_abbrev,summary,drive_length_in_time,start_time_of_drive)
    raw_field = raw_field + " " * (len(home_team_abbrev) + FIELD_HEADER_WIDTH + len(home_team_abbrev))

    if int(plays) > 0:

        number_of_dashes = abs(int(ending_yard_line) - int(starting_yard_line)) - 1
        
        if (offensive_team_abbrev == home_team_abbrev): # Drives move left to right
            left_pos_loc = int(starting_yard_line) + prefix_width
            right_pos_loc = int(ending_yard_line) + prefix_width
            if (int(ending_yard_line) >= int(starting_yard_line)): # normal case
                d_field = ">" + ("-" * number_of_dashes) + "%1s" % (get_result_abbrev(result))
            else: # went backwards...
                d_field = "%1s" % (get_result_abbrev(result)) + ("-" * number_of_dashes) + ">"
        else: # right to left
            right_pos_loc = int(starting_yard_line) + prefix_width
            left_pos_loc = int(ending_yard_line) + prefix_width
            if (int(starting_yard_line) >= int(ending_yard_line)): # normal case
                d_field = "%1s" % (get_result_abbrev(result)) + ("-" * number_of_dashes) + "<"
            else: # went backwards...
                d_field =  "<" + ("-" * number_of_dashes) + "%1s" % (get_result_abbrev(result))
        
        dc_string=raw_field[:left_pos_loc] + d_field + raw_field[(right_pos_loc+1):]
        
    else: # empty drive, likely a kickoff at end of game or half
        d_field = ""
        dc_string=raw_field
        
    return(dc_string)  
    
# ========================================================================
# Functions for graphical drive chart output
#

# To scale the horizontal axis, set a relationship between pixels and yards
pixels_per_yard = 2
def yds2px(yards):
    return(yards * pixels_per_yard)

# NFL field dimensions
# https://static.nfl.com/static/content/public/image/rulebook/pdfs/4_Rule1_The_Field.pdf
# 360 feet long (120 yards)
# 160 feet wide (53.333 yards)
# Outside border around field is minimum of 6 feet (2 yards)
# Yard lines every 5 yards are to stop 8 inches before the 6-foot border.
# Yardage numbers start 12 yards from the 6-foot border and need to be 2 yards long.
field_width = yds2px(120)
height_of_drive_box = 8 # was 5 when pixels_per_yard = 1. The get_triangle_coords() function now assumes this is an even number.
space_between_drive_boxes = 4 # was 2 for pixels_per_yard = 1
field_borders = yds2px(3)
# This is supposed to be 12 yards, but on a drive chart that takes up a lot of room.
yd_mrk_distance_from_border = 2
yardage_marker_height = 10 # was 4 when pixels_per_yard = 1

def get_dc_result_abbrev(result):
    if result == "Field Goal":
        return "FG"
    elif result == "Missed FG":
        return "MISS FG"
    elif result == "Touchdown":
        return "TD"
    elif result == "Interception": # If the interception leads to a Pick 6, this will not show the resulting TD
        return "INT"
    elif result == "Fumble":
        return "FUM"
    elif result == "Punt":
        return "PUNT"
    elif result == "End of Half":
        return "HALF"
    elif result == "End of Game":
        return "END"
    elif result == "Downs":
        return "DOWNS"
    elif result == "Safety":
        return "SAF"
    return(result[:1]) # by default, return first letter of the result string
    
# TBD: Only need some of these parameters but will include all for now to match get_dc_string()
# Returns lefthand yardage line - not including borders and end zone - plus the width of the box we need.
# This function does NOT adjust the width based on the pixels_per_yard. The caller must do that adjustment. 
def get_dc_coords(offensive_team_abbrev,home_team_abbrev,plays,net_yards_as_int,quarter,drive_length_in_time,start_time_of_drive,starting_yard_line,ending_yard_line,result):

    #print(offensive_team_abbrev)
    #print(home_team_abbrev)
    #print(plays)
    #print(net_yards_as_int)
    #print(quarter)
    #print(drive_length_in_time)
    #print(start_time_of_drive)
    #print(starting_yard_line)
    #print(ending_yard_line)
    #print(result)

    if int(plays) > 0:

        # unlike text version, we do not need space for a result and a ">" or "<" at start of drive
        width = abs(int(ending_yard_line) - int(starting_yard_line)) + 1 
        
        if (offensive_team_abbrev == home_team_abbrev): # Drives move left to right
            if net_yards_as_int >= 0:
                left = int(starting_yard_line)
            else:
                left = int(starting_yard_line) + net_yards_as_int
        else: # right to left
            if net_yards_as_int >= 0:
                left = int(ending_yard_line)
            else:
                left = int(ending_yard_line) + net_yards_as_int
        
    else: # empty drive, likely a kickoff at end of game or half, so will draw nothing for this
        left = 0
        width = 0
        
    return(left, width)
    

# Arrow will point in the "direction" passed in (left or right)
# The box_y_coord is the bottom of the drive box
# The box_x_coord is either the left-hand x coordinate or the right-hand x coordinate of the drive box
def get_triangle_coords(direction,box_x_coord,box_y_coord,box_height,width):
    # Create a horizontal spacer between the box and the arrow
    if direction == "left":
        x = box_x_coord - 1
    else: # right
        x = box_x_coord + 1

    # The arrows look better if we shrink the height by 2 pixels and add 1 to the y coordinate,
    # in order to center the arrow. This assumes that the box height is an EVEN number.
    y = box_y_coord + 1
    height = box_height - 2
    
    t_left = (x, y)
    if direction == "left":
        t_right = (x - (width/2), y + (height/2))
    else:
        t_right = (x + (width/2), y + (height/2))
    t_top = (x, y + height)    
    t_points = np.array([t_left,t_right,t_top])
    return(t_points)

    
# ========================================================================
# Functions for loading and manipulating simple drive data.
# Data can be obtained in .csv format from the Pro Football Reference
# box score pages.
#

def read_drive_datafile(the_file,r,h,team_home_or_road,offensive_team):
    drive_array = []
    with open(the_file,'r') as ifile:
        for line in ifile:
            # .csv format assumed to be: Drive#,Quarter,Time,LOS,Plays,Length,Net Yds,Result
            # User can also append an extra column of optional commentary
            if len(line) > 0 and ("Quarter" not in line) and line.count(",") >= 7:
                # Calculate elapsed time at start of drive                
                quarter = int(line.split(",")[1])
                clock_time = line.split(",")[2]
                # assume 15 minute quarters, but this also works for 10 minute overtime periods if we use it only for sorting purposes
                elapsed_time_from_start_of_game_in_seconds = (15*60*quarter) - ((int(clock_time.split(":")[0]) * 60) + int(clock_time.split(":")[1]))
                
                # Calculate field position at start and end of drive based on a 0 to 100 scale (left-to-right)
                plays = line.split(",")[4]
                starting_field_position = line.split(",")[3]
                
                # In SB51 there was just a kickoff before halftime which resulted in a zero-play drive with no line of scrimmage info
                # In SB49 there was a drive that started at midfield, and PFR listed the LOS as blank.
                if int(plays) > 0:

                    if len(starting_field_position) > 0:
                        starting_field_team = starting_field_position.split(" ")[0]
                        starting_field_yard_line = starting_field_position.split(" ")[1]
                        if starting_field_team == h:
                            adjusted_starting_yard_line = int(starting_field_yard_line)
                        else:
                            adjusted_starting_yard_line = 100 - int(starting_field_yard_line)
                    else: # assume midfield for now
                        adjusted_starting_yard_line = 50
                        
                    net_yards = line.split(",")[6]

                    if team_home_or_road == "HOME": # draw drives left-to-right
                        adjusted_ending_yard_line = adjusted_starting_yard_line + int(net_yards)
                    else: # draw drives right-to-left
                        adjusted_ending_yard_line = adjusted_starting_yard_line - int(net_yards)
                        
                else: # Zero-play drive
                    adjusted_starting_yard_line = -1
                    adjusted_ending_yard_line = -1

                line = line.strip()
                if line.count(",") == 7:
                    # There is no optional comment on this .csv line, so append a comma at the end to 
                    # create an empty column. But need to strip off the line ending (Newline, CR, LF, etc.) first.
                    line = line + ","

                # In the drive array, store the entire .csv line from the file, plus some additional data.                    
                # Note that the "#" column reflects the number of drives by the offensive_team
                #        0 1       2    3   4     5      6       7      8
                # line = #,Quarter,Time,LOS,Plays,Length,Net Yds,Result,OptionalComment
                #                                           9              10                                          11                          12                       
                new_line = "%s,%s,%s,%s,%s" % (line,offensive_team,elapsed_time_from_start_of_game_in_seconds,adjusted_starting_yard_line,adjusted_ending_yard_line)
                drive_array.append(new_line)
    
    ifile.close()
    return drive_array
    
# Brute-force merging of two drive arrays into a single array, sorted by the
# starting time of the drive.
COL_FOR_LENGTH_OF_DRIVE_IN_TIME = 5
COL_FOR_ELAPSED_TIME_SINCE_START_OF_GAME = 10
def merge_drive_arrays(d1,d2):
    d_merged = []
    d1_index = d2_index = 0
    d1_len = len(d1)
    d2_len = len(d2)
    
    while d1_index < d1_len or d2_index < d2_len:
        if d1_index < d1_len and d2_index < d2_len:
            d1_elapsed_time = int(d1[d1_index].split(",")[COL_FOR_ELAPSED_TIME_SINCE_START_OF_GAME])
            d2_elapsed_time = int(d2[d2_index].split(",")[COL_FOR_ELAPSED_TIME_SINCE_START_OF_GAME])
#            print("Time %s vs. %s" % (d1_elapsed_time,d2_elapsed_time))
            if d1_elapsed_time < d2_elapsed_time:
                d_merged.append(d1[d1_index])
                d1_index += 1
            elif d1_elapsed_time > d2_elapsed_time:
                d_merged.append(d2[d2_index])
                d2_index += 1
            else: # times are an exact match, assume that one team had a drive that lasted zero seconds
                d1_drive_time = d1[d1_index].split(",")[COL_FOR_LENGTH_OF_DRIVE_IN_TIME]
                d2_drive_time = d2[d2_index].split(",")[COL_FOR_LENGTH_OF_DRIVE_IN_TIME]
                if d1_drive_time == "0:00":
                    d_merged.append(d1[d1_index])
                    d1_index += 1                    
                elif d2_drive_time == "0:00":
                    d_merged.append(d2[d2_index])
                    d2_index += 1
                else:
                    print("Two drives found lasting two seconds - exiting")
                    quit()
        else: # drain whichever array still contains drive info
            while d1_index < d1_len:
                d_merged.append(d1[d1_index])
                d1_index += 1
            while d2_index < d2_len:
                d_merged.append(d2[d2_index])
                d2_index += 1
                
    return d_merged

# ========================================================================    
# Main
    
parser = argparse.ArgumentParser(description='Create Drive Charts from drive data or play-by-play data.') 
parser.add_argument('teams', help="Team abbreviations separated by commas (Road,Home)")
parser.add_argument('-drivedata', '-d', help="Drive data filenames separated by commas (Road,Home). These can be obtained from the Pro Football Reference box score pages.")
parser.add_argument('-exchangecolor', '-e', help="Exchange primary and secondary colors for this team (abbrevation needs to match one of the two teams)")
# TBD Add a -p option for play-by-play data file?
# TBD Maybe add a -s option for scoring play summary, but PFR does not provide option to export this as .csv
args = parser.parse_args()

if args.drivedata:
    road_drive_datafile = args.drivedata.split(",")[0]
    home_drive_datafile = args.drivedata.split(",")[1]
else:
    print("Must specify drive data files")
    
road_abbrev = args.teams.split(",")[0]
home_abbrev = args.teams.split(",")[1]

print("%s,%s,%s,%s" % (road_drive_datafile,home_drive_datafile,road_abbrev,home_abbrev))

road_drive_data = read_drive_datafile(road_drive_datafile,road_abbrev,home_abbrev,"ROAD",road_abbrev)
home_drive_data = read_drive_datafile(home_drive_datafile,road_abbrev,home_abbrev,"HOME",home_abbrev)

# print("ROAD: %s" % (road_drive_data))
# print("HOME: %s" % (home_drive_data))

merged_drive_data = merge_drive_arrays(road_drive_data,home_drive_data)

#for d in merged_drive_data:
#    print("%s" % (d))
#print("\n")

# Print a cleaner table for use alongside the graphical file.
print("Team,Q,StartTime,StartYardline,Plays,Time,Yards,Result")
for d in merged_drive_data:
    print("%s,%s" % (d.split(",")[9],','.join(d.split(",")[1:8])))
print("\n")
    
print("%s" % ( get_yard_marker_field_string(home_abbrev)))
print("%s" % (get_header_field_string(road_abbrev,home_abbrev)))
for d in merged_drive_data:  
    # args = offensive_team_abbrev,home_team_abbrev,plays,net_yards_as_int,quarter,drive_length_in_time,start_time_of_drive,starting_yard_line,ending_yard_line,result
    dc_line = get_dc_string(d.split(",")[9],home_abbrev,d.split(",")[4],int(d.split(",")[6]),d.split(",")[1],d.split(",")[5],d.split(",")[2],d.split(",")[11],d.split(",")[12],d.split(",")[7])
    print("%s" % (dc_line))
    
# Set this based on the number of drives, with a minimum height of 58 yards = 54 + 2 + 2
# Need enough room to fit all of the drives in between the yardage markers.
# Keep in mind that we drop "ghost drives" on the floor - drives that are zero yards in 
# length, so we can end up with some extra space at the bottom (this happens in SB51, for example).

number_of_drives = len(merged_drive_data)
# print("Number=%d" % (number_of_drives))
field_height = (number_of_drives * (height_of_drive_box + space_between_drive_boxes)) + (2 * (yd_mrk_distance_from_border + yardage_marker_height)) + space_between_drive_boxes # was 54
if field_height < 58:
    field_height = 58
field_height_with_borders = field_height + (field_borders * 2)

# 120 yards + 2 yard border all around + 1 yard black border all around
field_width_with_borders = field_width + (field_borders * 2) + 1

# I am having trouble getting the yardage markers to look good on the field. I am hoping
# that making the proportions of the figure size match the proportions of the field will help,
# but they look a little squished and the yardline runs into the numbers.
figure_size_width = 7 * pixels_per_yard
figure_size_height = int((field_height_with_borders / field_width_with_borders) * 7)
# print("w=%d (fw=%d), h=%d (fh=%d)" % (field_width_with_borders,figure_size_width,field_height_with_borders,figure_size_height))

# This is currently built-in to get_triangle_coords(): height_of_drive_arrows = height_of_drive_box - 1
width_of_drive_arrows = height_of_drive_box * (field_width_with_borders / field_height_with_borders)

fig, ax = plt.subplots(figsize=(figure_size_width, figure_size_height)) # default is 6.8 inches by 4.6 inches? with dpi=100
ax.set_xlim([0,field_width_with_borders+1]) # I had trouble with the outer black border looking "solid" unless I added 1 to both of these limits.
ax.set_ylim([0,field_height_with_borders+1]) 

# Mapping of team abbrevations used by Pro Football Reference to team nicknames.
# These are designed to cover the Tom Brady era (2000-).
team_nicknames = { 'NWE' : "Patriots",
                   'BAL' : "Ravens",
                   'BUF' : "Bills",
                   'CIN' : "Bengals",
                   'CLE' : "Browns",
                   'DEN' : "Broncos", 
                   'HOU' : "Texans",
                   'IND' : "Colts",
                   'JAX' : "Jaguars",
                   'KAN' : "Chiefs",
                   'LAC' : "Chargers", 'SDG' : "Chargers",
                   'LVR' : "Raiders", 'OAK' : "Raiders",
                   'MIA' : "Dolphins",
                   'NYJ' : "Jets",
                   'PIT' : "Steelers",
                   'TEN' : "Titans",
                   'ARI' : "Cardinals",
                   'ATL' : "Falcons",
                   'CAR' : "Panthers",
                   'CHI' : "Bears",
                   'DAL' : "Cowboys",
                   'DET' : "Lions",
                   'GNB' : "Packers",
                   'LAR' : "Rams", 'STL' : "Rams",
                   'MIN' : "Vikings",
                   'NOR' : "Saints",
                   'NYG' : "Giants",
                   'PHI' : "Eagles",
                   'SEA' : "Seahawks",
                   'SFO' : "49ers",
                   'TAM' : "Buccaneers",
                   'WAS' : "Commanders", # 2022 and beyond
                 }

# Mapping of team abbrevations used by Pro Football Reference to team colors.
#
# The first dictionary are the primary colors, which are the defaults for the
# end zones and the drive boxes.
#
# The second dictionary are the secondary colors, which are the defaults for
# the team names in the end zones and the outline of the drive boxes.
#
# If the primary colors for the two teams are similar, the "exchangecolor" argument
# gives us a work-around where the secondary color will be used in place of the
# primary color.
#
# If any team uses white as a primary or secondary color, it would hide our 
# default text, so we avoid this case for now. TBD if we want to try to use
# the team secondary color as a backup text color.

# https://matplotlib.org/stable/tutorials/colors/colors.html
# https://teamcolorcodes.com/nfl-team-color-codes/
primary_team_colors = { 'NWE' : '#002244',
                        'BAL' : '#241773',
                        'BUF' : '#00338D',
                        'DEN' : '#FB4F14',
                        'MIA' : '#008E97',
                        'NYJ' : '#125740',
                        'CIN' : '#FB4F14',
                        'CLE' : '#311D00',
                        'HOU' : '#03202F',
                        'IND' : '#002C5F',
                        'JAX' : '#D7A22A', # could also be black (101820)
                        'KAN' : '#E31837',
                        'LAC' : '#0080C6', 'SDG' : '#0080C6',
                        'LVR' : '#000000', 'OAK' : '#000000',
                        'PIT' : '#101820',
                        'TEN' : '#0C2340',
                        'ARI' : '#97233F',
                        'ATL' : '#A71930',
                        'CAR' : '#0085CA',
                        'CHI' : '#0B162A',
                        'DAL' : '#041E42',
                        'DET' : '#0076B6',
                        'GNB' : '#203731',
                        'LAR' : '#003594', 'STL' : '#002244',
                        'MIN' : '#4F2683',
                        'NYG' : '#0B2265',
                        'NOR' : '#101820',
                        'PHI' : '#004C54',
                        'SEA' : '#002244', # same as NWE
                        'SFO' : '#AA0000',
                        'TAM' : '#FF7900', # Or Red: '#D50A0A',
                        'WAS' : '#5A1414',
                      }
secondary_team_colors = { 'NWE' : '#B0B7BC',
                          'BAL' : '#9E7C0C',
                          'BUF' : '#C60C30',
                          'CIN' : '#000000',
                          'CLE' : '#FF3C00',
                          'DEN' : '#002244',
                          'HOU' : '#A71930',
                          'IND' : '#A2AAAD',
                          'JAX' : '#006778',
                          'KAN' : '#FFB81C',
                          'LAC' : '#FFC20E', 'SDG' : '#FFC20E',
                          'LVR' : '#A5ACAF', 'OAK' : '#A5ACAF',
                          'MIA' : '#FC4C02',
                          'NYJ' : '#000000', # Should be white so could make this gray
                          'PIT' : '#FFB612',
                          'TEN' : '#4B92DB',
                          'ARI' : '#000000',
                          'ATL' : '#000000',
                          'CAR' : '#101820',
                          'CHI' : '#C83803',
                          'DAL' : '#869397',
                          'DET' : '#B0B7BC',
                          'GNB' : '#FFB612',
                          'LAR' : '#FFA300', 'STL' : '#866D4B',
                          'MIN' : '#FFC62F',
                          'NOR' : '#D3BC8D',
                          'NYG' : '#A71930',
                          'PHI' : '#ACC0C6',
                          'SEA' : '#69BE28',
                          'SFO' : '#B3995D',
                          'TAM' : '#34302B',
                          'WAS' : '#FFB612',
                        }

home_team_primary_color = primary_team_colors[home_abbrev]
home_team_secondary_color = secondary_team_colors[home_abbrev]
road_team_primary_color = primary_team_colors[road_abbrev]
road_team_secondary_color = secondary_team_colors[road_abbrev]

# This argument provides flexibility for cases where the primary colors for
# the two teams are either the same or very similar, so the secondary color
# provides better contrast and creates an easier-to-follow drive chart.
if args.exchangecolor:
    if args.exchangecolor == home_abbrev:
        temp_color = home_team_primary_color
        home_team_primary_color = home_team_secondary_color
        home_team_secondary_color = temp_color
    elif args.exchangecolor == road_abbrev:
        temp_color = road_team_primary_color
        road_team_primary_color = road_team_secondary_color
        road_team_secondary_color = temp_color

                        
# ---- Draw the football field

                                                           # First four args = (left, bottom), width, height
home_endzone_rectangles = { team_nicknames[home_abbrev].upper() : patches.Rectangle((field_borders,field_borders),yds2px(10),field_height, facecolor=home_team_primary_color) } # was facecolor='silver'
                       
for r in home_endzone_rectangles:
    ax.add_artist(home_endzone_rectangles[r])
    rx, ry = home_endzone_rectangles[r].get_xy()
    cx = rx + home_endzone_rectangles[r].get_width()/2.0
    cy = ry + home_endzone_rectangles[r].get_height()/2.0
    ax.annotate(r, (cx, cy), color=home_team_secondary_color, weight='bold', 
                fontsize=30, ha='center', va='center', rotation=90) # used 16 with pixels_per_yard = 1
    # Reference: https://matplotlib.org/stable/tutorials/text/text_props.html                
                
road_endzone_rectangles = { team_nicknames[road_abbrev].upper() : patches.Rectangle((yds2px(111)+field_borders,field_borders),yds2px(10),field_height, facecolor=road_team_primary_color) }
                       
for r in road_endzone_rectangles:
    ax.add_artist(road_endzone_rectangles[r])
    rx, ry = road_endzone_rectangles[r].get_xy()
    cx = rx + road_endzone_rectangles[r].get_width()/2.5 # This is not a typo. I find that 270-degree rotated text tends to be rendered off-center (too far to the right) so I adjust the cx coord to shift it back to the left.
    cy = ry + road_endzone_rectangles[r].get_height()/2.0
    ax.annotate(r, (cx, cy), color=road_team_secondary_color, weight='bold', 
                fontsize=30, ha='center', va='center', rotation=270) # used 16 with pixels_per_yard = 1
                
# Note the tweak to the "bottom" and "height" coordinates. When I tried to place the border at 0,0,... the bottom line looked too thin.                
field_rectangles = { 'outerborder' : patches.Rectangle((0,1),field_width_with_borders,field_height_with_borders-1, facecolor='none', linewidth=1, edgecolor='black'),
                     'h0to5' : patches.Rectangle((field_borders+yds2px(11),field_borders),yds2px(4),field_height, facecolor='green'),
                     'h5to10' : patches.Rectangle((field_borders+yds2px(16),field_borders),yds2px(4),field_height, facecolor='green'),
                     'h10to15' : patches.Rectangle((field_borders+yds2px(21),field_borders),yds2px(4),field_height, facecolor='green'),
                     'h15to20' : patches.Rectangle((field_borders+yds2px(26),field_borders),yds2px(4),field_height, facecolor='green'),
                     'h20to25' : patches.Rectangle((field_borders+yds2px(31),field_borders),yds2px(4),field_height, facecolor='green'),
                     'h25to30' : patches.Rectangle((field_borders+yds2px(36),field_borders),yds2px(4),field_height, facecolor='green'),
                     'h30to35' : patches.Rectangle((field_borders+yds2px(41),field_borders),yds2px(4),field_height, facecolor='green'),
                     'h35to40' : patches.Rectangle((field_borders+yds2px(46),field_borders),yds2px(4),field_height, facecolor='green'),
                     'h40to45' : patches.Rectangle((field_borders+yds2px(51),field_borders),yds2px(4),field_height, facecolor='green'),
                     'h45to50' : patches.Rectangle((field_borders+yds2px(56),field_borders),yds2px(4),field_height, facecolor='green'),
                     'r50to45' : patches.Rectangle((field_borders+yds2px(61),field_borders),yds2px(4),field_height, facecolor='green'),
                     'r45to40' : patches.Rectangle((field_borders+yds2px(66),field_borders),yds2px(4),field_height, facecolor='green'),
                     'r40to35' : patches.Rectangle((field_borders+yds2px(71),field_borders),yds2px(4),field_height, facecolor='green'),
                     'r35to30' : patches.Rectangle((field_borders+yds2px(76),field_borders),yds2px(4),field_height, facecolor='green'),
                     'r30to25' : patches.Rectangle((field_borders+yds2px(81),field_borders),yds2px(4),field_height, facecolor='green'),
                     'r25to20' : patches.Rectangle((field_borders+yds2px(86),field_borders),yds2px(4),field_height, facecolor='green'),
                     'r20to15' : patches.Rectangle((field_borders+yds2px(91),field_borders),yds2px(4),field_height, facecolor='green'),
                     'r15to10' : patches.Rectangle((field_borders+yds2px(96),field_borders),yds2px(4),field_height, facecolor='green'),
                     'r10to5' : patches.Rectangle((field_borders+yds2px(101),field_borders),yds2px(4),field_height, facecolor='green'),
                     'r5to0' : patches.Rectangle((field_borders+yds2px(106),field_borders),yds2px(4),field_height, facecolor='green'),
                   }                

for r in field_rectangles:
    ax.add_artist(field_rectangles[r])                   

# The 9's here are based on placing a box in between two successive 5-yd lines (4 + 1 + 4) such that the
# yardage marker is centered in between. On real NFL fields, you can see the yardage line in between the 
# "X" and the "0" but I think that would be harder to read than the format I have chosen here.
bottom_coord_for_yardage_markers = field_borders + yd_mrk_distance_from_border
yardage_markers = { '<10' : patches.Rectangle((field_borders+yds2px(16),bottom_coord_for_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                    '<20' : patches.Rectangle((field_borders+yds2px(26),bottom_coord_for_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                    '<30' : patches.Rectangle((field_borders+yds2px(36),bottom_coord_for_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                    '<40' : patches.Rectangle((field_borders+yds2px(46),bottom_coord_for_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                    '50' : patches.Rectangle((field_borders+yds2px(56),bottom_coord_for_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                    '40>' : patches.Rectangle((field_borders+yds2px(66),bottom_coord_for_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                    '30>' : patches.Rectangle((field_borders+yds2px(76),bottom_coord_for_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                    '20>' : patches.Rectangle((field_borders+yds2px(86),bottom_coord_for_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                    '10>' : patches.Rectangle((field_borders+yds2px(96),bottom_coord_for_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                  }
 
for r in yardage_markers:
    ax.add_artist(yardage_markers[r])
    rx, ry = yardage_markers[r].get_xy()
    cx = rx + yardage_markers[r].get_width()/2.0
    cy = ry + yardage_markers[r].get_height()/2.0
    ax.annotate(r, (cx, cy), color='w', weight='bold', 
                fontsize=10, ha='center', va='center')

bottom_coord_for_top_yardage_markers = field_height_with_borders-field_borders - yd_mrk_distance_from_border - yardage_marker_height
top_yardage_markers = { '10>' : patches.Rectangle((field_borders+yds2px(16),bottom_coord_for_top_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                    '20>' : patches.Rectangle((field_borders+yds2px(26),bottom_coord_for_top_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                    '30>' : patches.Rectangle((field_borders+yds2px(36),bottom_coord_for_top_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                    '40>' : patches.Rectangle((field_borders+yds2px(46),bottom_coord_for_top_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                    '50' : patches.Rectangle((field_borders+yds2px(56),bottom_coord_for_top_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                    '<40' : patches.Rectangle((field_borders+yds2px(66),bottom_coord_for_top_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                    '<30' : patches.Rectangle((field_borders+yds2px(76),bottom_coord_for_top_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                    '<20' : patches.Rectangle((field_borders+yds2px(86),bottom_coord_for_top_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                    '<10' : patches.Rectangle((field_borders+yds2px(96),bottom_coord_for_top_yardage_markers),yds2px(9),yardage_marker_height, facecolor='green'),
                  }
 
for r in top_yardage_markers:
    ax.add_artist(top_yardage_markers[r])
    rx, ry = top_yardage_markers[r].get_xy()
    cx = rx + top_yardage_markers[r].get_width()/2.0
    cy = ry + top_yardage_markers[r].get_height()/2.0
    ax.annotate(r, (cx, cy), color='w', weight='bold', 
                fontsize=10, ha='center', va='center', rotation=180)


# ---- Create drive boxes

# Do home and road separately for now, so we can align text accordingly.
home_team_drives = {}
road_team_drives = {}
dashed_quarter_lines = {}
triangle_markers = {}
home_team_drive_count = 0
road_team_drive_count = 0
y_coord_for_drive_box = field_height_with_borders - field_borders - yd_mrk_distance_from_border - yardage_marker_height - space_between_drive_boxes - height_of_drive_box

this_quarter = 1
for d in merged_drive_data:
    if int(d.split(",")[4]) > 0:
        quarter = int(d.split(",")[1])
        start_time_of_drive = d.split(",")[2]
        plays = int(d.split(",")[4])
        length_in_time = d.split(",")[5]
        net_yards = int(d.split(",")[6])
        net_yards_as_string = get_net_yards_as_string(net_yards)
        result_of_drive = d.split(",")[7]
        optional_comment = d.split(",")[8]
        offensive_team_abbrev = d.split(",")[9]
        starting_yard_line = d.split(",")[11]
        ending_yard_line = d.split(",")[12]
        (left_coord,width_of_drive_box) = get_dc_coords(offensive_team_abbrev,home_abbrev,plays,net_yards,quarter,length_in_time,start_time_of_drive,starting_yard_line,ending_yard_line,result_of_drive)

        # Draw a line between each quarter. The lines break up the chart into pieces that are organized by the quarter in which each drive began.
        if quarter > this_quarter:
            quarter_line_name = "Q" + "%d" % this_quarter
            y_coord_for_drive_box += (height_of_drive_box + (space_between_drive_boxes/2))
            dashed_quarter_lines[quarter_line_name] = patches.Rectangle((1, y_coord_for_drive_box), field_width + (field_borders * 2) - 1, 0, linestyle="--", edgecolor='black')
            y_coord_for_drive_box -= (height_of_drive_box + (space_between_drive_boxes/2))
            this_quarter = quarter
        
        # Note on "hatch" patterns that are used for drives that lose yards.
        # Repeating the pattern more than once increases the density of the hatching.
        # See: https://matplotlib.org/stable/api/_as_gen/matplotlib.patches.Patch.html#matplotlib.patches.Patch.set_hatch
        
        if offensive_team_abbrev == home_abbrev:
            drive_name = "home" + str(home_team_drive_count) + "_" + get_dc_result_abbrev(result_of_drive) + "_" + "%d-%s %s" % (plays,net_yards_as_string,length_in_time) + "_" + optional_comment
            home_team_drive_count += 1
            if net_yards < 0: # use hatch='///' in the patches.Rectangle call to denote drives that lose yards.
                home_team_drives[drive_name] = patches.Rectangle((field_borders+yds2px(10)+yds2px(left_coord), y_coord_for_drive_box), yds2px(width_of_drive_box), height_of_drive_box, facecolor=home_team_primary_color, linewidth=2, edgecolor=home_team_secondary_color, hatch='////')
            else:
                home_team_drives[drive_name] = patches.Rectangle((field_borders+yds2px(10)+yds2px(left_coord), y_coord_for_drive_box), yds2px(width_of_drive_box), height_of_drive_box, facecolor=home_team_primary_color, linewidth=2, edgecolor=home_team_secondary_color)
            
            triangle_markers[drive_name] = patches.Polygon(get_triangle_coords("right",field_borders+yds2px(10+left_coord+width_of_drive_box),y_coord_for_drive_box,height_of_drive_box,width_of_drive_arrows), closed=True, facecolor=home_team_primary_color, linewidth=2, edgecolor=home_team_secondary_color)
            
            y_coord_for_drive_box -= (height_of_drive_box + space_between_drive_boxes)
        else:
            drive_name = "road" + str(road_team_drive_count) + "_" + get_dc_result_abbrev(result_of_drive) + "_" + "%d-%s %s" % (plays,net_yards_as_string,length_in_time) + "_" + optional_comment
            road_team_drive_count += 1
            if net_yards < 0: # use hatch='///' in the patches.Rectangle call to denote drives that lose yards.
                road_team_drives[drive_name] = patches.Rectangle((field_borders+yds2px(10)+yds2px(left_coord), y_coord_for_drive_box), yds2px(width_of_drive_box), height_of_drive_box, facecolor=road_team_primary_color, linewidth=2, edgecolor=road_team_secondary_color, hatch='////')
            else:
                road_team_drives[drive_name] = patches.Rectangle((field_borders+yds2px(10)+yds2px(left_coord), y_coord_for_drive_box), yds2px(width_of_drive_box), height_of_drive_box, facecolor=road_team_primary_color, linewidth=2, edgecolor=road_team_secondary_color)

            triangle_markers[drive_name] = patches.Polygon(get_triangle_coords("left",field_borders+yds2px(10+left_coord),y_coord_for_drive_box,height_of_drive_box,width_of_drive_arrows), closed=True, facecolor=road_team_primary_color, linewidth=2, edgecolor=road_team_secondary_color)

            y_coord_for_drive_box -= (height_of_drive_box + space_between_drive_boxes)
       
# Text layout examples taken from:
# https://matplotlib.org/stable/tutorials/text/text_props.html   

for r in home_team_drives:
    res_abbrev = r.split("_")[1]
    details_abbrev = r.split("_")[2]
    comment_abbrev = r.split("_")[3]
    text_string_to_apply = comment_abbrev + " (" + details_abbrev + ") " + res_abbrev
    ax.add_artist(home_team_drives[r])
    rx, ry = home_team_drives[r].get_xy()
    
    # TBD - If the drive is very short, the text will not fit. 15 yards seems to be a good minimum,
    # but could we determine the exact length of the text string and do this adjustment on the fly?
    # https://stackoverflow.com/questions/5320205/matplotlib-text-dimensions
    # my_renderer = fig.canvas.get_renderer()
    if home_team_drives[r].get_width() < yds2px(15):
         # place the text outside of the text box and use black as the text color
        if rx < field_borders+yds2px(20): # borders + endzone + 10 == drives that start inside the home team's 10 yard line
            # place text to the RIGHT of the drive box and the right-hand facing arrow
            tmp = ax.text(rx+home_team_drives[r].get_width() + width_of_drive_arrows, 0.5*(ry+ry+home_team_drives[r].get_height()), text_string_to_apply, ha='left', va='center', color='black', weight='bold', fontsize=9)
        else:
            tmp = ax.text(rx, 0.5*(ry+ry+home_team_drives[r].get_height()), text_string_to_apply, ha='right', va='center', color='black', weight='bold', fontsize=9)
    else:
        # place the text on top of the drive box, right-justified
        tmp = ax.text(rx+home_team_drives[r].get_width(), 0.5*(ry+ry+home_team_drives[r].get_height()), text_string_to_apply, ha='right', va='center', color='white', weight='bold', fontsize=9)
    # text_box = tmp.get_window_extent(renderer=my_renderer)
    # TBD - this does not work. The width of the rectangle is given in different units than the text.
    # But even if we do this, we have to redraw the original box and text again.
    # print("%s is %d wide, %d high (width of box is %d)" % (text_string_to_apply,text_box.width,text_box.height,home_team_drives[r].get_width()))
    
for r in road_team_drives:
    res_abbrev = r.split("_")[1]
    details_abbrev = r.split("_")[2]
    comment_abbrev = r.split("_")[3]
    text_string_to_apply =  res_abbrev + " (" + details_abbrev + ") " + comment_abbrev
    ax.add_artist(road_team_drives[r])
    rx, ry = road_team_drives[r].get_xy()
    
    # TBD - If the drive is very short, the text will not fit. 15 yards seems to be a good minimum,
    # but could we determine the exact length of the text string and do this adjustment on the fly?
    if road_team_drives[r].get_width() < yds2px(15):
         # place the text outside of the text box and use black as the text color
        if rx+road_team_drives[r].get_width() > field_borders+yds2px(100): # borders + endzone + 90 == drives that start inside the road team's 10 yard line
            # place text to the LEFT of the drive box and the left-hand facing arrow
            ax.text(rx-width_of_drive_arrows, 0.5*(ry+ry+road_team_drives[r].get_height()), text_string_to_apply, ha='right', va='center', color='black', weight='bold', fontsize=9)
        else:
            # place text to the right of the drive box
            ax.text(rx+road_team_drives[r].get_width(), 0.5*(ry+ry+road_team_drives[r].get_height()), text_string_to_apply, ha='left', va='center', color='black', weight='bold', fontsize=9)
    else:
        # place the text on top of the drive box, left-justified
        ax.text(rx, 0.5*(ry+ry+road_team_drives[r].get_height()), text_string_to_apply, ha='left', va='center', color='white', weight='bold', fontsize=9)
    
for q in dashed_quarter_lines:
    ax.add_artist(dashed_quarter_lines[q])
    
for t in triangle_markers:
    ax.add_artist(triangle_markers[t])

ax.set_axis_off() # Turning these off cleans up the plot

plt.show()    
    