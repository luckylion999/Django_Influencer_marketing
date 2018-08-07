import requests
import datetime
import time
from pprint import pprint
import tweepy

url = 'https://api.instagram.com/v1'
token = '3605340622.087bb2d.436b33cc4100465db29ef4fd28ac5eda'
# id = '3605340622'
id = '543805085'
# url_ = url + '/users/self/follows'
# resp = requests.get(url_, params={'access_token': token})
# print resp.url
# print resp.text
class IgException(Exception):
    pass

def get_user_info_ig(user_id, token):
    now = time.time()
    day_secs = datetime.timedelta(days=1).total_seconds()
    user_url = url + '/users/{}/'.format(user_id)
    token_params = {'access_token': token}
    user = requests.get(user_url, params=token_params)
    media_url = url + '/users/{}/media/recent/'.format(user_id)
    token_params['count'] = 50
    media = requests.get(media_url, params=token_params)
    if user.status_code == 200 and media.status_code == 200:
        user = user.json()
        media = media.json()
    else:
        raise IgException
    counts = user['data']['counts']
    post_num = counts['media']
    follower_num = counts['followed_by']
    like_num = []
    media_num = 0
    for m in media['data']:
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
    print post_num, follower_num, avg_like


# get_likes_followers_posts(id, token)
TW_KEY = '1ynxC3KlBEYha1afOr4YKN6gX'
TW_SECRET = 'ASIv4En5H8kscwhSIaL7k7f3A6VhSz4lWWyVaZvVacdutNfZCs'
key = '812321739443212289-rzvCynGiLYMFrx8jMmsrOUI0CPLbMUo'
secret = 'WczVMtrUZGY0yWodZMDEo1ogv05U6xgKRwOYnpNSt1nTZ'
def get_user_info_tw():
    auth = tweepy.OAuthHandler(TW_KEY, TW_SECRET)
    auth.set_access_token(key, secret)
    api = tweepy.API(auth)
    user = api.me()
    user = api.search_users('LanaDelRey')
    for u in user:
        if u.verified:
            user = u
    id_ = user.id
    tweets = api.user_timeline(user_id=id_, count=41)
    today = datetime.datetime.today()
    td = datetime.timedelta(hours=5)
    retweets_num = []
    favorites_num = []
    status_count = 0
    for status in tweets:
        if (today - status.created_at) >= td:
            retweets_num.append(status.retweet_count)
            favorites_num.append(status.favorite_count)
            status_count += 1
    retweets_len = len(retweets_num)
    if retweets_len == 0:
        avg_retweet = 0
        avg_fav = 0
    elif retweets_len >= 10:
        retweets_num.sort()
        favorites_num.sort()
        r = retweets_num[2:-2]
        f = favorites_num[2:-2]
        avg_retweet = sum(r) / len(r)
        avg_fav = sum(f) / len(f)
    else:
        avg_retweet = sum(retweets_num) / retweets_len
        avg_fav = sum(favorites_num) / len(favorites_num)
    name = user.name
    followers_num = user.followers_count
    statuses_num = user.statuses_count
    screenname = user.screen_name
    res = {
        'screenname': screenname, 'name': name, 'followerscount': followers_num,
        'statusescount': statuses_num, 'avgretweet': avg_retweet, 'avgfav': avg_fav,
        'userid': id_
    }
    return res



# def findAvgLike(user_id):
#
#     td = datetime.timedelta(days=1)
#     today = datetime.datetime.today()
#
#     while True:
#         try:
#             (user_media, pag) = cur_api.api.user_recent_media(user_id=user_id, count=30)
#             break
#         except InstagramAPIError as e:
#             print(e)
#             if e.status_code == 400:
#                 raise IgHashtagException()
#             else:
#                 cur_api = cur_api.next
#         except InstagramClientError as e:
#             print(e)
#             if e.status_code == 502:
#                 raise IgHashtagException()
#             else:
#                 cur_api = cur_api.next
#
#     media_num = 0
#     like_num = []
#     for media in user_media:
#         created_time = media.created_time
#         if (today - created_time) >= td:
#             like_num.append(media.like_count)
#             media_num += 1
#
#     if len(like_num) == 0:
#         avg_like = 0
#     elif len(like_num) >= 10:
#         like_num.sort()
#         l = like_num[1:-1]
#         avg_like = sum(l) / len(l)
#     else:
#         avg_like = sum(like_num) / len(like_num)
#
#     return avg_like

