import logging
import time
import os

import click
from peewee import *
import pandas as pd

from reddit_data.scrape import Scraper
from reddit_data.db import Submissions
from reddit_data.queue import RedisQueue


logging.basicConfig(filename='/data/reddit-data.log', level=logging.INFO)


@click.command()
@click.option('--subreddit', help='Exact name of subreddit to scrape.')
@click.option('--start',  help='Earliest date to begin scraping', type=str)
@click.option('--stop', help='Latest date to end sraping', default=None, type=str)
@click.option('--daily', is_flag=True)
def main(subreddit, start, stop, daily):
    if stop is not None:
        daily = False

    queue = RedisQueue(
        'reddit-data',
        host=os.environ.get('REDIS_HOST'),
        port=os.environ.get('REDIS_PORT', 6379),
        password=os.environ.get('REDIS_PASSWORD')
    )

    while True:
        scraper = Scraper()

        warm_start = Submissions.select(fn.MAX(Submissions.created_utc)).scalar()
        if warm_start is not None:
            start = warm_start
        else:
            start = pd.to_datetime(start)

        if stop is None:
            stop = pd.to_datetime('now') - pd.Timedelta('7D')

        logging.info(start)

        myrange = list(pd.date_range(start=pd.to_datetime(start), end=stop, freq='10min'))

        for i in myrange:
            logging.info(i)
            idlist = scraper.get_ids(i, subreddit)
            logging.info(f'Enqueueing {len(idlist)} posts.')
            for sid in idlist:
                logging.info(f'Enqueueing {sid}')
                queue.put(sid)

        if daily:
            time.sleep(60 * 60 * 24)
        else:
            break


if __name__ == '__main__':
    main()
