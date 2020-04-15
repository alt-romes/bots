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
import random

from Bot import Bot

class TwitterBot(Bot):

    def __init__ (self, username, password):
        self.platform = "Twitter"
        self.base_url = "https://www.twitter.com/"

        super().__init__(username, password)        


    def login(self):
        login_url = self.base_url + "login"
        self.driver.get(login_url)

        time.sleep(5)

        if (self.driver.current_url != login_url):
            return        

        self.driver.find_element_by_name("session[username_or_email]").send_keys(self.username)
        self.driver.find_element_by_name("session[password]").send_keys(self.password)
        self.driver.find_element_by_css_selector('div[role="button"][data-testid="LoginForm_Login_Button"]').click()

        time.sleep(2)


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
                    except ElementClickInterceptedException:
                        pass
                    finally:
                        self.posts_seen += 1
                        current_posts_seen += 1
                        self.likes_given+=1
                        liked=True
                else:
                    hearts = self.driver.find_elements_by_css_selector("div[data-testid='like']")
                body.send_keys(Keys.DOWN)
                
        time.sleep(3)

        


    def like_hashtags(self, hashtags):

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


    def run(self, params):


        self.max_likes = random.randrange(int(params[1]*0.90), params[1]+1)

        super().print_bot_starting()

        if(self.max_likes<=0):
            return

        self.driver = webdriver.Chrome(executable_path="/Users/romes/everything-else/botdev/organized/likebots/chromedriver", options=self.chrome_options)

        self.login()
        self.like_hashtags(params[0])
        self.quit()