from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from config import credentials, params

from exceptions.BotExceptions import FailedImageDownload, NoNewMessagesFromUser
from InstagramBot import InstagramBot


import os
import requests
import time
import logging
import threading
import queue
import traceback
import datetime

class InstagramManager(InstagramBot):

    DAYS_TO_APPROVE_TIMEOUT = 4
    ACCEPTANCE_MESSAGE = "allow"

    def __init__(self, username, password, ops=[], database=None, hashtags=[], permission_message="", timedelta_between_permission_request=300, timedelta_between_posts=3600, maxlikes=0, likehashtags=[], page_name="", token=""):
        """
        To allow messages from anyone, include "" in ops
        """
        
        super().__init__(username, password, database, page_name, token)

        self.log(logging.INFO, "Starting up...")

        self.platform = "IGManager"
        
        self.permission_message = permission_message
        self.hashtags = hashtags
        self.timedelta_between_permission_request = timedelta_between_permission_request
        self.timedelta_between_posts = timedelta_between_posts

        if ops == []:
            ops = [username]

        self.ops = ops


        #TODO: Retrieve current lists from DB

        self.getting_permission_queue = queue.Queue()

        self.pending_approval_list = list()

        self.posting_queue = queue.Queue()


        self.restore_queues_state()


    def manage(self):
        try:
            threads = list()

            getmessages = threading.Thread(target=self.get_new_messages)
            threads.append(getmessages)

            getpermissions = threading.Thread(target=self.get_posting_permissions)
            threads.append(getpermissions)

            publishposts = threading.Thread(target=self.publish_posts)
            threads.append(publishposts)

            # runlikes = threading.Thread(target=self.run, args=())
            # threads.append(runlikes)

            for t in threads:
                t.start()
                time.sleep(10)

            for t in threads:
                t.join()

        except Exception as e:
            self.log(logging.ERROR, "Quitting InstagramManager: {}".format(e))


    def restore_queues_state(self):

        pu = (self.platform, self.username)

        gp = """
                select post_op, post_url, operator, img_src, time from managerPostApproval
                where platform = ? and username = ? and sent_request=0 order by time desc
            """

        get_tags_query = """
                        select hashtag from managerPostApprovalHashtags where post_url = ?
                        """

        pending_permission_requests = self.db.query(gp, pu)
        self.log(logging.DEBUG, "Pending permission requests: "+str(pending_permission_requests))

        pa = """
                select post_op, post_url, operator, img_src, time from managerPostApproval
                where platform = ? and username = ? and sent_request=1 and approved = 0 order by time desc
            """
        
        pending_approvals = self.db.query(pa, pu)
        self.log(logging.DEBUG, "Pending approval: "+str(pending_approvals))

        pp = """
                select post_op, post_url, operator, img_src, time from managerPostApproval
                where platform = ? and username = ? and approved = 1 and posted = 0 order by time desc
            """

        pending_publish = self.db.query(pp, pu)
        self.log(logging.DEBUG, "Pending publish: "+str(pending_publish))

        for p in pending_permission_requests:
            hashtags = [h[0] for h in self.db.query(get_tags_query, (p[1],))]
            self.getting_permission_queue.put(p+(hashtags, ))

        for p in pending_approvals:
            hashtags = [h[0] for h in self.db.query(get_tags_query, (p[1],))]
            self.pending_approval_list.append(p+(hashtags, ))

        for p in pending_publish:
            hashtags = [h[0] for h in self.db.query(get_tags_query, (p[1],))]
            self.posting_queue.put(p + (hashtags,))


    def go_to_inbox(self, driver):
        if driver.current_url != self.base_url + "direct/inbox/":
            try:
                driver.find_element_by_css_selector('a[href="/direct/inbox/"]').click()
            except Exception as e:
                self.log(logging.WARNING, "Failed clicking on inbox, forcing page change.\n{}".format(e))
                traceback.print_exc()
                driver.get(self.base_url + "direct/inbox/")
                time.sleep(2)
            finally:
                #Dismiss notifications dialog
                try:
                    driver.find_element_by_css_selector('button.bIiDR').click()
                except NoSuchElementException:
                    self.log(logging.NOTSET, "Notifications already turned on.")


    def switch_to_msg_thread(self, driver, user):
        """
        Navigates to the messages thread with @user
        """
        #Find new message
        try:
            try:
                driver.find_element_by_css_selector('h5._7UhW9.xLCgt.qyrsm.gtFbE.uL8Hv.T0kll').click()
                driver.find_element_by_xpath('//*[contains(text(), "")]/../../../../../../../../a[@class="-qQT3 rOtsg"]').click()
                driver.find_element_by_css_selector('div._7UhW9.xLCgt.qyrsm.KV-D4.uL8Hv').click()
                time.sleep(1)
                driver.find_elements_by_css_selector('button.aOOlW.HoLwm').click()
                time.sleep(2)
            except NoSuchElementException:
                self.log(logging.DEBUG, "No new message requests.")
            driver.find_element_by_xpath('//*[contains(text(), "{}")]/../../../../../../div[@class="                   Igw0E   rBNOH          YBx95   ybXk5    _4EzTm                      soMvl                                                                                        "]'.format(user)).click()
        except NoSuchElementException:
            raise NoNewMessagesFromUser(user)
        else:
            self.log(logging.INFO, "Found message from {}.".format(user))



    def get_new_messages(self):
        """
        Gets new posts sent to inbox by self.ops
        The ops must be already in the bot's DMs. The bot won't accept message requests.
        """
        driver = self.init_driver(managefunction="get_new_messages")
        self.log(logging.NOTSET, "Messages driver {}".format(driver))
        driver.implicitly_wait(10) #TODO: set to higher number?
        action = ActionChains(driver)
        try:
            super().login(driver)
            while True and not self.first_run:
                try:
                    self.go_to_inbox(driver)

                    for p in list(self.pending_approval_list):
                        self.log(logging.DEBUG, "Get new replies:" + str(p))
                        try:
                            self.switch_to_msg_thread(driver, p[0])
                        except NoNewMessagesFromUser as e:
                            self.log(logging.DEBUG, "{} hasn't answered back.".format(e.get_user()))
                        else: 
                            msgs = driver.find_elements_by_css_selector('div[class="                   Igw0E     IwRSH        YBx95       _4EzTm                                                                                   XfCBB            g6RW6               "]')
                            for msg in msgs:
                                if self.permission_is_granted(msg.find_element_by_css_selector('div>span').text):
                                    self.posting_queue.put(p)
                                    self.pending_approval_list.remove(p)
                                    self.db.approve_post_approval((self.platform, self.username, p[1]))
                                    #Send message back. This means put in queue and send message from the other thread
                                    self.log(self.FINISHED_LEVEL, "Permission granted by {}".format(p[0]))
                                    self.reply_message(driver, "Thank you! Your post was scheduled.") #TODO: Set this up in a way that it only asks for permissions within a day's notice, and only until it has enough to post for a day
                                    break
                        
                        if datetime.datetime.now() - p[4] > datetime.timedelta(days=self.DAYS_TO_APPROVE_TIMEOUT):
                            self.pending_approval_list.remove(p)
                            self.db.invalidate_post_approval((self.platform, self.username, p[1]))

                    for op in self.ops:
                        try:
                            self.switch_to_msg_thread(driver, op)
                        except NoNewMessagesFromUser as e:
                            self.log(logging.DEBUG, str(e))
                        else:
                            msgsboard = driver.find_element_by_css_selector('div.VUU41')
                            driver.execute_script('arguments[0].scrollTo(0, arguments[0].scrollHeight)', msgsboard)
                            time.sleep(1)
                            #Retrieve new posts
                            dmp = driver.find_elements_by_css_selector('div[class="_6JFwq  e9_tN"]>div>div[class="  _3PsV3  CMoMH    _8_yLp  "]>div.ZyFrc') #Gets lastest posts sent to IGManager
                            dmp.reverse()
                            self.log(logging.DEBUG, "Posts to see: {}".format(dmp))
                            for post in dmp:
                                try:
                                    post_user = post.find_element_by_css_selector('div>span[class="_7UhW9   xLCgt       qyrsm KV-D4         se6yk        "]').text
                                    img_src = post.find_element_by_css_selector('img[decoding="auto"]').get_attribute("srcset").split(" ")[0]
                                    #This section of the code works mac only
                                    post.find_element_by_css_selector('div[class="z82Jr"]').click()
                                    post_url = driver.current_url
                                    d = driver.find_element_by_class_name("C4VMK").text
                                    hashtags = list({word.strip("#") for word in d.split() if word.startswith("#")})
                                    driver.execute_script("window.history.go(-1)")

                                    #Exit after retrieving information
                                except (NoSuchElementException, StaleElementReferenceException) as e:
                                    self.log(logging.NOTSET, "Old message unaccessible...")
                                else:
                                    #Post_Item Organization
                                    post_item = (post_user, post_url, op, img_src, datetime.datetime.now(), hashtags)

                                    self.log(logging.DEBUG, "Posts queued for approval: " + str(self.posts_queued_for_approval()))

                                    self.log(logging.DEBUG, "Post Item: {}".format(post_item))
                                    if post_url not in self.posts_queued_for_approval():
                                        self.log(logging.DEBUG, "Get new messages for ops" + str(post_item))
                                        self.getting_permission_queue.put(post_item)
                                        self.log(self.FINISHED_LEVEL, "Queued post from user \"{}\" for acceptance.".format(post_user))
                                        self.reply_message(driver, "Received and filed!")
                                        self.db.add_post_approval((self.platform, self.username, post_user, post_url, op, img_src, post_item[4]), hashtags)
                                    else:
                                        self.reply_message(driver, "Duplicate post!")
                                        self.log(logging.INFO, "Post already handled.")
                            self.go_to_inbox(driver)

                except Exception as e:
                    self.log(logging.ERROR, "Failed getting new messages:\n{}".format(e))
                    traceback.print_exc()
                finally:
                    time.sleep(5)
        except Exception as e:
            self.log(logging.ERROR, "Exiting: {}".format(e))
            traceback.print_exc()
        finally:
            self.quit(driver)


    def permission_is_granted(self, msg):
        return msg.strip().lower() == self.ACCEPTANCE_MESSAGE


    def posts_queued_for_approval(self):
        """
        Returns a list of all the posts ever queued for approval
        #TODO: Retrieve these from database
        """

        query = """select post_url from managerPostApproval
                    where platform = ? and username = ?
                    """
        
        return [p[0] for p in self.db.query(query, (self.platform, self.username))]


    def reply_message(self, driver, msg):
        """
        You must be with a message thread in focus 
        """
        msg += "\n"
        driver.find_element_by_css_selector('textarea[placeholder="Message..."]').send_keys(msg)


    def send_message(self, driver, user, msg):
        """
        Sends @msg to @user
        """
        msg+="\n"
        self.go_to_inbox(driver)
        time.sleep(1)
        driver.find_element_by_xpath('//*[@aria-label="New Message"]/..').click()
        time.sleep(2)
        driver.find_element_by_css_selector('input[placeholder="Search..."]').send_keys("@{}".format(user))
        time.sleep(2)
        driver.find_elements_by_css_selector('div.-qQT3>div>div[class="                   Igw0E   rBNOH          YBx95   ybXk5    _4EzTm                      soMvl                                                                                        "')[0].click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[contains(text(), "Next")]').click() 
        time.sleep(2)
        driver.find_element_by_css_selector('textarea[placeholder="Message..."]').send_keys(msg)
        time.sleep(2)

    def get_posting_permissions(self):
        time.sleep(5)
        driver = self.init_driver(managefunction="get_posting_permissions")
        self.log(logging.NOTSET, "Permissions driver {}".format(driver))
        driver.implicitly_wait(10) #TODO: set to higher number?
        try:
            super().login(driver)
            while True and not self.first_run:
                self.go_to_inbox(driver)
                try:
                    p = self.getting_permission_queue.get()
                    self.log(logging.DEBUG, "Get posting permissions " + str(p))
                except queue.Empty:
                    self.log(logging.INFO, "No posts pending approval.")
                else:
                    self.log(logging.INFO, "Getting permissions for post {}".format(p[0]))
                    self.send_message(driver, p[0], self.generate_approach(p))
                    driver.get(p[1])
                    driver.find_element_by_xpath('//*[@aria-label="Share Post"]/..').click()
                    driver.find_element_by_xpath('//*[contains(text(), "Share to Direct")]/../../../../..').click()
                    driver.find_element_by_css_selector('input[placeholder="Search..."]').send_keys("@{}".format(p[0]))
                    driver.find_elements_by_css_selector('div.-qQT3>div>div[class="                   Igw0E   rBNOH          YBx95   ybXk5    _4EzTm                      soMvl                                                                                        "]')[0].click()
                    time.sleep(5)
                    driver.find_element_by_xpath('//button[contains(text(), "Send")]').click()
                    time.sleep(1)
                    self.pending_approval_list.append(p)
                    self.db.sent_permission_request((self.platform, self.username, p[1]))
                    self.log(logging.INFO, "Sent permission request to {}".format(p[0]))
                finally:
                    time.sleep(self.timedelta_between_permission_request)
        except Exception as e:
            self.log(logging.ERROR, "Exiting: {}".format(e))
        finally:
            self.quit(driver)
            

    def generate_approach(self, p):
        """
        Generates a message sent to users. Must include line breaks so the message gets sent
        """

        m = """Hey! One of our curators marked this image, and we want your permission to repost it, with due credits, on our page. This is an automated message. If you have any question, DM the curator who selected your post (@{}). If you allow us to feature you, reply just "ALLOW". Thank you, Rodri and Tony.
                """

        if self.permission_message != "":
            m = self.permission_message


        return m.format(p[2])

    
    def download_image(self, url):
        """
        Downloads an image from a given url.
        Returns the image bytecode and the relative filepath
        """
        filename = url.split("/")[-1].split("?")[0]

        while True and not self.first_run:
            try:
                r = requests.get(url)
                break
            except Exception as e:
                self.log(logging.WARNING, 'Except on SendRequest (wait 60 sec and resend): ' + str(e))
                time.sleep(60)

        if r.status_code == 200:
            try:
                os.mkdir('profiles/managers/{}/{}/img'.format(self.platform, self.username))
            except OSError as e:
                self.log(logging.NOTSET, "Directory already exists - {}".format(e))
            filepath = "profiles/managers/{}/{}/img/{}".format(self.platform, self.username, filename)
            f = open(os.path.abspath(filepath), "wb")
            f.write(r.content)
            f.close()
            self.log(logging.DEBUG, "Successfully downloaded image.")
            return filepath
        else:
            e = FailedImageDownload()
            self.log(logging.ERROR, str(e))
            raise e

    

    def post_photo(self, driver, filepath, caption):
        """
        Params:
        driver: driver
        imgb: image bytecode
        caption: caption
        """
        driver.find_element_by_css_selector("div[data-testid='new-post-button']").click()

        inelall = driver.find_elements_by_css_selector('input[type="file"]')
        inelall[len(inelall)-1].send_keys(os.path.abspath(filepath))                
        driver.find_element_by_css_selector("button.UP43G").click()

        driver.find_element_by_css_selector('textarea[aria-label="Write a caption…"]').send_keys(caption)
        driver.find_element_by_css_selector("button.UP43G").click()
        

    def create_caption(self, user, extrahashtags=[]):
        #TODO: Add page hashtags to caption
        m = "Original post by @{}.⠀".format(user)
        for h in self.hashtags:
            m += "#{} ".format(h)
        for h in extrahashtags[:3]:
            m += "#{} ".format(h)
        
        return m


    def publish_posts(self):
        driver = self.init_driver(managefunction="publish_posts", user_agent="mobile")
        self.log(logging.NOTSET, "Messages driver {}".format(driver))
        driver.implicitly_wait(10) #TODO: set to higher number?
        try:
            super().login_mobile(driver)
            while True:
                try:
                    p = self.posting_queue.get()
                    self.log(logging.DEBUG, "Posting photo:" + str(p))
                except queue.Empty:
                    self.log(logging.INFO, "Waiting for approved posts...")
                else:
                    self.log(logging.INFO, "Posting to feed with credits to {}".format(p[0]))

                    path = self.download_image(p[3]) #p4 = 1080p img url

                    self.post_photo(driver, path, self.create_caption(p[0], p[5]))
                    self.db.posted_approved_post((self.platform, self.username, p[1]))

                    self.log(self.FINISHED_LEVEL, "Posted successfully image by {}!".format(p[0]))

                finally:
                    time.sleep(self.timedelta_between_posts)
        except Exception as e:
            self.log(logging.ERROR, "Exiting: {}".format(e))
            traceback.print_exc()
        finally:
            self.quit(driver)

    
    def quit(self, driver=None):

        if self.first_run:
            self.log(self.FINISHED_LEVEL, "Completed setup for the first run. Please relaunch to run the program.")

        super().quit(driver)
                

if __name__ == "__main__":
    
    # igm = InstagramManager(credentials["instagram"][2]['username'], credentials["instagram"][2]['password'], ["rodrigommesquita", "_soopm"], "dbbots.db")
    igm = InstagramManager(credentials["instagram"][3]['username'], credentials["instagram"][3]['password'], credentials["instagram"][3]["ops"], "dbbots.db", permission_message=credentials["instagram"][3]["permission_message"], hashtags=credentials["instagram"][3]["hashtags"], timedelta_between_permission_request=120, timedelta_between_posts=120, likehashtags=params["instagram"][3][0], maxlikes=params["instagram"][3][1])
    igm.manage()