from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException

#Parent class
from Bot import Bot

#Instagram API module
from InstagramAPI import InstagramAPI

import os
import time
import datetime
import random

class InstagramBot(Bot):

    def __init__ (self, username, password, database=None):
        self.platform = "Instagram"
        self.base_url = "https://www.instagram.com/"
        self.page_name = None

        super().__init__(username, password, database)

    def login(self):
        self.driver.get(self.base_url)

        time.sleep(1)

        try:
            self.driver.find_element_by_name("username").send_keys(self.username)
            self.driver.find_element_by_name("password").send_keys(self.password, Keys.ENTER)
            time.sleep(2)

        except NoSuchElementException:
            #Is already logged in
            pass
        finally:
            self.driver.find_element_by_css_selector('button.bIiDR').click()
            time.sleep(2)

        self.page_name = self.driver.find_element_by_css_selector("div.f5Yes.oL_O8").text

        self.is_logged_in = True

        time.sleep(3)

    def get_followers_list(self):
        if self.driver == None:
            self.driver = webdriver.Chrome(executable_path="/Users/romes/everything-else/botdev/organized/likebots/chromedriver", options=self.chrome_options)
            time.sleep(2)
        self.driver.get('https://www.instagram.com/{}/'.format(self.username))
        time.sleep(5)
        self.driver.find_element_by_css_selector('a[href="/{}/followers/"]'.format(self.username)).click()
        time.sleep(5)
        dialog = self.driver.find_element_by_css_selector('div.isgrP')
        time.sleep(1)
        self.scroll_down(dialog)
        time.sleep(2)
        followers = self.driver.find_elements_by_css_selector('div.d7ByH>a.notranslate')
        follower_list = [follower.text for follower in followers]
        self.driver.quit()
        self.driver = None
        return follower_list

    def get_unfollowers_list(self):
        #Match current followers with database?
        pass


    def like_posts(self, hashtag, maxLikesPerHashtag):
        current_posts_seen = 0
        self.driver.get(self.base_url + 'explore/tags/' + hashtag)
        time.sleep(2)
        self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/article/div[2]/div/div[1]/div[2]/a').click()
        time.sleep(5)

        #For each the post
        while (current_posts_seen < maxLikesPerHashtag and self.likes_given < self.max_likes):
            self.posts_seen+=1
            current_posts_seen+=1
            
            time.sleep(2)
            isLiked = self.driver.find_elements_by_css_selector('button > svg[fill="#ed4956"]')!=[]

            #Code to like the post
            if(self.should_like_post() and not isLiked):
                self.likes_given+=1
                waitTimeToLike = random.uniform(1, 3)
                time.sleep(waitTimeToLike)

                time_liked = datetime.datetime.now()
                op = self.driver.find_element_by_class_name("e1e1d").text
                tags = self.driver.find_element_by_class_name("C4VMK").text
                hashtags = list({tag.strip("#") for tag in tags.split() if tag.startswith("#")})

                liked_post = (op, time_liked, hashtag, hashtags)
                liked_post_entry = (self.get_username(), self.get_platform(), liked_post[0], liked_post[1], liked_post[2]) #op, time, hashtag liked in
                post_id = self.db.create_liked_post(liked_post_entry)
                self.db.add_post_hashtags(list ( map ( (lambda hashtag: (post_id, hashtag)), liked_post[3]) ) )
                # self.posts_liked.append((op, time_liked, hashtag, hashtags))

                self.driver.find_element_by_class_name("wpO6b").click()
                # print(self.username[0:1], end="", flush=True)
            
            waitTimeToMoveOn = random.uniform(1, 3)
            time.sleep(waitTimeToMoveOn)
            self.driver.find_element_by_class_name('coreSpriteRightPaginationArrow').click()
        # print("o", end="", flush=True)
        sleepTime = random.randrange(4,16)
        time.sleep(sleepTime)

    # Must be already in instagram logged in
    def like_hashtags(self, hashtags):
        
        try:
            if self.db is not None:
                self.db.add_account_hashtags( list( map( (lambda hashtag: (self.get_username(), self.get_platform(), hashtag)), hashtags) ) )

            mlphAux = int(((self.max_likes/len(hashtags))+1)*(random.randrange(2, 5)))
            max_likes_per_hashtag = random.randrange(int(mlphAux*0.9), mlphAux+1)
            random.shuffle(hashtags)
            
            while(self.likes_given<self.max_likes):
                for hashtag in hashtags:
                    try:
                        self.like_posts(hashtag, max_likes_per_hashtag)
                    except NoSuchElementException: 
                        pass
                    if(self.likes_given>=self.max_likes):
                        break
                time.sleep(random.randrange(4, 8))
            self.status = "Success"
        except KeyboardInterrupt:
            self.status = "Aborted"
        except ElementClickInterceptedException as e:
            time.sleep(5)
            print(e)
            if self.driver.find_elements_by_xpath("//*[text()='Action Blocked']") != []:
                self.status = "Action Blocked"
            else:
                self.status = "ElementClickedInterceptedException"

        self.db.create_likejob((self.get_username(), self.get_platform(), self.get_likes_given(), self.get_max_likes(), self.get_status(), self.get_time_started(), datetime.datetime.now(), self.get_posts_seen()))
    
    def be_human(self):
        print("Hi i'm human")
        time.sleep(1)
        self.driver.find_element_by_css_selector('a[href="/accounts/activity/"]').click()
        time.sleep(3)
        activity_feed = self.driver.find_element_by_css_selector('div.uo5MA._2ciX.tWgj8.XWrBI')

    def run(self, params):

        self.max_likes = random.randrange(int(params[1]*0.90), params[1]+1)

        super().print_bot_starting()

        if(self.max_likes>0):
            
            self.driver = webdriver.Chrome(executable_path="/Users/romes/everything-else/botdev/organized/likebots/chromedriver", options=self.chrome_options)

            self.login()

            self.be_human()

            self.like_hashtags(params[0])

            self.db.add_instagram_followers( list( map( (lambda follower: (self.get_platform(), self.get_username(), follower, datetime.datetime.now())), self.get_followers_list() ) ) )
        
        self.quit()