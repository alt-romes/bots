from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException

#Parent class
from Bot import Bot
from exceptions.BotExceptions import NotConfiguredAPI, NotLoggedIn, NoAccountCredentials, NoDatabase, NoDriver

#Instagram API module
from InstagramAPI import InstagramAPI

import os
import time
import datetime
import random
import logging

class InstagramBot(Bot):

    MAX_RUN_HOURS = 12
    MAXLPH = 60

    def __init__ (self, username='', password='', database=None, page_name=None, token=None, watch_feed_stories=True):
        """
        Creates an Instagram bot. Can be used to get information from an account, or to run jobs. 
        When done be sure to call the bot method quit()
        
        Get API Token from Facebook Graph API.
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

        self.max_likes_per_hour = self.MAXLPH #TODO: Make this very dynamic, as in it's calculated through the database. (Could start by saving the max likes per hour of a like job in the DB)


    def login(self, driver=None):

        if self.username=='' or self.password=='':
            e = NoAccountCredentials()
            self.log(logging.ERROR, str(e))
            raise e

        if self.driver==None and driver==None:
            e = NoDriver()
            self.log(logging.ERROR, str(e))
            raise e
        elif driver==None:
            driver = self.driver

        driver.get(self.base_url)

        time.sleep(1)

        self.log(logging.INFO, "Logging in. . .")

        try:
            driver.find_element_by_name("username").send_keys(self.username)
            driver.find_element_by_name("password").send_keys(self.password)
            time.sleep(1)
            driver.find_element_by_css_selector('button[type="submit"]').click()
            time.sleep(2)
        except NoSuchElementException:
            self.log(logging.INFO, "Already logged in.")

        try:
            time.sleep(3)
            driver.find_element_by_css_selector('button.bIiDR').click()
            time.sleep(3)
        except NoSuchElementException:
            self.log(logging.INFO, "Has already enabled notifications.")

        try:
            time.sleep(3)
            self.page_name = driver.find_element_by_css_selector("div.f5Yes.oL_O8").text
            self.log(logging.DEBUG, "User's page name is " + self.page_name)

        except Exception as e:
            self.log(logging.DEBUG, "Couldn't find user's page name: " + str(e))

        self.is_logged_in = True
        self.log(logging.INFO, "Logged in.")
        time.sleep(1)

    
    def login_mobile(self, driver):
        try:        
            driver.get(self.base_url)
            self.log(logging.INFO, "Logging in. . .")
            driver.find_element_by_xpath('//*[contains(text(), "Log In")]').click()
            driver.find_element_by_css_selector('input[aria-label="Phone number, username, or email"]').send_keys(self.username)
            driver.find_element_by_css_selector('input[aria-label="Password"]').send_keys(self.password)
            driver.find_element_by_xpath('//*[contains(text(), "Log In")]').click() 
            driver.find_element_by_xpath('//*[contains(text(), "Save Info")]').click() 
            driver.find_element_by_xpath('//*[contains(text(), "Cancel")]').click()
            driver.find_element_by_xpath('//*[contains(text(), "Not Now")]').click()
        except NoSuchElementException:
            self.log(logging.INFO, "Already logged in.")

        except Exception as e:
            self.log(logging.ERROR, "Error logging in: {}".format(e))
            return False
        else:
            return True

    def get_number_of_posts(self):
        if self.ig_api is not None:
            all_posts = self.ig_api.get_all_posts()
            return len(all_posts)
        else:
            e = NotConfiguredAPI()
            self.log(logging.ERROR, str(e))
            raise e


    def get_follows_list(self, username=None, mode="followers"):
        """
        Gets followers or following list for a username, if none provided, your username is used
        Accounts must be public
        Mode: followers to get followers
        Mode: following to get following
        """
        if not self.is_logged_in:
            e = NotLoggedIn()
            self.log(logging.ERROR, str(e))
            raise e

        if username is None:
            username = self.username
        
        if username == '':
            self.log(logging.ERROR, "You must provide a username, or be logged in!")
            return []

        self.log(logging.INFO, "Getting {} list for {}. . .".format(mode, username))

        self.driver.get('https://www.instagram.com/{}/'.format(username))
        time.sleep(5)
        self.driver.find_element_by_css_selector('a[href="/{}/{}/"]'.format(username, mode)).click()
        time.sleep(3)
        self.scroll_down(self.driver.find_element_by_css_selector('div.isgrP'))
        time.sleep(3)
        follows = self.driver.find_elements_by_css_selector('div.d7ByH>a.notranslate')
        follows_list = [follow.text for follow in follows]
        self.log(logging.INFO, "Looked up {} list from {}.".format(mode, username))

        if self.db is not None and username==self.username and mode=="followers":
            self.db.add_instagram_followers( list( map( (lambda follower: (self.get_platform(), self.get_username(), follower, datetime.datetime.now())), follows_list ) ) )

        return follows_list


    def get_not_following_back(self, username=None):
        if username is None:
            username = self.username

        if username == '':
            self.log(logging.ERROR, "You must provide a username or login!")
            return

        self.log(logging.INFO, "Getting users not following back for {}. . .".format(username))

        followers_list = self.get_follows_list(username, mode="followers")
        users = [user for user in self.get_follows_list(username, mode="following") if user not in followers_list] 
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
                    raise NoSuchElementException()
            else:
                self.driver.find_element_by_css_selector('div.T7reQ._0FuTv.pkWJh>div>div>img').click()
            time.sleep(2)
            self.log(logging.INFO, "Watching new stories in --" + mode + ".")
            while True:
                try:
                    self.driver.find_element_by_css_selector('div.coreSpriteRightChevron').click()
                    if mode=="--home":
                        self.home_stories_seen+=1
                    else:
                        self.hashtag_stories_seen+=1
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


    def take_a_break(self):
        waitTime = random.randrange(2100, 4500)
        self.log(logging.INFO, "Taking a break ({} minutes).".format(waitTime/60))
        time.sleep(waitTime)


    #Assumes you're on a page that has a clickable instagram reference to home page ( like their logo )
    def be_human(self):

        self.log(logging.INFO, "Being human!")
        if self.driver.current_url != self.base_url:
            try:
                self.driver.find_element_by_css_selector('a[href="/"]').click()
            except Exception as e:
                self.log(logging.ERROR, "Error searching for hashtag: " + str(e))
                self.log(logging.WARNING, "Changing URL directly. . .")
                self.driver.get(self.base_url)
            time.sleep(1.5)

        actions = [self.scroll_activity_feed, self.watch_new_stories, self.scroll_feed, self.go_to_profile]
        random.shuffle(actions)

        for action in actions:
            if random.random() < 0.8:
                action()

        if random.random() < 0.05:
            self.take_a_break()        

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


    def should_continue(self):
        return datetime.datetime.now() < datetime.timedelta(hours=self.MAX_RUN_HOURS) + self.time_started
    
    
    def like_selected_post(self, hashtag):
        """
        Pre: The post must be already selected
        Params: The hashtag it's on.
        Likes a post that's selected from the explore page, and adds it to the database if possible.
        """

        #TODO: If is a video or multiple image, scroll through / watch the video.

        #Time to like post
        time.sleep(random.uniform(2.5, 6))

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
        self.log(logging.INFO, "Liked a post ({}).".format(self.likes_given))

        #TODO: Randomly call function to check this profile, and if meets conditions, is followed and added to the DB.


    def like_posts(self, hashtag, maxLikesPerHour):

        random_modifier = random.randrange(-14, 15)

        #Select first picture
        self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/article/div[1]/div/div/div[1]/div[1]/a').click()
        time.sleep(3)

        #For each the post
        while self.current_posts_liked < (maxLikesPerHour + random_modifier) and self.should_continue(): #and self.likes_given < self.max_likes:
            self.posts_seen+=1
            isLiked = len(self.driver.find_elements_by_css_selector('button > svg[fill="#ed4956"]'))>0

            if(self.should_like_post() and not isLiked):
                self.current_posts_liked+=1
                self.like_selected_post(hashtag)
            
            #Time to move on
            time.sleep(random.uniform(2, 6))

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

        self.current_posts_liked = 0
        one_hour_later = datetime.datetime.now() + datetime.timedelta(hours=1)
        

        try:
            while self.should_continue() and self.likes_given<self.max_likes:

                for hashtag in hashtags:

                    if self.current_posts_liked >= self.max_likes_per_hour:
                        self.current_posts_liked = 0
                        one_hour_later = datetime.datetime.now() + datetime.timedelta(hours=1)

                    #Already randomized
                    self.be_human()

                    self.search_for_hashtag(hashtag)
                    time.sleep(1)

                    if random.random() < 0.8:
                        self.watch_new_stories(hashtag)
                        time.sleep(3)

                    try:
                        if random.random() < 0.8:
                            self.like_posts(hashtag, self.max_likes_per_hour)
                            time.sleep(2)
                    except NoSuchElementException as e:
                        self.log(logging.WARNING, "Forced hashtag switch: " + str(e))

                    if not self.should_continue() or self.likes_given>=self.max_likes:
                        break
                    
                    if self.current_posts_liked >= self.max_likes_per_hour and datetime.datetime.now() < one_hour_later:
                        sleepTime = int((one_hour_later - datetime.datetime.now() + datetime.timedelta(minutes=(random.randrange(1,6)))).total_seconds())
                        self.log(logging.INFO, "Sleeping for {} minutes until resuming. {} posts liked this hour.".format((sleepTime/60), self.current_posts_liked))
                        time.sleep(sleepTime)

                time.sleep(random.randrange(4, 8))
            if not self.should_continue():
                self.log(logging.WARNING, "Bot exceeded max runtime hours ({})!".format(self.MAX_RUN_HOURS))
                self.status = "Time Limit Exceeded"
            else:
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
        """
        params[0] is a list of hashtags
        params[1] is the max number of likes the bot can perform
        """

        try:
            self.max_likes = random.randrange(int(params[1]*0.90), params[1]+1)

            super().print_bot_starting()

            # if self.username == "romesrf":
            #     self.login()
            #     a = self.get_not_following_back()
            #     self.log(logging.INFO, "Users not following back {} ({}): \n{}".format(self.username, len(a), a))
                # self.log(logging.INFO, "Account has posted {} posts.".format(self.get_number_of_posts()))

            if(self.max_likes>0):

                if self.driver is None:
                    self.driver = self.init_driver()

                self.login()

                self.like_hashtags(params[0])

                self.get_follows_list()

        finally:
            self.quit()

    def get_new_followers(self):
        """
        Returns the number of people that followed you since the job started
        """

        return self.db.query("""
                                with oneAccFollowers as 
                                (select follower, time_detected from accFollowers
                                where platform=? and username=?)
                                select follower from oneAccFollowers
                                except
                                select follower from oneAccFollowers
                                where julianday(time_detected) < julianday(?)
                             """, (self.platform, self.username, self.time_started))


    def get_best_hashtags(self):
        """
        Returns a list of tuples (x, y) where x = hashtag and y = number of people whose post I liked in that hashtag AND follow me 
        """
        return self.db.query("""
                                select hashtag, count(follower) as followers
                                from (select accFollowers.username as username, accFollowers.platform as platform, found_in as hashtag, follower
                                from likedPosts inner join accFollowers
                                on likedPosts.platform = accFollowers.platform
                                and likedPosts.username = accFollowers.username
                                and op = follower
                                group by follower) 
                                where username = ? and platform = ?
                                group by hashtag
                                order by followers desc
                            """, (self.username, self.platform))


    def get_report_string(self):

        return """
                    Liked [ {} / {} ] posts today.
                    Watched {} stories in hashtags, and {} in home.
                    {} people followed you.
                    Your best hashtags are:
                    {}
                """.format(self.get_likes_given(), self.get_max_likes(), self.hashtag_stories_seen, self.home_stories_seen, len(self.get_new_followers()), self.get_best_hashtags())