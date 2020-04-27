"""
Dependencies:

have google chrome in default apps folder
download a chromedriver compatible with your chrome version (it's probably the latest) and put it in PATH
pip install selenium

Version i'm using: 81

"""
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import WebDriverException

import logging
import logging.handlers
import os
import datetime
import time
import random
import sys
import requests
import json
import pickle

from Database import Database

import config

class Bot:

    FINISHED_LEVEL = 42
    #TODO: Make it so that the log is not inside of a directory because the program can't create directories
    LOG_FILENAME = 'logs/bots.log'

    def __init__(self, username="", password="", database_path=None, logBot=False):

        self._init_logger()
        
        if logBot:
            self.username = "Main"
            self.platform = "Log"
            return

        self.username = username
        self.password = password

        self.db = None
        if database_path is not None:
            self.db = Database(database_path)
            self.db.create_account((self.get_username(), self.get_platform()))

        self.driver = None
        
        self.likes_given = 0
        self.max_likes = 0
        self.posts_seen = 0
        self.time_started = datetime.datetime.now()
        self.time_ended = 0

        self.status = "Unknown Error"

        self.is_logged_in = False


    def _init_logger(self):
        logging.addLevelName(self.FINISHED_LEVEL, "FINISHED")
        format = '%(asctime)s | %(levelname)8s | %(platform)9s | %(username)s > %(message)s'
        logging.basicConfig(format=format, datefmt='%Y-%m-%d %H:%M:%S')

        self.logger = logging.getLogger(__name__)
        if "--debug" in sys.argv:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

        # Remove all extra handlers. Needs to be redone if I ever need more than one handler - or want to clean this up in a way that handlers don't overlap ?
        if self.logger.handlers:
            self.logger.handlers.clear()

        handler = logging.handlers.RotatingFileHandler(self.LOG_FILENAME, maxBytes=20000000, backupCount=2) #Max size = 20 MB
        handler.setFormatter(logging.Formatter(format, datefmt='%Y-%m-%d %H:%M:%S'))
        self.logger.addHandler(handler)

    def init_driver(self, managefunction="", user_agent=""):
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument("--window-size=1200x800")

        #TODO: Use Chromium?

        if user_agent == "mobile":
            self.chrome_options.add_argument("--user-agent={}".format("Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"))

        #TODE(to decide): Use custom browser agent?
        # else:
        #     self.chrome_options.add_argument("--user-agent={}".format("Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"))

        if managefunction == "":
            user_data_dir = os.path.abspath("profiles/{}/{}".format(self.platform, self.username))
        else:
            user_data_dir = os.path.abspath("profiles/managers/{}/{}/{}".format(self.platform, self.username, managefunction))
        
        self.user_data_dir = user_data_dir

        self.chrome_options.add_argument("--user-data-dir={}".format(user_data_dir)) #TODO: Should I Keep The Data Dir ??
        self.log(logging.DEBUG, "Chrome --user-data-dir set to " + user_data_dir)

        if "--debug" not in sys.argv or "--headless" in sys.argv :
            self.chrome_options.add_argument("--headless")

        self.first_run = True
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            try:
                cookies = pickle.load(open("{}/cookies.pkl".format(user_data_dir), "rb"))
            except FileNotFoundError:
                self.log(logging.INFO, "Running for the first time! Setting up profiles...")
            else:
                self.first_run = False
                driver.get(self.base_url)
                for cookie in cookies:
                    driver.add_cookie(cookie)
            return driver
        except Exception as e:
            self.log(logging.ERROR, "While setting up driver: " + str(e))
            raise e


    def log(self, level, message):
        """
            Level is of type int, call using logging.LEVEL (ex: logging.WARNING)
            Msg is the string to log
        """
        extra = {'platform': self.platform, 'username': self.username}
        self.logger.log(level, message, extra=extra)

        if message == '':
            message = "No error message :("

        msgs = [message[i:i+2000] for i in range(0, len(message), 2000)]

        #Send message to discord
        if level >= logging.ERROR:
            for msg in msgs:
                discord_message = {
                    "content": msg[:2000],
                    "username": self.username + " (" + self.platform + ")"
                }
                try:
                    r = requests.post(config.ERROR_WEBHOOK, data=discord_message)
                except Exception as e:
                    self.log(logging.ERROR, "Failed post to discord: " + str(e))

                time.sleep(2)
                try: 
                    r.raise_for_status()
                except requests.exceptions.HTTPError as e: 
                    self.log(logging.WARNING, "Failed post to discord : " + str(e))
                time.sleep(1)


    def print_bot_starting(self):
        string = self.get_username() + " in " + self.get_platform() + " [ " + str(self.get_likes_given()) + " / " + str(self.get_max_likes()) + " ]"
        if self.get_max_likes()<1:
            self.log(logging.WARNING, "Uninitiated: " + string)
        else:
            self.log(logging.INFO, "Starting: " + string)


    def scroll_down(self, element, modifier=1):
        """A method for scrolling the page."""

        # Get scroll height.
        last_height = self.driver.execute_script("return arguments[0].scrollHeight", element)

        while True:

            # Scroll down to the bottom.
            for i in range(1, int(1/modifier)+1):
                self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight*arguments[1]);", element, modifier*i)
                time.sleep(0.2)

            # Wait to load more followers.
            time.sleep(2)

            # Calculate new scroll height and compare with last scroll height.
            new_height = self.driver.execute_script("return arguments[0].scrollHeight", element)

            if new_height == last_height:

                break

            last_height = new_height        

    def get_status(self):
        return self.status

    def get_username(self):
        return self.username

    def get_likes_given(self):
        return self.likes_given

    def get_platform(self):
        return self.platform

    def get_max_likes(self):
        return self.max_likes

    def get_posts_seen(self):
        return self.posts_seen

    def get_time_started(self):
        return self.time_started

    def get_time_ended(self):
        return self.time_ended

    def should_like_post(self, min=0.6, max=0.85):
        chanceToLikePost = random.uniform(min, max)
        r = random.random()
        return r <= chanceToLikePost
        
    def get_report_string(self):
        return "This method must be implemented by subclasses! Also, I should learn better how OOP works in python..."

    def quit(self, driver=None):
        if driver==None:
            driver = self.driver

        if self.get_likes_given()<self.get_max_likes() or self.get_max_likes()>0:
            self.log(self.FINISHED_LEVEL, self.get_report_string())

        try:
            pickle.dump( driver.get_cookies() , open("{}/cookies.pkl".format(self.user_data_dir),"wb") )
        except Exception as e:
            self.log(logging.ERROR, "Probably there is no user data dir set:\nUser data dir: {}.\nError: {}".format(self.user_data_dir, e))

        self.time_ended = datetime.datetime.now()
        
        if self.db is not None:
            self.db.close()

        if driver is not None:
            driver.quit()
            driver = None