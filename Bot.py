#External Dependencies
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

from Database import Database

import config

class Bot:

    FINISHED_LEVEL = 42
    LOG_FILENAME = 'logs/bots.log'

    def __init__(self, username, password, database_path=None):
        self.username = username
        self.password = password

        self.db = None
        if database_path is not None:
            self.db = Database(database_path)
            self.db.create_account((self.get_username(), self.get_platform()))

        self.driver = None
        self._config_chromedriver()

        self.likes_given = 0
        self.max_likes = "-"
        self.posts_seen = 0
        self.time_started = datetime.datetime.now()
        self.time_ended = 0

        self.status = "Unknown Failure"

        self.is_logged_in = False

        self._init_logger()

    def _config_chromedriver(self):
        self.chrome_options = webdriver.ChromeOptions()

        if not ("--debug" in sys.argv):
            self.chrome_options.add_argument("--headless")

        self.chrome_options.add_argument("--window-size=1200x800")
        self.chrome_options.add_argument("--mute-audio")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--disable-notifications")
        self.chrome_options.add_argument("--enable-automation")

        self.chrome_options.add_argument("--user-data-dir=/Users/romes/everything-else/botdev/organized/likebots/profiles/"+self.platform+"/"+self.username)


    def _init_logger(self):
        logging.addLevelName(self.FINISHED_LEVEL, "FINISHED")
        format = '%(asctime)s | %(levelname)8s | %(platform)9s | %(username)s > %(message)s'
        logging.basicConfig(format=format, datefmt='%Y-%m-%d %H:%M:%S')
        self.logging = logging

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Remove all extra handlers. Needs to be redone if I ever need more than one handler - or want to clean this up in a way that handlers don't overlap ?
        if self.logger.handlers:
            self.logger.handlers.clear()

        handler = logging.handlers.RotatingFileHandler(self.LOG_FILENAME, maxBytes=20000000, backupCount=2) #Max size = 20 MB
        handler.setFormatter(logging.Formatter(format, datefmt='%Y-%m-%d %H:%M:%S'))
        self.logger.addHandler(handler)


    # Level is of type int, call using logging.LEVEL (ex: logging.WARNING)
    # Msg is the string to log
    def log(self, level, msg):
        extra = {'platform': self.platform, 'username': self.username}
        self.logger.log(level, msg, extra=extra)

        #Send message to discord
        if level >= logging.ERROR:
            discord_message = {
                "content": msg[:2000],
                "username": self.username + " (" + self.platform + ")"
            }
            try:
                r = requests.post(config.ERROR_WEBHOOK, data=discord_message)
            except Exception as e:
                self.log(self.logging.ERROR, "Failed post to discord: " + str(e))

            time.sleep(2)
            try: 
                r.raise_for_status()
            except requests.exceptions.HTTPError as e: 
                self.log(logging.WARNING, "Failed post to discord : " + str(e))


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
                time.sleep(0.1)

            # Wait to load the page.
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
        return "This method must be implemented by subclasses! Also, I should learn how OOP works in python..."

    def quit(self):
        if self.get_likes_given()<self.get_max_likes() or self.get_max_likes()>0:
            self.log(self.FINISHED_LEVEL, self.get_report_string())

        self.time_ended = datetime.datetime.now()
        
        if self.db is not None:
            self.db.close()

        if self.driver is not None:
            self.driver.quit()
            self.driver = None