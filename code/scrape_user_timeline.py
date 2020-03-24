'''
scrape_user_timeline.py
'''

import selenium.webdriver.chrome.service as service
import pandas as pd
import subprocess
import lxml.html
import time
import pdb
import sys
import os
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime

# download chromedriver from https://chromedriver.chromium.org/downloads
path_to_chromedriver = '/Users/jbx9603/Applications/chromedriver'
WAIT_TIME = 15
SCROLL_TIME= 0.25
DEBUG=True


path_to_save = '../data/'

twitter_url = 'https://twitter.com/home'

sys.path.append('../credentials')
from users import users_list

'''
from scrape_user_timeline import *
my_service = service.Service(path_to_chromedriver)
my_service.start()
driver = webdriver.Remote(my_service.service_url)
driver.get(twitter_url)
log_in_user(driver,user=users_list[0])
articles=driver.find_elements_by_tag_name('article')
for a in articles:
    dict = tweet_article_to_dict(a) 
'''


def main():
    for u in users_list:
        print("collecting for {}".format(u['username']))

        my_service = service.Service(path_to_chromedriver)
        my_service.start()
        driver = webdriver.Remote(my_service.service_url)
        driver.get(twitter_url)
        try:
            log_in_user(driver,user=u)
            collect_timelines(driver,user=u,n_tweets=100)
        except TimeoutException as e:
            print("Timed out...")
        except ConnectionRefusedError as e:
            print("Connection error...")
        print("Done!")


def log_in_user(driver, user):
    # log in
    print("Logging in...")
    username_input = WebDriverWait(driver, WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH, "//input[@type='text']")))
    password_input = WebDriverWait(driver, WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH, "//input[@type='password']")))
    print("Found element!")
    username_input.send_keys(user['username'])
    password_input.send_keys(user['password'])
    login_button = driver.find_element_by_xpath("//span[(text()='Log in')]")
    login_button.click()



def collect_timelines(driver,user,n_tweets=100):
    # set up saving path
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d-at-%H%M')
    path_to_save = '../data/{}'.format(user['username'])
    if not os.path.exists(path_to_save):
        os.makedirs(path_to_save)

    # collect algorithmic timeline
    algorithmic_timeline = scrape_timeline(driver,n_tweets=n_tweets)
    alg_timeline_df = pd.DataFrame(algorithmic_timeline)
    file_path = '{}/{}-algorithmic-{}.csv'.format(path_to_save,user['username'],now_str) 
    alg_timeline_df.to_csv(file_path,index=False)

    # switch to chronological
    switch_to_chronological(driver)

    # collect chronological timeline
    chronological_timeline = scrape_timeline(driver,n_tweets=n_tweets)
    chron_timeline_df = pd.DataFrame(chronological_timeline)
    file_path = '{}/{}-chronological-{}.csv'.format(path_to_save,user['username'],now_str) 
    chron_timeline_df.to_csv(file_path,index=False)



def switch_to_chronological(driver):
    #button = driver.find_element_by_xpath("//div[@aria-label='Top Tweets on']/div")
    button = WebDriverWait(driver, WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Top Tweets on']/div")))
    button.click()
    latest_button = WebDriverWait(driver, WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH, "//span[(text()='See latest Tweets instead')]")))
    #latest_button = driver.find_element_by_xpath("//span[(text()='See latest Tweets instead')]")
    latest_button.click()
    print("Switched to chronological timeline!")



def scrape_timeline(driver,n_tweets=50):
    return scrape_timeline_as_articles_lxml(driver,n_tweets=n_tweets)




def scrape_timeline_as_articles_lxml(driver,n_tweets=50):
    '''
    lxml is WAY faster than selenium parsing
    vroom vroom
    '''
    # initialize the return object
    all_tweets = []
    all_tweet_links = []

    # get the first tweet
    #first_article=driver.find_element_by_tag_name('article')
    first_article = WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.TAG_NAME, "article")))
    a_html = first_article.get_attribute('innerHTML')
    to_add = tweet_article_to_dict_lxml(a_html)
    all_tweets.append(to_add)
    all_tweet_links.append(to_add['tweet_link'])
    minimum_y = first_article.location['y']

    # add tweets until there are n_tweets in the return object
    while len(all_tweets) < n_tweets:
        # collect article elements
        _ = WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.TAG_NAME, "article")))
        articles=driver.find_elements_by_tag_name('article')
        tmp_tweets = []
        tmp_tweet_links = []
        for a in articles:
            try:
                # check that article is beyond the first tweet 
                if a.location.get('y') < minimum_y:
                    continue
                a_html = a.get_attribute('innerHTML')
                to_add = tweet_article_to_dict_lxml(a_html)
                tmp_tweets.append(to_add)
                tmp_tweet_links.append(to_add['tweet_link'])
                '''
                # skip if already collected
                if ((to_add.get('tweet_link')==None) or (to_add['tweet_link'] in tweet_links)) and to_add.get('promoted')==None:
                    continue
                tweet_links.append(to_add['tweet_link'])
                tweets.append(to_add)
                '''
            except StaleElementReferenceException as e:
                print("Error a: stale element")
            except Exception as e:
                print("Error b: {}".format(str(e)))

        # add new articles
        # can't just check if tweet is in the list already,
        # since tweets can appear twice in a timeline,
        # so add based on non-overlap with most recent tweet in all_tweets
        new_index = 0
        if all_tweet_links[-1] in tmp_tweet_links:
            new_index = tmp_tweet_links.index(all_tweet_links[-1]) + 1
        all_tweets += tmp_tweets[new_index:]
        all_tweet_links += tmp_tweet_links[new_index:]
        print("\nAdding {} fresh tweets out of {} parsed".format(len(tmp_tweets[new_index:]), len(tmp_tweets)))

        print("scrolling...")
        # move down the page to last article examined
        _ = WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.TAG_NAME, "article")))
        articles=driver.find_elements_by_tag_name('article')
        ActionChains(driver).move_to_element(articles[-1]).perform()
        # let things load a bit
        time.sleep(SCROLL_TIME)


    # scroll back to top of page when done
    driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)
    return all_tweets 



def tweet_article_to_dict_lxml(a_html):
    '''
    input: html from an individual 'article' element
    output: a clean dictionary with tweet attributes
    '''
    to_add = {}
    external_links = set()
    a_lxml = lxml.html.fromstring(a_html)
    a_lxml.make_links_absolute('https://twitter.com')
    for link in a_lxml.xpath('.//a'):
        link_url = link.get('href')
        if link_url.count('/') == 3 and to_add.get('user_link')==None:
            to_add['user_link'] = link_url
        elif '/status/' in link_url and to_add.get('tweet_link')==None:
            to_add['tweet_link'] = link_url
        elif '/i/' in link_url and to_add.get('info_link')==None:
            to_add['info_link'] = link_url
            info_texts = [c.text for c in link.xpath('.//span') if c.text!= None]
            to_add['info_text'] = ' '.join(pd.Series(info_texts).drop_duplicates().tolist())
            #to_add['info_text'] = ' '.join(list(set([c.text for c in link.xpath('.//span') if c.text!= None])))
        elif 't.co' in link_url: #and to_add.get('external_text')==None:
            to_add['external_link'] = link_url
            external_links.add(link_url)
            text_blurbs = []
            for blurb in link.xpath('.//span'):
                if blurb.text == None:
                    continue
                elif blurb.text not in text_blurbs and blurb.text.count(' ') > 0:
                    text_blurbs.append(blurb.text)
                elif blurb.text.count(' ') == 0 and blurb.text.count('/') == 0 and blurb.text.count('.') > 0:
                    to_add['external_domain'] = blurb.text
            if len(text_blurbs) > 0:
                to_add['external_title'] = text_blurbs[0]
            if len(text_blurbs) > 1:
                to_add['external_text'] = text_blurbs[-1]
                
        if len(a_lxml.xpath(".//span[(text()='Promoted')]"))>0:
            to_add['promoted'] = 'promoted'
            to_add['tweet_link'] = to_add['user_link']
    if DEBUG:
        print('\n\n')
        for k in to_add.keys():
            print('{} : {}'.format(k, to_add[k]))
    if len(external_links) > 0:
        to_add['n_external_links'] = len(external_links)

    return to_add




def scrape_timeline_as_articles(driver,n_tweets=50):
    '''
    OLD
    scrapes tweets using selenium and 'article' key
    '''
    # initialize the return object
    tweets = []
    tweet_links = []
    first_article=driver.find_element_by_tag_name('article')
    minimum_y = first_article.location['y']
    while len(tweets) < n_tweets:
        # collect article elements
        articles=driver.find_elements_by_tag_name('article')
        for a in articles:
            try:
                # check that article is beyond the first tweet and has tweet link
                if (not a.find_elements_by_xpath('.//a[contains(@href,"/status/")]')) or (a.location['y'] < minimum_y):
                    continue
                to_add = tweet_article_to_dict(a)
                # skip if already collected
                if to_add['tweet_link'] in tweet_links:
                    continue
                tweet_links.append(to_add['tweet_link'])
                tweets.append(to_add)
            except StaleElementReferenceException as e:
                print("Stale element")
            except ConnectionRefusedError as e:
                print("Connection issue")
        print("\tscrolling...")
        # move down the page to last article examined
        articles=driver.find_elements_by_tag_name('article')
        ActionChains(driver).move_to_element(articles[-1]).perform()
        # let things load
        time.sleep(SCROLL_TIME)
    # scroll back to top of page when done
    driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)
    return tweets



def tweet_article_to_dict(a):
    '''
    OLD
    turns article/tweet element to dict using selenium
    '''
    to_add = {}
    for link in a.find_elements_by_tag_name('a'):
        link_url = link.get_attribute('href')
        if link_url.count('/') == 3 and to_add.get('user_link')==None:
            to_add['user_link'] = link_url
        elif '/status/' in link_url and to_add.get('tweet_link')==None:
            to_add['tweet_link'] = link_url
        elif '/i/' in link_url and to_add.get('info_link')==None:
            to_add['info_link'] = link_url
            to_add['info_text'] = ' '.join(list(set([c.text for c in link.find_elements_by_xpath('.//span')])))
        elif 't.co' in link_url: #and to_add.get('external_text')==None:
            to_add['external_link'] = link_url
            text_blurbs = []
            for blurb in link.find_elements_by_xpath('.//span'):
                if blurb.text not in text_blurbs and blurb.text.count(' ') > 0:
                    text_blurbs.append(blurb.text)
                elif blurb.text.count(' ') == 0 and blurb.text.count('.') > 0:
                    to_add['external_domain'] = blurb.text
            if len(text_blurbs) > 0:
                to_add['external_title'] = text_blurbs[0]
            if len(text_blurbs) > 2:
                to_add['external_text'] = text_blurbs[-1]
                
        if a.find_elements_by_xpath(".//span[(text()='Promoted')]"):
            to_add['promoted'] = 'promoted'
    if DEBUG:
        print('\n\n')
        for k in to_add.keys():
            print('{} : {}'.format(k, to_add[k]))
    return to_add



def tweet_article_to_dict_old(a):
    '''
    OLD
    turns article/tweet element to dict using selenium
    '''
    to_add = {}
    to_add['tweet_link']=a.find_element_by_xpath('.//a[contains(@href,"/status/")]').get_attribute('href')
    print(to_add['tweet_link'])
    to_add['metadata'] = a.find_elements_by_xpath(".//div[@role='group']")[-1].get_attribute('aria-label')
    print("\t{}".format(to_add['metadata']))
    if a.find_elements_by_xpath('.//a[contains(@href,"/i/user")]'):
        to_add['info_text']=a.find_element_by_xpath('.//a[contains(@href,"/i/user")]').text
        to_add['info_link']=a.find_element_by_xpath('.//a[contains(@href,"/i/user")]').get_attribute('href')
    if a.find_elements_by_xpath('.//a[contains(@href,"t.co")]'):
        print("\texternal link")
        link_element = a.find_element_by_xpath('.//a[contains(@href,"t.co")]')
        to_add['external_url']=link_element.get_attribute('href')
        to_add['external_real']=link_element.text
        try:
            to_add['external_url_text']= link_element.find_elements_by_tag_name('span')[0].text
            to_add['external_url_title'] = link_element.find_elements_by_tag_name('span')[1].text
        except:
            print("No text/title tho")
            pass
    if a.find_elements_by_xpath(".//span[(text()='Promoted')]"):
        to_add['promoted'] = 'promoted'
        print('\tpromoted!')
    return to_add





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
