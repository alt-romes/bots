from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import WebDriverException

import logging
import os
import datetime
import time
import random
import sys

from bcolors import bcolors

from Database import Database

class Bot:

    def __init__(self, username, password, database_path=None):
        self.username = username
        self.password = password
        self.db = None

        if database_path is not None:
            self.db = Database(database_path)
            self.db.create_account((self.get_username(), self.get_platform()))

        self.chrome_options = webdriver.ChromeOptions()

        if not ("--debug" in sys.argv):
            self.chrome_options.add_argument("--headless")

        self.chrome_options.add_argument("--window-size=1200x800")
        self.chrome_options.add_argument("--mute-audio")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--disable-notifications")
        self.chrome_options.add_argument("--enable-automation")

        self.chrome_options.add_argument("--user-data-dir=/Users/romes/everything-else/botdev/organized/likebots/profiles/"+self.platform+"/"+username)

        self.username = username
        self.password = password
        
        self.driver = None

        self.likes_given = 0
        self.max_likes = "-"
        self.posts_seen = 0

        self.time_started = datetime.datetime.now()
        self.time_ended = 0

        self.status = "Unknown Failure"

        self.is_logged_in = False

        format = "%(asctime)s: %(message)s"
        logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")


    def print_bot_starting(self):
        string = "Starting: " + self.get_username() + " in " + self.get_platform() + " [ " + str(self.get_likes_given()) + " / " + str(self.get_max_likes()) + " ]"
        if("--no-colors" in sys.argv):
            logging.info(string)
        else:
            if self.get_max_likes()<1:
                logging.info(bcolors.WARNING + string + bcolors.ENDC)
            else:
                logging.info(bcolors.OKBLUE + string + bcolors.ENDC)


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

    def quit(self):
        string = ("Finished: " + self.get_username() + " in " + self.get_platform() + " [ " + str(self.get_likes_given()) + " / " + str(self.get_max_likes()) + " ]")
        if("--no-colors" in sys.argv):
            logging.info(string)
        else:
            if self.get_likes_given()<self.get_max_likes():
                logging.info(bcolors.FAIL + string + bcolors.ENDC)
            elif self.get_max_likes()==0:
                logging.info(bcolors.WARNING + string + bcolors.ENDC)
            else:
                logging.info(bcolors.OKGREEN + string + bcolors.ENDC)

        self.time_ended = datetime.datetime.now()
        
        if self.db is not None:
            self.db.close()


        if self.driver is not None:
            self.driver.quit()
            self.driver = None