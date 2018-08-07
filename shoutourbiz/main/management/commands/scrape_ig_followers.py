"""
This class scrapes instagram followers and stores them in the ig_followers table.
The follower list dynamically updates, meaning that the top 25 followers
can (and will change) every time the followers modal is rendered. Therefore,
It is important to run the script only once so that we can get the top 
25 followers.

Usage: 
	python manage.py scrape_ig_followers --local True # for debugging
	python manage.py scrape_ig_followers # for Selenium grid server farm

To start a selenium grid hub:
	java -jar selenium-server-standalone-3.4.0.jar -role hub
To start a selenium grid node:
	java -jar selenium-server-standalone-3.4.0.jar -role webdriver -hub http://localhost:4444/grid/register -port 5566 
"""

import os
import sys
import time
import threading
import multiprocessing
import Queue
import logging

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException

from django.core.management.base import NoArgsCommand, BaseCommand, CommandError
from django.db import IntegrityError

from main.models import IgUsers, IgFollower
from internal.models import IgFollowerNumEvaluations

# Handle logging
logger = logging.getLogger('ig-scrape-followers')
handler = logging.FileHandler('skipped.log')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def spawn_threads(num, data):
	"""
	Create num amount of threads and run them in parallel.

	Parameters:
		num - the number of threads to spawn
	"""

	for i in range(num):
		t = threading.Thread(target=worker(data, False))
		t.daemon = True
		t.start()

class ElementNotFoundException(Exception):
	""" 
	Custom exception when HTML cannot
	be found by Selenium.
	"""
	pass

class AccountDoesNotHaveEnoughInfoException(Exception):
	"""
	Custom exception when account is private
	and Selenium cannot click on button to
	bring up followers modal.
	"""
	pass

class AlreadyProcessedException(Exception):
	""" 
	Custom exception when a user or element
	has already been processed or is already
	in the database.
	"""
	pass

def _print_followers(followers):
	"""
	Debug method to print out current instagram followers.
	"""
	for follower in followers:

		tmp = follower.find_elements_by_class_name('_4zhc5')[0].get_attribute('innerHTML');
		print tmp

	print '--------------------------------------------'

def _find_element_explicit_wait(driver, username, parentNode):

	attempt = 1
	_max_attempts = 3

	# search node repeatedly until element is no longer 'stale'
	result = []
	while len(result) <= 0:
		try:
			element = parentNode.find_elements_by_class_name('_4zhc5')

			if len(element) <= 0:
				attempt += 1
				continue

			result.append(element[0])

		except Exception as e:
			if attempt >= _max_attempts:
				logger.error(username)
				return False
			attempt += 1

	return result

def _get_followers(driver, username, followers):

	ret = []
	tmp = None

	for follower in followers:
		try:
			tmp = follower.find_elements_by_class_name('_4zhc5')
			uTmp = tmp[0].get_attribute('innerHTML').encode('ascii')
			ret.append(uTmp)

		except Exception as e:
			print e

			anotherTmp = _find_element_explicit_wait(driver, username, follower)
			if anotherTmp == False:
				continue

			uTmp = anotherTmp[0].get_attribute('innerHTML').encode('ascii')
			ret.append(uTmp)

	return ret

def _insert_followers_db(username, followers):
	"""
	Insert a max of 25 followers into database. 

	Parameters:
		username - the current instagram user
		followers - a list of people following the current instagram user
	Returns:
		Nothing
	"""

	# find user for foreign key
	ig_user = IgUsers.objects.get(username=username)
	ig_followers_pk = len(IgFollower.objects.filter(following_id=ig_user))

	# user already processed
	if ig_followers_pk > 0:
		raise AlreadyProcessedException('User already processed. Skipping...')

	# if no user exists, raise exception
	if ig_user is None:
		raise ElementNotFoundException('Cannot find original username in database!')

	# insert each follower into db (gets up to 25 followers)
	ndx = 0
	for follower in followers:

		if ndx >= 25:
			print('Reached 25 followers for {0}'.format(ig_user.username))
			break

		new_follower = IgFollower()
		new_follower.following = ig_user
		new_follower.username = follower

		# save if follower-user relationship does not already exist
		try:
			new_follower.save()
		except IntegrityError as e:
			print('Relationship {0} <-> {1} exists'.format(ig_user.username, new_follower.username))
			continue

		# initialize number of evaluations to 0
		num_evals = IgFollowerNumEvaluations()
		num_evals.ig_follower = new_follower
		num_evals.save()

		ndx += 1

def logIntoIg(driver):
	"""
	Log into instagram in order to access followers list

	Parameters:
		driver - an automated web driver
	Return:
		Nothing
	"""

	driver.get('https://www.instagram.com/')

	logInLink = driver.find_elements_by_xpath('//a[@class="_fcn8k"]')[0].click()
	WebDriverWait(driver, 10).until(
		EC.element_to_be_clickable((By.XPATH, '//input[@class="_kp5f7 _qy55y"]'))
	);

	loginBox = driver.find_elements_by_xpath('//input[@class="_kp5f7 _qy55y"]')

	usrname = os.environ.get('IG_USERNAME')
	psswd = os.environ.get('IG_PASSWORD')

	# username
	loginBox[0].click()
	loginBox[0].send_keys(usrname)
	# password
	loginBox[1].click()
	loginBox[1].send_keys(psswd)

	time.sleep(0.2)

	# click log in
	login = driver.find_elements_by_xpath('//button[@class="_ah57t _84y62 _i46jh _rmr7s"]')[0]
	login.click()

	time.sleep(2)

def processIgFollowers(driver, username):
	"""
	Get list of instagram followers

	Parameters:
		driver - an automated web driver
	Returns:
		Nothing
	"""

	# connect to url
	driver.get('https://www.instagram.com/{0}/'.format(username))


	# click on followers button to bring up modal
	results = driver.find_elements_by_xpath('//li[@class="_218yx"]')

	# if account is private or unavailable, skip this profile
	try:
		followers_button = results[1].find_elements_by_xpath('//a[@class="_s53mj"]')
	except (AttributeError, IndexError) as e:
		raise AccountDoesNotHaveEnoughInfoException('Account is private or unavailable. Skipping...')

	if len(followers_button) <= 0:
		raise AccountDoesNotHaveEnoughInfoException('Account is private or unavailable. Skipping...')

	# the second element is followers
	results[1].click()

	WebDriverWait(driver, 5).until(
		EC.element_to_be_clickable((By.XPATH, '//ul[@class="_539vh _4j13h"]'))
	);

	# scroll down
	driver.execute_script("document.querySelector('ul._539vh._4j13h').parentNode.scrollTop=50000;")
	time.sleep(0.5)

	# scroll down again
	driver.execute_script("document.querySelector('ul._539vh._4j13h').parentNode.scrollTop=500000;")
	time.sleep(0.5)

    # get list of followers
	followers3 = driver.find_elements_by_class_name('_cx1ua')

	_followers = _get_followers(driver, username, followers3)

	# insert into db
	_insert_followers_db(username, _followers)

def worker(usernames, is_local):

	if is_local:
		driver = webdriver.Chrome()
	else:
		driver = webdriver.Remote(
			command_executor="http://127.0.0.1:4444/wd/hub", 
			desired_capabilities=DesiredCapabilities.CHROME
		)

	logIntoIg(driver)

	for username in usernames:

		try:
			startTime = time.time()
			processIgFollowers(driver, username)
			print 'How long to run? {0} seconds'.format(time.time() - startTime)
		except (AccountDoesNotHaveEnoughInfoException, AlreadyProcessedException) as e:
			print e
			continue

	driver.quit()

def _get_ig_users():
	"""
	Get users from DB and add them to the queue for parallel processing.
	"""
	
	# Process the most popular instagrammers first 
	users = map(lambda x : x.username.encode('ascii'), IgUsers.objects.all().order_by('-followers')[:5000])
	return users

class Command(BaseCommand):

	def add_arguments(self, parser):

		parser.add_argument(
			'--local',
			default=False,
			help='Run web scraper locally instead of Selenium Grid'
		)

	def handle(self, *args, **options):

		#accounts = ['222foryou', 'futbolsport', 'letthelordbewithyou']

		if options['local']:
			data = _get_ig_users()
			worker(data, True)
		else:
			data = _get_ig_users()
			spawn_threads(3, data)