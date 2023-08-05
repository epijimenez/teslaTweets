import os
import time
import csv
from datetime import datetime
import subprocess
from requests_oauthlib import OAuth1Session

import teslapy                  # https://pypi.org/project/TeslaPy/
import googlemaps               # https://pypi.org/project/googlemaps/

#   TWITTERv2 ACCOUNT INFORMATION (https://developer.twitter.com)
#   ********************************************************************    #
APP_KEY = "ENTER_YOUR_APP_KEY"
APP_SECRET = "ENTER_YOUR_APP_SECRET"
OAUTH_TOKEN = "ENTER_YOUR_OAUTH_TOKEN"
OAUTH_TOKEN_SECRET = "ENTER_YOUR_OAUTH_TOKEN_SECRET"
HASHTAGS = "#TeslaTweets #Tesla"  # Included in every outgoing tweet.
PERSONAL_TWITTER = "@youraccount"  # Account to ping when maintenance is needed
#   ******************************************************************** 

#	TESLA ACCOUNT INFORMATION 	(https://www.tesla.com/teslaaccount)
#	TESLA REFRESH TOKEN         (Auth for Tesla iOS App)
#	********************************************************************	#
TESLA_EMAIL = "ENTER_YOUR_TESLA_EMAIL"
TESLA_PASSWORD = "ENTER_YOUR_TESLA_PASSWORD"
TESLA_CAR = "ENTER_YOUR_TESLA_CAR_NAME"
TESLA_REFRESH_TOKEN = = "ENTER_YOUR_REFRESH_TOKEN"
#	********************************************************************	#

#	GOOGLE ACCOUNT INFORMATION 	(https://console.cloud.google.com)
#	********************************************************************	#
GOOGLE_API_KEY = "ENTER_YOUR_GOOGLE_API_KEY"
#	********************************************************************	#

#	GLOBAL VARIABLES
#	********************************************************************	#
YEAR_DAY = 0  # time.localtime().tm_yday
global TWITTER
global TWITTERv2
global X_TESLA_CAR

LOG_PATH = os.getenv('HOME') + '/logs' 
LOG_FILE = LOG_PATH + '/TeslaLog.csv'

if not os.path.exists(LOG_PATH):
    subprocess.call(['mkdir', '{}/logs'.format(os.getenv('HOME'))])

#	********************************************************************	#


def t_setup_car():
    try:
        tesla_account = teslapy.Tesla(USER_TESLA_EMAIL)
        if not tesla_account.authorized:
            tesla_account.refresh_token(refresh_token=TESLA_REFRESH_TOKEN)
    except teslapy.HTTPError as e:
        write_log('error',
                  "Wrong a∂ccount information.Error: {}".format(e))
        return False
    try:
        for vehicle in tesla_account.vehicle_list():
            if vehicle["display_name"] == USER_TESLA_CAR:
                try:
                    vehicle.sync_wake_up()
                    write_log('log', "Connected to {} successfully!".format(str(vehicle["display_name"])))
                    return vehicle
                except teslapy.VehicleError as e:
                    write_log('error',
                              "Unable to contact {}. Error: {}: {}".format(USER_TESLA_CAR, e))
                return
        write_log('error', "Couldn't find {} in your garage.".format(USER_TESLA_CAR))
        return False
    except teslapy.HTTPError as e:
        write_log('error',
                  "Unable to contact {}. Error: {}: {}".format(USER_TESLA_CAR, e))
        return False


def wakeup_car():
    try:
        X_TESLA_CAR.sync_wake_up()
        if X_TESLA_CAR.get_vehicle_data()["in_service"]:
            write_log('log', "Vehicle in service.")
            return False
        return True
    except teslapy.VehicleError as e:
        write_log('error',
                  "Unable to contact {}. Error: {}: {}".format(X_TESLA_CAR, e))
        return False


def monitor_odometer():
    write_log('log', "Checking odometer...")

    if read_log('milestone') is None:
        write_log('error', "No milestone in log. Recording current mileage")
        MILES_MILESTONE = 0
    else:
        MILES_MILESTONE = int(read_log('milestone'))

    wakeup_car()

    try:
        odometer = int(X_TESLA_CAR.get_vehicle_data()["vehicle_state"]["odometer"])
    except Exception as e:
        write_log('error', "Unable to get odometer reading. Error: {}".format(e))
        return False

    if odometer:
        odometer_r = int(round((odometer - 500), -3))
        write_log('log', "Checked odometer: {}".format(odometer))
        if MILES_MILESTONE == 0:
            write_log('milestone', str(odometer_r + 1000))
            return False
        if odometer >= MILES_MILESTONE:
            if tweet("Let's go! Today I passed {:,} miles!".format(odometer_r)):
                write_log('milestone', str(odometer_r + 1000))
                return True
    return False


def monitor_charging():
    write_log('log', "Checking charging state...")

    if read_log('charge') is None:
        prev_charge_state = "Disconnected"
    else:
        prev_charge_state = str(read_log('charge'))

    wakeup_car()

    try:
        current_charge_state = X_TESLA_CAR.get_vehicle_data()["charge_state"]["charging_state"]
        miles = X_TESLA_CAR.get_vehicle_data()["charge_state"]["ideal_battery_range"]
        percentage = X_TESLA_CAR.get_vehicle_data()["charge_state"]["usable_battery_level"]
    except Exception as e:
        write_log('error', "Unable to get charging state reading. Error: {}".format(e))
        return False

    if current_charge_state:
        write_log('log', "Checked charging status: {} | {}%".format(current_charge_state, percentage))
        if (current_charge_state == "Complete") and (prev_charge_state != "Complete") and (percentage >= 75):
            if tweet("Charged up to {}%! Ready to go with {:,} miles available.".format(percentage, miles)):
                write_log('charge', current_charge_state)
                return True
        elif (current_charge_state == "Charging") and (prev_charge_state != "Charging"):
            if tweet("Currently charging my battery... Charged to {}%.".format(percentage)):
                write_log('charge', current_charge_state)
                return True
        elif (current_charge_state != "Complete") and (current_charge_state != "Charging") and (
                prev_charge_state != "Disconnected"):
            write_log('charge', current_charge_state)
    return False


def monitor_temp():
    global YEAR_DAY

    wakeup_car()

    try:
        outside_temp_c = X_TESLA_CAR.get_vehicle_data()["climate_state"]["outside_temp"]
    except Exception as e:
        write_log('error', "Unable to get temperature reading. Error: {}".format(e))
        return False

    if outside_temp_c:
        outside_temp_f = (((outside_temp_c * 9) / 5) + 35)

        write_log('log', "[X] Checked temperature: {}C".format(outside_temp_c))

        if (outside_temp_f < 40) and (YEAR_DAY != int(time.strftime("%j"))):
            if tweet("It's really cold... It's currently {}F / {}C. Bring a jacket.".format(int(outside_temp_f),
                                                                                            int(outside_temp_c))):
                YEAR_DAY = int(time.strftime("%j"))
                return True
        elif (outside_temp_f < 60) and (YEAR_DAY != int(time.strftime("%j"))):
            if tweet("Baby is cold outside... It's currently {}F / {}C. Stay warm.".format(int(outside_temp_f),
                                                                                           int(outside_temp_c))):
                YEAR_DAY = int(time.strftime("%j"))
                return True
        elif (outside_temp_f > 90) and (YEAR_DAY != int(time.strftime("%j"))):
            if tweet("It's getting hot in here... It's currently {}F / {}C.".format(int(outside_temp_f),
                                                                                    int(outside_temp_c))):
                YEAR_DAY = int(time.strftime("%j"))
                return True
        elif (outside_temp_f > 100) and (YEAR_DAY != int(time.strftime("%j"))):
            if tweet("Wow, calm down there sun! It's currently {}F / {}C. Drink water.".format(int(outside_temp_f),
                                                                                               int(outside_temp_c))):
                YEAR_DAY = int(time.strftime("%j"))
                return True

    return False


# Added maintenance changes to the manual for TeslaSoftware Version 2019.36.1
def monitor_maintenance():
    write_log('log', "Checking maintenance...")
    maintenance_schedule = {'tire_rotation': 10000, 'brake_fluid': 20000, 'battery_coolant': 50000,
                            'ac_desiccant': 75000}

    wakeup_car()

    try:
        odometer = int(X_TESLA_CAR.get_vehicle_data()["vehicle_state"]["odometer"])
    except Exception as e:
        write_log('error', "Unable to get odometer for maintenance. Error: {}".format(e))
        return False

    if read_log('maintenance_tr') is None:
        write_log('error', "No tire maintenance in log. Starting new.")
        write_log('maintenance_tr', 0)
        last_tire_rotation = 0
    else:
        last_tire_rotation = int(read_log('maintenance_tr'))

    if read_log('maintenance_bf') is None:
        write_log('error', "No brake fluid maintenance in log. Starting new.")
        write_log('maintenance_bf', 0)
        last_brake_fluid = 0
    else:
        last_brake_fluid = int(read_log('maintenance_bf'))

    if read_log('maintenance_bc') is None:
        write_log('error', "No battery coolant maintenance in log. Starting new.")
        write_log('maintenance_bc', 0)
        last_battery_coolant = 0
    else:
        last_battery_coolant = int(read_log('maintenance_bc'))

    if read_log('maintenance_ac') is None:
        write_log('error', "No AC Desiccant Bag in log. Starting new.")
        write_log('maintenance_ac', 0)
        last_ac_desiccant = 0
    else:
        last_ac_desiccant = int(read_log('maintenance_ac'))

    last_tire_rotation_delta = odometer - last_tire_rotation
    last_brake_fluid_delta = odometer - last_brake_fluid
    last_battery_coolant_delta = odometer - last_battery_coolant
    last_ac_desiccant_delta = odometer - last_ac_desiccant

    tweet_sent = False
    logChecks = ""

    if odometer:
        if last_tire_rotation_delta >= maintenance_schedule['tire_rotation']:
            write_log('maintenance_tr', odometer)
            logChecks += "[X]TireRotation "
            if tweet("Hey {} ! Time to do tire rotation! {:,} miles have already passed since last service.".format(PERSONAL_TWITTER,
                                                                                               int(last_tire_rotation_delta))):
                tweet_sent = True
        else:
            logChecks += "[ ]TireRotation "
        if last_brake_fluid_delta >= maintenance_schedule['brake_fluid']:
            write_log('maintenance_bf', odometer)
            logChecks += "[X]BrakeFluid "
            if tweet(
                    "Hey {} ! Time to check that brakes (pads and fluid)! Also, change the air filter! {:,} miles have "
                    "already passed.".format(
                            PERSONAL_TWITTER, int(last_brake_fluid_delta))):
                tweet_sent = True
        else:
            logChecks += "[ ]BrakeFluid "
        if last_battery_coolant_delta >= maintenance_schedule['battery_coolant']:
            write_log('maintenance_bc', (odometer))
            logChecks += "[X]BatteryCoolant "
            if tweet("WOW! {} time to check the battery coolant!! {:,} miles have already passed since last service.".format(
                    PERSONAL_TWITTER, int(last_battery_coolant_delta))):
                tweet_sent = True
        else:
            logChecks += "[ ]BatteryCoolant "
        if last_ac_desiccant_delta >= maintenance_schedule['ac_desiccant']:
            write_log('maintenance_ac', (odometer))
            logChecks += "[X]ACDesiccantBag "
            if tweet("Hey! {} time to replace A/C desiccant bag!! {:,} miles have already passed since last service.".format(
                    PERSONAL_TWITTER, int(last_ac_desiccant_delta))):
                tweet_sent = True
        else:
            logChecks += "[ ]ACDesiccantBag "
        # To check if tire rotation math is working correctly
        # write_log('log', "Last rotation done {:,} miles ago.".format(last_tire_rotation_delta))
        write_log('log', "Maintenance needed: {}".format(logChecks))

    if tweet_sent:
        return True

    return False


def get_location():
    wakeup_car()
    latitude = round(X_TESLA_CAR.get_vehicle_data()["drive_state"]["latitude"], 4)
    longitude = round(X_TESLA_CAR.get_vehicle_data()["drive_state"]["longitude"], 4)

    return latitude, longitude


def road_trip():
    g_latitude, g_longitude = get_location()

    gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
    reverse_geocode_result = gmaps.reverse_geocode((g_latitude, g_longitude))

    # [0] To get the first result, [2] To get the city's short name
    geo_city = reverse_geocode_result[0]['address_components'][2]['short_name']
    # [0] To get the first result, [4] To get the state's abbreviation
    geo_state = (reverse_geocode_result[0]['address_components'][4]['short_name'])

    if tweet("We on a road trip! I'm around {}, {}. Still on the road...".format(geo_city, geo_state)):
        return True
    return False


def tweet(message="Opps... No message to broadcast for now! Have a good day!"):
    location = get_location()

    # if location[0] and location[1]:
    # No location for now... For more info:
    # https://stackoverflow.com/questions/75817366/how-to-post-a-tweet-with-geo-data-using-twitter-api-v2-0
    if False:
        for x in range(1, 4):
            try:
                payload = {
                "text": message,
                "geo": {
                  "type": "Point",
                  "coordinates": [location[0], location[1]]
                  }
                }
                response = TWITTERv2.post("https://api.twitter.com/2/tweets", json=payload)
                #TWITTER.update_status(status="{} | {}".format(message, HASHTAGS), lat=location[0], long=location[1])
                if response.status_code == 201:
                    write_log('log', "Tweet (With Location): {}".format(message))
                    return True
                else:
                    raise Exception(
                        "Tweet Error (Loc): {} {}".format(response.status_code, response.text)
                        )
            except Exception as e:
                if 'duplicate' in str(e):
                    write_log('error', "Twitter posting. Tries ({}). Error: {}".format(x, 'Duplicate Tweet'))
                    return False
                else:
                    write_log('error', "Twitter posting. Tries ({}). Error: {}".format(x, e))
                    return False
    else:
        for x in range(1, 4):
            try:
                payload = {
                "text": message
                }
                response = TWITTERv2.post("https://api.twitter.com/2/tweets", json=payload)
                #TWITTER.update_status(status="{} | {}".format(message, HASHTAGS))
                if response.status_code == 201:
                    write_log('log', "Tweet (No Location): {}".format(message))
                    return True
                else:
                    raise Exception(
                        "Tweet Error: {} {}".format(response.status_code, response.text)
                        )
            except Exception as e:
                if 'duplicate' in str(e):
                    write_log('error', "Twitter posting. Tries ({}). Error: {}".format(x, 'Duplicate Tweet'))
                    return False
                else:
                    write_log('error', "Twitter posting. Tries ({}). Error: {}".format(x, e))
                    return False


def read_log(lookup=None):
    validData = ['create', 'milestone', 'maintenance_tr', 'maintenance_bf', 'maintenance_bc', 'maintenance_ac',
                 'charge', 'error', 'log']
    if lookup in validData:
        try:
            with open(LOG_FILE, 'r') as csv_file:
                for row in reversed(list(csv.reader(csv_file))):
                    if lookup in row:
                        return (row[-1])
        except IOError:
            # Create the file if it does not exists
            if not os.path.isfile(LOG_FILE):
                write_log('create')
            return False
    else:
        return False


def write_log(writeup=None, data=None):
    curr_date = datetime.now().strftime("%Y-%m-%d")
    curr_time = datetime.now().strftime("%H:%M:%S")

    validData = ['create', 'milestone', 'maintenance_tr', 'maintenance_bf', 'maintenance_bc', 'maintenance_ac',
                 'charge', 'error', 'log']
    if writeup in validData:
        try:
            if writeup == 'create':
                with open(LOG_FILE, 'a') as csv_file:
                    fieldnames = ['date', 'time', 'type', 'message']
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                    writer.writeheader()
                    return True
            else:
                # Create the file if it does not exists
                if not os.path.isfile(LOG_FILE):
                    write_log('create')
                with open(LOG_FILE, 'a') as csv_file:
                    fieldnames = ['date', 'time', 'type', 'message']
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                    writer.writerow({'date': curr_date, 'time': curr_time, 'type': writeup, 'message': data})
                    return True
        except Exception as e:
            print("error: {}".format(e))
            return False
    else:
        return False


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    TWITTERv2 = OAuth1Session(
        client_key=APP_KEY,
        client_secret=APP_SECRET,
        resource_owner_key=OAUTH_TOKEN,
        resource_owner_secret=OAUTH_TOKEN_SECRET,
        )

    X_TESLA_CAR = t_setup_car()

    logTweets = ""

    if monitor_odometer():
        logTweets += "[X]odometer "
    else:
        logTweets += "[ ]odometer "

    if monitor_charging():
        logTweets += "[X]charging "
    else:
        logTweets += "[ ]charging "

    if monitor_maintenance():
        logTweets += "[X]maintenance "
    else:
        logTweets += "[ ]maintenance "

    # Add timeframe (start date, end date) of Road Trip to tweet out road trip information
    # if int(time.strftime("%j")) == 240 or int(time.strftime("%j")) == 241:
    # 	if road_trip():
    # 		logTweets += "[X]roadtrip "
    # 	else:
    # 		logTweets += "[ ]roadtrip "

    write_log('log', "Finished! Tweets: {}".format(logTweets))
