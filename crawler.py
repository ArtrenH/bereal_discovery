from BeFake.BeFake import BeFake as BeFake_simple
from pymongo import MongoClient

from tqdm import tqdm
from utils import countdown, print_time
from settings import *


class BeFake(BeFake_simple):
    def load_database(self):
        client = MongoClient(MONGO_URL, document_class=dict, tz_aware=False, connect=True)
        db = client.bereal_discovery
        self.posts_db = db.posts
        self.users_db = db.users
        self.notifications_db = db.notifications

    def get_feed(self):
        res = self.client.get(
            f"{self.api_url}/feeds/discovery",
            headers={
                "authorization": self.token,
            },
        ).json()
        if "posts" not in res:
            return None
        return res["posts"]

    def get_feeds(self):
        print_time()
        print("crawling 100 posts...")
        for i in tqdm(range(101)):
            cur_posts = self.get_feed()
            if cur_posts is None:
                return None
            for post in cur_posts:
                self.insert_post_to_db(post)
    
    def update_database(self):
        self.load()
        self.load_database()
        print("updating database... (this may take a while)")
        all_posts = self.posts_db.find({})
        for post in tqdm(all_posts):
            self.insert_post_to_db(post)

    def insert_post_to_db(self, post):
        """ What databases to use:
            posts_db = db.posts
                -> raw data for every post
            users_db = db.users
                -> id of every user + list of post_IDs
            notifications_db = db.notifications
                -> id of every notification + list of post_IDs
        """
        # insert post
        post["_id"] = post["id"]
        self.posts_db.update_one({"_id": post["_id"]}, {"$set": post}, upsert=True)
        # insert post id to user
        user = post["user"]
        user_entry = {
            "_id": user["id"],
            "post": [post["id"]],
        }
        cur_user = self.users_db.find_one({"_id": user["id"]})
        if cur_user is not None:
            if post["id"] not in cur_user["post"]:
                user_entry["post"] = cur_user["post"] + [post["id"]]
        self.users_db.update_one({"_id": user["id"]}, {"$set": user_entry}, upsert=True)
        # insert post id to notification
        notification_entry = {
            "_id": post["notificationID"],
            "unix_time": post["takenAt"]["_seconds"]-post["lateInSeconds"],
            "post": [post["id"]]
        }
        cur_notification = self.notifications_db.find_one({"_id": post["notificationID"]})
        if cur_notification is not None:
            if post["id"] not in cur_notification["post"]:
                notification_entry["post"] = cur_notification["post"] + [post["id"]]
        self.notifications_db.update_one({"_id": post["notificationID"]}, {"$set": notification_entry}, upsert=True)
    
    def crawl_infinite(self):
        self.load()
        self.load_database()
        while True:
            try:
                cur_data = self.get_feeds()
                if cur_data is None:
                    print(f"max reached...")
            except KeyError as e:
                print("Server scheinen ueberlastet zu sein, warte 1 Minute...")
                countdown(60)
                continue
            countdown(300)



if __name__ == "__main__":
    befake = BeFake()
    #befake.update_database()
    befake.crawl_infinite()
