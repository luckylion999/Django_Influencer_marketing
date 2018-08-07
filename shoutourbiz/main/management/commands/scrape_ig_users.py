"""
This module scrapes IG users using the 'hashtag method' and stores
them in the IgFollowers model.

** Pseudocode for the 'hashtag method': **
1) Search up hastag: https://www.instagram.com/explore/tags/adidas/
2) Scrape top 9 posts
3) Go to media: https://www.instagram.com/p/BUoid3ygsRE/
4) Scrape username
5) If user has a minimum of 1,000 followers and if they have an email (regex)
	and if they aren't already in the database
	add them to the database
6) Later, email them

** SQL to see newly inserted IG users: **
SELECT * FROM test5.ig_users WHERE emailScraped BETWEEN '2017-01-01 00:00:00' AND '2018-01-01 00:00:00';
"""

from django.core.management.base import BaseCommand, CommandError
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

from main.models import IgHashtags, IgUsers, IgUserTags

logging.basicConfig(level=logging.ERROR, filename="scrape_ig_users.log", filemode="a+",
                        format="%(asctime)-15s %(message)s")

half_hour_timer = time.time()
timekeeper = time.time()
total_inserted = 0

def _get_data(ndx1, ndx2):
	"""
	Retrieve all hashtags for processing.
	"""
	hashtags = IgHashtags.objects.all()[ndx1:ndx2]
	return hashtags

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

def _main_process(hashtags, start_ndx):
	"""
	Main method to loop through hashtag.
	"""
	global timekeeper, total_inserted, half_hour_timer
	
	logging.error('Total # of hashtags: {0}'.format(len(hashtags)))

	ndx = 0 + start_ndx
	for hashtag in hashtags:

		hashtag = hashtag.hashtag.encode('utf-8')

		logging.error('-------#{0}: {1}--------'.format(ndx, hashtag))

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

		try:
			_process_hashtag(hashtag)
		except requests.exceptions.SSLError as e:
			logging.error(e)
			time.sleep(20)
			_process_hashtag(hashtag)
		except Exception as e:
			logging.error('******** EXTREME ERROR ********')
			logging.error(e)
			logging.error('...... skipping hashtag "{0}".....'.format(hashtag))
			time.sleep(300)
			continue

		ndx += 1

	logging.error('total_inserted = {0}'.format(total_inserted))

def _process_hashtag(hashtag):
	"""
	Process hashtag to get user, email, etc...
	"""

	global total_inserted

	site = requests.get('https://www.instagram.com/explore/tags/{0}/'.format(hashtag))
	soup = BeautifulSoup(site.text, 'html.parser')
	
	if site.status_code == 404:
		logging.error('[MISS] Tag not found. Continuing to next tag...')
		return

	shared_data_post = _parse_shared_data(soup)
	tag_nodes = shared_data_post['entry_data']['TagPage'][0]['tag']['media']['nodes']
	tag_nodes = sorted(tag_nodes, key=lambda k: k['likes'], reverse=True)

	logging.error('Number of posts: {0}'.format(len(tag_nodes)))

	ndx = -1
	for post in tag_nodes:
		ndx += 1

		if ndx > 50:
			return
		
		# get top posts
		post_url = 'https://www.instagram.com/p/{0}'.format(post['code'])
		media_page = requests.get(post_url)
		soup = BeautifulSoup(media_page.text, 'html.parser')

		shared_data_media_page = _parse_shared_data(soup)
		try:
			username = shared_data_media_page['entry_data']['PostPage'][0]['graphql']['shortcode_media']['owner']['username']
		except Exception as e:
			logging.error('Could not get username from post page. Continuing...')
			continue

		profile_page = requests.get('https://www.instagram.com/{0}/'.format(username))

		if profile_page.status_code == 404:
			logging.error('{0} leads to a 404 error. Skipping...'.\
					format(username))

		soup = BeautifulSoup(profile_page.text, 'html.parser')

		shared_data_user_profile = _parse_shared_data(soup)

		try:
			is_private = shared_data_user_profile['entry_data']['ProfilePage'][0]['user']['is_private']
			if is_private:
				logging.error('{0} is either unavailable, private, or deactivated. Skipping...'.\
					format(username))
				continue
		except Exception as e:
			logging.error(e)
			logging.error('{0} is either unavailable, private, or deactivated. Skipping...'.\
					format(username))
			continue 

		username = shared_data_user_profile['entry_data']['ProfilePage'][0]['user']['username']
		user_id = shared_data_user_profile['entry_data']['ProfilePage'][0]['user']['id']
		user_bio = shared_data_user_profile['entry_data']['ProfilePage'][0]['user']['biography']

		if not user_bio or user_bio == '':
			logging.error('[MISS] {0} has no bio (therefore no e-mail). Skipping...'.format(username))
			continue

		user_bio = re.sub(r'[^\x00-\x7f]', r'', user_bio.encode('utf-8').strip())
		email = re.search(r'[-0-9a-zA-Z.+_]+@[-0-9a-zA-Z.+_]+\.[a-zA-Z]{2,4}',
					str(user_bio))

		# if user has no email, skip
		if email:
			email = email.group()
		else:
			logging.error('[MISS] {0} has no email. Skipping...'.format(username))
			continue

		logging.error('{0} has an email!! :-) Processing...'.format(username))
		post_count = shared_data_user_profile['entry_data']['ProfilePage'][0]['user']['media']['count']

		try:
			followers = shared_data_user_profile['entry_data']['ProfilePage'][0]['user']['followed_by']['count']
		except Exception as e:
			logging.error('[MISS] Could not get # of followers user profile page. Continuing...')
			continue

		# if num followers is less than 100, skip
		if followers < 100:
			logging.error('[MISS] {0} has less than 100 followers. Skipping...'.format(username))
			continue

		# check if ig user already exists in database
		ig_user = IgUsers.objects.filter(username=username)

		if ig_user.exists():
			# if user exists, update e-mail, post counts, followers, and average likes
			ig_user = ig_user.first()
		else:
			# else create a new user and save into DB
			ig_user = IgUsers()
			ig_user.username = username
		
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

		# now loop through media and grab hashtags
		logging.error('... now processing hashtags for user {0}'.format(username))
		try:			
			media_desc = shared_data_media_page['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_media_to_caption']['edges'][0]['node']['text']
			media_desc = re.sub(r'[^\x00-\x7f]', r'', media_desc.encode('utf-8').strip())
			tmp_hashtag_arr = re.findall(r'#(\w+)', media_desc)
			hashtag_arr = []
			for ndx in range(len(tmp_hashtag_arr)):

				if len(tmp_hashtag_arr[ndx]) > 1 and not any(char.isdigit() for char in tmp_hashtag_arr[ndx]):
					hashtag_arr.append(tmp_hashtag_arr[ndx])					

			if not hashtag_arr:
				hashtag_arr.append(hashtag)

			# now save hashtags
			for tag in hashtag_arr:
				new_tag = IgUserTags()
				new_tag.userid = user_id
				new_tag.hashtag = tag
				new_tag.frequency = 0
				new_tag.save()

		except Exception as e:
			logging.error(e)
			logging.error('Influencer saved, but unable to save hashtag...!')
			print e
			pass

		total_inserted += 1

class Command(BaseCommand):

	def add_arguments(self, parser):

		parser.add_argument('ndx1', nargs=1, type=int)
		parser.add_argument('ndx2', nargs=1, type=int)

	def handle(self, *args, **options):
		if options['ndx1'][0] is not None and options ['ndx2'][0] is not None:
			hashtags = _get_data(options['ndx1'][0], options['ndx2'][0])
			_main_process(hashtags, options['ndx1'][0])
		else:
			logging.error('Uh oh, unable to parse indices...')