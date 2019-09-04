# teslaTweets
Python script that checks the status of your Tesla and tweets out on your behalf.


## Description
This is a simple Python script that combines the use of your Tesla's connection and Twitter in order to let your Tesla tweet out its status and changes.

The script will check your Tesla's Odometer, Charging state, and Outside temperature.

It has dependencies on some standard Python libraries and the following:
- [teslaJSON Python Class](https://github.com/gglockner/teslajson)
- [Python Wrapper for Twitter API](https://github.com/ryanmcgrath/twython)


## Installation
0. Download the repository zip file and uncompress it.
1. Install required libraries (teslaJSON and Twython)
2. Edit teslaTweets.py with the information (Twitter and Tesla account).
3. Run the following command with your Python interpreter: `python teslaTweets.py`
4. This will create a log file and record current milage for the milestones (every 1000 miles) and maintance checks.
5. EXTRA: If you will use the road_trip function, you need to create a Google API Key

## Credits
Thanks to authors 
- teslaJSON - [gglockner](https://github.com/gglockner/teslajson/commits?author=gglockner)
- Twython - [michaelhelmick](https://github.com/ryanmcgrath/twython/commits?author=michaelhelmick)

## Disclaimer
This software is provided as-is.  This software is not supported by or endorsed by Tesla Motors nor by Twitter Inc. The author makes no guarantee to release an updated version to fix any incompatibilities.
