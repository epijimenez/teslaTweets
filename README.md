# teslaTweets
Python script that checks the status of your Tesla and tweets out on your behalf.


## Description
This is a simple Python script that combines the use of your Tesla's connection and Twitter in order to let your Tesla tweet out its status and changes.

The script will check your Tesla's Odometer, Charging state, and Outside temperature.

It has dependencies on some standard Python libraries and the following:
- [teslaJSON Python Class](https://github.com/gglockner/teslajson)
- [Python Wrapper for Twitter API](https://github.com/ryanmcgrath/twython)


## Installation
0. Clone the repository
1. From the root folder of the cloned repository, use pip to install
    'pip3 install . --break-system-packages --user'
    Needs to add the --break-system-packages in order to run outside of virtualenvs 
2. Reboot the system
3. Run the script
    'teslatweets'
4. Your first run will guide you through the User Data set up
5. After User Data set up, try a run manually by just ruuning the script again
    'teslatweets'
6. This will create a log file and record current milage for the milestones (every 1000 miles) and maintance checks
7. Create a cronjob so it can run at an interval daily
    hint: https://crontab.guru/

## Credits
Thanks to authors 
- teslaJSON - [gglockner](https://github.com/gglockner/teslajson/commits?author=gglockner)
- Twython - [michaelhelmick](https://github.com/ryanmcgrath/twython/commits?author=michaelhelmick)

## Disclaimer
This software is provided as-is.  This software is not supported by or endorsed by Tesla Motors nor by Twitter Inc. The author makes no guarantee to release an updated version to fix any incompatibilities.
