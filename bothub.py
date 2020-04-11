#Dependencies
import random
import threading
import logging
import time
import curses

#Bots
from SubmitHubBot import SubmitHubBot
from InstagramBot import InstagramBot

#Credentials
from credentials import credentials

params = {
    #Each website has a list of lists of parameters, each list of parameters matches one account for that website.
    #A list of parameters is passed to the function bot.run(), and each element is a required argument for that said bot.
    #You can have just one list of parameters for more than one account.

    #SubmitHub: Number of songs to rate.
    'submithub': [
        [5]
    ],

    #Instagram: Hashtags, Number of posts to like
    'instagram': [
        [
            ['shoegaze', 'dreampop', 'experimental', 'soundscapes', "album", 'indie', "homestudio", "recording", "record", "altrock", 'music', 'artist', 'art', 'alternative', 'musician', "drawing", "instamusic", 'spotify'],
            5
        ]
    ],

    #Instagram da Mae: Mesma ordem
    'maeig': [
        [
            ["lookbook", "simplelook", "ootd", "outfitoftheday", "wiwt", "lookoftheday", "picoftheday", "simplestyle", "simpleoutfit", "styleover40", "instafashion", "instastyle", "imageconsultant", "personalstylist", "styleinspiration", "bossmom", "momof3", "consultoriadeimagem", "coachingdeimagem", "coachdeimagem", "stylist", "wiwt", "ootd", "outfitoftheday", "lookoftheday", "lookbook", "simplelook  ", "simplestyle", "simpleoutfit", "picoftheday", "instafashion", "instastyle ", "styleover40", "imageconsultant", "personalstylist", "fashionstylist", "fashionblogger", "bloguerdemoda ", "consultoriadeimagem", "coachingdeimagem", "bloguerportuguesa", "consultoradeimagem", "transformationalcoach", "jungiancoach", "stylediary", "lifecoach", "bossmom", "momof3"],
            5
        ],
        [
            (lambda x, y : (lambda z: random.sample(z, len(z)))(x+y)) (
                ["lookbook", "simplelook", "ootd", "outfitoftheday", "wiwt", "lookoftheday", "picoftheday", "simplestyle", "simpleoutfit", "styleover40", "instafashion", "instastyle", "imageconsultant", "personalstylist", "styleinspiration", "bossmom", "momof3", "consultoriadeimagem", "coachingdeimagem", "coachdeimagem", "stylist", "wiwt", "ootd", "outfitoftheday", "lookoftheday", "lookbook", "simplelook  ", "simplestyle", "simpleoutfit", "picoftheday", "instafashion", "instastyle ", "styleover40", "imageconsultant", "personalstylist", "fashionstylist", "fashionblogger", "bloguerdemoda ", "consultoriadeimagem", "coachingdeimagem", "bloguerportuguesa", "consultoradeimagem", "transformationalcoach", "jungiancoach", "stylediary", "lifecoach", "bossmom", "momof3"],
                ["lifecoach", "mindsetcoach", "jungiancoach", "transformationalcoach", "bemindful", "womenempoweringwomen", "womensupportingwomen", "behappy", "loveandlight", "spiritjunkie", "personaldevelopment", "liveinthemoment", "personalgrowth", "bepresent", "lifecoach ", "lifegoals", "selfdevelopment", "findyourself", "soulsearching", "choosehappiness", "freespirit", "attitudeofgratitude", "goodvibes", "raiseyourvibration", "embracelife", "propelwomen", "womenintheworld", "bebold", "empoweredwomen", "happyheart ", "liveyourdreams", "celebratelife"]
            ),
            5
        ]
    ]
}


def interface(stdscr, running_bots, finished_bots, threads):

    #Use colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
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

        strings = []
        for bot in running_bots:
            strings.append(("Liked by " + bot.get_username() + " in " + bot.get_site() + ": " + str(bot.get_likes_given()) + " / " + str(bot.get_max_likes())))
        for bot in finished_bots:
            strings.append(("Finished thread for " + bot.get_username() + " in " + bot.get_site() + ", did " + str(bot.get_likes_given()) + " / " + str(bot.get_max_likes()) + " likes"))

        start_y = int((height // 2) - 2)

        # Print
        for i, string in enumerate(strings):
            start_x = int((width // 2) - (len(string) // 2) - len(string) % 2)
            stdscr.addstr(start_y + (i*3), start_x, string[:width-1])

        # Refresh the screen 
        stdscr.refresh()

        time.sleep(0.5)




def bot_thread(bots, i, pvals, running_bots, finished_bots):
    logging.info("Thread %s: starting", i)
    for j in range(len(bots[i])):
        running_bots[i] = bots[i][j]
        bots[i][j].run(pvals[i][j%(len(pvals[i]))])
        finished_bots.append(bots[i][j])
        #set bigger waiting time in between bots ? like an hour
    logging.info("Thread %s: finishing", i)



def run_bots(bots):
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

    time.sleep(1)
    curses.wrapper(interface, running_bots, finished_bots, threads)

    for thread in threads:
        thread.join()



def get_bots():
    igbots = []
    for i in range(len(credentials['instagram'])): #instagram
        igbots.append(InstagramBot(credentials['instagram'][i]['username'], credentials['instagram'][i]['password']))
    igbots2 = []
    for i in range(len(credentials['instagram2'])): #mom's instagram
        igbots2.append(InstagramBot(credentials['instagram2'][i]['username'], credentials['instagram2'][i]['password']))




    bots = [
        [SubmitHubBot(credentials['submithub']['username'], credentials['submithub']['password'])],
        igbots,
        igbots2
    ]

    return bots



def main():
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

    bots = get_bots()

    logging.info("Main: Starting bot threads.")
    run_bots(bots)
    logging.info("Main: Finished all bot threads.")


if __name__ == "__main__":
    main()