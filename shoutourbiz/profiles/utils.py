"""
This module encapsulates the service layer for
the "utils" app, and abstracts business
logic and data access.

"""
from django.db import connection

from main.utils import dictfetchall

from pytrends.request import TrendReq
from django_countries import countries

import requests
import re
import json

from bs4 import BeautifulSoup
from datetime import date
from dateutil.relativedelta import relativedelta

from internal.utils import is_assistant
from main.models import VerifiedUserAccounts, IgUsers, IgFollowerTrend

def retrieve_follower_ratings_given_ig_user(ig_user):

	query = (
		'SELECT * FROM ig_follower_rating ' +
		'WHERE ig_follower_id IN ( ' +
			'SELECT id FROM ig_follower x ' +
		    'WHERE x.following_id = ' + str(ig_user.id) + 
		');'
	)

	with connection.cursor() as cursor:
		cursor.execute(query)
		row = dictfetchall(cursor)
		return row

def calculate_age_group_stats(ratings):
	results = {
		'0-17': 0,
		'18-24': 0,
		'25-34': 0,
		'35-44': 0,
		'45-54': 0,
		'55+': 0
	}

	for rating in ratings:
		if rating['age_group'] == '0-17':
			results['0-17'] += 1
		elif rating['age_group'] == '18-24':
			results['18-24'] += 1
		elif rating['age_group'] == '25-34':
			results['25-34'] += 1
		elif rating['age_group'] == '35-44':
			results['35-44'] += 1
		elif rating['age_group'] == '45-54':
			results['45-54'] += 1
		elif rating['age_group'] == '55+':
			results['55+'] += 1
		# else ignore unknown values

	return results

def calculate_engagement_stats(ig_user):
	""" avg likes per photo / num of follower """
	if ig_user.postavglike and ig_user.followers:
		stat = float(ig_user.postavglike) / float(ig_user.followers)
		return stat
	else:
		return None

def calculate_gender_stats(ratings):
	results = { 'M': 0, 'F': 0 }

	for rating in ratings:
		if rating['gender'] == 'M':
			results['M'] += 1
		elif rating['gender'] == 'F':
			results['F'] += 1

	return results

def calculate_country_stats(ratings):
	results = {}

	for rating in ratings:
		if rating['country'] not in results:
			results[rating['country']] = 0
		results[rating['country']] += 1

	return results

def _month_name_from_date(date):
	if not date:
		raise TypeError('Date to get month name from cannot be null')
	return date.strftime('%B')

def calculate_followers_stats(user):
	"""
	Return data for followers chart.
	"""

	# get the number of followers for the past 6 months
	current_day = date.today()
	six_mos_ago = date.today() + relativedelta(months=-7)
	followers_data = IgFollowerTrend.objects.filter(ig_user=user, 
						date__range=[str(six_mos_ago), str(current_day)]).order_by('date')

	processed_data = []

	# now add data for each month, making sure to check for duplicates
	for point in followers_data:
		skip = False
		# check for duplicate months
		for point2 in processed_data:
			if _month_name_from_date(point.date) == point2[0]:
				skip = True
		if skip:
			continue

		# add month data if no duplicate problems
		data = [_month_name_from_date(point.date), point.num_followers]
		processed_data.append(data)

	return processed_data

def _build_niche_str_arr(niches, is_confirmed, network):
	if not niches:
		return []

	result = []

	if is_confirmed:
		for niche in niches:
			result.append(niche.niche)
	else:
		if network == 'ig':
			for niche in niches:
				result.append(niche.hashtag)
		elif network == 'tw':
			for niche in niches:
				result.append(niche.keyword)
	return result

def calculate_interest_over_time(request_user, account_user, niches, network):
	verified_acc = VerifiedUserAccounts.objects.filter(network=network, account_id=account_user.id).first()
	niches = _build_niche_str_arr(niches, verified_acc, network)[:4]

	if request_user.is_authenticated() and \
			(request_user.is_superuser or is_assistant(request_user) or \
			verified_acc in request_user.opened_accounts.all()):
		niches.insert(0, account_user.username)

	try:
		pytrend = TrendReq('shoutourbiz.tester@gmail.com', 'shoutourbiz123', \
			hl='en-US', tz=360, custom_useragent=None)
		pytrend.build_payload(kw_list=niches)
		df = pytrend.interest_over_time()
	except Exception as e:
		return (None, None)

	cols = {}
	x_axis = []

	# initialize header groups
	for header in df.dtypes.index:
		cols[header] = []

	ndx = 0
	for index, row in df.iterrows():

		if ndx % 2 == 0 or ndx % 3 == 0 or ndx % 5 == 0 or ndx % 7 == 0 or ndx % 4 == 0:
			ndx += 1
			continue

		if not index.value in x_axis:
			x_axis.append(index.value)
		
		for key,value in cols.iteritems():
			cols[key].append(row[key])

		ndx += 1

	return (x_axis, cols)


class IgProfileParser:

	def __init__(self, uid, ig_user):
		self.uid = uid
		self.username = ig_user.username

	def _parse_shared_data(self, soup):
		"""
		Parse shared_data javascript variable, which contains all info
		we need to scrape ig users.
		"""
		script_tag = soup.find("script", text=re.compile("window\._sharedData"))
		script_tag = script_tag.string.partition("=")[-1].strip(" ;")
		shared_data = json.loads(script_tag)
		return shared_data

	def quick_scrape_ig_profile_picture(self):
		try:
			profile_page = requests.get('https://www.instagram.com/{0}/'.format(self.username))
			if profile_page.status_code == 404:
				return None

			soup = BeautifulSoup(profile_page.text, 'html.parser')
			shared_data_user_profile = self._parse_shared_data(soup)
			is_private = shared_data_user_profile['entry_data']['ProfilePage'][0]['user']['is_private']

			profile_url = shared_data_user_profile['entry_data']['ProfilePage'][0]['user']['profile_pic_url_hd']

			if profile_url:
				return profile_url
		except Exception as e:
			return None

	def quick_scrape_ig_profile_picture_and_bio(self):

		try:
			profile_page = requests.get('https://www.instagram.com/{0}/'.format(self.username))
			if profile_page.status_code == 404:
				return None

			soup = BeautifulSoup(profile_page.text, 'html.parser')
			shared_data_user_profile = self._parse_shared_data(soup)
			is_private = shared_data_user_profile['entry_data']['ProfilePage'][0]['user']['is_private']

			profile_url = shared_data_user_profile['entry_data']['ProfilePage'][0]['user']['profile_pic_url_hd']
			bio = shared_data_user_profile['entry_data']['ProfilePage'][0]['user']['media']['nodes'][0]['caption']
			
			return {
				'profile_url': profile_url,
				'bio': bio,
			}

		except Exception as e:
			return None