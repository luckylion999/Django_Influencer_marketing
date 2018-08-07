import requests
import time
import MySQLdb
import re
import datetime
import base64
from pprint import pprint
import sys

API_URL = 'https://api.twitter.com/'
tw_url = API_URL + '1.1/'

TW_KEY = '1ynxC3KlBEYha1afOr4YKN6gX'
TW_SECRET = 'ASIv4En5H8kscwhSIaL7k7f3A6VhSz4lWWyVaZvVacdutNfZCs'

DB = 'shoutourbiz'
USER = 'root'
PASSWD = 'mysql'
HOST = 'localhost'

MIN_FOL_COUNT = 10000
MIN_FAV_COUNT = 500
ROWS_PER_QUERY = 10000



def dbConnect():
    """Connect to database"""

    global db, c

    while True:
        try:
            db = MySQLdb.connect(host=HOST, user=USER, passwd=PASSWD, db=DB)
            c = db.cursor()
            break
        except:
            print("connection failed; reconnecting to db")
            time.sleep(30)


def find_user_email(user):
    """given a twitter user, find the user's email. return None if no email is found"""
    res = re.search(r'[-0-9a-zA-Z.+_]+@[-0-9a-zA-Z.+_]+\.[a-zA-Z]{2,4}', user['description'])
    if res:
        email = res.group(0)
    else:
        email = False
    return email


def user_meet_requirement(user):
    """return True iff user meets requirement to be inserted into Database"""

    if user.followers_count > MIN_FOL_COUNT:
        return True
    else:
        return False


def user_in_db(id, sn):
    """return True if user has already been inserted into Database"""

    global db, c

    c.execute("SELECT EXISTS(SELECT 1 FROM tw_users WHERE screenName=%s)",
              (sn,))
    k = c.fetchone()
    if k[0]:
        return True
    else:
        return False


def insert_user(user, email, keyword):
    """insert user into database"""

    global db, c

    # Get all the user's info
    screenName = user['screen_name']
    name = user['name']
    followersCount = user['followers_count']
    statusesCount = user['statuses_count']
    user_id = user['id_str']

    # find user's average favorites/retweets
    avg_retweet, avg_fav = findAvgFavRetweet(user_id)

    # insert into database
        # if avg_retweet == -1:
        #     c.execute("DELETE FROM tw_users WHERE user_id='%s'" % (user_id))
    try:
        if user_in_db(user_id, screenName):
            c.execute("UPDATE tw_users SET screenName=%s, name=%s, email=%s, emailScraped=%s, followersCount=%s, statusesCount=%s, avgRetweet=%s, avgFav=%s, userID=%s \
			    WHERE screenName=%s", (
            screenName, name, email,
            # time.strftime("%Y-%m-%d", time.gmtime()),
            datetime.date.today(),
            followersCount, statusesCount,
            avg_retweet, avg_fav, user_id, screenName))
            c.execute("SELECT id FROM tw_users WHERE screenName=%s", (screenName,))
            usr_pk = c.fetchone()
        else:
            c.execute("INSERT INTO tw_users(screenName, name, email, emailScraped, followersCount, statusesCount, avgRetweet, avgFav, userID, verified_acc_id) \
			    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NULL)", (
            screenName, name, email,
            #time.strftime("%Y-%m-%d", time.gmtime()),
            datetime.date.today(),
            followersCount, statusesCount,
            avg_retweet, avg_fav, user_id))
            c.execute("SELECT LAST_INSERT_ID()")
            usr_pk = c.fetchone()
        c.execute("INSERT IGNORE INTO tw_user_keywords(userID, keyword) \
		    VALUES (%s , %s)", (usr_pk, keyword[0]))
        db.commit()
    except UnicodeEncodeError:
        print 'Cannot insert user {} - credentials incompatible with unicode'.format(screenName)
    # except Exception as e:
    #     dbConnect()


def add_new_keywords(user):
    """add new hashtag into database, given a user.

        check a user's recent tweets, if the tweet has enough favorites, add it into database
    """
    global db, c

    user_id = user['id_str']

    params = {'count': 50, 'user_id': user_id}

    url = tw_url + 'statuses/user_timeline.json'
    tweets = make_request(url, params, header)
    # while True:
    #     tweets = requests.get(tw_url + 'statuses/user_timeline.json', params=params,
    #                           headers=header)
    #     tweets = process_response(tweets)
    #     if tweets:
    #         break

    for tweet in tweets:
        if tweet['favorite_count'] > MIN_FAV_COUNT:
            hashtags = tweet['entities']['hashtags']
            hashtags = [ent['text'] for ent in hashtags]
            for tag in hashtags:
                print 'tag:' + tag
                try:
                    c.execute("INSERT IGNORE INTO tw_keywords(keyword) VALUES (%s)", (tag,))
                    # c.execute("INSERT IGNORE INTO tw_user_keywords(userid, keyword) VALUES(%s, %s)",
                    #           (user_id, tag))
                    db.commit()
                except UnicodeEncodeError:
                    pass


def findAvgFavRetweet(user_id):
    """ find the average favorites/retweets of a user """

    global c, db

    params = {'count': 200, 'user_id': user_id}
    url = tw_url + 'statuses/user_timeline.json'
    tweets = make_request(url, params, header)
    # while True:
    #     tweets = requests.get(tw_url + 'statuses/user_timeline.json', params=params,
    #                           headers=header)
    #     tweets = process_response(tweets)
    #     if tweets:
    #         break

    td = datetime.timedelta(days=1)
    retweets_num = []
    favorites_num = []

    # Check every recent tweets, and add up the favorites/retweets count
    for status in tweets:
        today = datetime.datetime.today()
        created_time = status['created_at']
        created_time = created_time.split(' ')
        created_time.pop(-2)
        created_time = ' '.join(created_time)
        created_time = datetime.datetime.strptime(created_time, '%a %b %d %H:%M:%S %Y')
        if (today - created_time) >= td:
            retweets_num.append(status['retweet_count'])
            favorites_num.append(status['favorite_count'])

    # Find the averages for retweets and favorites
    len_retweets = len(retweets_num)
    if not retweets_num:
        return 0, 0
    if len_retweets >= 10:
        retweets_num.sort()
        favorites_num.sort()
        retweets_num = retweets_num[2:-2]
        favorites_num = favorites_num[2:-2]
    avg_retweet = int(sum(retweets_num) / float(len_retweets))
    avg_fav = int(sum(favorites_num) / float(len(favorites_num)))
    return avg_retweet, avg_fav


def get_keywords():
    """get all the existing keywords from database"""

    global db, c

    # while True:
    #     try:
    init_point = 0
    while True:
        c.execute("SELECT * FROM tw_keywords LIMIT %s, %s",
                  (init_point, ROWS_PER_QUERY))
        rows = c.fetchall()
        init_point += ROWS_PER_QUERY
        if rows:
            for row in rows:
                yield row
        else:
            raise StopIteration


def keyword_check_update(keyword, delete):
    """update the time last updated for a keyword. Delete it instead if delete is True"""
    global db, c

    if delete:
        c.execute("DELETE FROM tw_keywords WHERE keyword=%s", (keyword[0],))
    else:
        c.execute("UPDATE tw_keywords SET last_update=%s WHERE keyword=%s", (datetime.date.today(), keyword[0]))

    while True:
        try:
            db.commit()
            break
        except Exception as e:
            print(e)
            dbConnect()


def keyword_recheck(keyword):
    """return True iff it is time to re-check keyword"""

    last_checked = keyword[1]

    if not last_checked:
        return True

    if (datetime.date.today() - last_checked).days > 1:
        return True
    else:
        return False


def get_bearer_token():
    credentials = '{}:{}'.format(TW_KEY, TW_SECRET)
    credentials = base64.b64encode(credentials.encode('utf-8'))
    credentials_sent = 'Basic {}'.format(credentials)
    headers = {
        'Authorization': credentials_sent,
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    }
    url = API_URL + 'oauth2/token'
    resp = requests.post(url, data={'grant_type': 'client_credentials'},
                         headers=headers)
    if resp.status_code == 200:
        return resp.json()['access_token']
    else:
        print 'Cannot obtain twitter access token'

def make_request(url, params, headers, type='get'):
    while True:
        # limits = requests.get(tw_url + 'application/rate_limit_status.json', headers=headers)
        # limits = limits.json()['resources']
        # statuses = limits['statuses']['/statuses/user_timeline']
        # searches = limits['search']['/search/tweets']
        # rate_limits = limits['application']['/application/rate_limit_status']
        # statuses = statuses['remaining'] <= 500
        # searches = searches['remaining'] <= 15
        # rate_limits = rate_limits['remaining'] <= 15
        # if any([statuses, searches, rate_limits]):
        #     print 'rate limits exceeded'
        #     time.sleep(60 * 16)
        if type == 'get':
            resp = requests.get(url, params=params, headers=headers)
        else:
            resp = requests.post(url, data=params, headers=headers)
        if resp.status_code != 200:
            if resp.status_code == 429:
                print 'rate limits exceeded'
                time.sleep(60 * 16)
            else:
                print resp.status_code
                print resp.text
                raise Exception('Can\'t connect to twitter API')
        else:
            return resp.json()

if __name__ == '__main__':
    access_token = get_bearer_token()
    header = {'Authorization': 'Bearer {}'.format(access_token)}
    while True:
        dbConnect()
        count = 0
        for keyword in get_keywords():
            if not keyword_recheck(keyword):
                continue
            params = {
                'count': 100, 'q': keyword[0], 'result_type': 'recent',
            }
            url = tw_url + 'search/tweets.json'
            resp = make_request(url, params, header)
            resp = resp['statuses']
            for status in resp:
                user = status['user']
                if user['followers_count'] > MIN_FOL_COUNT:
                    email = find_user_email(user)
                    if email:
                        insert_user(user, email, keyword)
                    add_new_keywords(user)
            keyword_check_update(keyword, False)
        db.close()

