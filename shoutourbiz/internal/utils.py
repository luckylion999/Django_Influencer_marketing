"""
This module encapsulates the service layer for
the "internal" app, and abstracts business
logic and data access.

"""
import datetime

from dateutil.relativedelta import relativedelta
from random import randint

from django.db import connection

from .models import IgFollowerRating
from main.models import AuthUser, VerifiedUserAccounts, IgFollower
from main.utils import sql_query, dictfetchall

def _query_get_followers_all_ig_users(user_id):
	"""
	Query database to obtain the next follower
	for assistant.
	"""

	query = (
		'SELECT t2.id as FOLLOWER_ID, t2.username as FOLLOWER_USRNAME, ' + 
		't1.username as BASE_USRNAME, t1.followers as BASE_NUM_FOLLOWERS ' +
		'FROM ig_users t1 ' +
		'RIGHT JOIN ( ' + 
			'SELECT * ' +
			'FROM ig_follower a ' +
			'WHERE a.id NOT IN ( ' +
				'SELECT ig_follower_id FROM ig_follower_rating ' +
		    ') ' +
		') t2 ' +
		'ON t1.id = t2.following_id ' +
		'ORDER BY t1.followers DESC ' +
		'LIMIT 1;'
	)

	with connection.cursor() as cursor:
		cursor.execute(query)
		row = dictfetchall(cursor)
		return row

def _query_get_followers_verified_users(user_id):
	"""
	Query database to obtain the next follower
	for assistant. Gets verified users only because
	they are the most useful ones. Order by number
	of followers descending.
	"""

	query = (
		'SELECT t2.id as FOLLOWER_ID, t2.username as FOLLOWER_USRNAME, ' +
		't1.username as BASE_USRNAME, t1.followers as BASE_NUM_FOLLOWERS ' +
		'FROM ig_users t1 ' +
		'INNER JOIN verified_user_accounts v ' +
			'ON t1.id = v.account_id AND v.network = "ig" ' +
		'INNER JOIN ( ' +
			'SELECT * ' +
			'FROM ig_follower a ' +
			'WHERE a.id NOT IN ( ' +
				'SELECT ig_follower_id FROM ig_follower_rating ' +
			') ' +
		') t2 ' +
		'ON t1.id = t2.following_id ' +
		'WHERE t2.retrieved = 0 ' +
		'ORDER BY BASE_NUM_FOLLOWERS DESC ' +
		'LIMIT 1;'
	)

	with connection.cursor() as cursor:
		cursor.execute(query)
		row = dictfetchall(cursor)
		return row

def getBatch(user):
	"""
	Algorithm to distribute accounts amongst assistants.

	Pseudocode:
	1) Retrieve all IG accounts by # of followers descending
	2) Check to see how many assistants have evaluated each follower
	3) Order follower by # of evaluations descending
	4) Check which profile assistant has not analyzed yet
	5) Return remaining profiles
	"""

	# Retrieve IG followers and order by # of followers descending

	# first, try retrieving confirmed/verified users
	row = _query_get_followers_verified_users(int(user.id))
	# then, if no confirmed/verified users are found, get regular IgUsers
	if not row:
		row = _query_get_followers_all_ig_users(int(user.id))

	row = row[0]

	# now, check to see if that follower already has an existing rating
	ig_follower = IgFollower.objects.filter(id=int(row['FOLLOWER_ID'])).first()
	existing_rating = IgFollowerRating.objects.filter(ig_follower__username=ig_follower.username)

	# create a new rating automatically and then recursively
	# call this function again
	if existing_rating.exists():
		existing_rating = existing_rating.first()
		new_rating = IgFollowerRating()
		new_rating.ig_follower = ig_follower
		new_rating.assistant = user
		new_rating.age_group = existing_rating.age_group
		new_rating.country = existing_rating.country
		new_rating.gender = existing_rating.gender
		new_rating.date_created = datetime.datetime.now()
		new_rating.save()
		return getBatch(user)

	return {
		'FOLLOWER_USRNAME': row['FOLLOWER_USRNAME'].encode('ascii'),
		'FOLLOWER_ID': int(row['FOLLOWER_ID']),
		'BASE_USRNAME': row['BASE_USRNAME'].encode('ascii')
	}

def get_assistant_info(assistant_id):
	"""
	Retrieve the ratings that assistant_id performed
	"""
	ratings = IgFollowerRating.objects.filter(assistant_id=assistant_id)
	return ratings

def _query_get_all_assistant_info(month):

	query = (
		"SELECT assistant_id, COUNT(assistant_id) AS count " +
		"FROM ig_follower_rating " +
		"WHERE MONTH(ig_follower_rating.date_created) = " + str(month) + " "
		"GROUP BY assistant_id;"
	)
	
	results = sql_query(query)

	if len(results) <= 0:
		return []

	# set unique id for each assistant (for the front-end template)
	id_already_used = []
	for result in results:
		tmp = randint(0, 100000)
		while tmp in id_already_used:
			tmp = randint(0, 100000)
		id_already_used.append(tmp)

		result['id'] = tmp

	# get assistant object for each assistant id
	for result in results:
		assistant = AuthUser.objects.filter(id=result['assistant_id'])
		if assistant.exists():
			result['assistant_info'] = assistant.first()
		else:
			result['assistant_info'] = None

	# get total count for this month
	month_count = 0
	for result in results:
		month_count += result['count']

	# get month string
	tmp = datetime.datetime.now()
	current_day = datetime.datetime(tmp.year, month, 1)

	return {
		'month': month, 
		'month_str': current_day.strftime('%B'),
		'year': current_day.year,
		'month_count': month_count,
		'data': results
	}

def get_all_assistant_info():
	"""
	Retrieve ratings for all assistants for this month and the previous month
	"""

	# get stats for current month
	now = datetime.datetime.now()
	this_month_stats = _query_get_all_assistant_info(now.month)

	# get stats for previous month
	previous_month = (now - relativedelta(months=1)).month
	previous_month_stats = _query_get_all_assistant_info(previous_month)

	all_months_stats = [previous_month_stats, this_month_stats]

	num_ratings = 0
	for month in all_months_stats:
		if month:
			for assistant in month['data']:
				num_ratings += assistant['count']

	return (num_ratings, all_months_stats)

def make_niches_str(niches_arr):
	niches = [niche.niche for niche in niches_arr]
	return ', '.join(niches)
def make_niches_str_unverified(niches_arr, network):
	if network == 'ig':
		niches = [niche.hashtag for niche in niches_arr]
	elif network == 'tw':
		niches = [niche.keyword for niche in niches_arr]
	return ', '.join(niches)
def get_niches(acc):
	return acc.niches.all()
def get_niches_unverified(acc, network):
	if network == 'ig':
		niches = acc.igusertags_set.all()
	elif network == 'tw':
		niches = acc.twuserkeywords_set.all()

	return niches

def is_assistant(user):
	"""
	Return true if user is an assistant, False otherwise
	"""

	if user.groups.filter(name='assistant').exists():
		return True
	return False

def _query_get_finished_influencers():
	query = (
		'SELECT ' + 
		    't3.id as influencer_id, t3.username as influencer_username, ' +
		    't3.followers as influencer_followers, ' +
		    'COUNT(t3.id) as num_followers_evaluated ' +
		'FROM ig_follower_rating t1 ' +
		'INNER JOIN ig_follower t2 ' +
			'ON t1.ig_follower_id = t2.id ' +
		'INNER JOIN ig_users t3 ' +
			'ON t2.following_id = t3.id ' +
		'INNER JOIN auth_user t4 ' +
			'ON t1.assistant_id = t4.id ' +
		'GROUP BY influencer_id, influencer_username, influencer_followers;'
	)

	with connection.cursor() as cursor:
		cursor.execute(query)
		row = dictfetchall(cursor)
		return row

def get_finished_influencers():
	return _query_get_finished_influencers()