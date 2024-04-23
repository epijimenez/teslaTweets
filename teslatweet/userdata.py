import sys
from requests_oauthlib import OAuth1Session
import teslapy
import googlemaps

"""
TWITTER ACCOUNT
"""
TWITTER_APP_KEY = "TWITTER_APP_KEY"
TWITTER_APP_SECRET = "TWITTER_APP_SECRET"
TWITTER_OAUTH_TOKEN = "TWITTER_OAUTH_TOKEN"
TWITTER_OAUTH_TOKEN_SECRET = "TWITTER_OAUTH_TOKEN_SECRET"
TWITTER_HASHTAGS = "#TeslaTweets #Tesla"  # Included in every outgoing tweet.
TWITTER_PERSONAL = "@your_account"  # Account to ping when maintenance is needed

"""
TESLA ACCOUNT
"""
TESLA_USER_EMAIL = "TESLA_USER_EMAIL"
TESLA_USER_CAR = "TESLA_USER_CAR"
TESLA_REFRESH_TOKEN = "TESLA_REFRESH_TOKEN"

"""
GOOGLE ACCOUNT
"""
GOOGLE_API_KEY = "GOOGLE_API_KEY"


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
                print(f"Error: Unable to setup Twitter account [{e}]")
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
                print(f"Error: Unable to setup Tesla account [{e}]")
                sys.exit()
            try:
                for vehicle in tesla_account.vehicle_list():
                    if vehicle["display_name"] == TESLA_USER_CAR:
                        try:
                            vehicle.sync_wake_up()
                            # write_log('log', "Connected to {} successfully!".format(str(vehicle["display_name"])))
                            self._tesla = vehicle
                        except teslapy.VehicleError as e:
                            print(f"Error: Unable to connect Tesla car [{e}]")
                            # write_log('error',
                            #           "Unable to contact {}. Error: {}: {}".format(USER_TESLA_CAR, e))
                # write_log('error', "Couldn't find {} in your garage.".format(USER_TESLA_CAR))
                print(f"Error: Unable to find to Tesla car [{TESLA_USER_CAR}]")
            except teslapy.HTTPError as e:
                print(f"Error: Unable to setup Tesla account [{e}]")
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
            try:
                self._google = googlemaps.Client(key=GOOGLE_API_KEY)
            except Exception as e:
                print(f"Error: Unable to setup Google account [{e}]")

            return self._google
