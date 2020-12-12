from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / 'README.md').read_text(encoding='utf-8')

with open(here / 'requirements.txt', 'r') as f:
    requirements = f.read().splitlines()


setup(
    name='reddit-data-scraper',  # Required
    version='0.0.0',
    description='Tools for scraping submissions and comments by subreddit',
    url='https://github.com/benbenboben/reddit-data-scraper',
    author_email='ellis.bh89@gmail.com',
    package_dir={'': 'reddit_data_scraper'},
    packages=find_packages(where='reddit_data_scraper'),
    python_requires='>=3.5, <4',
    install_requires=requirements
)
