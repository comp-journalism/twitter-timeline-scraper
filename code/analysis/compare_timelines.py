'''
compare_timelines.py
Input: an algorithmic timeline and a chronological timeline (intended)
Output: tweets with metadata about rankings and ranking changes
'''
import jack_twitter_config as config
import pandas as pd
import tweepy
import math

# tweepy api
consumer_key = config.consumer_key
consumer_secret = config.consumer_secret
access_key = config.access_key
access_secret = config.access_secret
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth)


alg_path = '../../data/jackbandy/jackbandy-algorithmic-2020-03-17-at-1722.csv'
chr_path = '../../data/jackbandy/jackbandy-chronological-2020-03-17-at-1722.csv'
out_path = '../../data/jackbandy/jackbandy-tweets-2020-03-17-at-1722.csv'


def main():
    alg_timeline = pd.read_csv(alg_path)
    alg_timeline['alg_rank_n'] = alg_timeline.index
    alg_timeline['alg_rank_pct'] = alg_timeline.alg_rank_n.rank(pct=True)
    chr_timeline = pd.read_csv(chr_path)
    chr_timeline['chr_rank_n'] = chr_timeline.index
    chr_timeline['chr_rank_pct'] = chr_timeline.chr_rank_n.rank(pct=True)
    tweets = alg_timeline.merge(chr_timeline,indicator='merged',
                                on='tweet_link',how='outer',suffixes=('_alg','_chr'))

    # ex. if rank was 0 in algorithm (top tweet) and 5 in chronological (5th tweet), boost=5
    tweets['alg_boost_n'] = tweets['chr_rank_n'] - tweets['alg_rank_n']
    tweets['alg_boost_pct'] = tweets['chr_rank_pct'] - tweets['alg_rank_pct']

    # which tweets were exclusive to one or the other
    tweets['alg_only'] = tweets.chr_rank_n.isnull() # no rank in chronological
    tweets['chr_only'] = tweets.alg_rank_n.isnull() # no rank in algorithmic
    tweets['id_str'] = tweets.tweet_link.str[-19:]

    tweet_info = populate_tweets(tweets.id_str.tolist())
    tweet_info = tweet_info.merge(tweets,on='id_str')
    tweet_info.to_csv(out_path,index=False)



def populate_tweets(tweet_ids):
    n_pages = math.ceil(len(tweet_ids)/100)
    tweet_dicts = []
    for i in range(n_pages):
        end_loc = min((i + 1) * 100, len(tweet_ids))
        print("Getting page {}, end_loc={}...".format(i,end_loc))
        tweets = api.statuses_lookup(tweet_ids[i*100:end_loc],include_entities=True,trim_user=True)
        for t in tweets:
            t_dict = {}
            t_json = t._json
            t_dict['text'] = t_json['text']
            t_dict['id'] = t_json['id']
            t_dict['id_str'] = t_json['id_str']
            if t_json['entities'].get('media') != None:
                if len(t_json['entities']['media']) > 1:
                    print("Multiple media on tweetid {}".format(t_json['id']))
                media_json = t_json['entities']['media'][0]
                t_dict['media_url_https'] = media_json['media_url_https']
                t_dict['media_expanded_url'] = media_json['expanded_url']
                t_dict['media_url'] = media_json['media_url']
                t_dict['media_type'] = media_json['type']
            if t_json['entities'].get('urls') != None:
                if len(t_json['entities']['urls']) == 1:
                    url_json = t_json['entities']['urls'][0]
                    t_dict['expanded_url'] = url_json['expanded_url']
                    print("1 url on tweetid {}".format(t_json['id']))
                elif len(t_json['entities']['urls']) > 1:
                    print("{} urls on tweetid {}".format(len(t_json['entities']['urls']),t_json['id']))
            tweet_dicts.append(t_dict)
    return pd.DataFrame(tweet_dicts)
    
    



if __name__=="__main__":
    main()
