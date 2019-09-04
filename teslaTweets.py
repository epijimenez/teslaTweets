import os
import time
import urllib2
import logging
import random
import subprocess
import googlemaps

import teslajson				# Source: https://github.com/gglockner/teslajson
from twython import Twython 	# Source: https://github.com/ryanmcgrath/twython

#	TWITTER ACCOUNT INFORMATION (https://developer.twitter.com)
#	********************************************************************	#
APP_KEY= "ENTER_YOUR_APP_KEY"
APP_SECRET = "ENTER_YOUR_APP_SECRET"
OAUTH_TOKEN = "ENTER_YOUR_OAUTH_TOKEN"
OAUTH_TOKEN_SECRET = "ENTER_YOUR_OAUTH_TOKEN_SECRET"
HASHTAGS = "#TeslaTweets #Tesla" # Included in every outgoing tweet.
PERSONAL_TWITTER= "@iamepijimenez" # Account to ping when maintenance is needed
TWITTER = None
#	********************************************************************	#

#	TESLA ACCOUNT INFORMATION 	(https://www.tesla.com/teslaaccount)
#	********************************************************************	#
TESLA_EMAIL = "ENTER_YOUR_TESLA_EMAIL"
TESLA_PASSWORD = "ENTER_YOUR_TESLA_PASSWORD"
TESLA_CAR = "ENTER_YOUR_TESLA_CAR_NAME"
#	********************************************************************	#

#	GOOGLE ACCOUNT INFORMATION 	(https://console.cloud.google.com)
#	********************************************************************	#
GOOGLE_API_KEY = "ENTER_YOUR_GOOGLE_API_KEY"
#	********************************************************************	#

#	GLOBAL VARIABLES
#	********************************************************************	#
YEAR_DAY = 0
#	********************************************************************	#
subprocess.call(['mkdir', '{}/logs'.format(os.getcwd())])
LOG_PATH = os.getcwd() + '/logs/TeslaLog.txt'
#	********************************************************************	#

def t_setup():
	c = establish_connection()
	userCar= get_car(c)
	return c, userCar

def establish_connection():
	userEmail = TESLA_EMAIL
	userPassword = TESLA_PASSWORD
	for x in range(1, 4):
		try:
			c = teslajson.Connection(userEmail, userPassword)
			return c
		except urllib2.HTTPError as e:
			write_log('error', "Wrong email or password. Tried {} times. Retrying in 60 seconds. Error: {}".format(x, e))
			time.sleep(60)
			x =+ 1
	write_log('error', "Can not connect to Tesla account. Verify credentials.")
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
					write_log('error', "Unable to contact {}. Tried {} times. Retrying in 60 seconds. Error: {}".format(car, x, e))
					x += 1
			else:
				write_log('error', "Couldn't find {} in your garage.\n".format(userCar))
				return False
	write_log('error', "Can not find car in Tesla account. Verify credentials.")
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
					write_log('error', "Unable to contact {}. Tried {} times. Retrying in 60 seconds. Error: {}".format(car, x, e))
					x += 1
					time.sleep(60)
	return False

def monitor_odometer(c, car):
	write_log('log', "Checking odometer...")
	try:
		MILES_MILESTONE = int(read_log('milestone'))
	except Exception as e:
		write_log('error', "No milestone in log. Recording current milage")
		MILES_MILESTONE = 0
	odometer = False
	wakeup_car(c, car)
	
	for v in c.vehicles:
		if v["display_name"] == car:
			try:
				d = v.data_request("vehicle_state")
				odometer = int(d["odometer"])
			except urllib2.HTTPError as e:
				write_log('error', "Unable to get odometer reading. Error: {}".format(e))
				odometer = False
	
	if odometer:
		odometer_r = int(round((odometer-500), -3))
		write_log('log', "Checked odometer: {}".format(odometer))
		if (MILES_MILESTONE == 0):
			write_log('milestone', str(odometer_r))
			return False
		if (odometer >= MILES_MILESTONE):
			if tweet(c, car, "Let's go! Today I passed {} miles!".format(odometer_r)):
				write_log('milestone', str(odometer_r+1000))
				return True

	return False

def monitor_charging(c, car):
	write_log('log', "Checking charging state...")
	prev_charge_state = str(read_log('charge'))
	current_charge_state = False
	miles = None

	wakeup_car(c, car)

	for v in c.vehicles:
		if v["display_name"] == car:
			try:
				d = v.data_request("charge_state")
				current_charge_state = d["charging_state"]
				miles = int(d["ideal_battery_range"])
				percentage = int(d["usable_battery_level"])
			except urllib2.HTTPError as e:
				write_log('error', "Unable to get charging state. Error: {}".format(e))
				current_charge_state = False

	if current_charge_state:
		write_log('log', "Checked charging status: {}".format(current_charge_state))
		if (current_charge_state == "Complete") and (prev_charge_state != "Complete") and (percentage >= 75):
			if tweet(c, car, "Charged up to {}%! Ready to go with {} miles available.".format(percentage, miles)):
				write_log('charge', current_charge_state)
				return True
		elif (current_charge_state == "Charging") and (prev_charge_state != "Charging"):
			if tweet(c, car, "Currently charging my battery... Charged to {}%.".format(percentage)):
				write_log('charge', current_charge_state)
				return True
		elif (current_charge_state != "Complete") and (current_charge_state != "Charging") and (prev_charge_state != "Disconnected"):
			write_log('charge', current_charge_state)
	return False

def monitor_temp(c, car):
	global YEAR_DAY
	outside_temp_c = None

	wakeup_car(c, car)

	for v in c.vehicles:
		if v["display_name"] == car:
			try:
				d = v.data_request('climate_state')
				outside_temp_c = int(d["outside_temp"])
			except urllib2.HTTPError as e:
				write_log('error', "Unable to get temperature.\nError: {}\n".format(e))
				outside_temp_c = False

	if outside_temp_c:
		outside_temp_f = (((outside_temp_c * 9) / 5) + 35 )

		write_log('log', "[X] Checked temperature: {}C\n".format(outside_temp_c))

		if (outside_temp_f < 40) and (YEAR_DAY != int(time.strftime("%j"))):
			if tweet(c, car, "It's really cold... It's currently {}F / {}C. Bring a jacket.".format(int(outside_temp_f), int(outside_temp_c))):
				YEAR_DAY = int(time.strftime("%j"))
				return True
		elif (outside_temp_f < 60) and (YEAR_DAY != int(time.strftime("%j"))):
			if tweet(c, car, "Baby is cold outside... It's currently {}F / {}C. Stay warm.".format(int(outside_temp_f), int(outside_temp_c))):
				YEAR_DAY = int(time.strftime("%j"))
				return True
		elif (outside_temp_f > 90) and (YEAR_DAY != int(time.strftime("%j"))):
			if tweet(c, car, "It's getting hot in here... It's currently {}F / {}C.".format(int(outside_temp_f), int(outside_temp_c))):
				YEAR_DAY = int(time.strftime("%j"))
				return True
		elif (outside_temp_f > 100) and (YEAR_DAY != int(time.strftime("%j"))):
			if tweet(c, car, "Wow, calm down there sun! It's currently {}F / {}C. Drink water.".format(int(outside_temp_f), int(outside_temp_c))):
				YEAR_DAY = int(time.strftime("%j"))
				return True

	return False

# TODO: Re-log last maintance on TeslaLog, so it will recent on the log (maybe?)
def monitor_maintenance(c, car):
	write_log('log', "Checking maintenance...")
	maintenance_schedule = {'tire_rotation': 6250, 'brake_fluid': 25000, 'battery_coolant': 50000}

	try:
		last_tire_rotation = int(read_log('maintenance_tr'))
	except Exception as e:
		write_log('error', "No tire maintenance in log. Starting new.")
		write_log('maintenance_tr', 0)
		last_tire_rotation = 0
	try:
		last_brake_fluid = int(read_log('maintenance_bf'))
	except Exception as e:
		write_log('error', "No brake fluid maintenance in log. Starting new.")
		write_log('maintenance_bf', 0)
		last_brake_fluid = 0
	try:
		last_battery_coolant = int(read_log('maintenance_bc'))
	except Exception as e:
		write_log('error', "No battery coolant maintenance in log. Starting new.")
		write_log('maintenance_bc', 0)
		last_battery_coolant = 0

	odometer = False
	wakeup_car(c, car)

	for v in c.vehicles:
		if v["display_name"] == car:
			try:
				d = v.data_request("vehicle_state")
				odometer = int(d["odometer"])
			except urllib2.HTTPError as e:
				write_log('error', "Unable to get odometer reading. Error: {}".format(e))
				odometer = False

	last_tire_rotation_delta = odometer - last_tire_rotation
	last_brake_fluid_delta = odometer - last_brake_fluid
	last_battery_coolant_delta = odometer - last_battery_coolant

	tweet_sent = False
	logChecks = ""

	if odometer:
		if last_tire_rotation_delta >= maintenance_schedule['tire_rotation']:
			write_log('maintenance_tr', (odometer))
			logChecks += "[X]TireRotation "
			if tweet(c, car, "Hey {} ! Time to do tire rotation! {} miles have already passed.".format(PERSONAL_TWITTER, int(last_tire_rotation_delta))):
				tweet_sent = True
		else:
			logChecks += "[ ]TireRotation "
		if last_brake_fluid_delta >= maintenance_schedule['brake_fluid']:
			write_log('maintenance_bf', (odometer))
			logChecks += "[X]BrakeFluid "
			if tweet(c, car, "Hey {} ! Time to change that brake fluid! {} miles have already passed.".format(PERSONAL_TWITTER, int(last_brake_fluid_delta))):
				tweet_sent = True
		else:
			logChecks += "[ ]BrakeFluid "
		if last_battery_coolant_delta >= maintenance_schedule['battery_coolant']:
			write_log('maintenance_bc', (odometer))
			logChecks += "[X]BatteryCoolant "
			if tweet(c, car, "WOW! {} time to change the battery coolant!! {} miles have already passed.".format(PERSONAL_TWITTER, int(last_battery_coolant_delta))):
				tweet_sent = True
		else:
			logChecks += "[ ]BatteryCoolant "
		#To check if tire rotation math is working correctly
		#write_log('log', "Last rotation done {} miles ago.".format(last_tire_rotation_delta))
		write_log('log', "Maintenance needed: {}".format(logChecks))
	
	if tweet_sent:
		return True

	return False

def get_location(c, car):
	#location = None
	wakeup_car(c, car)

	for v in c.vehicles:
		if v["display_name"] == car:
			try:
				d = v.data_request('drive_state')
				latitude = round(d["latitude"], 2)
				longitude = round(d["longitude"], 2)
			except urllib2.HTTPError as e:
				write_log('error', "Unable to get location.\nError: {}\n".format(e))
				latitude = False
				latitude = False
	#geolocator = Nominatim(user_agent="tesla reporter")
	#location = geolocator.reverse("{}, {}".format(latitude, longitude))
	#address = location.address.split(",")
	#city = address[-5].strip()
	#state = address[-3].strip()
	#return city, state
	# This is to get the city and state based on the coordinates, but TWITTER handles this.
	# Leaving this here in case is needed in future. Will need to import " from geopy.geocoders import Nominatim ".
	return latitude, longitude

def road_trip(c, car):
	g_latitude, g_longitude = get_location(c, car)

	gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
	reverse_geocode_result = gmaps.reverse_geocode((g_latitude, g_longitude))

	#[0] To get the first result, [2] To get the city's short name
	geo_city = reverse_geocode_result[0]['address_components'][2]['short_name']
	#[0] To get the first result, [4] To get the states's abbreviaton
	geo_state = (reverse_geocode_result[0]['address_components'][4]['short_name'])

	if tweet(c, car, "We on a road trip! I'm around {}, {}. Still on the road...".format(geo_city, geo_state)):
		return True
	
	return False

def tweet(c, car, message = "Opps... No message to broadcast for now! Have a good day!"):
	location = get_location(c, car)

	if location[0] and location[1]:
		for x in range(1,4):
			try:
				TWITTER.update_status(status= "{} | {}".format(message, HASHTAGS), lat= location[0], long= location[1]) 
				write_log('log', "Tweet (With Location): {}".format(message))
				return True
				break
			except Exception as e:
				if 'duplicate' in str(e):
					write_log('error', "Twitter posting. Tries ({}). Error: {}".format(x, 'Duplicate Tweet'))
					return False
					break
				else:
					write_log('error', "Twitter posting. Tries ({}). Error: {}".format(x, e))
					return False
	else:
		for x in range(1,4):
			try:
				TWITTER.update_status(status= "{} | {}".format(message, HASHTAGS)) 
				write_log('log', "Tweet (No Location): {}".format(message))
				return True
				break
			except Exception as e:
				if 'duplicate' in str(e):
					write_log('error', "Twitter posting. Tries ({}). Error: {}".format(x, 'Duplicate Tweet'))
					return False
					break
				else:
					write_log('error', "Twitter posting. Tries ({}). Error: {}".format(x, e))
					return False

def read_log(lookup=None):
	validData = ['create', 'milestone', 'maintenance_tr', 'maintenance_bf', 'maintenance_bc', 'charge', 'error', 'log']
	if lookup in validData:
		try:
			with open(LOG_PATH, "r") as f:
				lines = f.readlines()
				#return lines[-1]
				for i in reversed(lines):
					if lookup in i:
						return i.split("/")[-1].strip()
		except IOError:
			write_log('create')
			return False
	else:
		return False

def write_log(writeup=None, data=None):
	validData = ['create', 'milestone', 'maintenance_tr', 'maintenance_bf', 'maintenance_bc', 'charge', 'error', 'log']
	if writeup in validData:
		try:
			with open(LOG_PATH, "a") as f:
				f.write("\n{}: {}/{}".format(time.asctime(), writeup, str(data)))
		except Exception as e:
			return False
	else:
		return False

def main():
	global TWITTER
	TWITTER = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
	
	c, userCar = t_setup()
	if c and userCar:
		write_log('log', "Connected to {} successfully!".format(userCar))
	else:
		return 0
	logTweets = ""

	if monitor_odometer(c, userCar):
		logTweets += "[X]odometer "
	else:
		logTweets += "[ ]odometer "

	if monitor_charging(c, userCar):
		logTweets += "[X]charging "
	else:
		logTweets += "[ ]charging "
	
	if monitor_maintenance(c, userCar):
		logTweets += "[X]maintenance "
	else:
		logTweets += "[ ]maintenance "
	
	# Set the day-of-the-year you want this to run; in this case is only on 240 and 241
	if int(time.strftime("%j")) == 240 or int(time.strftime("%j")) == 241:
		if road_trip(c, userCar):
			logTweets += "[X]roadtrip "
		else:
			logTweets += "[ ]roadtrip "

	write_log('log', "Finished! Tweets: {}\n".format(logTweets))

main()


