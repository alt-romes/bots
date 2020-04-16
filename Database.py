import sqlite3


class Database:

    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.create_database()

    def add_instagram_follower(self, accfollower):

        insert = ''' INSERT OR IGNORE INTO accFollowers(platform, username, follower, time_detected)
                VALUES(?, ?, ?, ?)
                    '''

        cur = self.conn.cursor()
        cur.execute(insert, accfollower)
        self.conn.commit()    

    def add_account_hashtag(self, acchashtag):

        insert = ''' INSERT OR IGNORE INTO accHashtags(username, platform, hashtag, followers_revenue)
                VALUES(?, ?, ?, ?)
                    '''

        cur = self.conn.cursor()
        cur.execute(insert, acchashtag)
        self.conn.commit()    


    def add_post_hashtag(self, posthashtag):

        insert = ''' INSERT OR IGNORE INTO likedPostsHashtags(post_id, hashtag)
                VALUES(?, ?)
                    '''

        cur = self.conn.cursor()
        cur.execute(insert, posthashtag)
        self.conn.commit()


    def create_liked_post(self, liked_post):

        insert = ''' INSERT INTO likedPosts(username, platform, op, time, found_in)
                VALUES(?, ?, ?, ?, ?)
                    '''

        cur = self.conn.cursor()
        cur.execute(insert, liked_post)
        self.conn.commit()
        return cur.lastrowid


    def create_likejob(self, likejob):

        insert = ''' INSERT INTO likeJobs(username, platform, likes_given, max_likes, status, time_start, time_end, posts_seen)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                    '''

        cur = self.conn.cursor()
        cur.execute(insert, likejob)
        self.conn.commit()

        
    def create_account(self, account):

        insert = ''' INSERT OR IGNORE INTO accounts(username, platform)
                VALUES(?, ?)
                    '''

        cur = self.conn.cursor()
        cur.execute(insert, account)
        self.conn.commit()


    def create_table(self, create_table_sql):
        """ create a table from the create_table_sql statement
        :param conn: Connection object
        :param create_table_sql: a CREATE TABLE statement
        :return:
        """
        c = self.conn.cursor()
        c.execute(create_table_sql)
        self.conn.commit()


    def create_database(self):

        if self.conn is not None:

            accounts_table = """ CREATE TABLE IF NOT EXISTS accounts (
                                                username text NOT NULL,
                                                platform text NOT NULL,
                                                PRIMARY KEY(username, platform)
                                            ); """

            likejobs_table = """ CREATE TABLE IF NOT EXISTS likeJobs (
                                                username text NOT NULL,
                                                platform text NOT NULL,
                                                likes_given integer,
                                                max_likes integer,
                                                status text NOT NULL,
                                                time_start timestamp,
                                                time_end timestamp,
                                                posts_seen integer,
                                                PRIMARY KEY (username, platform, time_start),
                                                FOREIGN KEY (username, platform) REFERENCES accounts (username, platform)
                                            ); """ 

            acchashtags_table = """ CREATE TABLE IF NOT EXISTS accHashtags (
                                                username text NOT NULL,
                                                platform text NOT NULL,
                                                hashtag text NOT NULL,
                                                followers_revenue integer,
                                                PRIMARY KEY (username, platform, hashtag),
                                                FOREIGN KEY (username, platform) REFERENCES accounts (username, platform)
                                            ); """

            likedposts_table = """ CREATE TABLE IF NOT EXISTS likedPosts (
                                                post_id integer,
                                                username text NOT NULL,
                                                platform text NOT NULL,
                                                op text NOT NULL,
                                                time timestamp,
                                                found_in text NOT NULL,
                                                PRIMARY KEY (post_id),
                                                FOREIGN KEY (username, platform) REFERENCES accounts (username, platform)
                                            ); """

            likedpostshashtags_table = """ CREATE TABLE IF NOT EXISTS likedPostsHashtags (
                                                post_id integer,
                                                hashtag text NOT NULL,
                                                FOREIGN KEY (post_id) REFERENCES likedPosts (post_id),
                                                PRIMARY KEY (post_id, hashtag)
                                            ); """

            accfollowers_table = """ CREATE TABLE IF NOT EXISTS accFollowers (
                                                platform text NOT NULL,
                                                username text NOT NULL,
                                                follower text NOT NULL,
                                                time_detected timestamp,
                                                FOREIGN KEY (username, platform) REFERENCES accounts (username, platform),
                                                PRIMARY KEY (username, platform, follower)
                                            ); """

            self.create_table(accounts_table)
            self.create_table(likejobs_table)
            self.create_table(acchashtags_table)
            self.create_table(likedposts_table)
            self.create_table(likedpostshashtags_table)
            self.create_table(accfollowers_table)
        
        else:
            print("Error connecting to database!")

    def close(self):
        if self.conn is not None:
            self.conn.close()