from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException
import os
import time
import random

class SubmitHubBot:

    def __init__ (self, username, password):
        self.username = username
        self.password = password
        
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument("--mute-audio")
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--window-size=1200x800")

        self.driver = None

        self.base_url = "https://www.submithub.com/"

        self.likes_given = 0
        self.posts_seen = 0


    def login(self):
        self.driver = webdriver.Chrome(executable_path="./chromedriver", options=self.chrome_options)
        self.driver.get(self.base_url + "login")

        time.sleep(5)
        self.driver.find_element_by_id("usernameOrEmail").send_keys(self.username)
        self.driver.find_element_by_id("password").send_keys(self.password)
        self.driver.find_element_by_xpath('//*[@id="my-account-login"]/form/div[3]/button[1]').click()

        time.sleep(5)
        print("Logged in as " + self.username + " in " + self.base_url)

    def quit(self):
        print("%-------------------------------------------------------%")
        print("Liked " + str(self.likes_given) + " posts for account " + self.username + " in " + self.base_url)
        print("%-------------------------------------------------------%")
        self.driver.quit()

    def listen_time(self):
        return random.randrange(29, 61)
    
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
        print("!", end="", flush=True)
        time.sleep(random.randrange(8, 12))
        self.driver.find_element_by_class_name('skip-next').click()
        self.likes_given+=1


    def hot_or_not(self, amount):
            self.driver.get(self.base_url + "hot-or-not") 
            while(self.likes_given<amount):
                try:
                    self.like_music()
                except NoSuchElementException as e:
                    print(e)

    def run(self, params):
        self.login()
        print()
        self.hot_or_not(params[0])
        self.quit()