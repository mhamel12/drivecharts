# drivecharts
Drive chart generator for (American) Football games

usage: dc.py [-h] [-drivedata DRIVEDATA] [-exchangecolor EXCHANGECOLOR] teams

Example:dc.py ATL,NWE -d SB51ATL_Drives_Enhanced.txt,SB51NWE_Drives_Enhanced.txt

Developed with Python 3.6.0, tested with Python 3.10.8

Requires the matplotlib (tested with 3.6.2) and numpy (tested with 1.23.4) libraries.

Input files must match the .csv format used by Pro Football Reference (https://www.pro-football-reference.com/) in their "drive" tables on their boxscore pages, but can contain an optional column with a text string that will be added to the chart for that drive. The "Enhanced" text files in the samples are an example.

Team colors and nicknames in the script are mostly up-to-date for the 2022 season, with a few limited 'historical' teams.

Horizontal dashed lines separate each quarter. Drives that span two quarters are presented as having taken place in the quarter where the drive began.

Lightly tested, with lots of room for improvement. For example, hard-coded values are used to determine if the description of a drive can "fit" inside the drive rectangle or not, and the logic that determines whether the drive details are presented to the left or right of the rectangle could use some tweaking. Also, kickoff/punt returns for touchdowns are not included.
