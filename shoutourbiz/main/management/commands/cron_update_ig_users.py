"""
This module updates information for all Instagram users
already in the database.

It also tracks the growth of followers.

To see the latest log, input the following command: "check_update_ig_users_log"
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db import IntegrityError

import requests
import re
import os
import time
import json
import datetime
import random
import logging

from bs4 import BeautifulSoup
from pprint import pprint

from main.models import IgUsers, IgUserTags, IgFollowerTrend

logging.basicConfig(level=logging.ERROR, filename="cron_update_ig_users.log", filemode="a+",
                        format="%(asctime)-15s %(message)s")

half_hour_timer = time.time()
timekeeper = time.time()
total_inserted = 0
current_ndx = 0
num_steps = 10

def reset_database_connection():
	connection.close()

def _get_data(nxd1, ndx2):
	"""
	Retrieve all hashtags for processing.
	"""
	users = IgUsers.objects.all()[nxd1:ndx2]
	return users

def _parse_shared_data(soup):
	"""
	Parse shared_data javascript variable, which contains all info
	we need to scrape ig users.
	"""
	script_tag = soup.find("script", text=re.compile("window\._sharedData"))
	script_tag = script_tag.string.partition("=")[-1].strip(" ;")
	shared_data = json.loads(script_tag)
	return shared_data

def _find_avg_likes(shared_data):
    """ 
    	Return the average like of an Instagram user
    """

    td = datetime.timedelta(days=1)
    today = datetime.datetime.today()

    # retrieve most recent media by user 
    try:
    	media_nodes = shared_data['entry_data']['ProfilePage'][0]['user']['media']['nodes']
    except Exception as e:
    	logging.error(e)
    	logging.error('Uh oh...something went wrong when trying to parse through the user profile. Continuing...')

    	return

    # Check each media, and add them into a list if they are over 1 day old
    media_num = 0
    like_num = []
    for node in media_nodes:
    	
    	timestamp = int(node['date'])
    	created_time = datetime.datetime.fromtimestamp(int(timestamp))

    	if today - created_time >= td:
    		like_num.append(int(node['likes']['count']))

    	media_num += 1

    # find the average like
    if len(like_num) == 0:
        avg_like = 0
    elif len(like_num) >= 10:
        like_num.sort()
        l = like_num[1:-1]
        avg_like = sum(l) / len(l)
    else:
        avg_like = sum(like_num) / len(like_num)

    return avg_like

def _main_process(users, start_ndx):
	"""
	Main method to loop through all users in the database.
	"""
	
	ndx = 0 + start_ndx
	for user in users:

		logging.error('>> #{0}: {1}'.format(ndx, user.username))

		try:
			_process_user(user)
		except requests.exceptions.SSLError as e:
			logging.error(e)
			time.sleep(20)
			_process_user(user)
		except Exception as e:
			logging.error('******** EXTREME ERROR ********')
			logging.error(e)
			logging.error('..... trying to reconnect to database ......')
			reset_database_connection()
			logging.error('..... sleeping for 10 seconds ......')
			time.sleep(10)
			try:
				_process_user(user)
			except requests.exceptions.SSLError as e:
				logging.error(e)
				time.sleep(20)
				_process_user(user)
			except Exception as e:
				logging.error('******** 2ND EXTREME ERROR ********')
				logging.error(e)
				logging.error('...... skipping user "{0}".....'.format(user.username))
				continue
		ndx += 1

	logging.error('inserted so far = {0}'.format(total_inserted))

def _process_user(user):
	"""
	Process user to get followers, email, etc...
	"""

	global total_inserted

	profile_page = requests.get('https://www.instagram.com/{0}/'.format(user.username))

	if profile_page.status_code == 404:
		# user could not be found
		logging.error('{0} leads to a 404 error. User was removed or does not exist. Marking it deleted now...'.\
				format(user.username))
		has_deleted = user.deleted
		if not has_deleted:
			user.deleted = 1
			user.save()
		else:
			logging.error('User {0} has already been marked deleted'.format(user.username))
		return

	soup = BeautifulSoup(profile_page.text, 'html.parser')
	shared_data_user_profile = _parse_shared_data(soup)

	try:
		is_private = shared_data_user_profile['entry_data']['ProfilePage'][0]['user']['is_private']
		if is_private:
			logging.error('{0} is either unavailable, private, or deactivated. Skipping...'.format(user.username))
			return
	except Exception as e:
		logging.error(e)
		logging.error('{0} is either unavailable, private, or deactivated. Skipping...'.\
				format(user.username))
		return 

	username = shared_data_user_profile['entry_data']['ProfilePage'][0]['user']['username']
	user_id = shared_data_user_profile['entry_data']['ProfilePage'][0]['user']['id']
	user_bio = shared_data_user_profile['entry_data']['ProfilePage'][0]['user']['biography']

	email = None

	if user_bio and user_bio != '':
		user_bio = re.sub(r'[^\x00-\x7f]', r'', user_bio.encode('utf-8').strip())
		email = re.search(r'[-0-9a-zA-Z.+_]+@[-0-9a-zA-Z.+_]+\.[a-zA-Z]{2,4}', str(user_bio))
	else:
		logging.error('[MISS] {0} has no bio (therefore no e-mail).'.format(user.username))

	# if user has no email, skip
	if email:
		email = email.group()
	else:
		logging.error('{0} has no email'.format(username))

	post_count = shared_data_user_profile['entry_data']['ProfilePage'][0]['user']['media']['count']

	try:
		followers = shared_data_user_profile['entry_data']['ProfilePage'][0]['user']['followed_by']['count']
	except Exception as e:
		logging.error('Could not get # of followers. Continuing...')
		return

	# check if ig user already exists in database
	ig_user = IgUsers.objects.filter(username=user.username)

	if ig_user.exists():
		# if user exists, update e-mail, post counts, followers, and average likes
		ig_user = ig_user.first()
	else:
		# else create a new user and save into DB
		ig_user = IgUsers()
		ig_user.username = username
	
	# if user already has email, then update with this new one
	# else if email is removed, keep the current one in the system
	if email:
		ig_user.email = email

	ig_user.followers = followers
	ig_user.emailscraped = datetime.datetime.now()
	ig_user.postcount = post_count
	ig_user.postavglike = _find_avg_likes(shared_data_user_profile)
	ig_user.verified = ig_user.verified or 0
	ig_user.userid = user_id
	ig_user.emailsent = ig_user.verified or 0
	ig_user.related_accs_scraped = ig_user.related_accs_scraped or False
	ig_user.save()

	# now update follower trend
	trend_exists = IgFollowerTrend.objects.filter(ig_user=ig_user, date=datetime.datetime.today())
	if trend_exists:
		logging.error('Trend already exists...')
	else:
		logging.error('Trend does not exist already exists. Creating one...')
		follower_trend = IgFollowerTrend()
		follower_trend.ig_user = ig_user
		follower_trend.num_followers = followers
		follower_trend.date_created = datetime.datetime.today()
		ig_user.igfollowertrend_set.add(follower_trend)
		follower_trend.save()

	logging.error('[SUCCESS] ...username: {0} ~ email: {1} ...'.format(ig_user.username, ig_user.email))
	total_inserted += 1

class Command(BaseCommand):

	def add_arguments(self, parser):
		parser.add_argument('startndx', nargs=1, type=int)

	def handle(self, *args, **options):
		global current_ndx, timekeeper, total_inserted, half_hour_timer

		if options['startndx'][0] is not None:
			current_ndx = options['startndx'][0]

		total_num = IgUsers.objects.all().count()
		logging.error('There are {0} number of IG users.... Looping through all of them now...'.format(total_num))

		start = time.time()

		while current_ndx < total_num:
			logging.error('.................. Current ndx: [{0}:{1}] ...................'.format(current_ndx, current_ndx + num_steps))
			
			_main_process(_get_data(current_ndx, current_ndx + num_steps), current_ndx)

			max_time = random.randint(10, 100)
			if time.time() - timekeeper >= max_time:
				sleep_time = random.randint(7, 15)
				logging.error('Sleeping for {0}s. Max time: {1}...'.format(sleep_time, max_time))
				time.sleep(sleep_time)
				timekeeper = time.time()

			if time.time() - half_hour_timer >= 1800:
				sleep_time = 300
				logging.error('Sleeping for *5 minutes*....')
				time.sleep(sleep_time)
				half_hour_timer = time.time()

			current_ndx += num_steps

		end = time.time() - start
		m, s = divmod(end, 60)
		h, m = divmod(m, 60)
		logging.error('Total time: %d:%02d:%02d' % (h, m, s))