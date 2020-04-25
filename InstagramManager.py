from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from config import credentials

from exceptions.BotExceptions import FailedImageDownload
from InstagramBot import InstagramBot


import os
import requests
import time
import logging
import threading
import queue

class InstagramManager(InstagramBot):

    CHECK_FOR_NEW_MESSAGES_FREQUENCY = 60
    MAX_PERMISSIONS_PER_HOUR = 6
    ACCEPTANCE_MESSAGE = "allow"

    def __init__(self, username, password, ops, page_name="", token=""):
        
        super().__init__(username, password, page_name, token)

        self.log(logging.INFO, "Starting up...")

        self.platform = "IGManager"

        self.ops = ops

        self.all_posts_for_approval = []
        self.getting_permission_queue = queue.Queue()

        self.pending_approval_list = list()

        self.posting_queue = queue.Queue()

    def manage(self):
        try:
            threads = list()

            getmessages = threading.Thread(target=self.get_new_messages)
            threads.append(getmessages)

            getpermissions = threading.Thread(target=self.get_posting_permissions)
            threads.append(getpermissions)

            publishposts = threading.Thread(target=self.publish_posts)
            threads.append(publishposts)

            for t in threads:
                t.start()
                time.sleep(1)

            for t in threads:
                t.join()

        except Exception as e:
            self.log(logging.ERROR, "Quitting InstagramManager: {}".format(e))


    def go_to_inbox(self, driver):
        if driver.current_url != self.base_url + "direct/inbox/":
            try:
                driver.find_element_by_css_selector('a[href="/direct/inbox/"]').click()
            except Exception as e:
                self.log(logging.WARNING, "Failed clicking on inbox, forcing page change.\n{}".format(e))
                driver.get(self.base_url + "direct/inbox/")
            else:
                #Dismiss notifications dialog
                try:
                    driver.find_element_by_css_selector('button.bIiDR').click()
                except NoSuchElementException:
                    self.log(logging.NOTSET, "Notifications already turned on.")


    def get_new_messages(self):
        """
        Gets new posts sent to inbox by self.ops
        The ops must be already in the bot's DMs. The bot won't accept message requests.
        """
        driver = self.init_driver(managefunction="get_new_messages")
        self.log(logging.NOTSET, "Messages driver {}".format(driver))
        driver.implicitly_wait(5) #TODO: set to higher number?
        action = ActionChains(driver)
        try:
            super().login(driver)
            while True:
                try:
                    self.go_to_inbox(driver)

                    for op in self.ops:
                        try:
                            #Find new message
                            mthread = driver.find_element_by_xpath('//*[contains(text(), "{}")]/../../../../../../div[@class="                   Igw0E   rBNOH          YBx95   ybXk5    _4EzTm                      soMvl                                                                                        "]'.format(op))
                            self.log(logging.INFO, "Found message from {}.".format(op))
                            mthread.click()
                            time.sleep(1)
                            #Retrieve new posts
                            dmp = driver.find_elements_by_css_selector('div[class="_6JFwq  e9_tN"]>div>div[class="  _3PsV3  CMoMH    _8_yLp  "]>div.ZyFrc') #Gets lastest posts sent to IGManager
                            dmp.reverse()
                            for post in dmp:
                                try:
                                    post_user = post.find_element_by_css_selector('div>span[class="_7UhW9   xLCgt       qyrsm KV-D4         se6yk        "]').text
                                    post_desc = post.find_element_by_css_selector('div>span[class="_7UhW9   xLCgt      MMzan  KV-D4         se6yk        "]>span>span').text
                                    img_src = post.find_element_by_css_selector('div[class="z82Jr"]>img').get_attribute("srcset").split(" ")[0]
                                    #This section of the code works mac only
                                    post.find_element_by_css_selector('div[class="z82Jr"]').click()
                                    post_url = driver.current_url
                                    driver.execute_script("window.history.go(-1)")

                                    #Exit after retrieving information
                                except (NoSuchElementException, StaleElementReferenceException) as e:
                                    self.log(logging.NOTSET, "Ignoring old messages...")
                                else:
                                    #Post_Item Organization
                                    post_item = (post_user, post_desc, post_url, op, img_src)

                                    if (post_item[0], post_item[1]) not in [(p[0], p[1]) for p in self.posts_queued_for_approval()]:
                                        self.log(self.FINISHED_LEVEL, "Queued post from user \"{}\" for acceptance.".format(post_user))
                                        self.all_posts_for_approval.append(post_item) #TODO: Make this add to DB instead
                                        self.getting_permission_queue.put(post_item)
                                    else:
                                        self.log(logging.INFO, "Post already queued.")
                            self.go_to_inbox(driver)
                        except NoSuchElementException:
                            self.log(logging.INFO, "No new messages from {}.".format(op))

                    for p in list(self.pending_approval_list):
                        try:
                            mthread = driver.find_element_by_xpath('//*[contains(text(), "{}")]/../../../../../../div[@class="                   Igw0E   rBNOH          YBx95   ybXk5    _4EzTm                      soMvl                                                                                        "]'.format(p[0]))
                            self.log(logging.INFO, "Found message from {}.".format(p[0]))
                            mthread.click()

                            msgs = driver.find_elements_by_css_selector('div[class="                   Igw0E     IwRSH        YBx95       _4EzTm                                                                                   XfCBB            g6RW6               "]')
                            for msg in msgs:
                                if self.permission_is_granted(msg.find_element_by_css_selector('div>span').text):
                                    self.pending_approval_list.remove(p)
                                    self.log(self.FINISHED_LEVEL, "Permission granted by {}".format(p[0]))
                                    self.posting_queue.put(p)
                                    break
                        except NoSuchElementException:
                            self.log(logging.DEBUG, "{} hasn't answered back.".format(p[0]))

                except Exception as e:
                    self.log(logging.ERROR, "Failed getting new messages: {}".format(e))
                finally:
                    time.sleep(10) #TODO: REPLACE BY self.CHECK_FOR_NEW_MESSAGES_FREQUENCY
        except Exception as e:
            self.log(logging.ERROR, "Exiting: {}".format(e))
            driver.quit()


    def permission_is_granted(self, msg):
        return msg.strip().lower() == self.ACCEPTANCE_MESSAGE


    def posts_queued_for_approval(self):
        """
        Returns a list of all the posts ever queued for approval
        #TODO: Retrieve these from databse
        """
        return self.all_posts_for_approval


    def send_message(self, driver, user, msg):
        """
        Sends @msg to @user
        """
        self.go_to_inbox(driver)
        driver.find_element_by_xpath('//*[@aria-label="New Message"]/..').click()
        driver.find_element_by_css_selector('input[placeholder="Search..."]').send_keys("@{}".format(user))
        driver.find_elements_by_css_selector('div.-qQT3>div>div[class="                   Igw0E   rBNOH          YBx95   ybXk5    _4EzTm                      soMvl                                                                                        "')[0].click()
        driver.find_element_by_xpath('//*[contains(text(), "Next")]').click() 
        driver.find_element_by_css_selector('textarea[placeholder="Message..."]').send_keys(msg)

    def get_posting_permissions(self):
        driver = self.init_driver(managefunction="get_posting_permissions")
        self.log(logging.NOTSET, "Permissions driver {}".format(driver))
        driver.implicitly_wait(5) #TODO: set to higher number?
        try:
            super().login(driver)
            while True:
                # self.go_to_inbox(driver)
                try:
                    #I know some things are repeating, but it's the full workflow, and it repeats just twice.
                    p = self.getting_permission_queue.get()
                    self.log(logging.INFO, "Getting permissions for post {}".format(p[0], p[1]))
                    driver.get(p[2])
                    driver.find_element_by_xpath('//*[@aria-label="Share Post"]/..').click()
                    driver.find_element_by_xpath('//*[contains(text(), "Share to Direct")]/../../../../..').click()
                    driver.find_element_by_css_selector('input[placeholder="Search..."]').send_keys("@{}".format(p[0]))
                    driver.find_elements_by_css_selector('div.-qQT3>div>div[class="                   Igw0E   rBNOH          YBx95   ybXk5    _4EzTm                      soMvl                                                                                        "]')[0].click()
                    driver.find_element_by_xpath('//*[contains(text(), "Send")]').click()
                    self.send_message(driver, p[0], self.generate_approach(p))
                    self.pending_approval_list.append(p)
                except queue.Empty:
                    self.log(logging.INFO, "No posts pending approval.")
                finally:
                    self.go_to_inbox(driver)
                    # time.sleep(10) #TODO: Replace with (3600 / self.MAX_PERMISSIONS_PER_HOUR)
        except Exception as e:
            self.log(logging.ERROR, "Exiting: {}".format(e))
            driver.quit()
            

    def generate_approach(self, p):
        """
        Generates a message sent to users. Must include line breaks so the message gets sent
        """
        return """
                Hey! One of our curators marked this image, and we want your permission to repost it, with due credits, on our page. This is an automated message. If you have any question, DM the curator who selected your post (@{}). If you allow us to feature you, reply just "ALLOW". Thank you, Rodri and Tony.
                """.format(p[3])

    
    def download_image(self, url):
        """
        Downloads an image from a given url.
        Returns the image bytecode and the relative filepath
        """
        filename = url.split("/")[-1].split("?")[0]

        while True:
            try:
                r = requests.get(url)
                break
            except Exception as e:
                self.log(logging.WARNING, 'Except on SendRequest (wait 60 sec and resend): ' + str(e))
                time.sleep(60)

        if r.status_code == 200:
            try:
                os.mkdir('profiles/IGManager/{}/img'.format(self.username))
            except OSError as e:
                self.log(logging.NOTSET, "Directory already exists - {}".format(e))
            filepath = "profiles/IGManager/{}/img/{}".format(self.username, filename)
            f = open(os.path.abspath(filepath), "wb")
            f.write(r.content)
            f.close()
            self.log(logging.DEBUG, "Successfully downloaded image.")
            return (r.content, filepath)
        else:
            e = FailedImageDownload()
            self.log(logging.ERROR, str(e))
            raise e

    

    def post_photo(self, driver, imgb, caption):
        """
        Params:
        imgb: image bytecode
        caption: caption
        """
        upload_id = str(int(time.time()))
        requests.post("https://instagram.com/create/upload/photo/", data={"formData": {"upload_id": upload_id, "photo": str(imgb), "media_type": "1"}})
        requests.post("POST", "https://instagram.com/create/configure/", data={"form": {upload_id, caption}})
        

    def create_caption(self, user):
        #TODO: Add page hashtags to caption
        return "Original image by @{}. Check out their profile!".format(user)


    def publish_posts(self):
        driver = self.init_driver(managefunction="publish_posts", user_agent="mobile")
        self.log(logging.NOTSET, "Messages driver {}".format(driver))
        driver.implicitly_wait(5) #TODO: set to higher number?
        try:
            super().login_mobile(driver)
            while True:
                try:
                    p = self.posting_queue.get()
                    self.log(logging.INFO, "Posting to feed with credits to {}".format(p[0]))

                    imgb, relpath = self.download_image(p[4]) #p4 = 1080p img url

                    self.post_photo(driver, imgb, self.create_caption(p[0]))

                    # inel = driver.find_elements_by_css_selector('input[type="file"]')[2]
                    # inel.send_keys(os.path.abspath(filepath))
                    
                    # driver.find_element_by_css_selector("div[data-testid='new-post-button']").click()

                except queue.Empty:
                    self.log(logging.INFO, "Waiting for approved posts...")
                finally:
                    time.sleep(10) #TODO: Replace with amount of time between posts?
        except Exception as e:
            self.log(logging.ERROR, "Exiting: {}".format(e))
            driver.quit()
                

if __name__ == "__main__":
    
    igm = InstagramManager(credentials["instagram"][2]['username'], credentials["instagram"][2]['password'], ["rodrigommesquita", "_soopm"])

    igm.manage()