import os
import time
import csv
from datetime import datetime
import subprocess
from teslatweets.userdata import UserAccount
import logging

"""
GLOBAL VARIABLES
"""
LOG_PATH = os.getenv('HOME') + '/logs'
LOG_FILE = LOG_PATH + '/TeslaLog.csv'

YEAR_DAY = 0  # time.localtime().tm_yday
UserAccount = UserAccount()

def wakeup_car():
    try:
        UserAccount.tesla.sync_wake_up()
        if UserAccount.tesla.get_vehicle_data()["in_service"]:
            write_log('log', "Vehicle in service.")
            return False
        return True
    except Exception as e:
        write_log('error',
                  f"Unable to contact {UserAccount.tesla}. Error: {e}")
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
        odometer = int(UserAccount.tesla.get_vehicle_data()["vehicle_state"]["odometer"])
    except Exception as e:
        write_log('error', f"Unable to get odometer reading. Error: {e}")
        return False

    if odometer:
        odometer_r = int(round((odometer - 500), -3))
        write_log('log', f"Checked odometer: {odometer}")
        if MILES_MILESTONE == 0:
            write_log('milestone', str(odometer_r + 1000))
            return False
        if odometer >= MILES_MILESTONE:
            if tweet(f"Let's go! Today I passed {odometer_r:,} miles!"):
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
        current_charge_state = UserAccount.tesla.get_vehicle_data()["charge_state"]["charging_state"]
        miles = UserAccount.tesla.get_vehicle_data()["charge_state"]["ideal_battery_range"]
        percentage = UserAccount.tesla.get_vehicle_data()["charge_state"]["usable_battery_level"]
    except Exception as e:
        write_log('error', f"Unable to get charging state reading. Error: {e}")
        return False

    if current_charge_state:
        write_log('log', f"Checked charging status: {current_charge_state} | {percentage}%")
        if (current_charge_state == "Complete") and (prev_charge_state != "Complete") and (percentage >= 75):
            if tweet(f"Charged up to {percentage}%! Ready to go with {miles:,} miles available."):
                write_log('charge', current_charge_state)
                return True
        elif (current_charge_state == "Charging") and (prev_charge_state != "Charging"):
            if tweet(f"Currently charging my battery... Charged to {percentage}%."):
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
        outside_temp_c = UserAccount.tesla.get_vehicle_data()["climate_state"]["outside_temp"]
    except Exception as e:
        write_log('error', f"Unable to get temperature reading. Error: {e}")
        return False

    if outside_temp_c:
        outside_temp_f = (((outside_temp_c * 9) / 5) + 35)

        write_log('log', f"[X] Checked temperature: {outside_temp_c}C")

        if (outside_temp_f < 40) and (YEAR_DAY != int(time.strftime("%j"))):
            if tweet(f"It's really cold... It's currently {int(outside_temp_f)}F / {int(outside_temp_c)}C. "
                     f"Bring a jacket."):
                YEAR_DAY = int(time.strftime("%j"))
                return True
        elif (outside_temp_f < 60) and (YEAR_DAY != int(time.strftime("%j"))):
            if tweet(f"Baby is cold outside... It's currently {int(outside_temp_f)}F / {int(outside_temp_c)}C. "
                     f"Stay warm."):
                YEAR_DAY = int(time.strftime("%j"))
                return True
        elif (outside_temp_f > 90) and (YEAR_DAY != int(time.strftime("%j"))):
            if tweet(f"It's getting hot in here... It's currently {int(outside_temp_f)}F / {int(outside_temp_c)}C."):
                YEAR_DAY = int(time.strftime("%j"))
                return True
        elif (outside_temp_f > 100) and (YEAR_DAY != int(time.strftime("%j"))):
            if tweet(f"Wow, calm down there sun! It's currently {int(outside_temp_f)}F / {int(outside_temp_c)}C. "
                     f"Drink water."):
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
        odometer = int(UserAccount.tesla.get_vehicle_data()["vehicle_state"]["odometer"])
    except Exception as e:
        write_log('error', f"Unable to get odometer for maintenance. Error: {e}")
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
            if tweet(
                    f"Hey {UserAccount.twitter_extras_ping_account} ! Time to do tire rotation! {int(last_tire_rotation_delta):,} miles "
                    f"have already passed since last service."):
                tweet_sent = True
        else:
            logChecks += "[ ]TireRotation "
        if last_brake_fluid_delta >= maintenance_schedule['brake_fluid']:
            write_log('maintenance_bf', odometer)
            logChecks += "[X]BrakeFluid "
            if tweet(f"Hey {UserAccount.twitter_extras_ping_account} ! Time to check that brakes (pads and fluid)! "
                     f"Also, change the air filter! {int(last_brake_fluid_delta):,} miles have "
                     "already passed."):
                tweet_sent = True
        else:
            logChecks += "[ ]BrakeFluid "
        if last_battery_coolant_delta >= maintenance_schedule['battery_coolant']:
            write_log('maintenance_bc', odometer)
            logChecks += "[X]BatteryCoolant "
            if tweet(f"WOW! {UserAccount.twitter_extras_ping_account} time to check the battery coolant!! "
                     f"{int(last_battery_coolant_delta):,} miles have already passed since last service."):
                tweet_sent = True
        else:
            logChecks += "[ ]BatteryCoolant "
        if last_ac_desiccant_delta >= maintenance_schedule['ac_desiccant']:
            write_log('maintenance_ac', odometer)
            logChecks += "[X]ACDesiccantBag "
            if tweet(f"Hey! {UserAccount.twitter_extras_ping_account} time to replace A/C desiccant bag!! "
                     f"{int(last_ac_desiccant_delta):,} miles have already passed since last service."):
                tweet_sent = True
        else:
            logChecks += "[ ]ACDesiccantBag "
        write_log('log', f"Maintenance needed: {logChecks}")

    if tweet_sent:
        return True

    return False


def get_location():
    wakeup_car()
    latitude = round(UserAccount.tesla.get_vehicle_data()["drive_state"]["latitude"], 4)
    longitude = round(UserAccount.tesla.get_vehicle_data()["drive_state"]["longitude"], 4)

    return latitude, longitude


def road_trip():
    g_latitude, g_longitude = get_location()
    if UserAccount.google is None:
        return False
    reverse_geocode_result = UserAccount.google.reverse_geocode((g_latitude, g_longitude))

    # [0] To get the first result, [2] To get the city's short name
    geo_city = reverse_geocode_result[0]['address_components'][2]['short_name']
    # [0] To get the first result, [4] To get the state's abbreviation
    geo_state = (reverse_geocode_result[0]['address_components'][4]['short_name'])

    if tweet(f"We on a road trip! I'm around {geo_city}, {geo_state}. Still on the road..."):
        return True
    return False


def tweet(message="Opps... No message to broadcast for now! Have a good day!"):
    location = False
    location = get_location()

    # TODO: Bring back location; For more info: https://stackoverflow.com/questions/75817366/how-to-post-a-tweet-with-geo-data-using-twitter-api-v2-0
    location = False

    if location:
        for x in range(1, 4):
            try:
                payload = {
                    "text": message,
                    "geo": {
                        "type": "Point",
                        "coordinates": [location[0], location[1]]
                    }
                }
                response = UserAccount.twitter.post("https://api.twitter.com/2/tweets", json=payload)
                #TWITTER.update_status(status= f"{message} | {UserAccount.twitter_extras_hashtags}", lat=location[0], long=location[1])
                if response.status_code == 201:
                    write_log('log', f"Tweet (With Location): {message}")
                    return True
                else:
                    raise Exception(f"Tweet Error (Loc): {response.status_code} {response.text}")
            except Exception as e:
                if 'duplicate' in str(e):
                    write_log('error', f"Twitter posting. Tries ({x}). Error: Duplicate Tweet")
                    return False
                else:
                    write_log('error', f"Twitter posting. Tries ({x}). Error: {e}")
                    return False
    else:
        for x in range(1, 4):
            try:
                payload = {
                    "text": message
                }
                response = UserAccount.twitter.post("https://api.twitter.com/2/tweets", json=payload)
                #TWITTER.update_status(status= f"{message} | {UserAccount.twitter_extras_hashtags}")
                if response.status_code == 201:
                    write_log('log', f"Tweet (No Location): {message}")
                    return True
                else:
                    raise Exception(f"Tweet Error: {response.status_code} {response.text}")
            except Exception as e:
                if 'duplicate' in str(e):
                    write_log('error', f"Twitter posting. Tries ({x}). Error: Duplicate Tweet")
                    return False
                else:
                    write_log('error', f"Twitter posting. Tries ({x}). Error: {e}")
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
            # Create the file if it does not exist
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
            print(f"error: {e}")
            return False
    else:
        return False


# Press the green button in the gutter to run the script.
def teslatweets():
    if not os.path.exists(LOG_PATH):
        subprocess.call(['mkdir', f"{os.getenv('HOME')}/logs"])

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

    write_log('log', f"Finished! Tweets: {logTweets}")
