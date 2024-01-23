import os
import requests
import re
import bs4
import tweepy
import configparser

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
config = configparser.ConfigParser()
config.read(dname+'/settings')
bot_config = config['Bot']
twitter_config = config['Twitter']
url = bot_config['url']
log_file = bot_config['log_file']
api_key = twitter_config['api_key']
api_secret = twitter_config['api_secret']
token = twitter_config['token']
token_secret = twitter_config['token_secret']


def make_soup(url):
    raw_data = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = bs4.BeautifulSoup(raw_data.text, "lxml")
    info = soup.find('p', class_='text2')
    info_text = info.get_text()
    info_para = re.sub(r'\s+', ' ', info_text).strip()
    previous_port_data = soup.find('div', class_='vi__r1 vi__stp')
    return info_para,previous_port_data

def check_last_log(log_file,log_line):
    with open(log_file, 'r') as logs:
        try:
            previous_log = logs.readlines()[-1].rsplit('\t',1)[0]
            if previous_log in log_line:
                return True
        except IndexError:
            return False

def post_to_twitter(data,is_enroute,is_arrived):
    if is_enroute:
        tweet_text = f'🛳️ {data[0]}\n\nCurrently at📍 {data[1]}\n\nHeaded To ➡️ {data[2]}\n\nETA 🕒 {data[3]}\n\nLatest Port ⛱️ {data[4]}'
    elif is_arrived:
        tweet_text = f'🛳️ {data[0]}\n\nCurrently at📍 {data[1]}\n\nArrived at 🕒 {data[2]}\n\nPrevious Port ⛱️ {data[3]}'
    api = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=token,
        access_token_secret=token_secret
    )
    tweet = api.create_tweet(text=tweet_text)
    print("Update Posted to Twitter ✅")
    return tweet[0]["id"]

def add_to_log(log_file, log_line, tweet_id):
    log_line += (str(tweet_id)+'\n')
    with open(log_file, 'a') as logs:
        logs.write(log_line)
    print("Added Data to Log ✅")
    print(log_line)

def main():
    info_para,previous_port_data = make_soup(url)
    ship_name = info_para.split('position of ')[1].split(' is ')[0]
    is_enroute = re.search("en route to", info_para)
    is_arrived = re.search("arrived at", info_para)
    try:
        previous_port = previous_port_data('a')[0].get_text()
    except:
        previous_port = previous_port_data('div')[0].get_text()
    if is_enroute:
        location = info_para.split('is at ')[1].split(' reported ')[0]
        enroute_to = info_para.split('route to ')[1].split(',')[0]
        eta = info_para.split('arrive there on ')[1].split('.')[0]
        data = [ship_name, location.title(), enroute_to.title(), eta, previous_port.title()]
    elif is_arrived:
        location = info_para.split(' port of ')[1].split(' on ')[0]
        ata = info_para.split(' on ')[1].split('.')[0]
        data = [ship_name, location.title(), ata, previous_port.title()]
    log_line = ''
    for info in data:
        log_line += info+'\t'
    if not check_last_log(log_file, log_line):
        tweet_id = post_to_twitter(data,is_enroute,is_arrived)
        add_to_log(log_file, log_line, tweet_id)
        
    else:
        print("No New Update Found ❌")

if __name__ == "__main__":
    main()
