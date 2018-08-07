from __future__ import absolute_import, unicode_literals
import requests
import datetime
import time
import MySQLdb
import re
from pprint import pprint
import sys

DB = 'shoutourbiz'
USER = 'root'
PASSWD = 'mysql'
HOST = 'localhost'
API_URL = 'https://api.instagram.com/v1/'

ROWS_PER_QUERY = 10000
MIN_FLWR_NUM = 1000
rate_limits = 0
rate_max = 4800
db = MySQLdb.connect(host=HOST, user=USER, passwd=PASSWD, db=DB)
c = db.cursor()

def main_process(user):
    access_token = {'access_token': user['token']}
    while True:
        for usr_id, username in users_generator():
            process_user_friends(usr_id, access_token)
            c.execute('UPDATE ig_users SET related_accs_scraped=1 WHERE username=%s',
                      (username,))
            db.commit()
        print('iter stopped')


def users_generator():
    init_point = 0
    while True:
        c.execute('SELECT userID, username FROM ig_users WHERE related_accs_scraped=0 LIMIT %s, %s',
                  (init_point, ROWS_PER_QUERY))
        rows = c.fetchall()
        init_point += ROWS_PER_QUERY
        if rows:
            for row in rows:
                yield row
        else:
            raise StopIteration

def process_user_friends(usr_id, token):
    try:
        media = get_media(usr_id, token)
    except Exception:
        # maybe delete accs from db?
        return
    for ent in media:
        likes_num = ent['likes']['count']
        if likes_num > 0:
            media_id = ent['id']
            url = API_URL + 'media/{}/likes'.format(media_id)
            users_liked = make_request(url, token)
            users_liked = users_liked['data']
            # pprint(users_liked)
            for user in users_liked:
                res = process_user(user, token)
                if res:
                    tags, id = res
                    process_hashtags(tags, id, token)


def find_email(data):
    res = re.search(r'[-0-9a-zA-Z.+_]+@[-0-9a-zA-Z.+_]+\.[a-zA-Z]{2,4}', data)
    if res:
        return res.group(0)


def process_user(user, token):
    username = user['username']
    user_exists_bool, scraped_date = user_exists(username)
    td = datetime.timedelta(days=5)
    today_date = datetime.date.today()
    if user_exists_bool:
        if scraped_date > (today_date - td):
            return False
    user_id = user['id']
    user_url = API_URL + 'users/{}/'.format(user_id)
    user_info = make_request(user_url, token)
    user_info = user_info['data']
    counts = user_info['counts']
    follower_num = counts['followed_by']
    # here should be a condition if > min followers num
    if follower_num < MIN_FLWR_NUM:
        return False
    usr_data = [user_info['bio'], user_info['website']]
    for data in usr_data:
        email = find_email(data)
        if email:
            break
    if not email:
        # email = 'mymail@mail.com'
        return False
    now = time.time()
    day_secs = datetime.timedelta(days=1).total_seconds()
    post_num = counts['media']
    like_num = []
    media_num = 0
    media = get_media(user['id'], token)
    tags = []
    # print len(media)
    for m in media:
        tags += m['tags']
        created_time = m['created_time']
        if (now - int(created_time)) >= day_secs:
            like_num.append(m['likes']['count'])
            media_num += 1
    like_len = len(like_num)
    if like_len == 0:
        avg_like = 0
    elif like_len >= 10:
        like_num.sort()
        l = like_num[1:-1]
        avg_like = sum(l) / len(l)
    else:
        avg_like = sum(like_num) / like_len
    # print avg_like, follower_num, post_num, email, username, user_id
    now = datetime.date.today()
    # function to send email should be here
    try:
        if user_exists_bool:
            c.execute('UPDATE ig_users SET email=%s, followers=%s, emailScraped=%s, postCount=%s,'
                      'postAvgLike=%s, userID=%s, emailSent=%s WHERE username=%s',
                      (email, follower_num, now, post_num, avg_like, user_id, 1, username))
            c.execute('SELECT id FROM ig_users WHERE username=%s', (username,))
            return_id = c.fetchone()
        else:
            c.execute('INSERT INTO ig_users(username, email, followers, emailScraped, '
                      'postCount, postAvgLike, verified, userID, emailSent, verified_acc_id, related_accs_scraped)'
                      'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, 0)',
                      (username, email, follower_num, now, post_num, avg_like, 0, user_id, 1))
            c.execute('SELECT LAST_INSERT_ID()')
            return_id = c.fetchone()
    except UnicodeEncodeError:
        return False
    db.commit()
    return tags, return_id

def process_hashtags(tags, usr_id, token):
    tags = set(tags)
    for tag in tags:
        url = API_URL + u'tags/{}'.format(tag)
        tag_info = make_request(url, token)
        tag_info = tag_info['data']
        frequency = tag_info['media_count']
        try:
            if hashtag_exists(tag, usr_id):
                print 'hashtag update'
                c.execute('UPDATE ig_user_tags SET frequency=%s WHERE userID=%s AND hashtag=%s',
                          (frequency, usr_id, tag))
            else:
                print 'hashtag insert'
                c.execute('INSERT INTO ig_user_tags(userID, hashtag, frequency) VALUES (%s, %s, %s)',
                          (usr_id, tag, frequency))
        except UnicodeEncodeError:
            pass
        db.commit()






def hashtag_exists(tag, usr_id):
    c.execute('SELECT EXISTS(SELECT 1 FROM ig_user_tags WHERE userID=%s AND hashtag=%s)', (usr_id, tag))
    res = c.fetchone()
    print res
    return res[0]

def user_exists(username):
    c.execute('SELECT emailScraped FROM ig_users WHERE username=%s', (username,))
    res = c.fetchone()
    if res:
        return True, res[0]
    else:
        return False, False


def make_request(url, params, type='get'):
    check_rate_lims()
    while True:
        if type == 'get':
            resp = requests.get(url, params=params)
        else:
            resp = requests.post(url, data=params)
        if resp.status_code != 200:
            if resp.status_code == 429:
                print 'rate limits exceeded'
                time.sleep(60 * 61)
            else:
                print resp.text
                raise Exception('Can\'t connect to instagram API')
        else:
            return resp.json()

def check_rate_lims():
    global rate_limits
    rate_limits += 1
    if rate_limits >= rate_max:
        print 'reached rate limit'
        time.sleep(60 * 61)
        rate_limits = 0
    # global redis_db
    # rate_limit = redis_db.incr('rate_limit')
    # print rate_limit
    # if rate_limit > 50:
    #     redis_db.set('rate_limit', 0)
    #     print 'reached rate lim'
    #     time.sleep(60 * 61)

def get_media(usr_id, token):
    url = API_URL + 'users/{}/media/recent'.format(usr_id)
    params = dict(token, count=50)
    media = make_request(url, params)
    media = media['data']
    return media


if __name__ == '__main__':
    user = {
    'username': 'shalfeyyy', 'token': '3605340622.087bb2d.436b33cc4100465db29ef4fd28ac5eda',
    'usr_id':'3605340622',
    }
    main_process(user)

