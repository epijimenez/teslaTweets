import os
import time
import urllib2
import logging
import random

import teslajson				# Source: https://github.com/gglockner/teslajson
from twython import Twython 	# Source: https://github.com/ryanmcgrath/twython

#	TWITTER ACCOUNT INFORMATION (https://developer.twitter.com)
#	********************************************************************	#
APP_KEY= "ENTER_YOUR_APP_KEY"
APP_SECRET = "ENTER_YOUR_APP_SECRET"
OAUTH_TOKEN = "ENTER_YOUR_OAUTH_TOKEN"
OAUTH_TOKEN_SECRET = "ENTER_YOUR_OAUTH_TOKEN_SECRET"
HASTAGS = "#TeslaTweets #Tesla @elonmusk" # Included in every outgoing tweet.
TWITTER = None
#	********************************************************************	#

#	TESLA ACCOUNT INFORMATION 	(https://www.tesla.com/teslaaccount)
#	********************************************************************	#
TESLA_EMAIL = "ENTER_YOUR_TESLA_EMAIL"
TESLA_PASSWORD = "ENTER_YOUR_TESLA_PASSWORD"
TESLA_CAR = "ENTER_YOUR_TESLA_CAR_NAME"
#	********************************************************************	#

#	GLOBAL VARIABLES
#	********************************************************************	#
CHARGE_STATUS = 0 # 0 = Not Charging, 1 = Charging, 2 = Charged
YEAR_DAY = 0
LOGGER = None
#	********************************************************************	#


def establish_connection(token=None):
	userEmail = TESLA_EMAIL
	userPassword = TESLA_PASSWORD

	for x in range(1, 4):
		try:
			c = teslajson.Connection(userEmail, userPassword)

			return c
		except urllib2.HTTPError as e:
			LOGGER.error("\n>>>>> Wrong email or password. Tried {} times. Retrying in 60 seconds...\nError: {}\n".format(x, e))
			time.sleep(60)
			x =+ 1
	return False


def get_car(c):
	userCar = TESLA_CAR
	
	for x in range(1, 4):
		for v in c.vehicles:
			if v["display_name"] == userCar:
				try:
					v.wake_up()
					time.sleep(10)
					return str(userCar)
				except urllib2.HTTPError as e:
					LOGGER.error("\n>>>>> Unable to contact {}. Tried {} times. Retrying in 60 seconds...\nError: {}\n".format(car, x, e))
					x += 1
			else:
				LOGGER.error("\n>>>>> Couldn't find {} in your garage.\n".format(userCar))
				return False
	return False


def wakeup_car(c, car):
	for x in range(1, 4):
		for v in c.vehicles:
			if v["display_name"] == car:
				try:
					v.wake_up()
					time.sleep(10)
					return True
				except urllib2.HTTPError as e:
					LOGGER.error("\n>>>>> Unable to contact {}. Tried {} times. Retrying in 60 seconds...\nError: {}\n".format(car, x, e))
					x += 1
					time.sleep(60)
	return False


def monitor_odometer(c, car):
	MILES_MILESTONE = int(read_miles_milestone())
	odometer = None

	wakeup_car(c, car)

	for v in c.vehicles:
		if v["display_name"] == car:
			d = v.data_request("vehicle_state")
			odometer = int(d["odometer"])
	odometer_r = int(round((odometer-500), -3))
	
	LOGGER.info("\n[X] Checked odometer: {}. Using rounded number: {}\n".format(odometer, odometer_r))
	
	if (odometer >= MILES_MILESTONE):
		tweet(c, car, "Let's go! I just passed {} miles!".format(odometer_r))
		change_miles_milestone(str(odometer_r+1000))
		return True

	return False


def monitor_charging(c, car):
	global CHARGE_STATUS
	charge_state = None
	miles = None

	wakeup_car(c, car)

	for v in c.vehicles:
		if v["display_name"] == car:
			d = v.data_request("charge_state")
			charge_state = d["charging_state"]
			miles = int(d["ideal_battery_range"])
			percentage = int(d["usable_battery_level"])

	LOGGER.info("\n[X] Checked charging status: {}\n".format(charge_state))

	if (charge_state == "Complete") and (CHARGE_STATUS != 2) and (percentage >= 75):
		tweet(c, car, "All charged up! Ready to go with {} miles available.".format(miles))
		CHARGE_STATUS = 2
		return True
	elif (charge_state == "Charging") and (CHARGE_STATUS != 1):
		tweet(c, car, "Currently charging my battery... Charged to {}%.".format(percentage))
		CHARGE_STATUS = 1
		return True
	else:
		CHARGE_STATUS = 0
	
	return False


def monitor_temp(c, car):
	global YEAR_DAY
	outside_temp_c = None

	wakeup_car(c, car)

	for v in c.vehicles:
		if v["display_name"] == car:
			d = v.data_request('climate_state')
			outside_temp_c = int(d["outside_temp"])

	outside_temp_f = (((outside_temp_c * 9) / 5) + 35 )

	LOGGER.info("\n[X] Checked temperature: {}C\n".format(outside_temp_c))

	if (outside_temp_f < 40) and (YEAR_DAY != int(time.strftime("%j"))):
		tweet(c, car, "It's really cold... It's currently {}F / {}C. Bring a jacket.".format(int(outside_temp_f), int(outside_temp_c)))
		YEAR_DAY = int(time.strftime("%j"))
		return True
	elif (outside_temp_f < 60) and (YEAR_DAY != int(time.strftime("%j"))):
		tweet(c, car, "Baby is cold outside... It's currently {}F / {}C. Stay warm.".format(int(outside_temp_f), int(outside_temp_c)))
		YEAR_DAY = int(time.strftime("%j"))
		return True
	elif (outside_temp_f > 90) and (YEAR_DAY != int(time.strftime("%j"))):
		tweet(c, car, "It's getting hot in here... It's currently {}F / {}C.".format(int(outside_temp_f), int(outside_temp_c)))
		YEAR_DAY = int(time.strftime("%j"))
		return True
	elif (outside_temp_f > 100) and (YEAR_DAY != int(time.strftime("%j"))):
		tweet(c, car, "Wow, calm down there sun! It's currently {}F / {}C. Drink water.".format(int(outside_temp_f), int(outside_temp_c)))
		YEAR_DAY = int(time.strftime("%j"))
		return True

	return False


def get_location(c, car):
	#location = None

	wakeup_car(c, car)

	for v in c.vehicles:
		if v["display_name"] == car:
			d = v.data_request('drive_state')
			latitude = round(d["latitude"], 2)
			longitude = round(d["longitude"], 2)
	#geolocator = Nominatim(user_agent="tesla reporter")
	#location = geolocator.reverse("{}, {}".format(latitude, longitude))
	#address = location.address.split(",")
	#city = address[-5].strip()
	#state = address[-3].strip()
	#return city, state
	# This is to get the city and state based on the coordinates, but TWITTER handles this.
	# Leaving this here in case is needed in future. Will need to import " from geopy.geocoders import Nominatim ".
	# Source: https://github.com/geopy/geopy
	return latitude, longitude


def tweet(c, car, message = "Opps... No message to broadcast for now! Have a good day!"):
	location = get_location(c, car)
	try:
		TWITTER.update_status(status= "{} | {}".format(message, HASTAGS), lat= location[0], long= location[1]) 
		LOGGER.info("\n>>>>> Posted to Twitter: {}\n".format(message))
	except Exception as e:
		LOGGER.error("\n>>>>> Error posting to Twitter. Error: {}\n".format(e))


def setup_logging():
	global LOGGER
	LOGGER = logging.getLogger('TeslaTweets')
	hdlr = logging.FileHandler('TeslaTweets.log')
	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	hdlr.setFormatter(formatter)
	LOGGER.addHandler(hdlr)
	LOGGER.setLevel(logging.INFO)


def read_miles_milestone():
	try:
		with open("MILES_MILESTONE.txt", "r") as f:
			lines = f.readlines()
			return lines[-1]
	except IOError:
		change_miles_milestone("0")
		return "0"

def change_miles_milestone(newMilestone):
	try:
		with open("MILES_MILESTONE.txt", "a") as f:
			f.write("\n{}".format(str(newMilestone)))
	except Exception as e:
		LOGGER.error("\n>>>>> Can not write MILES_MILESTONE.txt file. Check permission on folder.\nError: {}".format)

def main():
	global TWITTER
	TWITTER = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

	setup_logging()
	
	c = establish_connection()
	if not c:
		LOGGER.error("\n>>>>> Wrong email or password. Please verify your Tesla Account credentials.")
	LOGGER.info("\n>>>>> Connected to Tesla account sucessfully!\n")

	userCar = get_car(c)
	if not userCar:
		LOGGER.error("\n>>>>> Unable to find your car. Please verify your information.")
	LOGGER.info("\n>>>>> Connected to {} sucessfully!\n".format(userCar))

	while True:
		LOGGER.info("\n[ ] Checking odomenter...\n")
		if monitor_odometer(c, userCar):
			LOGGER.info("\n[X] Tweeted odometer.\n")

		LOGGER.info("\n[ ] Checking charging state...\n")
		if monitor_charging(c, userCar):
			LOGGER.info("\n[X] Tweeted charging state.\n")
		
		LOGGER.info("\n[ ] Checking temperature...\n")
		if monitor_temp(c, userCar):
			LOGGER.info("\n[X] Tweeted temperature.\n")

		LOGGER.info("\n>>>>> Going to sleep for 60 minutes...\n")
		time.sleep(3600)

main()







