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

#Database module
from Database import Database

#Credentials
from config import credentials

#Params
from config import params

#Run with param --no-interface to hide interface
#Run the crontab with param --no-interface --no-colors 


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

        start_y = int((height // 3))

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
                stdscr.addstr(start_y + (i*3), start_x, string, curses.color_pair(4)) 
            elif(bot.get_likes_given()>=bot.get_max_likes()):
                stdscr.addstr(start_y + (i*3), start_x, string, curses.color_pair(2))
            else:
                stdscr.addstr(start_y + (i*3), start_x, string, curses.color_pair(3)) 
            

        # Refresh the screen 
        stdscr.refresh()

        time.sleep(1)



def bot_thread(bots, i, pvals, running_bots, finished_bots):
    logging.info("Thread %s: starting", i)
    for j in range(len(bots[i])):
        running_bots[i] = bots[i][j]

        #i could call the print outs here, but instead i'm calling the print outs from Bot.py, when starting to run, and on quit

        #the % bit is to re-use the same parameter for multiple accounts
        bots[i][j].run(pvals[i][j%(len(pvals[i]))])
        finished_bots.append(bots[i][j])
        running_bots[i] = None
        #set bigger waiting time in between bots ? like an hour
    logging.info("Thread %s: finishing", i)


def run_bots(bots, db):
    pvals = list(params.values())
    threads=list()
    running_bots = list()
    finished_bots = list()
    
    for i in range(len(bots)):
        running_bots.append(None)
        #separate in threads
        x = threading.Thread(target=bot_thread, args=(bots, i, pvals, running_bots, finished_bots), daemon=True)
        threads.append(x)
        x.start()

    if not ("--no-interface" in sys.argv):
        curses.wrapper(interface, running_bots, finished_bots, threads)

    for i, thread in enumerate(threads):
        thread.join()

    #add finished_bots to database
    for bot in finished_bots:
        if bot.get_max_likes() > 0:
            likejob = (bot.get_username(), bot.get_platform(), bot.get_likes_given(), bot.get_max_likes(), bot.get_status(), bot.get_time_started(), bot.get_time_ended(), bot.get_posts_seen())
            db.create_likejob(likejob)
            liked_posts = bot.get_posts_liked()
            if len(liked_posts)>0:
                for post in liked_posts:
                    liked_post = (bot.get_username(), bot.get_platform(), post[0], post[1])
                    post_id = db.create_liked_post(liked_post)
                    for hashtag in post[2]:
                        db.add_post_hashtag((post_id, hashtag))



def get_bots(db):

    igbots = []
    for i in range(len(credentials['instagram'])): #instagram
        igbots.append(InstagramBot(credentials['instagram'][i]['username'], credentials['instagram'][i]['password']))
    igbots2 = []
    for i in range(len(credentials['instagram2'])): #mom's instagram
        igbots2.append(InstagramBot(credentials['instagram2'][i]['username'], credentials['instagram2'][i]['password']))
    ttbots = []
    for i in range(len(credentials['twitter'])):
        ttbots.append(TwitterBot(credentials['twitter'][i]['username'], credentials['twitter'][i]['password']))

    bots = [
        [SubmitHubBot(credentials['submithub']['username'], credentials['submithub']['password'])],
        ttbots,
        igbots,
        igbots2
    ]

    for botlist in bots:
        for bot in botlist:
            db.create_account((bot.get_username(), bot.get_platform()))

    pvals = list(params.values()) 
    for i in range(1, len(pvals)):
        for j in range(len(pvals[i])):
            for hashtag in pvals[i][j][0]:
                db.add_account_hashtag((bots[i][j].get_username(), bots[i][j].get_platform(), hashtag, 0))

    return bots



def main():
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

    db = Database("/Users/romes/everything-else/botdev/organized/likebots/dbbots.db")

    bots = get_bots(db)

    logging.info("Main: Starting bot threads.")
    run_bots(bots, db)
    logging.info("Main: Finished all bot threads.")

    db.close()

    logging.info("Closed database. End program.")



if __name__ == "__main__":
    main()
