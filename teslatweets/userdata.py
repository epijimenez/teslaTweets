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
    print("> Get Twitter data from: https://developer.twitter.com")
    print("> Get Tesla data from: https://www.tesla.com/teslaaccount, and Auth for Tesla (iOS App)")
    print("> Get Google data from (optional): https://console.cloud.google.com")

    run_setup = input("\nRun first time boot setup now? (y/n): ")[0].lower()
    if run_setup != "y":
        exit()

    print(f"Running first time boot to gather user data")

    TWITTER_APP_KEY = "TWITTER_APP_KEY"
    TWITTER_APP_SECRET = "TWITTER_APP_SECRET"
    TWITTER_OAUTH_TOKEN = "TWITTER_OAUTH_TOKEN"
    TWITTER_OAUTH_TOKEN_SECRET = "TWITTER_OAUTH_TOKEN_SECRET"
    TWITTER_HASHTAGS = "TWITTER_HASHTAGS"
    TWITTER_PERSONAL = "TWITTER_PERSONAL"
    TESLA_USER_EMAIL = "TESLA_USER_EMAIL"
    TESLA_USER_CAR = "TESLA_USER_CAR"
    TESLA_REFRESH_TOKEN = "TESLA_REFRESH_TOKEN"
    GOOGLE_API_KEY = "GOOGLE_API_KEY"

    for n in range(3):
        verified_twitter = "n"
        verified_tesla = "n"
        verified_google = "n"
        if verified_twitter == "y" and verified_tesla == "y" and verified_google == "y":
            break
        if verified_twitter == "n":
            print(f"\nGathering Twitter data...")
            TWITTER_APP_KEY = input("Twitter App Key: ")
            TWITTER_APP_SECRET = input("Twitter App Secret: ")
            TWITTER_OAUTH_TOKEN = input("Twitter OAuth Token: ")
            TWITTER_OAUTH_TOKEN_SECRET = input("Twitter OAuth Token Secret: ")
            TWITTER_HASHTAGS = "#TeslaTweets"
            TWITTER_PERSONAL = input("Twitter Username: ")

            print("Verify Twitter Data:")
            print(f"TWITTER_APP_KEY: \t{TWITTER_APP_KEY}")
            print(f"TWITTER_APP_SECRET: \t{TWITTER_APP_SECRET}")
            print(f"TWITTER_OAUTH_TOKEN: \t{TWITTER_OAUTH_TOKEN}")
            print(f"TWITTER_OAUTH_TOKEN_SECRET: \t{TWITTER_OAUTH_TOKEN_SECRET}")
            #print(f"TWITTER_HASHTAGS: \t{TWITTER_HASHTAGS}")
            print(f"TWITTER_PERSONAL: \t{TWITTER_PERSONAL}")
            verified_twitter = input("Twitter Data Correct? (y/n): ")[0].lower()

        if verified_tesla == "n":
            print(f"\nGathering Tesla data...")
            TESLA_USER_EMAIL = input("Tesla User Email: ")
            TESLA_USER_CAR = input("Tesla Car's Name: ")
            TESLA_REFRESH_TOKEN = input("Tesla Refresh Token: ")

            print("Verify Tesla data:")
            print(f"TESLA_USER_EMAIL: \t{TESLA_USER_EMAIL}")
            print(f"TESLA_USER_CAR: \t{TESLA_USER_CAR}")
            print(f"TESLA_REFRESH_TOKEN: \t{TESLA_REFRESH_TOKEN}")
            verified_tesla = input("Twitter Tesla Correct? (y/n): ")[0].lower()

        if verified_google == "n":
            print(f"\nGathering Google data...")
            GOOGLE_API_KEY = input("Google API Key (optional, press Enter to skip): ")
            if len(GOOGLE_API_KEY) < 10:
                GOOGLE_API_KEY = "GOOGLE_API_KEY"
                verified_google = "y"
            else:
                print("Verify Google data:")
                print(f"GOOGLE_API_KEY: \t{GOOGLE_API_KEY}")
                verified_google = input("Twitter Google Correct? (y/n): ")[0].lower()

    dictionary = {
        "TWITTER_APP_KEY": TWITTER_APP_KEY,
        "TWITTER_APP_SECRET": TWITTER_APP_SECRET,
        "TWITTER_OAUTH_TOKEN": TWITTER_OAUTH_TOKEN,
        "TWITTER_OAUTH_TOKEN_SECRET": TWITTER_OAUTH_TOKEN_SECRET,
        "TWITTER_HASHTAGS": TWITTER_HASHTAGS,
        "TWITTER_PERSONAL": TWITTER_PERSONAL,
        "TESLA_USER_EMAIL": TESLA_USER_EMAIL,
        "TESLA_USER_CAR": TESLA_USER_CAR,
        "TESLA_REFRESH_TOKEN": TESLA_REFRESH_TOKEN,
        "GOOGLE_API_KEY": GOOGLE_API_KEY
    }

    json_object = json.dumps(dictionary, indent=4)

    with open(dir_teslatweet_userdata, "w") as outfile:
        outfile.write(json_object)
        logging.warning(f"User data file created at {dir_teslatweet_userdata}. Please run again.")

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
