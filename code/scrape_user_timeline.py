'''
scrape_user_timeline.py
'''

import selenium.webdriver.chrome.service as service
import pandas as pd
import subprocess
import time
import pdb
import sys
import os
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime

# download chromedriver from https://chromedriver.chromium.org/downloads
path_to_chromedriver = '/Users/jbx9603/Applications/chromedriver'
WAIT_TIME = 4
SCROLL_TIME= 0.5
N_AT_TIME = 4


path_to_save = '../data/'

twitter_url = 'https://twitter.com/home'

sys.path.append('../credentials')
from users import users_list



def main():
    for u in users_list:
        print("collecting for {}".format(u['username']))
        try:
            my_service = service.Service(path_to_chromedriver)
            my_service.start()
            driver = webdriver.Remote(my_service.service_url)
            driver.get(twitter_url)
            time.sleep(WAIT_TIME)
            log_in_user(driver,user=u)
            log_in_and_collect_timelines(driver,user=u)
        except Exception as e:
            print("Error! {}".format(str(e)))
            pdb.set_trace()


def log_in_user(driver, user):
    # set up saving path
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d-at-%H%M')
    path_to_save = '../data/{}'.format(user['username'])
    if not os.path.exists(path_to_save):
        os.makedirs(path_to_save)
    # log in
    driver.implicitly_wait(0.01)
    username_input = driver.find_element_by_xpath("//input[@type='text']")
    password_input = driver.find_element_by_xpath("//input[@type='password']")
    username_input.send_keys(user['username'])
    password_input.send_keys(user['password'])
    login_button = driver.find_element_by_xpath("//span[(text()='Log in')]")
    login_button.click()
    time.sleep(WAIT_TIME)



def log_in_and_collect_timelines(driver,user,n_tweets=100):

    # collect algorithmic timeline
    algorithmic_timeline = scrape_timeline(driver,n_tweets=n_tweets)
    alg_timeline_df = pd.DataFrame(algorithmic_timeline)
    file_path = '{}/{}-algorithmic-{}.csv'.format(path_to_save,user['username'],now_str) 
    alg_timeline_df.to_csv(file_path,index=False)

    # switch to chronological
    switch_to_chronological(driver)
    time.sleep(WAIT_TIME)

    # collect chronological timeline
    chronological_timeline = scrape_timeline(driver,n_tweets=n_tweets)
    chron_timeline_df = pd.DataFrame(chronological_timeline)
    file_path = '{}/{}-chronological-{}.csv'.format(path_to_save,user['username'],now_str) 
    chron_timeline_df.to_csv(file_path,index=False)



def switch_to_chronological(driver):
    button = driver.find_element_by_xpath("//div[@aria-label='Top Tweets on']/div")
    button.click()
    time.sleep(0.5)
    latest_button = driver.find_element_by_xpath("//span[(text()='See latest Tweets instead')]")
    latest_button.click()

    print("Switched to chronological timeline!")



def scrape_timeline(driver,n_tweets=50):
    return scrape_timeline_as_articles(driver,n_tweets=n_tweets)



def scrape_timeline_as_hrefs(driver,n_tweets=50):
    # initialize the return object
    tweet_links = []
    blacklist=['/photo','/media_tags']

    while len(tweet_links) < n_tweets:
        # collect tweet elements
        els =driver.find_elements_by_xpath('//a[contains(@href,"/status/")]')

        # add the ones not already collected
        for el in els:
            href = el.get_attribute('href')
            if href in tweet_links or any([w in href for w in blacklist]):
                continue
            tweet_links.append(href)

        # move down the page
        ActionChains(driver).move_to_element(els[-1]).perform()
        # let things load
        time.sleep(SCROLL_TIME)
    
    # scroll back to top of page
    driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)

    return tweet_links



def scrape_timeline_as_articles(driver,n_tweets=50):
    # initialize the return object
    tweets = []
    tweet_links = []

    # 1 collect ALL articles/tweets currently in view
    articles=driver.find_elements_by_xpath('//article')
    articles=driver.find_elements_by_tag_name('article')
    for a in articles:
        if not a.find_elements_by_xpath('.//a[contains(@href,"/status/")]'):
            # no tweet link means no tweet
            continue
        to_add = tweet_article_to_dict(a)
        # add if not already collected
        if to_add['tweet_link'] in tweet_links:
            continue
        tweet_links.append(to_add['tweet_link'])
        tweets.append(to_add)
        print("\tadded!")


    # 2 move down the page
    print("\tscrolling...")
    # move down the page to last article examined
    articles=driver.find_elements_by_xpath('//article')
    ActionChains(driver).move_to_element(articles[-1]).perform()
    # let things load
    time.sleep(SCROLL_TIME)


    # 3 collect N_AT_TIME articles
    while len(tweets) < n_tweets:
        # collect article elements
        articles=driver.find_elements_by_xpath('//article')

        n_added = 0
        for a in articles:
            if n_added > N_AT_TIME:
                continue 
            if not a.find_elements_by_xpath('.//a[contains(@href,"/status/")]'):
                # no tweet link means no tweet
                continue
            to_add = tweet_article_to_dict(a)
            # add if not already collected
            if to_add['tweet_link'] in tweet_links:
                continue
            tweet_links.append(to_add['tweet_link'])
            tweets.append(to_add)
            n_added += 1
            print("\tadded!")

        print("\tscrolling...")
        # move down the page to last article examined
        articles=driver.find_elements_by_xpath('//article')
        ActionChains(driver).move_to_element(articles[-1]).perform()
        # let things load
        time.sleep(SCROLL_TIME)
   

    # scroll back to top of page when done
    driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)

    return tweets




def tweet_article_to_dict(a):
    to_add = {}
    to_add['tweet_link']=a.find_element_by_xpath('.//a[contains(@href,"/status/")]').get_attribute('href')
    print(to_add['tweet_link'])
    to_add['metadata'] = a.find_elements_by_xpath(".//div[@role='group']")[-1].get_attribute('aria-label')
    print("\t{}".format(to_add['metadata']))
    if a.find_elements_by_xpath('.//a[contains(@href,"/i/user")]'):
        to_add['info_text']=a.find_element_by_xpath('.//a[contains(@href,"/i/user")]').text
        to_add['info_link']=a.find_element_by_xpath('.//a[contains(@href,"/i/user")]').get_attribute('href')
    if a.find_elements_by_xpath(".//span[(text()='Promoted')]"):
        to_add['promoted'] = 'promoted'
        print('\tpromoted!')
    return to_add





def get_tweet_link(driver):
    # old method based on copy and paste button lol
    # but good for demos!
    time.sleep(0.5)
    copy_button=driver.find_element_by_xpath("//span[contains(text(),'Copy link to')]")
    time.sleep(0.5)
    copy_button.click()

    p = subprocess.Popen(['pbpaste'], stdout=subprocess.PIPE)
    retcode = p.wait()
    link = p.stdout.read()
    print("Link: {}".format(link))

    return(link)
    


if __name__ == "__main__":
    main()
