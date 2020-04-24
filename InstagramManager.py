from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from config import credentials

from InstagramBot import InstagramBot

import time
import logging
import threading
import queue

class InstagramManager(InstagramBot):

    CHECK_FOR_NEW_MESSAGES_FREQUENCY = 60
    MAX_PERMISSIONS_PER_HOUR = 6
    ACCEPTANCE_MESSAGE = "you have my permission"

    def __init__(self, username, password, page_name, token, ops):
        
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
                            #Retrieve new posts
                            dmp = driver.find_elements_by_css_selector('div[class="_6JFwq  e9_tN"]>div>div[class="  _3PsV3  CMoMH    _8_yLp  "]>div.ZyFrc') #Gets lastest posts sent to IGManager
                            for post in dmp:
                                try:
                                    post_user = post.find_element_by_css_selector('div>span[class="_7UhW9   xLCgt       qyrsm KV-D4         se6yk        "]').text
                                    post_desc = post.find_element_by_css_selector('div>span[class="_7UhW9   xLCgt      MMzan  KV-D4         se6yk        "]>span>span').text

                                    #This section of the code works mac only
                                    post_button = post.find_element_by_css_selector('div[class="z82Jr"]')
                                    action.key_down(Keys.COMMAND).click(post_button).key_up(Keys.COMMAND).key_down(Keys.COMMAND).send_keys("2").key_up(Keys.COMMAND).perform()
                                    post_url = driver.current_url
                                    action.key_down(Keys.COMMAND).send_keys("w").key_up(Keys.COMMAND)

                                    # driver.execute_script("window.history.go(-1)")
                                    #Exit after retrieving information
                                except (NoSuchElementException, StaleElementReferenceException) as e:
                                    self.log(logging.INFO, "Message selected is not a user post. {}".format(e))
                                else:
                                    post_item = (post_user, post_desc, post_url, op)
                                    is_queued = False
                                    for p in self.posts_queued_for_approval():
                                        if "{} {}".format(post_user, post_desc) == "{} {}".format(p[0], p[1]):
                                            is_queued = True
                                            break
                                    if not is_queued:
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


    def get_posting_permissions(self):
        time.sleep(2)
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
                    self.log(logging.DEBUG, "Got post url")
                    driver.find_element_by_xpath('//*[@aria-label="Share Post"]/..').click()
                    self.log(logging.DEBUG, "Clicked share")
                    driver.find_element_by_xpath('//*[contains(text(), "Share to Direct")]/../../../../..').click()
                    self.log(logging.DEBUG, "Selected share to direct")
                    driver.find_element_by_css_selector('input[placeholder="Search..."]').send_keys("@{}".format(p[0]))
                    driver.find_elements_by_css_selector('div.-qQT3>div>div[class="                   Igw0E   rBNOH          YBx95   ybXk5    _4EzTm                      soMvl                                                                                        "]')[0].click()
                    driver.find_element_by_xpath('//*[contains(text(), "Send")]').click()
                    self.go_to_inbox(driver)
                    driver.find_element_by_xpath('//*[@aria-label="New Message"]/..').click()
                    driver.find_element_by_css_selector('input[placeholder="Search..."]').send_keys("@{}".format(p[0]))
                    driver.find_elements_by_css_selector('div.-qQT3>div>div[class="                   Igw0E   rBNOH          YBx95   ybXk5    _4EzTm                      soMvl                                                                                        "')[0].click()
                    driver.find_element_by_xpath('//*[contains(text(), "Next")]').click() 
                    driver.find_element_by_css_selector('textarea[placeholder="Message..."]').send_keys(self.generate_approach(p))
                    self.pending_approval_list.append(p)
                except queue.Empty:
                    self.log(logging.INFO, "No posts pending approval.")
                finally:
                    self.go_to_inbox(driver)
                    time.sleep(10) #TODO: Replace with (3600 / self.MAX_PERMISSIONS_PER_HOUR)
        except Exception as e:
            self.log(logging.ERROR, "Exiting: {}".format(e))
            driver.quit()
            

    def generate_approach(self, p):
        """
        Generates a message sent to users. Must include line breaks so the message gets sent
        """
        return """
                Hey! One of our curators marked this image, and we want your permission to repost it, with due credits, on our page. This is an automated message. If you have a question, you can speak to the curator who selected your post (@{}). If you allow us to feature you, reply exactly "you have my permission". Thank you, Rodri and Tony.
                """.format(p[3])


    def publish_posts(self):
        while True:
            try:
                p = self.posting_queue.get()
            except queue.Empty:
                self.log(logging.INFO, "Waiting for approved posts...")
            else:
                self.log(self.FINISHED_LEVEL, "Permission granted by {}. Posting to feed.".format(p[0]))
            finally:
                time.sleep(10) #TODO: Replace with amount of time between posts?

if __name__ == "__main__":
    
    igm = InstagramManager(credentials["instagram"][2]['username'], credentials["instagram"][2]['password'], credentials["instagram"][0]['page_name'], credentials["instagram"][0]['token'], ["rodrigommesquita", "_soopm"])

    #TODO: put in 2 threads igm.manage and igm.run
    igm.manage()


#one of our curaters sugested your post: i need your permission