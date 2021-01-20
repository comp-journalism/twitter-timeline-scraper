'''
scrape_user_timeline.py
'''

import selenium.webdriver.chrome.service as service
import pandas as pd
import subprocess
import lxml.html
import signal
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
from random import shuffle,randint
from selenium import webdriver
from datetime import datetime

# download chromedriver from https://chromedriver.chromium.org/downloads
path_to_chromedriver = '/Users/jbx9603/Applications/chromedriver2'
data_path= '/Users/jbx9603/Box/Jack/Public/twitter-timeline-scraper/output'
SCROLL_TIME= 1.5
WAIT_TIME = 1.5
N_TWEETS = 50
DEBUG=False

twitter_url = 'https://twitter.com/home'


def main():
    print("Starting!\n-------------------------------")
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--enable-javascript')
    options.add_argument('--no-sandbox')
    #options.add_argument('--window-size=1920,1080')
    #options.add_argument('--start-maximized')
    #options.add_argument('--headless')
    

    my_service = service.Service(path_to_chromedriver)
    my_service.start()
    driver = webdriver.Remote(my_service.service_url,desired_capabilities=options.to_capabilities())
    driver.get(twitter_url)
    
    input("(1) Log in to Twitter\n(2)Make sure you're at home/Top Tweets\n(3)Press Enter/Return to continue...")
    
    try:
        collect_timelines(driver,n_tweets=N_TWEETS,chronological=True)
    except TimeoutException as e:
        print("Timeout error...")
    except ConnectionRefusedError as e:
        print("Connection error...")
    except Exception as e:
        print("Unrecognized error: {}".format(str(e)))
    else:
        print("No errors...")
    finally:
        print("Done!")
        time.sleep(SCROLL_TIME)
        driver.quit()



def log_in_user(driver, user):
    # log in
    print("Logging in...")
    time.sleep(SCROLL_TIME)

    username_input = WebDriverWait(driver, WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH, "//input[@type='text']")))
    username_input.send_keys(user['username'])
    print("Entered username...")
    password_input = WebDriverWait(driver, WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH, "//input[@type='password']")))
    password_input.send_keys(user['password'])
    login_button = driver.find_element_by_xpath("//span[(text()='Log in')]")
    print("Clicking login button...")
    login_button.click()



def collect_timelines(driver,n_tweets,chronological=False):
    # set up saving path
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d-at-%H%M')
    print(now_str)
    path_to_save = '{}'.format(data_path)
    if not os.path.exists(path_to_save):
        os.makedirs(path_to_save)

    # collect algorithmic timeline
    algorithmic_timeline = scrape_timeline(driver,n_tweets=n_tweets)
    alg_timeline_df = pd.DataFrame(algorithmic_timeline)
    file_path = '{}/algorithmic-{}.csv'.format(path_to_save,now_str)
    if len(algorithmic_timeline) == 0:
        file_path = '{}/algorithmic-{}-NONE.csv'.format(path_to_save,now_str)
    alg_timeline_df.to_csv(file_path,index=False)

    if chronological:
        # switch to chronological
        time.sleep(randint(1,4))
        switch_to_chronological(driver)
        time.sleep(randint(1,4))

        # collect chronological timeline
        chronological_timeline = scrape_timeline(driver,n_tweets=n_tweets)
        chron_timeline_df = pd.DataFrame(chronological_timeline)
        file_path = '{}/chronological-{}.csv'.format(path_to_save,now_str)
        if len(chronological_timeline) == 0:
            file_path = '{}/chronological-{}-NONE.csv'.format(path_to_save,now_str)
        chron_timeline_df.to_csv(file_path,index=False)



def switch_to_chronological(driver):
    print("Finding chronological toggle...")
    button = WebDriverWait(driver, WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Top Tweets on']/div")))
    print("Clicking chronological toggle...")
    button.click()
    latest_button = WebDriverWait(driver, WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH, "//span[(text()='See latest Tweets instead')]")))
    print("Switching to chronological...")
    latest_button.click()
    print("Switched to chronological timeline!")




def scrape_timeline(driver,n_tweets=50):
    to_return = scrape_timeline_as_articles_lxml(driver,n_tweets=n_tweets)

    return to_return
    



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
        print("{} / {} tweets collected".format(len(all_tweets), n_tweets))
        if len(all_tweets) >= n_tweets:
            print("Continuing...")
            continue # early break if possible

        print("scrolling...")
        # move down the page to last article examined
        _ = WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.TAG_NAME, "article")))
        articles=driver.find_elements_by_tag_name('article')
        ActionChains(driver).move_to_element(articles[-1]).perform()
        # let things load a bit and don't be predictable!
        time.sleep(SCROLL_TIME + (randint(10,50)/100))



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
    # old method based on copy and paste button
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
