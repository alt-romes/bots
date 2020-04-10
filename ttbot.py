from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException
import os
import time
import random

class InstagramBot:

    def __init__ (self, username, password):
        self.username = username
        self.password = password
        
        self.driver = webdriver.Chrome(executable_path="./chromedriver")

        self.base_url = "https://www.twitter.com/"

        self.likes_given = 0

        self.login()

        print()
        print("Liking for account: " + username)
        print('vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv')
        print()
        
        smallhashtags = ['shoegaze', 'dreampop', 'experimental', "album", 'indie', "homestudio", "recording", "record", "altrock"]#'altrock', 'dreampop',
        hashtags = ['music',  "drawing",  'musician', 'spotify', 'artist', "instamusic", 'art', "me", 'alternative']

        try:
            for i in smallhashtags:
                try:
                    print("Liking "+str(i)+ " feed")
                    print()
                    self.like_new_posts("/hashtag/"+i)
                except NoSuchElementException:
                    print()
                    print("Something wrong happened with this hashtag, moving on...")

            for j in range(2):
                for i in hashtags:
                    try:
                        print("Liking "+str(i)+ " feed")
                        print()
                        self.like_new_posts("/hashtag/"+i)
                    except NoSuchElementException:
                        print()
                        print("Something wrong happened with this hashtag, moving on...")
                time.sleep(100)
        except ElementClickInterceptedException:
            self.driver.quit()
        self.driver.quit()



    def login(self):
        self.driver.get(self.base_url + "/login")

        time.sleep(1)
        self.driver.find_element_by_name("session[username_or_email]").send_keys(self.username)
        self.driver.find_element_by_name("session[password]").send_keys(self.password)
        self.driver.find_element_by_xpath('//*[@id="react-root"]/div/div/div[2]/main/div/div/form/div/div[3]/div/div').click()

        time.sleep(2)


    def like_new_posts(self, explore_path):
        current_likes_given = 0
        self.driver.get(self.base_url + explore_path)
        
        time.sleep(5)
        body = self.driver.find_element_by_tag_name('body')
        while (current_likes_given < 242):
            time.sleep(2)
            tweets=self.driver.find_elements_by_css_selector("div.css-18t94o4.css-1dbjc4n.r-1777fci.r-11cpok1.r-1ny4l3l.r-bztko3.r-lrvibr")
            print(len(tweets))
            try:
                for i in range(len(tweets)):
                    if(i%5==3):
                        chanceToLikePost = random.uniform(0.6, 0.8)
                        r = random.random()
                        if(r <= chanceToLikePost):
                            print()
                            print("Current likes given: " + str(self.likes_given))
                            self.likes_given+=1
                            current_likes_given+=1
                            waitTimeToLike = random.uniform(1, 3)
                            time.sleep(waitTimeToLike)
                            self.driver.execute_script("arguments[0].click();", tweets[i])
                            waitTimeToMoveOn = random.uniform(0.2, 0.6)
                            time.sleep(waitTimeToMoveOn)
                            print()
                            body.send_keys(Keys.PAGE_DOWN)
            except StaleElementReferenceException:
                body.send_keys(Keys.PAGE_DOWN * 6)
        
        sleepTime = random.randrange(160, 320)
        print("Finished set, sleeping for: " + str(sleepTime/60) + " minutes.")
        time.sleep(sleepTime)
        print()
















































if __name__ == '__main__':
    accounts = ['alt.romes@gmail.com', 'romesrf']
    passwords = ['Cl0udR1ft', 'Cl0udR1ft']
    
    for i in range(len(accounts)):
        ig_bot = InstagramBot(accounts[i], passwords[i])
        time.sleep(100)


