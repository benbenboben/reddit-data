import multiprocessing as mp
import time
import logging

import click
from peewee import *
import pandas as pd

from reddit_data.scrape import SubmissionScraper, CommentScraper
from reddit_data.db import Submissions, get_db


logging.basicConfig(filename='/data/reddit-data.log', level=logging.INFO)


def comment_scraper(sid):
    cs = CommentScraper()
    cs.get_comments(sid)


@click.command()
@click.option('--subreddit', help='Exact name of subreddit to scrape.')
@click.option('--start',  help='Earliest date to begin scraping')
@click.option('--stop', help='Latest date to end sraping', default=None)
@click.option('--daily', is_flag=True)
@click.option('--ncpu', help='Number of cpus', default=None)
def main(subreddit, start, stop, daily, ncpu):
    scraper = SubmissionScraper(subreddit)
    warm_start = Submissions.select(fn.MAX(Submissions.created_utc)).scalar()
    if warm_start is not None:
        start = warm_start
    else:
        start = int(pd.to_datetime(start).timestamp())

    while True:
        logging.info(f'Scraping {subreddit} starting from {start}')

        start_new = scraper.get_submissions(start=start)

        new_data = Submissions.select(
            Submissions.id
        ).where(
            Submissions.created_utc >= start
        )

        dicts = list(new_data.dicts())

        print(dicts)

        if len(dicts):
            new_data = pd.DataFrame(dicts)

            with mp.Pool(processes=ncpu if ncpu else mp.cpu_count()) as pool:
                pool.map(comment_scraper, new_data['id'].values.ravel())

        start = start_new

        if not daily or start >= int(pd.to_datetime(stop).timestamp()):
            break

        if start >= int((pd.to_datetime('now') - pd.Timedelta('7 days')).timestamp()):
            logging.info('Sleeping for one day')
            time.sleep(60 * 60 * 24)


if __name__ == '__main__':
    main()
