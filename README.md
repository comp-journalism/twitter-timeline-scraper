# twitter-timeline-scraper
Lightweight scripts for scraping the algorithmically-curated Twitter timeline


## Audit Your Timeline Algorithm in 5 Minutes
1. Clone the repository via `git clone https://github.com/comp-journalism/twitter-timeline-scraper.git`
2. Install required packages via `pip install -r requirements.txt`
3. Download a [chromedriver](https://chromedriver.chromium.org/downloads) that matches your Chrome version
4. Add your environment variables in `scrape_user_timeline.py`
  * `path_to_chromedriver` is the location of the download in step 3
  * `data_path` is the folder where you want to save the collected data (two csv files)
5. run `python scrape_user_timeline.py`, log in to Twitter, and enjoy!



#### Checklist for EC2
(see https://gist.github.com/ziadoz/3e8ab7e944d02fe872c3454d17af31a5 for guidance)
* `sudo timedatectl set-timezone America/Chicago` (to set the time zone)
* Get the tools:
```
sudo apt update
sudo apt upgrade
sudo apt install unzip
sudo apt install python3-pip
pip3 install selenium pandas lxml
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb
```
* `dpkg -s google-chrome-stable | grep Version` (to check version)
* `wget https://chromedriver.storage.googleapis.com/80.0.3987.106/chromedriver_linux64.zip` (with version from previous command)
* Install chrome driver:
```
unzip ~/chromedriver_linux64.zip -d ~/
rm ~/chromedriver_linux64.zip
sudo mv -f ~/chromedriver /usr/local/bin/chromedriver
sudo chown root:root /usr/local/bin/chromedriver
sudo chmod 0755 /usr/local/bin/chromedriver
```
* Selenium (check versions):
```
SELENIUM_STANDALONE_VERSION=3.141.59
SELENIUM_SUBDIR=$(echo "$SELENIUM_STANDALONE_VERSION" | cut -d"." -f-2)
wget -N https://selenium-release.storage.googleapis.com/$SELENIUM_SUBDIR/selenium-server-standalone-$SELENIUM_STANDALONE_VERSION.jar -P ~/
sudo mv -f ~/selenium-server-standalone-$SELENIUM_STANDALONE_VERSION.jar /usr/local/bin/selenium-server-standalone.jar
sudo chown root:root /usr/local/bin/selenium-server-standalone.jar
sudo chmod 0755 /usr/local/bin/selenium-server-standalone.jar
```
* to get around Twitter's apparent selenium detection: https://stackoverflow.com/questions/33225947/can-a-website-detect-when-you-are-using-selenium-with-chromedriver
