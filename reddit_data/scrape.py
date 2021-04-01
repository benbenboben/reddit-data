import pandas as pd
import praw
import requests
import time
import os
import logging
from reddit_data.db import insert_submissions, insert_comments, insert_error

logging.basicConfig(filename='/data/reddit-data.log', level=logging.INFO)


def scrape_id(sid):
    scraper = Scraper()
    scraper.scrape(sid)


class Scraper:
    """
    Tool for scraping submissions and inserting them into a database.
    """
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.environ.get('REDDIT_CLIENT_ID'),
            client_secret=os.environ.get('REDDIT_CLIENT_SECRET'),
            user_agent=os.environ.get('REDDIT_USER_AGENT')
        )

    def scrape(self, sid):
        logging.info(f'Begin scraping {sid}')
        sub = self.reddit.submission(id=sid)
        # PRAW lazy-loads objects. it seems like trying to access through the sub.__dict__
        # doesn't trigger the load (from what i can tell) so we coerce it
        _ = sub.selftext
        subcols = [
            'id', 'author', 'created_utc', 'num_comments', 'over_18',
             'permalink', 'score', 'subreddit', 'title', 'selftext'
        ]
        submission_data = {k: sub.__dict__.get(k, None) for k in subcols}
        submission_data = pd.DataFrame([submission_data])
        if submission_data['created_utc'].isna().any():
            logging.info('Missing required data -- ending early.')
            return
        try:
            insert_submissions(submission_data.fillna(0).to_dict(orient='records'))
        except Exception as e:
            logging.info('Error in submission scraping.  See errors table.')
            insert_error(dict(typ='submission', params=str(sid), info=str(e)))

        sub.comments.replace_more(limit=int(1e6))
        comment_queue = sub.comments[:]
        data = []
        while comment_queue:
            comment = comment_queue.pop(0)
            data.append({
                'submission_id': sid,
                'author': comment.author,
                'body': comment.body,
                'id': comment.id,
                'score': comment.score,
                'parent_id': comment.parent_id
            })
            comment_queue.extend(comment.replies)
        try:
            insert_comments(data)
        except Exception as e:
            logging.info('Error in comments scraping.  See errors table.')
            insert_error(dict(typ='comments', params=sid, info=str(e)))
        logging.info(f'Finished scraping {sid}')
        time.sleep(1)


    def get_ids(self, start, subreddit, minutes=10):
        logging.info(start)
        start = int(pd.to_datetime(start).timestamp())
        logging.info(start)
        stop = int(start + (minutes * 60))
        url = self.url_factory(start=start, stop=stop, subreddit=subreddit)
        r = requests.get(url)
        if not r:
            return []
        if r.json() and len(r.json()):
            data = pd.DataFrame(r.json()['data'])
            logging.info(f'{start} got {len(data)}')
            if 'id' in data and len(data):
                return list(data['id'])
            else:
                return []
        else:
            return []

    def url_factory(self, start=None, stop=None, subreddit=None, blocksize=100):
        """Create URL based on subreddit and start/stop times.

        :param start: earlier time
        :param stop: later time
        # :param blocksize: number of records to get at a time
        :return: URL string
        """
        preamble = f'https://api.pushshift.io/reddit/search/submission/?subreddit='
        if start is None and stop is not None:
            return preamble + f'{subreddit}&sort=asc&sort_type=created_utc&before={stop}&size={blocksize}'
        elif start is not None and stop is None:
            return preamble + f'{subreddit}&sort=asc&sort_type=created_utc&after={start}&size={blocksize}'
        elif start is None and stop is None:
            return preamble + f'{subreddit}&sort=asc&sort_type=created_utc&size={blocksize}'
        else:
            return preamble + \
                   f'{subreddit}&sort=asc&sort_type=created_utc&after={start}&before={stop}&size={blocksize}'
