from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException

#Parent class
from Bot import Bot
from exceptions.BotExceptions import NotConfiguredAPI, NotLoggedIn, NoAccountCredentials

#Instagram API module
from InstagramAPI import InstagramAPI

import os
import time
import datetime
import random
import logging

class InstagramBot(Bot):

    def __init__ (self, username='', password='', database=None, page_name=None, token=None, watch_feed_stories=True):
        """
        Creates an Instagram bot. Can be used to get information from an account, or to run jobs. 
        When done be sure to call the bot method quit()
        
        TODO: Include description on how to get API TOKEN
        """

        self.watch_feed_stories = watch_feed_stories
        self.platform = "Instagram"
        self.base_url = "https://www.instagram.com/"
        self.token = token
        self.page_name = page_name
        self.hashtag_stories_seen = 0
        self.home_stories_seen = 0

        self.ig_api = None
        if self.page_name is not None and token is not None:
            self.ig_api = InstagramAPI(self.page_name, self.token, logf=self.log) #Use parent's logger

        super().__init__(username, password, database)


    def login(self):
        if self.username=='' or self.password=='':
            e = NoAccountCredentials()
            self.log(logging.ERROR, str(e))
            raise e

        if self.driver is None:
            self.init_driver()

        self.driver.get(self.base_url)

        time.sleep(1)

        try:
            self.driver.find_element_by_name("username").send_keys(self.username)
            self.driver.find_element_by_name("password").send_keys(self.password, Keys.ENTER)
            time.sleep(2)
        except NoSuchElementException:
            self.log(logging.NOTSET, "Already logged in.")

        try:
            self.driver.find_element_by_css_selector('button.bIiDR').click()
            time.sleep(2)
        except NoSuchElementException:
            self.log(logging.NOTSET, "Has already enabled notifications")

        try:
            time.sleep(3)
            self.page_name = self.driver.find_element_by_css_selector("div.f5Yes.oL_O8").text
            self.log(logging.NOTSET, "User's page name is " + self.page_name)

        except Exception as e:
            self.log(logging.ERROR, "Couldn't find user's page name: " + str(e))

        self.is_logged_in = True
        self.log(logging.INFO, "Logged in.")
        time.sleep(1)


    def get_number_of_posts(self):
        if self.ig_api is not None:
            all_posts = self.ig_api.get_all_posts()
            return len(all_posts)
        else:
            e = NotConfiguredAPI()
            self.log(logging.ERROR, str(e))
            raise e


    def get_followers_list(self, username=None):
        self.log(logging.INFO, "Getting followers list for {}.".format(username))
        if not self.is_logged_in:
            e = NotLoggedIn()
            self.log(logging.ERROR, str(e))
            raise e

        if username is None:
            username = self.username

        if self.driver is None:
            self.init_driver()
        
        if username == '':
            self.log(logging.ERROR, "You must provide a username, or login!")
            return []

        self.driver.get('https://www.instagram.com/{}/'.format(username))
        time.sleep(5)
        self.driver.find_element_by_css_selector('a[href="/{}/followers/"]'.format(username)).click()
        time.sleep(5)
        self.scroll_down(self.driver.find_element_by_css_selector('div.isgrP'))
        time.sleep(2)
        followers = self.driver.find_elements_by_css_selector('div.d7ByH>a.notranslate')
        follower_list = [follower.text for follower in followers]
        self.log(logging.INFO, "Looked up followers list from {}.".format(username))

        if self.db is not None and username==self.username:
            self.db.add_instagram_followers( list( map( (lambda follower: (self.get_platform(), self.get_username(), follower, datetime.datetime.now())), follower_list ) ) )

        return follower_list


    def get_following_list(self, username=None):
        self.log(logging.INFO, "Getting following list for {}.".format(username))
        if not self.is_logged_in:
            e = NotLoggedIn()
            self.log(logging.ERROR, str(e))
            raise e

        if username is None:
            username = self.username
        if self.driver is None:
            self.init_driver()

        if username == '':
            self.log(logging.ERROR, "You must provide a username or login!")
            return []

        self.driver.get('https://www.instagram.com/{}/'.format(username))
        time.sleep(5)
        self.driver.find_element_by_css_selector('a[href="/{}/following/"]'.format(username)).click()
        time.sleep(5)
        self.scroll_down(self.driver.find_element_by_css_selector('div.isgrP'))
        time.sleep(2)
        followers = self.driver.find_elements_by_css_selector('div.d7ByH>a.notranslate')
        follower_list = [follower.text for follower in followers]
        self.log(logging.INFO, "Looked up following list from {}.".format(username))
        
        return follower_list


    def get_not_following_back(self, username=None):
        self.log(logging.INFO, "Getting users not following back for {}.".format(username))
        if username is None:
            username = self.username

        if username == '':
            self.log(logging.ERROR, "You must provide a username or login!")
            return

        followers_list = self.get_followers_list(username)
        users = [user for user in self.get_following_list(username) if user not in followers_list] 
        return users


    def get_unfollowers_list(self):
        #Match current followers with database?
        pass


    # Assumes you're in a page with the activity feed button (notifications hear)
    def scroll_activity_feed(self):
        try:
            time.sleep(1)
            self.driver.find_element_by_css_selector('a[href="/accounts/activity/"]').click()
            time.sleep(3)
            if random.random()<0.5:
                self.scroll_down(self.driver.find_element_by_css_selector('div._01UL2'), 0.05)
            time.sleep(3)
            self.driver.execute_script('arguments[0].click();' ,self.driver.find_element_by_css_selector('div.wgVJm'))
            time.sleep(1)
            self.log(logging.INFO, "Scrolled activity feed.")
        except Exception as e:
            self.log(logging.ERROR, "Error scrolling activity feed: " + str(e))


    # It'll only watch new stories, mode="--home" if you're watching stories of who you follow, mode="--hashtag" if you're watching stories with a hashtag
    def watch_new_stories(self, mode="--home"):

        try:
            if mode=="--home" and not self.watch_feed_stories:
                self.log(logging.INFO, "Not watching feed stories.")
                return
            elif mode=="--home" and self.watch_feed_stories:
                canvas = self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/section/div[3]/div[2]/div[2]/div/div/div/div[1]/button[@class="jZyv1  H-yu6"]/div[1]/canvas') #('button.jZyv1.H-yu6>div>canvas.CfWVH[height="44"]')
                if int(canvas.get_attribute("height")) % 11 == 0:
                    self.driver.find_element_by_css_selector('button.jZyv1.H-yu6>div>span>img._6q-tv').click()
            else:
                self.driver.find_element_by_css_selector('div.T7reQ._0FuTv.pkWJh>div>div>img').click()
            time.sleep(2)
            self.log(logging.INFO, "Watching new stories in --" + mode + ".")
            while True:
                try:
                    if mode=="--home":
                        self.home_stories_seen+=1
                    else:
                        self.hashtag_stories_seen+=1
                    self.driver.find_element_by_css_selector('div.coreSpriteRightChevron').click()
                    self.log(logging.INFO, "Watched a story.")
                    time.sleep(random.uniform(0.5, 2))
                except Exception as e:
                    self.log(logging.WARNING, "While clicking skip story: " + str(e))
                finally:
                    try:
                        self.driver.find_element_by_css_selector('section.carul')
                    except NoSuchElementException:
                        self.log(logging.INFO, 'Finished watching stories.')
                        break
                    except Exception:
                        self.log(logging.ERROR, "Error exiting carousell " + str(e))

        except NoSuchElementException as e:
            # No available story to watch
            self.log(logging.INFO, 'No story available to watch.')


    # Assumes you're on the front page aka your feed. It'll scroll and like pictures, at a lower rate than the ones in /new
    def scroll_feed(self):
        #TODO
        #Scroll until it finds a post already liked
        #Clicks "more" on descriptions
        #Clicks "right" on carousell
        # print("Scrolling feed!")
        pass


    def go_to_profile(self):
        #TODO: Go to profile, click notifications, scroll a bit down
        # print("Going to profile!")
        pass


    #Assumes you're on a page that has a clickable instagram reference to home page ( like their logo )
    def be_human(self):

        self.log(logging.INFO, "Being human!")
        if self.driver.current_url != self.base_url:
            self.driver.find_element_by_css_selector('a[href="/"]').click()
            time.sleep(1.5)

        actions = [self.scroll_activity_feed, self.watch_new_stories, self.scroll_feed, self.go_to_profile]
        random.shuffle(actions)
        
        for action in actions:
            if random.random() < 0.8:
                action()
        self.log(logging.INFO, "Was human!")


    # Assumes you're on front page, and there's a search bar
    def search_for_hashtag(self, hashtag):
        try:
            search = self.driver.find_element_by_css_selector('input[placeholder="Search"]')
            self.driver.execute_script("arguments[0].click();", search)
            time.sleep(1.5)
            search.send_keys("#"+hashtag)
            time.sleep(4)
            self.driver.find_element_by_css_selector('div.fuqBx>a[href="/explore/tags/'+hashtag+'/"]').click()
            time.sleep(4)
            self.log(logging.INFO, "Searched for hashtag succesfully.")
        except Exception as e:
            self.log(logging.ERROR, "Error searching for hashtag: " + str(e))
            self.log(logging.WARNING, "Changing URL directly. . .")
            self.driver.get(self.base_url + 'explore/tags/' + hashtag)


    # Mode = "--new" to like new posts, Mode = "--best" to like best posts
    # Must already be 
    def like_posts(self, hashtag, maxLikesPerHashtag):
        current_posts_seen = 0

        #Select first picture
        self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/article/div[1]/div/div/div[1]/div[1]/a').click()
        time.sleep(3)

        #For each the post
        while (current_posts_seen < maxLikesPerHashtag and self.likes_given < self.max_likes):
            self.posts_seen+=1
            current_posts_seen+=1
            isLiked = len(self.driver.find_elements_by_css_selector('button > svg[fill="#ed4956"]'))>0

            if(self.should_like_post() and not isLiked):
                
                #Time to like post
                time.sleep(random.uniform(1, 3))

                #Like post
                self.driver.find_element_by_class_name("wpO6b").click()

                if self.db is not None:
                    #Prepare data for database
                    time_liked = datetime.datetime.now()
                    op = self.driver.find_element_by_class_name("e1e1d").text
                    tags = self.driver.find_element_by_class_name("C4VMK").text
                    hashtags = list({tag.strip("#") for tag in tags.split() if tag.startswith("#")})
                    liked_post_entry = (self.get_username(), self.get_platform(), op, time_liked, hashtag) #op, time, hashtag liked in

                    #Add liked post to database 
                    post_id = self.db.create_liked_post(liked_post_entry)

                    #Add hashtags of liked post to database
                    self.db.add_post_hashtags(list ( map ( (lambda hashtag: (post_id, hashtag)), hashtags) ) )
                    

                self.likes_given+=1
                self.log(logging.INFO, "Liked a post.")

                #TODO: Randomly call function to check this profile, and if meets conditions, is followed and added to the DB.
            
            #Time to move on
            time.sleep(random.uniform(1, 3))

            #Move on
            self.driver.find_element_by_class_name('coreSpriteRightPaginationArrow').click()
            time.sleep(2)

        #Close dialog
        self.driver.find_element_by_css_selector('svg[aria-label="Close"]').click()
        time.sleep(random.randrange(4, 6))


    # Must be already in instagram in a page with the search bar and must be logged in
    def like_hashtags(self, hashtags):

        #Add to database hashtags chosen by user
        if self.db is not None:
            self.db.add_account_hashtags( list( map( (lambda hashtag: (self.get_username(), self.get_platform(), hashtag)), hashtags) ) )

        #Prepare number of likes to give, and order of hashtags
        mlphAux = int(((self.max_likes/len(hashtags))+1)*(random.randrange(2, 5)))
        max_likes_per_hashtag = random.randrange(int(mlphAux*0.9), mlphAux+1)
        random.shuffle(hashtags)

        try:
            while(self.likes_given<self.max_likes):
                for hashtag in hashtags:

                    #Already randomized
                    self.be_human()

                    self.search_for_hashtag(hashtag)
                    time.sleep(1)

                    if random.random() < 0.8:
                        self.watch_new_stories(hashtag)
                        time.sleep(3)

                    try:
                        if random.random() < 0.8:
                            self.like_posts(hashtag, max_likes_per_hashtag)
                            time.sleep(2)

                    except NoSuchElementException as e:
                        self.log(logging.WARNING, "Forced hashtag switch: " + str(e))

                    if(self.likes_given>=self.max_likes):
                        break

                time.sleep(random.randrange(4, 8))
            self.status = "Success"
            self.log(logging.INFO, "Finished the like job.")
        #Handle errors
        except ElementClickInterceptedException as e:
            time.sleep(0.5)
            if self.driver.find_elements_by_xpath("//*[contains(text(), 'Action Blocked')]") != []:
                self.status = "Action Blocked"
                self.log(logging.CRITICAL, "Was action blocked!")
            else:
                self.log(logging.ERROR, "While liking hashtags: " + str(e))
        except KeyboardInterrupt as e:
            self.status = "KeyboardInterrupt"
            raise e

        except Exception as e:
            self.log(logging.ERROR, str(e))
            raise e
        
        #Update database
        finally:
            if self.db is not None:
                now = datetime.datetime.now()
                try:
                    self.db.create_likejob((self.get_username(), self.get_platform(), self.get_likes_given(), self.get_max_likes(), self.get_status(), self.get_time_started(), now, self.get_posts_seen()))
                    self.db.create_instagram_likejob((self.get_platform(), self.get_username(), now, self.hashtag_stories_seen, self.home_stories_seen))
                except Exception as e:
                    self.log(logging.ERROR, "Error inserting row in a likejob table! " + str(e))
    
    
    def run(self, params):

        try:
            self.max_likes = random.randrange(int(params[1]*0.90), params[1]+1)

            super().print_bot_starting()

            if self.username == "romesrf":
                self.login()
                self.log(logging.INFO, "Users not following you back: \n"+str(self.get_not_following_back("antmancancar")))
                self.log(logging.INFO, "Account has posted {} posts.".format(self.get_number_of_posts()))
                

            if(self.max_likes>0):
                self.init_driver()

                self.login()

                self.like_hashtags(params[0])

                self.get_followers_list()

        finally:
            self.quit()


    def get_report_string(self):
        return ("Liked [ " + str(self.get_likes_given()) + " / " + str(self.get_max_likes()) + " ] posts, watched " + str(self.hashtag_stories_seen) + " stories in hashtags, and " + str(self.home_stories_seen) + " in home.")