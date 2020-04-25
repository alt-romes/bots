import requests
import json
import string
import random
import logging

class InstagramAPI:

    API_URL = 'https://graph.facebook.com/v6.0/'

    def __init__(self, page_name, access_token, logf=None):
        # self.state = (lambda stringLength: ''.join(random.choice(string.ascii_letters) for i in range(stringLength)))(12)
        self.page_name = page_name
        self.token = access_token
        self.isLoggedIn = True
        self.LastResponse = None
        self.s = requests.Session()

        if logf is None:
            self.log = (lambda level, msg: print(msg))
        else:
            self.log = logf


    #THIS FUNCTION IS NOT BEING RUN
    def login(self, force=False):
        self.log(logging.WARNING, "I'm using a developer token. I should already be logged in.")
        if (not self.isLoggedIn or force):
            login_params = {
                'client_id': self.app_id,
                'redirect_uri': 'https://www.facebook.com/connect/login_success.html',
                'state': self.state
                
            }
            r = self.s.post('https://www.facebook.com/v6.0/dialog/oauth', params=login_params)


    # page_name: Name of the business page associated with the instagram account
    def get_ig_uid(self):
        if self.SendRequest('me/accounts', {'access_token': self.token}):
            user_page_id = ""
            for i in range(len(self.LastJson['data'])):
                if(self.LastJson['data'][i]['name']==self.page_name):
                    user_page_id = self.LastJson['data'][i]['id']
                    break
            if self.SendRequest(user_page_id, {'fields': 'instagram_business_account','access_token': self.token}):
                return self.LastJson['instagram_business_account']['id']


    def get_all_posts(self):
        if self.SendRequest("{}/media".format(self.get_ig_uid()), {'access_token': self.token}):
            return self.LastJson['data']
        return


    def SendRequest(self, endpoint, params=None, post=None, login=False):

            if (not self.isLoggedIn and not login):
                raise Exception("Not logged in!\n")

            # self.s.headers.update({'Connection': 'close',
            #                     'Accept': '*/*',
            #                     'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            #                     'Cookie2': '$Version=1',
            #                     'Accept-Language': 'en-US',
            #                     'User-Agent': self.USER_AGENT})

            while True:
                try:
                    if (post is not None):
                        response = self.s.post(self.API_URL + endpoint, data=post)
                    else:
                        response = self.s.get(self.API_URL + endpoint, params=params)
                    break
                except Exception as e:
                    self.log(logging.WARNING, 'Except on SendRequest (wait 60 sec and resend): ' + str(e))
                    time.sleep(60)

            if response.status_code == 200:
                self.LastResponse = response
                self.LastJson = json.loads(response.text)
                return True
            else:
                self.LastResponse = response
                self.LastJson = json.loads(response.text)
                self.log(logging.ERROR, "Request return " + str(response.status_code) + " error!\n" + str(self.LastJson))
                return False