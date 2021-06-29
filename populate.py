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
        logging.info(f'WARM START: {warm_start}')
        if warm_start is not None:
            start = warm_start * 1000
            start = pd.to_datetime(start, unit='ms')
        else:
            logging.info('warm start set to start')
            start = pd.to_datetime(start)

        if stop is None:
            stop = pd.to_datetime('now') - pd.Timedelta('7D')

        logging.info(f'START: {start}')
        logging.info(f'STOP: {stop}')


        myrange = list(pd.date_range(start=pd.to_datetime(start), end=stop, freq='10min'))

        for idx in range(len(myrange) - 1):
            idlist = scraper.get_ids(myrange[idx], myrange[idx + 1], subreddit)
            for sid in idlist:
                queue.put(sid)

        if daily:
            time.sleep(60 * 60 * 24)
        else:
            break


if __name__ == '__main__':
    main()
