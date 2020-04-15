from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException

from Bot import Bot

import os
import time
import random

class SubmitHubBot(Bot):

    def __init__ (self, username, password):
        self.platform = "SubmitHub"
        self.base_url = "https://www.submithub.com/"
        super().__init__(username, password)

        self.chrome_options.add_argument("--mute-audio")


    def login(self):
        login_url = self.base_url + "login"
        self.driver.get(login_url)
        time.sleep(5)

        if (self.driver.current_url != login_url):
            return

        self.driver.find_element_by_id("usernameOrEmail").send_keys(self.username)
        self.driver.find_element_by_id("password").send_keys(self.password)
        self.driver.find_element_by_xpath('//*[@id="my-account-login"]/form/div[3]/button[1]').click()

        time.sleep(5)

    def listen_time(self):
        return random.randrange(49, 81)
    
    def like_music(self):
        time.sleep(5)
        isPremium = self.driver.find_elements_by_class_name("premium-circle")!=[]
        if(self.driver.find_elements_by_class_name('spinner')==[]):
            self.driver.find_element_by_css_selector("div.hot-or-not-track>div.circle.left").click()
            time.sleep(3)
            if(self.driver.find_elements_by_class_name('spinner')==[]):
                if(isPremium):
                    self.driver.find_element_by_css_selector('body').send_keys(Keys.PAGE_DOWN)
                time.sleep(1)
                self.driver.find_element_by_class_name('skip-hot-or-not').click()
                return False
        self.posts_seen+=1
        listen_time = self.listen_time()
        time.sleep(listen_time)
        if(isPremium):
            stars = self.driver.find_elements_by_class_name("hot-or-not-star")
            for i in range(3):
                if(i==2):
                    self.driver.find_element_by_css_selector('body').send_keys(Keys.PAGE_DOWN)
                time.sleep(1)
                stars[random.randrange(3, 5) + (i*5)].click()
                time.sleep(1)
                
        self.driver.find_element_by_class_name('thumb-up').click()
        time.sleep(random.randrange(8, 16))
        self.driver.find_element_by_class_name('skip-next').click()
        self.likes_given+=1


    def hot_or_not(self):


        self.driver.get(self.base_url + "hot-or-not")

        while(self.likes_given<self.max_likes):
            try:
                self.like_music()
            except NoSuchElementException as e:
                self.status = "NoSuchElementException"
            finally:
                self.status = "Success"

    def run(self, params):
        self.max_likes = params[0]

        super().print_bot_starting()

        if(self.max_likes<=0):
            return

        self.driver = webdriver.Chrome(executable_path="/Users/romes/everything-else/botdev/organized/likebots/chromedriver", options=self.chrome_options)
        
        self.login()
        self.hot_or_not()
        self.quit()