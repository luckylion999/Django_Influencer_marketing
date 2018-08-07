"""
This module encapsulates the service layer for
the "main" app, and abstracts business
logic and data access.

"""
import time
import datetime
import requests
import custom_elasticsearch as es

from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import Group
from django.utils.timezone import get_default_timezone_name
from django.db.models import Q
from django.db import connection

from itertools import chain
from decimal import Decimal

from haystack.query import SearchQuerySet
from haystack.inputs import AutoQuery, Exact, Clean

from . import models

def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict
    """
    
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def sql_query(query):
    """
    Directly query SQL
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        row = dictfetchall(cursor)
        return row

def get_instagram_link(request, next=None):
    redirect_url = """
    		https://api.instagram.com/oauth/authorize/?client_id={}&redirect_uri={}
    		&response_type=code&scope=basic+public_content+follower_list
    		"""
    redirect_uri = '{}://{}{}'.format(request.scheme, request.get_host(),
                                      reverse('main:authenticate_successful', args=('ig', )))
    if next:
        redirect_uri += '?next={}'.format(next)
    redirect_url = redirect_url.format(settings.IG_ID, redirect_uri)
    return redirect_url

def create_ig_user(json):
    user = {
        'token': json['access_token'], 'username': json['user']['username'],
        'id': json['user']['id']
    }
    return user

class IgException(Exception):
    pass

def get_user_info_ig(user_id, token):
    url = settings.IG_API_URL
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
        print user.text
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
    return post_num, follower_num, avg_like

def get_user_info_tw(api):
    user = api.me()
    id_ = user.id
    tweets = api.user_timeline(user_id=id_, count=41)
    today = datetime.datetime.today()
    td = datetime.timedelta(days=1)
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
        'username': screenname, 'name': name, 'followers': followers_num,
        'statusescount': statuses_num, 'avgretweet': avg_retweet, 'avgfav': avg_fav,
        'userid': id_
    }
    return res

def check_uses_active(user):
    if not user.groups.filter(name='month_buyer').exists():
        return 0, 'not buyer'
    uses = user.buyeruses_set.all()
    if uses.exists():
        uses = uses[0]
        subscription = user.subscription
        if subscription.check_active():
            return uses.uses, 'ok'
        else:
            buyer_group = Group.objects.get(name='month_buyer')
            user.groups.remove(buyer_group)
            uses.uses = 0
            uses.save()
    return 0, 'expired'

def calcul_new_date(date, months):
    month = date.month
    year = date.year
    num_years = months / 12
    next_month = (month + months) % 12
    day = date.day
    if next_month == 0:
        next_month = 12
    year += num_years
    while True:
        try:
            new_date = date.replace(year=year, month=next_month, day=day)
        except ValueError:
            day -= 1
        else:
            return new_date

def _calculate_cpm(account):

    if account.verified == 0:
        return None

    if account.followers > 0 and account.followers < 1000:
        ratio = 6.262
    elif account.followers >= 1000 and account.followers < 10000:
        ratio = 15
    elif account.followers >= 10000 and account.followers < 20000:
        ratio = 24.5
    elif account.followers >= 20000 and account.followers < 100000:
        ratio = 4.86
    elif account.followers >= 100000 and account.followers < 1000000:
        ratio = 21.06
    elif account.followers >= 1000000 and account.followers < 10000000:
        ratio = 10.64
    elif account.followers >= 10000000 and account.followers < 50000000:
        ratio = 25.6
    elif account.followers >= 50000000:
        ratio = 10
    else:
        return None

    num_views_per_thousand = (Decimal(account.followers) / Decimal(ratio)) / 1000

    # get price of running add
    price = Decimal(account.verified_acc.price)

    # calculate cpm
    cpm = price / Decimal(num_views_per_thousand)

    return cpm

def unique_chain(*iterables):
    known_ids = set()
    for it in iterables:
        for element in it:
            if element.id not in known_ids:
                known_ids.add(element.id)
                yield element

class SobSearchEngine():

    def __init__(self, niches_list, accs_list_base):
        self.niches_list = niches_list
        self.accs_list_base = accs_list_base

    def search_verified(self):
        
        accs_list = list()
        for niche in self.niches_list:
            accs_list = list(chain(accs_list, \
                self.accs_list_base.filter(verified_acc__niches__niche__icontains=niche)))
        return accs_list

    def search_verified_and_unverified(self, network):
        
        accs_list_1 = self.search_verified()
        accs_list_2 = list()

        for niche in self.niches_list:
            if network == 'ig':
                accs_list_2 = list(chain(accs_list_2, \
                    self.accs_list_base.filter(igusertags__hashtag__icontains=niche)))
            elif network == 'tw':
                accs_list_2 = list(chain(accs_list_2, \
                    self.accs_list_base.filter(twuserkeywords__keyword__icontains=niche)))

        return list(unique_chain(accs_list_1, accs_list_2))

class ES_SobSearchEngine:

    def __init__(self, network, search_unverified):
        self.network = network
        self.search_unverified = search_unverified
        self.results = None
        self.has_niches = False
        self.query = None

    def _search_niches_match_all(self):

        if self.search_unverified:
            # search both confirmed and unconfirmed users
            if self.network == 'ig':
                self.results = es.ConfigurableSearchQuerySet().models(models.IgUsers).all()
            elif self.network == 'tw':
                self.results = es.ConfigurableSearchQuerySet().models(models.TwUsers).all()
        else:
            # search only confirmed users
            if self.network == 'ig':
                self.results = es.ConfigurableSearchQuerySet().models(models.VerifiedUserAccounts).filter(network__exact='ig')
            elif self.network == 'tw':
                self.results = es.ConfigurableSearchQuerySet().models(models.VerifiedUserAccounts).filter(network__exact='tw')

    def _get_query(self, terms):

        if self.search_unverified:
            if self.network == 'ig':
                network_model = "main.igusers"
            elif self.network == 'tw':
                network_model = "main.twusers"
        else:
            network_model = "main.verifieduseraccounts"

        if self.search_unverified:
            self.query = {
                "query":{"constant_score": {"filter": {"bool": {"must": [{"term": {"django_ct": network_model}},
                            {"bool": {"must": []}}]}}}}
            }

            for term in terms:
                self.query['query']['constant_score']['filter']['bool']['must'][1]['bool']['must'].append({"term": {"text": term}})

        else:
            self.query = {
                "query":{"constant_score": {"filter": {"bool": {
                    "must": [{"term": {"django_ct": network_model}},
                    {"term": {"network": self.network}}, {"bool": {"must": []}}]}}}}
            }

            for term in terms:
                self.query['query']['constant_score']['filter']['bool']['must'][2]['bool']['must'].append({"term": {"text": term}})

        self.has_niches = True
        return self.query

    def search_niches(self, niches_list):            
        self._search_niches_match_all()
        
        if niches_list == 'match_all':
            return

        niches_list = niches_list.split(',')
        m_query = self._get_query(niches_list)
        self.results = self.results.custom_query(m_query)

    def filter_by_followers(self, min_followers, max_followers):
        if self.has_niches:
            range_query = {"range": {"followers": {"gte": min_followers,"lte": max_followers}}}
            self.query['query']['constant_score']['filter']['bool']['must'].append(range_query)
            self.results = self.results.custom_query(self.query)
        else:
            self.results = self.results.filter(followers__gte=min_followers, followers__lte=max_followers)

    def filter_by_cpm(self, min_cpm, max_cpm):

        if self.has_niches:
            range_query = {"range": {"cpm": {"gte": min_cpm, "lte": max_cpm}}}
            self.query['query']['constant_score']['filter']['bool']['must'].append(range_query)
            self.results = self.results.custom_query(self.query)
        else:
            self.results = self.results.filter(cpm__gte=min_cpm, cpm__lte=max_cpm)

    def filter_by_engagement(self, min_engagement, max_engagement):
        # convert percent back to decimal
        min_engagement = min_engagement / 100;
        max_engagement = max_engagement / 100;

        if self.has_niches:
            range_query = {"range": {"engagement": {"gte": min_engagement, "lte": max_engagement}}}
            self.query['query']['constant_score']['filter']['bool']['must'].append(range_query)
            self.results = self.results.custom_query(self.query)
        else:
            self.results = self.results.filter(engagement__gte=min_engagement, engagement__lte=max_engagement)

    def sort(self, order_by):
        if order_by == 'followers':
            self.results = self.results.order_by('followers')
        elif order_by == 'followers_reverse':
            self.results = self.results.order_by('-followers')
        elif order_by == 'id':
            self.results = self.results.order_by('iid')
        elif order_by == 'id_reverse':
            self.results = self.results.order_by('-iid')
        elif order_by == 'cpm':
            self.results = self.results.order_by('cpm')
        elif order_by == 'cpm_reverse':
            self.results = self.results.order_by('-cpm')
        elif order_by == 'confirmed':
            self.results = self.results.order_by('verified')
        elif order_by == 'confirmed_reverse':
            self.results = self.results.order_by('-verified')
        elif order_by == 'engagement':
            self.results = self.results.order_by('engagement')
        elif order_by == 'engagement_reverse':
            self.results = self.results.order_by('-engagement')
        else:
            self.results = self.results.order_by('-followers')

    def get_results(self):
        return self.results