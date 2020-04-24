from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException

from config import credentials

from InstagramBot import InstagramBot

import time
import logging
import threading
import queue

class InstagramManager(InstagramBot):

    def __init__(self, username, password, page_name, token, ops):
        
        super().__init__(username, password, page_name, token)

        self.log(logging.INFO, "Starting up...")

        self.platform = "IGManager"

        self.ops = ops

        self.all_posts_for_approval = []
        self.getting_permission_queue = queue.Queue()

        self.posting_queue = queue.Queue()

    def manage(self):
        try:
            threads = list()

            getmessages = threading.Thread(target=self.get_new_messages)
            threads.append(getmessages)

            getpermissions = threading.Thread(target=self.get_posting_permissions)
            threads.append(getpermissions)

            for t in threads:
                t.start()

            for t in threads:
                t.join()

        except Exception as e:
            self.log(logging.ERROR, "Quitting InstagramManager: {}".format(e))

        finally:
            self.quit()


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
                                post_el = post.find_element_by_css_selector('div[class="z82Jr"]')
                                #Exit after retrieving information
                            except NoSuchElementException as e:
                                self.log(logging.INFO, "Message selected is not a user post. {}".format(e))
                            else:
                                post_item = (post_user, post_desc, post_el)
                                is_queued = False
                                for p in self.posts_queued_for_approval():
                                    if "{} {}".format(post_user, post_desc) == "{} {}".format(p[0], p[1]):
                                        is_queued = True
                                        break
                                if not is_queued:
                                    self.log(logging.INFO, "Queued post from user \"{}\" for acceptance.".format(post_user))
                                    self.all_posts_for_approval.append(post_item) #TODO: Make this add to DB instead
                                    self.getting_permission_queue.put(post_item)
                                else:
                                    self.log(logging.INFO, "Post already queued.")
                        self.go_to_inbox(driver)
                    except NoSuchElementException:
                        self.log(logging.INFO, "No new messages from {}.".format(op))

            except Exception as e:
                self.log(logging.ERROR, "Failed getting new messages: {}".format(e))
            finally:
                time.sleep(5)


    def posts_queued_for_approval(self):
        """
        Returns a list of all the posts ever queued for approval
        #TODO: Retrieve these from databse
        """
        return self.all_posts_for_approval


    def get_posting_permissions(self):
        time.sleep(10)
        driver = self.init_driver(managefunction="get_posting_permissions")
        self.log(logging.NOTSET, "Permissions driver {}".format(driver))
        driver.implicitly_wait(5) #TODO: set to higher number?
        super().login(driver)
        self.go_to_inbox(driver)
        while True:
            try:
                p = self.getting_permission_queue.get()
                self.log(logging.INFO, "Getting permissions for post {}".format(p[0], p[1]))
            except queue.Empty:
                self.log(logging.INFO, "No posts pending approval.")
            time.sleep(6)
            


if __name__ == "__main__":
    
    igm = InstagramManager(credentials["instagram"][2]['username'], credentials["instagram"][2]['password'], credentials["instagram"][0]['page_name'], credentials["instagram"][0]['token'], ["rodrigommesquita", "_soopm"])

    #TODO: put in 2 threads igm.manage and igm.run
    igm.manage()


#one of our curaters sugested your post: i need your permission