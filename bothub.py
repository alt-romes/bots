#Dependencies
import random
import threading
import logging
import time
import curses
import sys

import sqlite3
from sqlite3 import Error

#Bots
from SubmitHubBot import SubmitHubBot
from InstagramBot import InstagramBot
from TwitterBot import TwitterBot

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
                string = ("Ongoing: " + bot.get_username() + " in " + bot.get_site() + " [ " + str(bot.get_likes_given()) + " / " + str(bot.get_max_likes()) + " ]" )[:width-1]
                start_x = int((width // 2) - (len(string) // 2) - len(string) % 2)
                stdscr.addstr(start_y + (i*3), start_x, string)

        start_y+=len(running_bots)*3
        for i, bot in enumerate(finished_bots):
            string = ("Finished: " + bot.get_username() + " in " + bot.get_site() + " [ " + str(bot.get_likes_given()) + " / " + str(bot.get_max_likes()) + " ]")[:width-1]
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


def run_bots(bots, connection):
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





    
def create_account(conn, account):

    sql = ''' INSERT INTO projects(username, platform)
              VALUES(?, ?)'''
    cur = conn.cursor()
    cur.execute(sql, account)
    return cur.lastrowid


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def create_database(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
        return

    if conn is not None:

        accounts_table = """ CREATE TABLE IF NOT EXISTS accounts (
                                            id integer PRIMARY KEY,
                                            username text NOT NULL,
                                            platform text NOT NULL
                                        ); """

        likejobs_table = """ CREATE TABLE IF NOT EXISTS likeJobs (
                                            acc_id integer,
                                            time_start text NOT NULL,
                                            time_end text NOT NULL,
                                            likes_given integer,
                                            max_likes integer,
                                            posts_seen integer,
                                            PRIMARY KEY (acc_id, time_start),
                                            FOREIGN KEY (acc_id) REFERENCES Accounts (id)
                                        ); """ 

        acchashtags_table = """ CREATE TABLE IF NOT EXISTS accHashtags (
                                            acc_id integer PRIMARY KEY,
                                            hashtag text NOT NULL,
                                            FOREIGN KEY (acc_id) REFERENCES Accounts (id)
                                        ); """

        likedposts_table = """ CREATE TABLE IF NOT EXISTS likedPosts (
                                            acc_id integer,
                                            post_id integer,
                                            user_liked text NOT NULL,
                                            time text NOT NULL,
                                            PRIMARY KEY (acc_id, post_id),
                                            FOREIGN KEY (acc_id) REFERENCES Accounts (id)
                                        ); """

        likedpostshashtags_table = """ CREATE TABLE IF NOT EXISTS likedPostsHashtags (
                                            post_id integer PRIMARY KEY,
                                            hashtag text NOT NULL,
                                            FOREIGN KEY (post_id) REFERENCES LikedPosts (post_id)
                                        ); """

        create_table(conn, accounts_table)
        create_table(conn, likejobs_table)
        create_table(conn, acchashtags_table)
        create_table(conn, likedposts_table)
        create_table(conn, likedpostshashtags_table)
    
    else:
        print("Error connecting to database!")

    return conn

def get_bots(conn):

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
            pass

    return bots



def main():
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

    conn = create_database("/Users/romes/everything-else/botdev/organized/likebots/dbbots.db")

    bots = get_bots(conn)

    logging.info("Main: Starting bot threads.")
    run_bots(bots, 0) #conn
    logging.info("Main: Finished all bot threads.")

    conn.close()

    logging.info("Closed database. End program.")



if __name__ == "__main__":
    main()
