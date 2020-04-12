from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException
import os
import time
import random

from Bot import Bot

class TwitterBot(Bot):

    def __init__ (self, username, password):
        super().__init__(username, password)        

        self.site = "Twitter"
        self.base_url = "https://www.twitter.com/"


    def login(self):
        self.driver = webdriver.Chrome(executable_path="/Users/romes/everything-else/botdev/organized/likebots/chromedriver", options=self.chrome_options)
        self.driver.get(self.base_url + "login")

        time.sleep(1)
        self.driver.find_element_by_name("session[username_or_email]").send_keys(self.username)
        self.driver.find_element_by_name("session[password]").send_keys(self.password)
        self.driver.find_element_by_css_selector('div[role="button"][data-testid="LoginForm_Login_Button"]').click()

        time.sleep(2)


    def like_posts(self, hashtag, maxLikesPerHashtag):
        current_posts_seen = 0
        self.driver.get(self.base_url + "hashtag/" + hashtag)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        while (current_posts_seen < maxLikesPerHashtag and self.likes_given < self.max_likes):
            time.sleep(2)
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            tweet_hearts = self.driver.find_elements_by_css_selector("div[data-testid='like']")

            for heart in tweet_hearts:
                print(self.driver.execute_script("return arguments[0].getBoundingClientRect();", heart)['y'])

            element_y = 0
            for heart in tweet_hearts:

                element_y += element_y - self.driver.execute_script("return arguments[0].getBoundingClientRect();", heart)['y']
                print(element_y)
                self.driver.execute_script("window.scrollTo(0, {})".format(element_y-107)) #200 for twitter's top nav bar 

                time.sleep(5)

                self.posts_seen += 1
                current_posts_seen += 1

                chanceToLikePost = random.uniform(0.6, 0.85)
                r = random.random()

                # if(r <= chanceToLikePost):

                self.likes_given+=1

                waitTimeToLike = random.uniform(1, 3)
                time.sleep(waitTimeToLike)

                heart.click()

                waitTimeToMoveOn = random.uniform(0.2, 0.6)
                time.sleep(waitTimeToMoveOn)


        # self.driver.execute_script("window.scrollTo(0, {})".format(last_height+500))
        time.sleep(3)
        new_height = self.driver.execute_script("return document.body.scrollHeight")

        


    def like_hashtags(self, hashtags):

        mlphAux = int(((self.max_likes/len(hashtags))+1)*(random.randrange(2, 5)))
        max_likes_per_hashtag = random.randrange(int(mlphAux*0.9), mlphAux+1)

        while(self.likes_given<self.max_likes):
            for hashtag in hashtags:
                self.like_posts(hashtag, max_likes_per_hashtag)
                if(self.likes_given>=self.max_likes):
                    break
            time.sleep(random.randrange(4, 8))


    def run(self, params):

        self.max_likes = random.randrange(int(params[1]*0.90), params[1]+1)

        super().print_bot_starting()

        if(self.max_likes<=0):
            return

        # self.login()
        # self.like_hashtags(params[0])
        self.quit()