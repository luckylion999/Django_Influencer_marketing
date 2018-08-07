import tweepy
from tweepy import OAuthHandler
import re
import time
import datetime
import MySQLdb
from warnings import filterwarnings
from requests.packages.urllib3.exceptions import InsecurePlatformWarning

access_token = '185893191-X6z7VZx4GsrvuNpdZ8TUYddSt41Nje4x3JpPFhHH'
access_token_secret = '79cOqacKVVKfELSphAs4RXRobg1wiXx84pNy3In7QZrhd'
consumer_key = 'Ksc7qA3PcEHaRPLEIHXEtyOOL'
consumer_secret = 'cbFFe2OwtKOI6INYMacD0gKfFv1xwhsKUvLm6cdhbVyXS579MA'
HOST = "localhost"
USER = "otto"
DB = "shout_out_biz"
PASSWD = "96in236"
MIN_FOL_COUNT = 10000
MIN_FAV_COUNT = 1300
filterwarnings('ignore', category = MySQLdb.Warning)
filterwarnings('ignore', category = InsecurePlatformWarning)

class api_node(object):
	"""class for storing Twitter API information"""

	def __init__(self, access_token, access_token_secret, consumer_key, consumer_secret):
		self.access_token = access_token
		self.access_token_secret = access_token_secret
		self.consumer_key = consumer_key
		self.consumer_secret = consumer_secret
		self.next = None

def api_setup():
	"""setup Twitter APIs. Create a linked list of api_nodes."""

	global cur_api

	api1 = api_node('185893191-J780RTMy04rjqCfnefCybCfeg3cMWAEcQ1aGH8al',
		'SiHhtyxr3A308RkTpeM6o3agG7tATTV4SNoyNcrY45JGs',
		'nnlO5j0biiVFMCmyVB749angp',
		'a1gX1MnTYYwGa0LWk8KsKIxdGgUJajbZG2fhU5yRhz8DHCBjTQ')
	api2 = api_node('185893191-DYPNlZl7F9N1XY5gq4yrJLHPSS1xoVenTHhHLaJb',
		'9qllKf8a4t7omZ1P3Z7SQyGZCNLCwqRCOyed0ccnAtH8U',
		'tLkU6sivD5FkYYhLwjKxVibQZ',
		'K2NLqT0QPzMSmTUfHamlHXIhYZmkA5HTRbGSpZSSj5C9hzhw22')
	api3 = api_node('185893191-wpqv1IxYYqO1sPDwnpxpj7Pedwhewzc9jO9jfQ4I',
		'G2zQb9urpYZVljhl9LaQdqUQamUlD21xlQcwKinPMVUMx',
		'KPCeHK2ylaGWe6PZ1YycDu1Sm',
		'VFOM1ZlJQBTZnYp4aCNrTWQaRqTHPtgU0ulq4xfOZf8sgexdLd')
	api4 = api_node('185893191-uOrhhGTgfZj1GcrUPmnrFmeJpwKOEb8voMY1nWZA',
		'iC5oPDShH1tHM8XeLi8V891pJAM3V7o3vaxAmTB8jyNOH',
		'zpFqDlebXg1qVCHpUQrU0oCG8',
		'8aoEOZ01064aCEH5AoYoA9oYb5WZT5cgC9LqGUlf0Ezgbs4jsm')
	api5 = api_node('185893191-nAssDZDjKiRi3Su3CaMhVcKganjKV2kMiEFkQOAd',
		'CWsGTkwV0SqAktusZ9m4dLh3r1IQ693GTSDE7PqOAlj4a',
		'bzWprMjK0w276a7R7MG8GBIZo',
		'u1cIlXJVV6qKWhBgz6M9oHQD54vxEgK84Gs8ONUOSSQC8vK23o')
	api6 = api_node('185893191-Rda2NGInn5l0DzJnjhEh34B2Ay2SdwcpksdFAEeO',
		'ILziqL4ur1SbmAxdt2P7JjXPj3ANfqzYsACIm80rjs4RQ',
		'IbUJOMq7o2MaZ75uUtRwjC31N',
		'Wjx1ebRFuBUsg3fL05tYggJYyNPM7JQxxBBFeWPUFc0GbjkDhl')
	api7 = api_node('185893191-XOfLRaIPpQCuuKWpx055Tv8s0wc7Efc1pkMnGGrt',
		'gF4fsLD7ArJ8wiDndeg5FY5eIFarAwbMfx8Y2lLjRHFVW',
		'61gbQdm84CAJA8t6aPpuX7mnP',
		'U9UBc6umz3GLAbEMRgUJKaf0GW6uLXj8veD50v4A3nWdGydYd3')
	api1.next = api2
	api2.next = api3
	api3.next = api4
	api4.next = api5
	api5.next = api6
	api6.next = api7
	api7.next = api1
	cur_api = api1


def api_reset():
	"""use the next API in linked list"""

	global cur_api, api

	cur_api = cur_api.next
	auth = OAuthHandler(cur_api.consumer_key, cur_api.consumer_secret)
	auth.set_access_token(cur_api.access_token, cur_api.access_token_secret)
	api = tweepy.API(auth)
	time.sleep(10)


def dbConnect():
	"""Connect to database"""

	global db, c

	while True:
		try:
			db=MySQLdb.connect(host=HOST, user=USER, passwd=PASSWD, db=DB)
			c=db.cursor()
			break
		except:
			print("connection failed; reconnecting to db")
			time.sleep(30)


def find_user_email(user):
	"""given a twitter user, find the user's email. return None if no email is found"""

	email = re.search(r'[-0-9a-zA-Z.+_]+@[-0-9a-zA-Z.+_]+\.[a-zA-Z]{2,4}', user.description)

	return email


def user_meet_requirement(user):
	"""return True iff user meets requirement to be inserted into Database"""

	if user.followers_count > MIN_FOL_COUNT:
		return True
	else:
		return False

def user_in_db(user_id):
	"""return True if user has already been inserted into Database"""

	global db, c


	while True:
		try:
			c.execute("SELECT EXISTS(SELECT 1 FROM tw_users WHERE userID='%s')" % (user_id))
			k = c.fetchone()
			if k[0]:
				return True
			else:
				return False
		except Exception as e:
			print(e)
			dbConnect()
	


def insert_user(user, email, keyword):
	"""insert user into database"""

	global db, c

	# Get all the user's info
	screenName = user.screen_name
	name = user.name
	followersCount = user.followers_count
	statusesCount = user.statuses_count
	user_id = user.id_str

	#find user's average favorites/retweets
	(avg_retweet, avg_fav) = findAvgFavRetweet(user_id)

	#insert into database
	try:
		if avg_retweet == -1:
			c.execute("DELETE FROM tw_users WHERE user_id='%s'" % (user_id))
		if user_in_db(user_id):
			c.execute("UPDATE tw_users SET screenName='%s', name='%s', email='%s', emailScraped='%s', followersCount='%s', statusesCount='%s', avgRetweet='%d', avgFav='%d' \
				WHERE screenName='%s'" % (screenName, name, email, time.strftime("%Y-%m-%d", time.gmtime()), followersCount, statusesCount, avg_retweet, avg_fav, screenName))
		else:
			c.execute("INSERT INTO tw_users(screenName, name, email, emailScraped, followersCount, statusesCount, avgRetweet, avgFav, userID) \
				VALUES ('%s','%s','%s','%s','%s','%s','%d','%d','%s')" % (screenName, name, email, time.strftime("%Y-%m-%d", time.gmtime()), followersCount, statusesCount, avg_retweet, avg_fav, user_id))
		c.execute("INSERT IGNORE INTO tw_user_keywords(userID, keyword) \
			VALUES ('%s','%s')" % (user_id, keyword[0]))
		db.commit()
	except Exception as e:
		dbConnect()

def add_new_keywords(user):
	"""add new hashtag into database, given a user.

		check a user's recent tweets, if the tweet has enough favorites, add it into database
	"""
	global db, c

	user_id = user.id

	while True:
		try:
			tweets = api.user_timeline(user_id=user_id, count=10)
			break
		except tweepy.error.TweepError as e:
			if e.reason == "[{u'message': u'Rate limit exceeded', u'code': 88}]":
				api_reset()
			else:
				return

	for tweet in tweets:
		if tweet.favorite_count > MIN_FAV_COUNT:
			for tag in tweet.entities['hashtags']:
				try:
					c.execute("INSERT IGNORE INTO tw_keywords(keyword) VALUES ('%s')" % (tag['text']))
					db.commit()
				except Exception as e:
					dbConnect()


def findAvgFavRetweet(user_id):
	""" find the average favorites/retweets of a user """

	global c,db,api

	td = datetime.timedelta(hours=5)

	while True:
		try:
			tweets1 = api.user_timeline(user_id=user_id, count=20, page=1)
			tweets2 = api.user_timeline(user_id=user_id, count=20, page=2)
			break
		except tweepy.error.TweepError as e:
			if e.reason == "[{u'message': u'Rate limit exceeded', u'code': 88}]":
				api_reset()
			else:
				return (-1,-1)

	retweets_num = []
	favorites_num = []
	status_count = 0

	# Check every recent tweets, and add up the favorites/retweets count
	for status in tweets1:
		today = datetime.datetime.today()
		created_time = status.created_at
		if (today-created_time) >= td:
			retweets_num.append(status.retweet_count)
			favorites_num.append(status.favorite_count)
			status_count += 1

	for status in tweets2:
		today = datetime.datetime.today()
		created_time = status.created_at
		if (today-created_time) >= td:
			retweets_num.append(status.retweet_count)
			favorites_num.append(status.favorite_count)
			status_count += 1

	# Find the averages for retweets and favorites
	if len(retweets_num) == 0:
		avg_retweet = 0
		avg_fav = 0
	elif len(retweets_num) >= 10:
		retweets_num.sort()
		favorites_num.sort()
		r = retweets_num[2:-2]
		f = favorites_num[2:-2]
		avg_retweet = sum(r)/len(r)
		avg_fav = sum(f)/len(f)
	else:
		avg_retweet = sum(retweets_num)/len(retweets_num)
		avg_fav = sum(favorites_num)/len(favorites_num)

	return (avg_retweet, avg_fav)


def get_keywords():
	"""get all the existing keywords from database"""

	global db, c

	while True:
		try:
			c.execute("SELECT * FROM tw_keywords")
			keywords = c.fetchall()
			break
		except Exception as e:
			print(e)
			dbConnect()


	return keywords


def keyword_check_update(keyword, delete):
	"""update the time last updated for a keyword. Delete it instead if delete is True"""
	global db,c

	while True:
		try:
			if delete:
				c.execute("DELETE FROM tw_keywords WHERE keyword='%s'" % (keyword[0]))
				break
			else:
				c.execute("UPDATE tw_keywords SET last_update='%s' WHERE keyword='%s'" % (time.strftime("%Y-%m-%d", time.gmtime()), keyword[0]))
				break
		except Exception as e:
			print(e)
			dbConnect()

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

if __name__ == '__main__':

	#setup API
	api_setup()
	api_reset()


	while True:

		#Setup DB
		dbConnect()

		#get all keywords
		keywords = get_keywords()

		for keyword in keywords:
			# process a keyword only if it has been 2 days since its last checked
			if not keyword_recheck(keyword):
				continue
			counter = 0
			delete = False

			# get 1000 users whose tweets are related to a keyword, and process the users
			# if 10 users in a row do not meet requirement, skip the keyword and move on to the next
			for k in range(1,51):
				while True:
					try:
						users = api.search_users(q=keyword[0], count=20,page=k)
						break
					except tweepy.error.TweepError as e:
						if e.reason == "[{u'message': u'Rate limit exceeded', u'code': 88}]":
							api_reset()
						else:
							print(keyword[0])
							counter = 11
							delete = True
							break
				if not delete:
					for user in users:
						if counter > 10:
							break
						if user_meet_requirement(user):
							counter = 0
							email = find_user_email(user)
							if email:
								insert_user(user, email.group(0), keyword)
							add_new_keywords(user)
						else:
							counter += 1
				if counter > 10:
					break
			keyword_check_update(keyword, delete)

		db.close()
		time.sleep(60)

