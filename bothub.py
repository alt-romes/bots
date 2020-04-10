#Dependencies
import random
import threading
import logging

#Bots
from SubmitHubBot import SubmitHubBot
from InstagramBot import InstagramBot

#Credentials
from credentials import credentials

def bot_thread(bots, i, pvals):
    logging.info("Thread %s: starting", i)
    for j in range(len(bots[i])):
        bots[i][j].run(pvals[i][j%(len(pvals[i]))])
    logging.info("Thread %s: finishing", i)



def run_bots(bots):
    pvals = list(params.values())
    threads=list()
    for i in range(len(bots)):
        #separate in threads
        x = threading.Thread(target=bot_thread, args=(bots, i, pvals), daemon=True)
        threads.append(x)
        x.start()
    
    for thread in threads:
        thread.join()




params = {
    #Each website has a list of lists of parameters, each list of parameters matches one account for that website.
    #A list of parameters is passed to the function bot.run(), and each element is a required argument for that said bot.
    #You can have just one list of parameters for more than one account.

    #SubmitHub: Number of songs to rate.
    'submithub': [
        [50]
    ],

    #Instagram: Hashtags, Number of posts to like
    'instagram': [
        [
            ['shoegaze', 'dreampop', 'experimental', 'soundscapes', "album", 'indie', "homestudio", "recording", "record", "altrock", 'music', 'artist', 'art', 'alternative', 'musician', "drawing", "instamusic", 'spotify'],
            250
        ]
    ],

    #Instagram da Mae: Mesma ordem
    'maeig': [
        [
            ["lookbook", "simplelook", "ootd", "outfitoftheday", "wiwt", "lookoftheday", "picoftheday", "simplestyle", "simpleoutfit", "styleover40", "instafashion", "instastyle", "imageconsultant", "personalstylist", "styleinspiration", "bossmom", "momof3", "consultoriadeimagem", "coachingdeimagem", "coachdeimagem", "stylist", "wiwt", "ootd", "outfitoftheday", "lookoftheday", "lookbook", "simplelook  ", "simplestyle", "simpleoutfit", "picoftheday", "instafashion", "instastyle ", "styleover40", "imageconsultant", "personalstylist", "fashionstylist", "fashionblogger", "bloguerdemoda ", "consultoriadeimagem", "coachingdeimagem", "bloguerportuguesa", "consultoradeimagem", "transformationalcoach", "jungiancoach", "stylediary", "lifecoach", "bossmom", "momof3"],
            200
        ],
        [
            (lambda x, y : (lambda z: random.sample(z, len(z)))(x+y)) (
                ["lookbook", "simplelook", "ootd", "outfitoftheday", "wiwt", "lookoftheday", "picoftheday", "simplestyle", "simpleoutfit", "styleover40", "instafashion", "instastyle", "imageconsultant", "personalstylist", "styleinspiration", "bossmom", "momof3", "consultoriadeimagem", "coachingdeimagem", "coachdeimagem", "stylist", "wiwt", "ootd", "outfitoftheday", "lookoftheday", "lookbook", "simplelook  ", "simplestyle", "simpleoutfit", "picoftheday", "instafashion", "instastyle ", "styleover40", "imageconsultant", "personalstylist", "fashionstylist", "fashionblogger", "bloguerdemoda ", "consultoriadeimagem", "coachingdeimagem", "bloguerportuguesa", "consultoradeimagem", "transformationalcoach", "jungiancoach", "stylediary", "lifecoach", "bossmom", "momof3"],
                ["lifecoach", "mindsetcoach", "jungiancoach", "transformationalcoach", "bemindful", "womenempoweringwomen", "womensupportingwomen", "behappy", "loveandlight", "spiritjunkie", "personaldevelopment", "liveinthemoment", "personalgrowth", "bepresent", "lifecoach ", "lifegoals", "selfdevelopment", "findyourself", "soulsearching", "choosehappiness", "freespirit", "attitudeofgratitude", "goodvibes", "raiseyourvibration", "embracelife", "propelwomen", "womenintheworld", "bebold", "empoweredwomen", "happyheart ", "liveyourdreams", "celebratelife"]
            ),
            500
        ]
    ]
}


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

format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

logging.info("Main: Starting bot threads.")
print()
print("for romes' liked posts:                   r")
print("for mother's liked posts:                 l")
print("for upvoted songs:                        !")
print("for full iteration of hashtag:            o")
print("for forced hashtag change due to error:   x")
print()
run_bots(bots)
logging.info("Main: Finished all bot threads.")