
#Fill information, and rename file to "credentials.py"

credentials={
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