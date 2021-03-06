# fxcrawler
A simple fxcrawler to determine when is the best time to exchange currency on FSM.

### Pre-Requisites
```bash
sudo apt update
sudo apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools python3-venv mongodb
```

### Create a virtualenv and activate the virtual environment
```bash
virtualenv env
source env/bin/activate
```

### Set up geckodriver, download from https://github.com/mozilla/geckodriver/releases
```
sudo cp geckodriver /usr/bin/geckodriver
```

### Install the requirements
```bash
pip3 install -r requirements.txt
```

### Add environment variables in ~/.bash_profile
```
vim ~/.bash_profile
export bot_token=tele_bot_token
export chat_id=bot_chat_id
```

### Running at an interval of 30 minutes 
```bash
watch --interval=3600 python web_scraper.py 
```
### Alternatively, using crontab:
```
crontab -e

Add the following line:
*/30 * * * * cd /home/dev/fxcrawler-telegram-bot && . /home/dev/.bash_profile && env/bin/python3 web_scraper.py

sudo service crontab reload
```
