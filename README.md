# drivecharts
Drive chart generator for (American) Football games

usage: dc.py [-h] [-drivedata DRIVEDATA] [-exchangecolor EXCHANGECOLOR] teams

Example:dc.py ATL,NWE -d SB51ATL_Drives_Enhanced.txt,SB51NWE_Drives_Enhanced.txt

Developed with Python 3.6.0
Requires the matplotlib (tested with 3.3.4) and numpy (tested with 1.19.4) libraries.

Input files must match the .csv format used by Pro Football Reference (https://www.pro-football-reference.com/) in their "drive" tables on their boxscore pages, but can contain an optional column with a text string that will be added to the chart for that drive. The "Enhanced" text files in the samples are an example.

Team colors and nicknames in the script mostly match 2022 information, with a few limited 'historical' teams.

Lightly tested, with lots of room for improvement.
