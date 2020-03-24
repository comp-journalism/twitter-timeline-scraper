# twitter-timeline-scraper
Lightweight scripts for scraping the algorithmically-curated Twitter timeline


### Requirements:
* https://chromedriver.chromium.org/downloads
* Google Chrome with version that matches chromedriver

### Checklist for EC2
(see https://gist.github.com/ziadoz/3e8ab7e944d02fe872c3454d17af31a5 for guidance)
* `sudo apt update`
* `sudo apt upgrade`
* `wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb`
* `sudo apt install ./google-chrome-stable_current_amd64.deb`
* `dpkg -s google-chrome-stable | grep Version` (to see version)
* `wget https://chromedriver.storage.googleapis.com/80.0.3987.106/chromedriver_linux64.zip`
* `sudo apt install unzip`
* `sudo apt install python3-pip`
* `pip3 install selenium pandas lxml`
* to get around Twitter's apparent selenium detection: https://stackoverflow.com/questions/33225947/can-a-website-detect-when-you-are-using-selenium-with-chromedriver
* Selenium:
```
SELENIUM_STANDALONE_VERSION=3.141.59
SELENIUM_SUBDIR=$(echo "$SELENIUM_STANDALONE_VERSION" | cut -d"." -f-2)
wget -N https://selenium-release.storage.googleapis.com/$SELENIUM_SUBDIR/selenium-server-standalone-$SELENIUM_STANDALONE_VERSION.jar -P ~/
sudo mv -f ~/selenium-server-standalone-$SELENIUM_STANDALONE_VERSION.jar /usr/local/bin/selenium-server-standalone.jar
sudo chown root:root /usr/local/bin/selenium-server-standalone.jar
sudo chmod 0755 /usr/local/bin/selenium-server-standalone.jar
```
