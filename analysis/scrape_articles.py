'''
scrape_articles.py
retrieve and save urls
'''
import lxml.html.clean
from lxml import etree
import pandas as pd
import random
import requests
import re
from readability.readability import Document
from progressbar import progressbar
from bs4 import BeautifulSoup
from time import sleep,time


all_links_file_path = '../data/links/all_links.csv'
hydrated_file_path = '../data/links/hydrated_links.csv'

user_agent_list = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
]

def main():
    print('Reading in data...')
    links = pd.read_csv(all_links_file_path)
    links['hydrated'] = False
    hydrated_stories = pd.DataFrame()
    try:
        print('Cross-referencing...')
        hydrated_stories = pd.read_csv(hydrated_file_path)
        links['hydrated'] = links.external_link.apply(lambda x: x in hydrated_stories.url.tolist())
        print("{} stories already hydrated".format(len(hydrated_stories)))
    except FileNotFoundError:
        print("No hydrated stories.")

    stories_to_hydrate = links[~links.hydrated].sample(4000) 
    story_dicts = []
    try:
        for index,row in progressbar(stories_to_hydrate.iterrows(),max_value=len(stories_to_hydrate)):
            story_dicts.append(url_to_dict(row.external_link))
    except KeyboardInterrupt:
        print("Stopped!")

    new_stories = pd.DataFrame(story_dicts)
    new_stories.dropna(how='all', inplace=True)
    print("added {} stories".format(len(new_stories)))

    all_stories = pd.concat([hydrated_stories, new_stories])
    all_stories.to_csv(hydrated_file_path, index=False)
    print("saved {} stories".format(len(all_stories)))



def domain_from_url(url):
    # from https://pydeep.com/get-domain-name-from-url-python-snippet/
    domain = re.sub(r'(.*://)?([^/?]+).*', '\g<1>\g<2>', url)
    domain = domain.replace('https://','').replace('http://','').replace('www.','')
    domain = domain.replace('/','')
    return domain



def url_to_dict(url):
    story_dict = {}
    user_agent = random.choice(user_agent_list)
    header = {'User-Agent': user_agent}
    try:
        response = requests.get(url,headers=header,timeout=5)
        doc = Document(response.text)
        html_text = doc.summary()
        summary_soup = BeautifulSoup(html_text,features="lxml")
        all_soup = BeautifulSoup(response.text,features="lxml")
        story_dict['domain'] = domain_from_url(url)
        story_dict['title'] = doc.short_title()
        story_dict['text'] = clean_lxml(summary_soup.decode_contents())
        story_dict['url'] = url

        # canonical url and domain, if possible
        soup = BeautifulSoup(response._content,features="lxml")
        try:
            story_dict['canonical_url'] = all_soup.find('link', {'rel': 'canonical'})['href']
        except:
            story_dict['canonical_url'] = response.url
        story_dict['domain'] = domain_from_url(story_dict['canonical_url'])

        # site-specific handlers
        if 'http://hill.cm/' in url or 'https://thehill.com/' in story_dict['canonical_url']:
            story_dict['text'] = clean_lxml(all_soup.find('article').decode_contents()) 
        elif 'https://youtu.be' in url or 'https://www.youtube.com/' in story_dict['canonical_url']:
            story_dict['title'] = all_soup.find('meta',{"property" : "og:title"})['content']
            story_dict['text'] = all_soup.find('meta',{"property" : "og:description"})['content']
        elif 'https://www.thegatewaypundit.com/' in url:
            story_dict['text'] = clean_lxml(all_soup.find('article').decode_contents())

    except Exception as e:
        pass
        #print("Error with {}: {}".format(url,str(e)))
    return story_dict


    
def clean_lxml(content):
    cleaner = lxml.html.clean.Cleaner(
        safe_attrs_only=True,
        remove_unknown_tags=True,
        style=True,
    )
    html = lxml.html.document_fromstring(content)
    html_clean = cleaner.clean_html(html)
    spaced_html = " ".join(html_clean.itertext())
    clean_text = spaced_html.strip()
    reduced_whitespace = '\n\n'.join([c for c in clean_text.splitlines() if len(c.strip()) > 0])
    return reduced_whitespace



if __name__ == "__main__":
    main()
