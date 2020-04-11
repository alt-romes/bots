from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException

import os
import time
import random

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
        

    def get_username(self):
        return self.username

    def get_likes_given(self):
        return self.likes_given

    def get_site(self):
        return self.site

    def get_max_likes(self):
        return self.max_likes

    def quit(self):
        print("%-------------------------------------------------------%")
        print("Liked " + str(self.likes_given) + " posts for account " + self.username + " in " + self.base_url)
        print("%-------------------------------------------------------%")
        self.driver.quit()