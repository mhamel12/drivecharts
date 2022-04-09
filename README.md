# drivecharts
Drive chart generator for (American) Football games

dc.py -h
usage: dc.py [-h] [-drivedata DRIVEDATA] [-exchangecolor EXCHANGECOLOR] teams

Example:dc.py ATL,NWE -d SB51ATL_Drives_Enhanced.txt,SB51NWE_Drives_Enhanced.txt

Developed with Python 3.6.0
Requires the matplotlib (tested with 3.3.4) and numpy (tested with 1.19.4) libraries.

Input files must match the .csv format used by Pro Football Reference in their "drive" tables on their boxscore pages.
