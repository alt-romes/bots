import sqlite3


class Database:

    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.create_database()

    def query(self, query, params):
        """
        Receives a query and it's params as arguments.
        Returns the list of rows from the table gotten by the query
        """

        cur = self.conn.cursor()
        cur.execute(query, params)
        self.conn.commit()
        return cur.fetchall()


    def add_post_approval(self, postApproval, hashtags):

        insert = ''' INSERT OR IGNORE INTO managerPostApproval(platform, username, post_op, post_url, operator, img_src, sent_request, approved, posted, time)
            VALUES(?, ?, ?, ?, ?, ?, 0, 0, 0, ?)
                '''
        cur = self.conn.cursor()
        cur.execute(insert, postApproval)
        self.conn.commit()


        insertHashtags = ''' INSERT OR IGNORE INTO managerPostApprovalHashtags(platform, username, post_url, hashtag)
            VALUES(?, ?, ?, ?)
                '''
        cur = self.conn.cursor()
        cur.executemany(insert, [(postApproval[0], postApproval[1], postApproval[3], h) for h in hashtags])
        self.conn.commit()  

    
    def invalidate_post_approval(self, postInv):
        """
        approved = 0 pending
        approved = 1 accepted
        approved = 2 timelimit for approval was exceeded
        """
        update = """ UPDATE managerPostApproval
                        SET approved = -1
                    WHERE platform=? AND username=? AND post_url=?
                """

        cur = self.conn.cursor()
        cur.execute(update, post)
        self.conn.commit() 

    def sent_permission_request(self, post):
        
        update = """ UPDATE managerPostApproval
                        SET sent_request = 1
                    WHERE platform=? AND username=? AND post_url=?
                """

        cur = self.conn.cursor()
        cur.execute(update, post)
        self.conn.commit()

    def approve_post_approval(self, postApproved):
        
        update = """ UPDATE managerPostApproval
                        SET approved = 1
                    WHERE platform=? AND username=? AND post_url=?
                """

        cur = self.conn.cursor()
        cur.execute(update, postApproved)
        self.conn.commit()

    def posted_approved_post(self, postApproved):
        
        update = """ UPDATE managerPostApproval
                        SET posted = 1
                    WHERE platform=? AND username=? AND post_url=?
                """

        cur = self.conn.cursor()
        cur.execute(update, postApproved)
        self.conn.commit()

    def add_instagram_followers(self, accfollowers):

        insert = ''' INSERT OR REPLACE INTO accFollowers(platform, username, follower, time_detected)
                VALUES(?, ?, ?, ?)
                    '''

        cur = self.conn.cursor()
        cur.executemany(insert, accfollowers)
        self.conn.commit()   

    def add_account_hashtags(self, acchashtags):

        insert = ''' INSERT OR IGNORE INTO accHashtags(username, platform, hashtag)
                VALUES(?, ?, ?)
                    '''

        cur = self.conn.cursor()
        cur.executemany(insert, acchashtags)
        self.conn.commit()    


    def add_post_hashtags(self, posthashtags):

        insert = ''' INSERT OR IGNORE INTO likedPostsHashtags(post_id, hashtag)
                VALUES(?, ?)
                    '''

        cur = self.conn.cursor()
        cur.executemany(insert, posthashtags)
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

    def create_instagram_likejob(self, likejob_ig):

        insert = ''' INSERT INTO likeJobsInstagram(platform, username, time_start, hashtag_stories_seen, home_stories_seen)
                VALUES(?, ?, ?, ?, ?)
                    '''

        cur = self.conn.cursor()
        cur.execute(insert, likejob_ig)
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
                                                PRIMARY KEY (username, platform, follower, time_detected)
                                            ); """

            likejobsinstagram_table = """ CREATE TABLE IF NOT EXISTS likeJobsInstagram (
                                                platform text NOT NULL,
                                                username text NOT NULL,
                                                time_start timestamp,
                                                hashtag_stories_seen integer NOT NULL,
                                                home_stories_seen integer NOT NULL,
                                                FOREIGN KEY (username, platform, time_start) REFERENCES likeJob (username, platform, time_start),
                                                PRIMARY KEY (username, platform, time_start)
                                            ); """


            managerpostapproval_table = """ CREATE TABLE IF NOT EXISTS managerPostApproval (
                                                platform text NOT NULL,
                                                username text NOT NULL,
                                                post_op text NOT NULL,
                                                post_url text NOT NULL,
                                                operator text NOT NULL,
                                                img_src text NOT NULL,
                                                sent_request integer NOT NULL,
                                                approved integer NOT NULL,
                                                posted integer NOT NULL,
                                                time timestamp NOT NULL,
                                                FOREIGN KEY (username, platform) REFERENCES accounts (username, platform),
                                                PRIMARY KEY (username, platform, post_url)
                                            ); """
                                            
            managerpostapprovalhashtags_table = """ CREATE TABLE IF NOT EXISTS managerPostApprovalHashtags (
                                                        platform text NOT NULL,
                                                        username text NOT NULL,
                                                        post_url text NOT NULL,
                                                        hashtag text NOT NULL,
                                                        FOREIGN KEY (username, platform, post_url) REFERENCES managerPostApproval (username, platform, post_url),
                                                        PRIMARY KEY (username, platform, post_url, hashtag)
                                                    ); """

            self.create_table(accounts_table)
            self.create_table(likejobs_table)
            self.create_table(acchashtags_table)
            self.create_table(likedposts_table)
            self.create_table(likedpostshashtags_table)
            self.create_table(accfollowers_table)
            self.create_table(likejobsinstagram_table)
            self.create_table(managerpostapproval_table)
            self.create_table(managerpostapprovalhashtags_table)
        
        else:
            print("Error connecting to database!")

    def close(self):
        if self.conn is not None:
            self.conn.close()