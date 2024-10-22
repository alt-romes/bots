#Dependencies
import random
import threading
import logging
import time
import curses
import sys

#Bots
from SubmitHubBot import SubmitHubBot
from InstagramBot import InstagramBot
from TwitterBot import TwitterBot
from Bot import Bot

#Database module
from Database import Database

#Credentials
from config import credentials

#Params
from config import params

logBot = Bot(logBot=True)

#Run with param --curses to use curses interface
def interface(stdscr, running_bots, finished_bots, threads): #stdscr, 
    time.sleep(1)

    #Use colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    stdscr.bkgd(' ', curses.color_pair(1) | curses.A_BOLD)

    #Set cursor invisible
    curses.curs_set(0)

    # Clear and refresh the screen for a blank canvas

    while any(t.is_alive() for t in threads):

        stdscr.clear()

        height, width = stdscr.getmaxyx()

        # Remember this, it's pretty funny
        #curses.beep()
        #curses.flash()

        start_y = int((height // 5))

        # Print
        for i, bot in enumerate(running_bots):
            if bot!=None:
                string = ("Ongoing: " + bot.get_username() + " in " + bot.get_platform() + " [ " + str(bot.get_likes_given()) + " / " + str(bot.get_max_likes()) + " ]" )[:width-1]
                start_x = int((width // 2) - (len(string) // 2) - len(string) % 2)
                stdscr.addstr(start_y + (i*3), start_x, string)

        start_y+=len(running_bots)*3
        for i, bot in enumerate(finished_bots):
            string = ("Finished: " + bot.get_username() + " in " + bot.get_platform() + " [ " + str(bot.get_likes_given()) + " / " + str(bot.get_max_likes()) + " ]")[:width-1]
            start_x = int((width // 2) - (len(string) // 2) - len(string) % 2)
            if(bot.get_max_likes()<=0):
                # stdscr.addstr(start_y + (i*3), start_x, string, curses.color_pair(4)) 
                pass
            elif(bot.get_likes_given()>=bot.get_max_likes()):
                stdscr.addstr(start_y + (i*3), start_x, string, curses.color_pair(2))
            else:
                stdscr.addstr(start_y + (i*3), start_x, string, curses.color_pair(3)) 
            

        # Refresh the screen 
        stdscr.refresh()

        time.sleep(1)



def bot_thread(bots, i, pvals, running_bots, finished_bots):
    logBot.log(logging.INFO, "Thread {}: starting".format(i))
    for j in range(len(bots[i])):
        running_bots[i] = bots[i][j]

        #i could call the print outs here, but instead i'm calling the print outs from Bot.py, when starting to run, and on quit

        #the % bit is to re-use the same parameter for multiple accounts
        try:
            bots[i][j].run(pvals[i][j%(len(pvals[i]))])
        except Exception as e:
            logBot.log(logging.CRITICAL, "Bot crashed! {}".format(str(e)))
        finished_bots.append(bots[i][j])
        running_bots[i] = None
        #set bigger waiting time in between bots ? like an hour
    logBot.log(logging.INFO, "Thread {}: finishing".format(i))


def run_bots(bots): 
    pvals = list(params.values())
    threads=list()
    running_bots = list()
    finished_bots = list()
    
    for i in range(len(bots)):
        running_bots.append(None)
        #separate in threads
        x = threading.Thread(target=bot_thread, args=(bots, i, pvals, running_bots, finished_bots))
        threads.append(x)
        x.start()

    if  "--curses" in sys.argv :
        curses.wrapper(interface, running_bots, finished_bots, threads)

    for i, thread in enumerate(threads):
        thread.join()


def create_bots(db):

    igbots = []
    igbots.append(InstagramBot(credentials['instagram'][0]['username'], credentials['instagram'][0]['password'], db, credentials['instagram'][0]['page_name'], credentials['instagram'][0]['token']))
    for i in range(1, len(credentials['instagram'])): #instagram
        igbots.append(InstagramBot(credentials['instagram'][i]['username'], credentials['instagram'][i]['password'], db))
    igbots2 = []
    for i in range(len(credentials['instagram2'])): #mom's instagram
        igbots2.append(InstagramBot(credentials['instagram2'][i]['username'], credentials['instagram2'][i]['password'], db, watch_feed_stories=False))
    ttbots = []
    for i in range(len(credentials['twitter'])):
        ttbots.append(TwitterBot(credentials['twitter'][i]['username'], credentials['twitter'][i]['password'], db))

    bots = [
        [SubmitHubBot(credentials['submithub']['username'], credentials['submithub']['password'], db)],
        ttbots,
        igbots,
        igbots2
    ]

    return bots


def main():

    db = "dbbots.db"

    bots = create_bots(db)

    #TODO: NOT EXTENSIBLE CALL. ALSO, THIS TOKEN EXPIRES IN TWO MONTHS. Steps (IN THIS ORDER) : 1- Add the permissions, 2- Select Generate Key
    # InstagramAPI shall be called from InstagramBot. this file only interacts with InstagramBot.
    # igAPI = InstagramAPI('Romes', 'EAAEjpIcjnsEBAPwg4SW3ZAvElCZBnoWgN85t8VifWPhU1VTiGWlk6kVV5lOKPxPeWxYrIBEpbqDA66FYqgYKOCW6XgrxEWo1MuD1Ld8KkYkvcWZAtsvakx0VCXpcUH4MFMvIqkvpd6MZBFKmq6yZAUHDcDZA9go78ZD')

    logBot.log(logging.INFO, "Main: Starting bot threads.")
    run_bots(bots) #, db
    logBot.log(logging.INFO, "Program end.")



if __name__ == "__main__":
    main()

