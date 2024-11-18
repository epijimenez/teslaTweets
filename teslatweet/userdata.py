import sys
from requests_oauthlib import OAuth1Session
import teslapy
import googlemaps
import os.path
import json
import logging


home_dir = os.getenv('HOME')
dir_teslatweet_userdata = f"{home_dir}/teslatweet-data.json"

# checking if the user data file is available
if os.path.isfile(dir_teslatweet_userdata):
    # opening json file
    with open(dir_teslatweet_userdata, 'r') as openfile:
        json_object = json.load(openfile)

    # checking if there is default data
    if json_object["TWITTER_APP_KEY"] == "TWITTER_APP_KEY":
        raise Exception(f"User data has default values. Please update {dir_teslatweet_userdata}")

    TWITTER_APP_KEY = json_object["TWITTER_APP_KEY"]
    TWITTER_APP_SECRET = json_object["TWITTER_APP_SECRET"]
    TWITTER_OAUTH_TOKEN = json_object["TWITTER_OAUTH_TOKEN"]
    TWITTER_OAUTH_TOKEN_SECRET = json_object["TWITTER_OAUTH_TOKEN_SECRET"]
    TWITTER_HASHTAGS = json_object["TWITTER_HASHTAGS"]
    TWITTER_PERSONAL = json_object["TWITTER_PERSONAL"]
    TESLA_USER_EMAIL = json_object["TESLA_USER_EMAIL"]
    TESLA_USER_CAR = json_object["TESLA_USER_CAR"]
    TESLA_REFRESH_TOKEN = json_object["TESLA_REFRESH_TOKEN"]
    GOOGLE_API_KEY = json_object["GOOGLE_API_KEY"]
else:
    # creating the user data file so the user can add their data
    logging.warning(f"Need to configure user data in {dir_teslatweet_userdata}")
    logging.info("> Get Twitter data from: https://developer.twitter.com")
    logging.info("> Get Tesla data from: https://www.tesla.com/teslaaccount, and Auth for Tesla (iOS App)")
    logging.info("> Get Google data from (optional): https://console.cloud.google.com")
    dictionary = {
        "TWITTER_APP_KEY": "TWITTER_APP_KEY",
        "TWITTER_APP_SECRET": "TWITTER_APP_SECRET",
        "TWITTER_OAUTH_TOKEN": "TWITTER_OAUTH_TOKEN",
        "TWITTER_OAUTH_TOKEN_SECRET": "TWITTER_OAUTH_TOKEN_SECRET",
        "TWITTER_HASHTAGS": "#TeslaTweets #Tesla",
        "TWITTER_PERSONAL": "@your_account",
        "TESLA_USER_EMAIL": "TESLA_USER_EMAIL",
        "TESLA_USER_CAR": "TESLA_USER_CAR",
        "TESLA_REFRESH_TOKEN": "TESLA_REFRESH_TOKEN",
        "GOOGLE_API_KEY": "GOOGLE_API_KEY"
    }

    json_object = json.dumps(dictionary, indent=4)

    with open(dir_teslatweet_userdata, "w") as outfile:
        outfile.write(json_object)

    raise Exception(f"No user data provided. Please update {dir_teslatweet_userdata}")


class UserAccount:
    def __init__(self):
        self._twitter = None
        self._tesla = None
        self._google = None
        self._twitter_extras_hashtags = None
        self._twitter_extras_ping_account = None

    @property
    def twitter(self):
        """
        Set up your Twitter account (https://developer.twitter.com)
        :return:
        """
        if self._twitter is None:
            try:
                self._twitter = OAuth1Session(
                    client_key=TWITTER_APP_KEY,
                    client_secret=TWITTER_APP_SECRET,
                    resource_owner_key=TWITTER_OAUTH_TOKEN,
                    resource_owner_secret=TWITTER_OAUTH_TOKEN_SECRET,
                )
            except Exception as e:
                logging.error(f"Unable to setup Twitter account [{e}]")
                sys.exit()

        return self._twitter

    @property
    def twitter_extras_ping_account(self):
        if self._twitter_extras_ping_account is None:
            self._twitter_extras_ping_account = TWITTER_PERSONAL
        return self._twitter_extras_ping_account

    @property
    def twitter_extras_hashtags(self):
        if self._twitter_extras_hashtags is None:
            self._twitter_extras_hashtags = TWITTER_HASHTAGS
        return self._twitter_extras_hashtags

    @property
    def tesla(self):
        """
        Set up your Tesla account (https://www.tesla.com/teslaaccount) and
        refresh token from the iOS App (Auth for Tesla)
        :return:
        """
        if self._tesla is None:
            try:
                tesla_account = teslapy.Tesla(TESLA_USER_EMAIL)
                if not tesla_account.authorized:
                    tesla_account.refresh_token(refresh_token=TESLA_REFRESH_TOKEN)
            except teslapy.HTTPError as e:
                logging.error(f"Unable to setup Tesla account [{e}]")
                sys.exit()
            try:
                for vehicle in tesla_account.vehicle_list():
                    if vehicle["display_name"] == TESLA_USER_CAR:
                        try:
                            vehicle.sync_wake_up()
                            # write_log('log', "Connected to {} successfully!".format(str(vehicle["display_name"])))
                            self._tesla = vehicle
                            break
                        except teslapy.VehicleError as e:
                            logging.error(f"Unable to connect Tesla car [{e}]")
                            # write_log('error',
                            #           "Unable to contact {}. Error: {}: {}".format(USER_TESLA_CAR, e))
                # write_log('error', "Couldn't find {} in your garage.".format(USER_TESLA_CAR))
                logging.error(f"Unable to find to Tesla car [{TESLA_USER_CAR}]")
            except teslapy.HTTPError as e:
                logging.error(f"Unable to setup Tesla account [{e}]")
                # write_log('error',
                #           "Unable to contact {}. Error: {}: {}".format(USER_TESLA_CAR, e))
        if self._tesla is not None:
            return self._tesla

    @property
    def google(self):
        """
        Set up your Google account (https://console.cloud.google.com)
        :return:
        """
        if self._google is None:
            if GOOGLE_API_KEY == "GOOGLE_API_KEY":
                logging.error(f"No Google Account provided in {dir_teslatweet_userdata}")
                self._google = None
            try:
                self._google = googlemaps.Client(key=GOOGLE_API_KEY)
            except Exception as e:
                logging.error(f"Unable to setup Google account [{e}]")
                self._google = None

            return self._google
