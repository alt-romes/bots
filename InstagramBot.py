from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException
import os
import time
import random

class InstagramBot:

    def __init__ (self, username, password):
        self.username = username
        self.password = password

        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--window-size=1200x800")
        
        self.driver = None

        self.base_url = "https://www.instagram.com/"

        self.likes_given = 0
        self.posts_seen = 0
        
    def quit(self):
        print("%-------------------------------------------------------%")
        print("Liked " + str(self.likes_given) + " posts for account " + self.username + " in " + self.base_url)
        print("%-------------------------------------------------------%")
        self.driver.quit()


    def login(self):
        self.driver = webdriver.Chrome(executable_path="./chromedriver", options=self.chrome_options)
        self.driver.get(self.base_url + "accounts/login")

        time.sleep(5)
        self.driver.find_element_by_name("username").send_keys(self.username)
        self.driver.find_element_by_name("password").send_keys(self.password)
        self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/article/div/div[1]/div/form/div[4]/button').click()

        print("Logged in as " + self.username + " in " + self.base_url)

        time.sleep(5)


    def like_posts(self, hashtag, maxLikes):
        current_posts_seen = 0
        self.driver.get(self.base_url + 'explore/tags/' + hashtag)
        time.sleep(2)
        self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/article/div[2]/div/div[1]/div[2]/a').click()
        time.sleep(5)

        #For each the post
        while (current_posts_seen < maxLikes):
            self.posts_seen+=1
            current_posts_seen+=1
            chanceToLikePost = random.uniform(0.6, 0.85)
            r = random.random()
            time.sleep(2)
            isLiked = self.driver.find_elements_by_css_selector('button > svg[fill="#ed4956"]')!=[]
            if(r <= chanceToLikePost and not isLiked):
                self.likes_given+=1
                waitTimeToLike = random.uniform(1, 3)
                time.sleep(waitTimeToLike)
                self.driver.find_element_by_class_name("wpO6b").click()
                print(self.username[0:1], end="", flush=True)
            waitTimeToMoveOn = random.uniform(1, 3)
            time.sleep(waitTimeToMoveOn)
            self.driver.find_element_by_class_name('coreSpriteRightPaginationArrow').click()
        print("o", end="", flush=True)
        sleepTime = random.randrange(32, 64)
        time.sleep(sleepTime)


    def like_hashtags(self, hashtags, amount):
        while(self.likes_given<amount):
            for hashtag in hashtags:
                try:
                    self.like_posts(hashtag, (amount/len(hashtags))*3)
                except NoSuchElementException: 
                    print("x", end="", flush=True)
            time.sleep(random.randrange(16, 64))


    def run(self, params):
        self.login()
        print()
        try:
            self.like_hashtags(params[0], params[1])
        except ElementClickInterceptedException as e:
            print(e)
        self.quit()