from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException

import logging
import os
import time
import random
import sys

from bcolors import bcolors

class Bot:
    def __init__(self, username, password):
        self.username = username
        self.password = password

        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--window-size=1200x800")

        self.username = username
        self.password = password
        
        self.driver = None

        self.likes_given = 0
        self.max_likes = "-"
        self.posts_seen = 0

        format = "%(asctime)s: %(message)s"
        logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

    def print_bot_starting(self):
        string = "Starting: " + self.get_username() + " in " + self.get_site() + " [ " + str(self.get_likes_given()) + " / " + str(self.get_max_likes()) + " ]"
        if(len(sys.argv)>2 and sys.argv[2]=="--no-colors"):
            logging.info(string)
        else:
            if self.get_max_likes()<1:
                logging.info(bcolors.WARNING + string + bcolors.ENDC)
            else:
                logging.info(bcolors.OKBLUE + string + bcolors.ENDC)

    def get_username(self):
        return self.username

    def get_likes_given(self):
        return self.likes_given

    def get_site(self):
        return self.site

    def get_max_likes(self):
        return self.max_likes

    def quit(self):
        string = ("Finished: " + self.get_username() + " in " + self.get_site() + " [ " + str(self.get_likes_given()) + " / " + str(self.get_max_likes()) + " ]")
        if(len(sys.argv)>2 and sys.argv[2]=="--no-colors"):
            logging.info(string)
        else:
            if self.get_likes_given()<self.get_max_likes():
                logging.info(bcolors.FAIL + string + bcolors.ENDC)
            elif self.get_max_likes()==0:
                logging.info(bcolors.WARNING + string + bcolors.ENDC)
            else:
                logging.info(bcolors.OKGREEN + string + bcolors.ENDC)
        # print("%-------------------------------------------------------%")
        # print("Liked " + str(self.likes_given) + " posts for account " + self.username + " in " + self.base_url)
        # print("%-------------------------------------------------------%")
        self.driver.quit()