import pandas as pd
import praw
import json
import requests
import time
import os
import logging

from reddit_data.db import Submissions, Comments, Errors, db

logging.basicConfig(filename='/data/reddit-data.log', level=logging.INFO)

class SubmissionScraper:
    """
    Tool for scraping submissions and inserting them into a database.
    """

    def __init__(self, subreddit):
        self.subreddit = subreddit

    def get_submissions(self, start=None, cutoff=None):
        """Get list of submissions between give times.

        :param start: earliest timestamp
        :param cutoff: most recent timestamp (if None, will be 'now')
        :return: None
        """
        if cutoff is None:
            # by default, give posts a week to accumulate votes/comments/etc
            cutoff = pd.to_datetime('now') - pd.Timedelta('7 days')

        # start = int(pd.to_datetime(start).timestamp())
        stop = int(start + pd.Timedelta('1D').total_seconds())
        while True:
            logging.info(f'Getting submissions {start} -- {stop}')

            url = self.url_factory(start=start, stop=stop)
            data = {}
            status_code = -1
            text = 'request unsuccessful'
            r = False
            try:
                r = requests.get(url)
                if r.json() == {}:
                    continue
                data = pd.DataFrame(r.json()['data'])
                data_dict = data[
                    ['id', 'author', 'created_utc', 'num_comments', 'over_18',
                     'permalink', 'score', 'subreddit', 'title', 'selftext']
                ].to_dict(orient='records')
                Submissions.insert_many(data_dict).on_conflict(action='IGNORE').execute()
            except Exception as e:
                logging.info('Error in submission scraping.  See errors table.')
                if r:
                    status_code = r.status_code
                    text = r.text
                Errors.insert(
                    typ='submission',
                    params=str(start),
                    info=json.dumps({
                        'status_code': status_code,
                        'text': text,
                        'exception': str(e)
                    })
                ).execute()

            try:
                start = int(data['created_utc'].max())
            except KeyError:
                start += int(pd.Timedelta('1D').total_seconds())

            stop = int(start + pd.Timedelta('1D').total_seconds())

            if start >= pd.to_datetime(cutoff).timestamp():
                return

            time.sleep(1)
        logging.info('Submission scrape completed')

    def url_factory(self, start=None, stop=None, blocksize=100):
        """Create URL based on subreddit and start/stop times.

        :param start: earlier time
        :param stop: later time
        :param blocksize: number of records to get at a time
        :return: URL string
        """
        preamble = f'https://api.pushshift.io/reddit/search/submission/?subreddit='
        if start is None and stop is not None:
            return preamble + f'{self.subreddit}&sort=asc&sort_type=created_utc&before={stop}&size={blocksize}'
        elif start is not None and stop is None:
            return preamble + f'{self.subreddit}&sort=asc&sort_type=created_utc&after={start}&size={blocksize}'
        elif start is None and stop is None:
            return preamble + f'{self.subreddit}&sort=asc&sort_type=created_utc&size={blocksize}'
        else:
            return preamble + \
                   f'{self.subreddit}&sort=asc&sort_type=created_utc&after={start}&before={stop}&size={blocksize}'


class CommentScraper:
    """
    Object for scraping comments on specific reddit threads.
    """

    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.environ.get('REDDIT_CLIENT_ID'),
            client_secret=os.environ.get('REDDIT_CLIENT_SECRET'),
            user_agent=os.environ.get('REDDIT_USER_AGENT')
        )

    def get_comments(self, sid):
        """Get all comments for a specific reddit submission and insert into databse.

        :param sid: unique id for a reddit submission
        :return: None
        """
        # if isinstance(sid, str):
        #     submissionid = [sid]

        # if not isinstance(submissionid, Iterable):
        #     raise ValueError('Provide submission id as string or list of strings')
        logging.info(f'Scraping comments {sid}')
        try:
            data = []
            sub = self.reddit.submission(id=sid)
            sub.comments.replace_more(limit=None)
            comment_queue = sub.comments[:]
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

            Comments.insert_many(data).on_conflict(action='IGNORE').execute()

            # don't overwhelm source
            time.sleep(1)
        except Exception as e:
            logging.info('Error in comments scraping.  See errors table.')
            Errors.insert(
                typ='comments',
                params=sid,
                info=str(e)
            )
        logging.info(f'Scraping comments completed {sid}')
