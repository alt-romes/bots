
#Fill information, and rename file to "credentials.py"

credentials = {
    'submithub': {
        'username': 'yourusername',
        'password': 'yourpassword'
    },
    #The accounts here will run consecutively
    'instagram': [
        {
            'username': 'yourusername1',
            'password': 'yourpassword1'
        },
        {
            'username': 'yourusername2',
            'password': 'yourpassword2'
        }
    ],
    #Use for a second account you want to run in parallel with the above one
    'instagram2': [
        {
            'username': 'yourusername3',
            'password': 'yourpassword3'
        },
    ]
}

params = {
    #Each website has a list of lists of parameters, each list of parameters matches one account for that website.
    #A list of parameters is passed to the function bot.run(), and each element is a required argument for that said bot.
    #You can have just one list of parameters for more than one account.

    #SubmitHub: Number of songs to rate.
    'submithub': [
        [5] #Number of likes
    ],

    #Twitter: Hashtags and number of tweets to fav
    'twitter': [
        [
            ["hashtag1", "hashtag2"], #Hashtags
            0 #number of likes, 0 to prevent from running
        ]
    ], 

    #Instagram: Hashtags, Number of posts to like
    'instagram': [
        [
            ["hashtag1", "hashtag2"], #Hashtags
            15 #number of likes
        ]
    ],

    #Instagram 2: Same order
    'instagram2': [
        [
            ["hashtag1", "hashtag2"], #Hashtags
            100 #number of likes
        ],
        [
            ["hashtag1", "hashtag2"], #Hashtags
            0 #number of likes, 0 to prevent from running
        ]
    ]
}