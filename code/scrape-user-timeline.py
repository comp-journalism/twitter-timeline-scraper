'''
scrape-user-timeline.py
'''

import pandas as pd
import time
import pdb
import subprocess
import selenium.webdriver.chrome.service as service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from selenium import webdriver

# download chromedriver from https://chromedriver.chromium.org/downloads
path_to_chromedriver = '/Users/jackbandy/Devel/chromedriver'

path_to_save = '../data/test.csv'

twitter_url = 'https://twitter.com/home'


def main():
    print("Starting!")
    my_service = service.Service(path_to_chromedriver)
    my_service.start()
    capabilities = {}
    driver = webdriver.Remote(my_service.service_url, capabilities)
    driver.get(twitter_url)

    time.sleep(3)
    username_input = driver.find_element_by_xpath("//input[@type='text']")
    password_input = driver.find_element_by_xpath("//input[@type='password']")
    #username_input.send_keys('jackbandy')

    print("Log in to twitter,")
    input("then press Enter to continue...")
    pdb.set_trace()

    timeline = scrape_timeline(driver)
    timeline_df = pd.DataFrame(timeline)
    timeline_df.to_csv(path_to_save)



def scrape_timeline(driver,n_tweets=50):
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
        time.sleep(0.2)

    return tweet_links



def get_tweet_link(driver):
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
