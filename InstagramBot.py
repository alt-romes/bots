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

        try:
            self.driver.find_element_by_css_selector('button.bIiDR').click()
            time.sleep(2)
        except:
            #Already enabled notifications
            pass

        try:
            time.sleep(1)
            self.page_name = self.driver.find_element_by_css_selector("div.f5Yes.oL_O8").text
        except Exception as e:
            print("Couldn't find page name", e)

        self.is_logged_in = True
        time.sleep(1)


    def get_followers_list(self):
        if self.driver == None:
            self.driver = webdriver.Chrome(executable_path="/Users/romes/everything-else/botdev/organized/likebots/chromedriver", options=self.chrome_options)
            time.sleep(2)
        self.driver.get('https://www.instagram.com/{}/'.format(self.username))
        time.sleep(5)
        self.driver.find_element_by_css_selector('a[href="/{}/followers/"]'.format(self.username)).click()
        time.sleep(5)
        self.scroll_down(self.driver.find_element_by_css_selector('div.isgrP'))
        time.sleep(2)
        followers = self.driver.find_elements_by_css_selector('div.d7ByH>a.notranslate')
        follower_list = [follower.text for follower in followers]
        self.driver.quit()
        self.driver = None
        return follower_list


    def get_unfollowers_list(self):
        #Match current followers with database?
        pass


    # Assumes you're in a page with the activity feed button (notifications hear)
    def scroll_activity_feed(self):
        try:
            # print("Scrolling activity feed!")
            time.sleep(1)
            self.driver.find_element_by_css_selector('a[href="/accounts/activity/"]').click()
            time.sleep(3)
            if random.random()<0.5:
                self.scroll_down(self.driver.find_element_by_css_selector('div._01UL2'), 0.05)
            time.sleep(3)
            self.driver.execute_script('arguments[0].click();' ,self.driver.find_element_by_css_selector('div.wgVJm'))
            time.sleep(1)
        except Exception as e:
            print("Error scrolling activity feed", e)


    # It'll only watch new stories, mode="--home" if you're watching stories of who you follow, mode="--hashtag" if you're watching stories with a hashtag
    def watch_new_stories(self, mode="--home"):


        #TODO: COULD ALSO VOTE POLLS ?? DO they work on web??

        try:
            if mode=="--home":
                canvas = self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/section/div[3]/div[2]/div[2]/div/div/div/div[1]/button[@class="jZyv1  H-yu6"]/div[1]/canvas') #('button.jZyv1.H-yu6>div>canvas.CfWVH[height="44"]')
                if int(canvas.get_attribute("height")) % 11 == 0:
                    self.driver.find_element_by_css_selector('button.jZyv1.H-yu6>div>span>img._6q-tv').click()
            elif mode=="--hashtag":
                self.driver.find_element_by_css_selector('div.T7reQ._0FuTv.pkWJh>div>div>img').click()
            time.sleep(2)
            # print("Watching new stories!")
            while True:
                try:
                    self.driver.find_element_by_css_selector('div.coreSpriteRightChevron').click()
                    time.sleep(random.uniform(0.5, 2))
                except Exception as e:
                    # print("Tried to skip story too fast.")
                    pass
                finally:
                    try:
                        self.driver.find_element_by_css_selector('section.carul')
                    except NoSuchElementException:
                        # print("Finished watching stories!")
                        break
                    except Exception:
                        print("Error exiting carousell", e)

        except NoSuchElementException as e:
            # No available story to watch
            pass


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

        if self.driver.current_url != self.base_url:
            self.driver.find_element_by_css_selector('a[href="/"]').click()
            time.sleep(1.5)

        actions = [self.scroll_activity_feed, self.watch_new_stories, self.scroll_feed, self.go_to_profile]
        random.shuffle(actions)
        
        for action in actions:
            if random.random() < 0.8:
                action()


    # Assumes you're on front page, and there's a search bar
    def search_for_hashtag(self, hashtag):
        # self.driver.get(self.base_url + 'explore/tags/' + hashtag)
        search = self.driver.find_element_by_css_selector('input[placeholder="Search"]')
        self.driver.execute_script("arguments[0].click();", search)
        time.sleep(1.5)
        search.send_keys("#"+hashtag)
        time.sleep(2)
        self.driver.find_element_by_css_selector('div.fuqBx>a[href="/explore/tags/'+hashtag+'/"]').click()
        time.sleep(4)


    # Mode = "--new" to like new posts, Mode = "--best" to like best posts
    # Must already be 
    def like_posts(self, hashtag, maxLikesPerHashtag, mode="--new"):
        current_posts_seen = 0


        if mode=="--best":
            self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/article/div[1]/div/div/div[1]/div[1]/a').click()
        elif mode=="--new":
            self.driver.execute_script("window.scrollTo(0, 1000)")
            time.sleep(1)
            self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/article/div[2]/div/div[1]/div[2]/a').click()
        time.sleep(3)

        #For each the post
        while (current_posts_seen < maxLikesPerHashtag and self.likes_given < self.max_likes):
            self.posts_seen+=1
            current_posts_seen+=1
            isLiked = len(self.driver.find_elements_by_css_selector('button > svg[fill="#ed4956"]'))>0
            #
            shouldLikePost = False
            if mode=="--best":
                shouldLikePost = self.should_like_post()
            elif mode=="--new":
                shouldLikePost = self.should_like_post(0.3, 0.5)

            if(shouldLikePost and not isLiked):
                self.likes_given+=1

                #Time to like post
                time.sleep(random.uniform(1, 3))

                #Like post
                self.driver.find_element_by_class_name("wpO6b").click()

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

        try:
            #Add to database hashtags chosen by user
            if self.db is not None:
                self.db.add_account_hashtags( list( map( (lambda hashtag: (self.get_username(), self.get_platform(), hashtag)), hashtags) ) )

            #Prepare number of likes to give, and order of hashtags
            mlphAux = int(((self.max_likes/len(hashtags))+1)*(random.randrange(2, 5)))
            max_likes_per_hashtag = random.randrange(int(mlphAux*0.9), mlphAux+1)
            random.shuffle(hashtags)
            

            while(self.likes_given<self.max_likes):
                for hashtag in hashtags:
                    try:

                        #Already randomized
                        self.be_human()

                        self.search_for_hashtag(hashtag)
                        time.sleep(1)

                        if random.random() < 0.8:
                            self.watch_new_stories("--hashtag")
                            time.sleep(3)

                        if random.random() < 0.8:
                            self.like_posts(hashtag, max_likes_per_hashtag*(1/10), "--best")
                            time.sleep(2)

                        if random.random() < 0.8:
                            self.like_posts(hashtag, max_likes_per_hashtag*(9/10), "--new")
                            time.sleep(2)


                    except NoSuchElementException as e:
                        print("Forced hashtag switch", e)
                        pass

                    if(self.likes_given>=self.max_likes):
                        break

                time.sleep(random.randrange(4, 8))
            self.status = "Success"


        #Handle errors    
        except KeyboardInterrupt:
            self.status = "Aborted"
            print("keyboard interrupt")
        except ElementClickInterceptedException as e:
            time.sleep(0.5)
            if self.driver.find_elements_by_xpath("//*[contains(text(), 'Action Blocked')]") != []:
                self.status = "Action Blocked"
                print(self.username, "was action blocked.")
            else:
                self.status = "ElementClickedInterceptedException"
                print("Something weird happened while liking hashtags:", e)


        #Update database
        finally:
            self.db.create_likejob((self.get_username(), self.get_platform(), self.get_likes_given(), self.get_max_likes(), self.get_status(), self.get_time_started(), datetime.datetime.now(), self.get_posts_seen()))
    
    

    def run(self, params):

        self.max_likes = random.randrange(int(params[1]*0.90), params[1]+1)

        super().print_bot_starting()

        if(self.max_likes>0):
            
            self.driver = webdriver.Chrome(executable_path="/Users/romes/everything-else/botdev/organized/likebots/chromedriver", options=self.chrome_options)

            self.login()

            self.like_hashtags(params[0])

            self.db.add_instagram_followers( list( map( (lambda follower: (self.get_platform(), self.get_username(), follower, datetime.datetime.now())), self.get_followers_list() ) ) )
        
        self.quit()