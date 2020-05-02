from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
import time
import datetime
import random
import logging

from Bot import Bot

class TwitterBot(Bot):

    def __init__ (self, username, password, database=None):
        self.platform = "Twitter"
        self.base_url = "https://www.twitter.com/"

        super().__init__(username, password, database)        


    def login(self):
        login_url = self.base_url + "login"
        self.driver.get(login_url)

        time.sleep(5)

        if (self.driver.current_url != login_url):
            self.log(logging.NOTSET, "Already logged in.")
            self.is_logged_in = True
            return        

        self.driver.find_element_by_name("session[username_or_email]").send_keys(self.username)
        self.driver.find_element_by_name("session[password]").send_keys(self.password)
        self.driver.find_element_by_css_selector('div[role="button"][data-testid="LoginForm_Login_Button"]').click()

        self.is_logged_in = True

        time.sleep(2)

        self.log(logging.INFO, "Logged in.")


    def like_posts(self, hashtag, maxLikesPerHashtag):
        current_posts_seen = 0
        self.driver.get(self.base_url + "hashtag/" + hashtag)
        time.sleep(2)
        body = self.driver.find_element_by_css_selector('body')
        
        
        #Each iteration is a like
        while (current_posts_seen < maxLikesPerHashtag and self.likes_given < self.max_likes):
            time.sleep(random.randrange(1,2))

            hearts = self.driver.find_elements_by_css_selector("div[data-testid='like']")

            liked = False
            while not liked:
                if len(hearts)>0:
                    try:
                        hearts[0].click()
                        self.posts_seen += 1
                        current_posts_seen += 1
                        self.likes_given+=1
                        liked=True
                        self.log(logging.INFO, "Liked tweet.")
                    except ElementClickInterceptedException:
                        self.log(logging.NOTSET, "Twitter scrolling by. . .")
                else:
                    hearts = self.driver.find_elements_by_css_selector("div[data-testid='like']")
                body.send_keys(Keys.DOWN)
                
        time.sleep(3)

        


    def like_hashtags(self, hashtags):
        try:
            if self.db is not None:
                self.db.add_account_hashtags( list( map( (lambda hashtag: (self.get_username(), self.get_platform(), hashtag)), hashtags) ) )

            mlphAux = int(((self.max_likes/len(hashtags))+1)*(random.randrange(2, 5)))
            max_likes_per_hashtag = random.randrange(int(mlphAux*0.9), mlphAux+1)

            random.shuffle(hashtags)

            while(self.likes_given<self.max_likes):
                for hashtag in hashtags:
                    self.like_posts(hashtag, max_likes_per_hashtag)
                    if(self.likes_given>=self.max_likes):
                        break
                time.sleep(random.randrange(4, 8))

            self.status = "Success"
        except KeyboardInterrupt as e:
            self.status = "KeyboardInterrupt"
            raise e

        except Exception as e:
            self.log(logging.ERROR, str(e))

        finally:
            if self.db is not None:
                self.db.create_likejob((self.get_username(), self.get_platform(), self.get_likes_given(), self.get_max_likes(), self.get_status(), self.get_time_started(), datetime.datetime.now(), self.get_posts_seen()))

    def run(self, params):

        try:
            self.max_likes = random.randrange(int(params[1]*0.90), params[1]+1)

            super().print_bot_starting()

            if(self.max_likes>0):
                self.driver = self.init_driver()

                self.login()
                self.like_hashtags(params[0])

        except Exception as e:
            self.log(logging.ERROR, str(e))
        finally:
            self.quit()

    
    def get_report_string(self, driver=None):
        return ("Liked [ " + str(self.get_likes_given()) + " / " + str(self.get_max_likes()) + " ] tweets.")