'''
scrape_all_tweets_twint.py
Run this once per day
Benefit of twint is the "Since" key
'''

import pandas as pd
import time
import sys
import twint
from progressbar import progressbar
from random import randint


# read in users
friends = pd.read_csv('../data/all_friends.csv')
friends = friends.sample(frac=0.25)
#friends.sort_values(by='statuses_count',ascending=False,inplace=True)


# get tweets for each user
for row in progressbar(friends.itertuples(), max_value=len(friends)):
    # read in existing db if it exists
    path_to_tweets = '../data/tweets/{}_tweets.csv'.format(row.screen_name)
    try:
        tweet_db=pd.read_csv(path_to_tweets)
        most_recent = tweet_db.date.max()
    except:
        print("No existing tweets for {}".format(row.screen_name))
        tweet_db=pd.DataFrame()
        most_recent = '2020-03-31 23:59:59'

    # set up twint search
    c=twint.Config()
    c.Limit=2000
    c.Username=row.screen_name
    c.Pandas=True
    c.Pandas_clean=True
    c.Hide_output = True
    c.Since=most_recent

    # run search
    twint.run.Search(c)
    new_tweets_df = twint.storage.panda.Tweets_df
    if len(new_tweets_df) >= 2000:
        print("MISSED TWEETS for {}".format(row.screen_name))

    # append new tweets and remove any duplicates
    tweet_db=tweet_db.append(new_tweets_df)
    new_tweets_df.drop_duplicates(inplace=True,subset='id',keep='last')

    # save
    tweet_db.to_csv(path_to_tweets,index=False)

    # be nice to Twitter
    time.sleep(randint(3,8))
