from instagram.client import InstagramAPI
from instagram.bind import InstagramAPIError, InstagramClientError
import re
import time
import datetime
from random import randint
import MySQLdb
from warnings import filterwarnings
filterwarnings('ignore', category = MySQLdb.Warning)

# PASSWD = "96in236"
# COUNT_PER_CHECK = 50
# MIN_LIKE_COUNT = 500
# MIN_ID = "100000000000000000"
# HOST = "localhost"
# USER = "otto"
# DB = "shout_out_biz"
# min_freq = 500

PASSWD = 'iguser'
COUNT_PER_CHECK = 50
MIN_LIKE_COUNT = 500
MIN_ID = '100000000000000000'
HOST = 'localhost'
USER = 'iguser'
DB = 'igsite'
min_freq = 500

class client_node(object):
	""" used to cycle through various client_id/secret """

	def __init__(self, client_id, client_secret):
		self.api = InstagramAPI(client_id=client_id, client_secret=client_secret)
		self.next = None

	def __unicode__(self):
		return "client_id:%s, client_secret:%s" % (self.id, self.secret)


class IgHashtagException(Exception):
	pass


def apiSetup():
	"""setting up Instagram api"""

	global cur_api

	api1 = client_node('6734eaae10fe44658076019e1942c4f9','f5874c78532c44e7a074626391d4874b')
	api2 = client_node('1a9bb1bf4808428d93cdcf7439e19dc8','8b58055c1ee043eaa3e035751878f3e4')
	api3 = client_node('3e8b94aa253d43319f337633b69ee4d5','6801e6f575c94f54bf0c9a6243b99462')
	api4 = client_node('2c7b5edd3e0542409c1b13a2d0c799e4','b525b9fbffd34936b63c352e9765f0d2')
	api1.next=api2
	api2.next=api3
	api3.next=api4
	api4.next=api1

	cur_api = api1


def dbConnect():
	"""connect to database"""

	global db, c

	while True:
		try:
			db=MySQLdb.connect(host=HOST, user=USER, passwd=PASSWD, db=DB)
			c=db.cursor()
			break
		except:
			print("connection failed; reconnecting to db")
			time.sleep(30)


def newHashtagSetup(hashtag):
	"""setup hashtag in table ig_hashtag_ranges """

	global cur_api,MIN_ID

	# Try retrieving hashtag information from Instagram API (max 5 tries)
	retry = 0
	while True:
		retry += 1
		if retry > 5:
			raise IgHashtagException()
		try:
			media_list, next = cur_api.api.tag_recent_media(count=1, tag_name=hashtag, max_tag_id=0)
			break
		except InstagramAPIError as e:
			print(e)
			if e.status_code == 400:
				raise IgHashtagException()
			else:
				cur_api = cur_api.next
				time.sleep(30)
		except InstagramClientError as e:
			print(e)
			if e.status_code == 502:
				raise IgHashtagException()
			else:
				cur_api = cur_api.next
				time.sleep(30)

	# Insert range of IDs into ig_hashtag_ranges
	max_tag_id=next.split('max_tag_id=')[1]
	while True:
		try:
			c.execute("INSERT INTO ig_hashtag_ranges(hashtag,firstID,lastID) \
					VALUES('%s', '%s', '%s') \
					ON DUPLICATE KEY UPDATE firstID='%s'" % (hashtag, max_tag_id, MIN_ID, max_tag_id))
			break
		except:
			dbConnect()

	return max_tag_id


def search_init(hashtag, max_tag_id, lastID):
	"""repeatedly search and process 25 batches of medias for a hashtag

		search_cond is False if the latest hashtag processed is out of range.
	"""

	global c

	search_cond = (len(max_tag_id) > len(lastID)) or ((len(max_tag_id) == len(lastID)) and max_tag_id > lastID)
	cycle_count = 0

	while search_cond and cycle_count < 25:
		try: #process hashtag repeatedly
			max_tag_id = search_and_add(hashtag, max_tag_id)
			search_cond = (len(max_tag_id) > len(lastID)) or ((len(max_tag_id) == len(lastID)) and max_tag_id > lastID)
			cycle_count += 1
		except InstagramAPIError as e:
			print(e)
			if e.status_code == 400:
				raise IgHashtagException()
			else:
				cur_api = cur_api.next
				time.sleep(30)
		except InstagramClientError as e:
			print(e)
			if e.status_code == 502:
				raise IgHashtagException()
			else:
				cur_api = cur_api.next
				time.sleep(30)

	return (search_cond, max_tag_id)


def update_range(hashtag, tag_range):
	"""update range in ig_hashtag_ranges for hashtag to the most recent medias"""

	global cur_api

	firstID = tag_range[1]

	# Retrieve the most recent media_id
	while True:
		try:
			media_list, next = cur_api.api.tag_recent_media(count=1, tag_name=hashtag, max_tag_id=0)
			break
		except InstagramAPIError as e:
			print(e)
			if e.status_code == 400:
				raise IgHashtagException()
			else:
				cur_api = cur_api.next
				time.sleep(30)
		except InstagramClientError as e:
			print(e)
			if e.status_code == 502:
				raise IgHashtagException()
			else:
				cur_api = cur_api.next
				time.sleep(30)

	max_tag_id=next.split('max_tag_id=')[1]

	# Update firstID to the most recent media_id, and lastID to the firstID in previous ranges.
	c.execute("UPDATE ig_hashtag_ranges SET firstID='%s',lastID='%s' WHERE hashtag='%s'" % (max_tag_id, firstID, hashtag))

	return max_tag_id


def process_hashtag(row):
	""" Input: a row from table ig_hashtags, which represents a hashtag

		Process the hashtag:
		1. Setup ig_hashtag_ranges if hashtag has never been processed
		2. retreive range for hashtag to be processed
		3. search hashtag in API, and process hashtag accordinly
		4. Update range after processing hashtag if last_img_id is not within range
		5. Update last_img_id
	"""

	global db, c

	hashtag = row[0]
	max_tag_id = row[1]

	#if it's the first time this hashtag is checked, do an initital setup.
	if max_tag_id == '0':
		try:
			max_tag_id = newHashtagSetup(hashtag)
		except IgHashtagException: #if hashtag cannot be setup, it's problematic, so delete and move on
			c.execute("DELETE FROM ig_hashtags WHERE hashtag='%s'" % (hashtag))
			c.execute("DELETE FROM ig_hashtag_ranges WHERE hashtag='%s'" % (hashtag))
			return

	#get the ranges of the hashtag
	while True:
		try:
			c.execute("SELECT * FROM ig_hashtag_ranges WHERE hashtag='%s' LIMIT 1" % (hashtag))
			tag_range = c.fetchone()
			lastID = tag_range[2]
			break
		except IndexError as e:
			newHashtagSetup(hashtag)
		except:
			dbConnect()
			while True:
				try:
					c.execute("INSERT INTO ig_hashtag_ranges(hashtag,firstID,lastID) \
							VALUES('%s', '%s', '%s') \
							ON DUPLICATE KEY UPDATE firstID='%s'" % (hashtag, max_tag_id, MIN_ID, max_tag_id))
					break
				except:
					dbConnect()

	# search hashtag in Instagram API, and process each media accordingly
	try:
		(inRange, max_tag_id) = search_init(hashtag, max_tag_id, lastID)
	except IgHashtagException:
		c.execute("DELETE FROM ig_hashtags WHERE hashtag='%s'" % (hashtag))
		c.execute("DELETE FROM ig_hashtag_ranges WHERE hashtag='%s'" % (hashtag))
		return

	# hashtag range runs out; need to update range
	if not inRange:
		while True:
			try:
				max_tag_id = update_range(hashtag, tag_range)
				break
			except IgHashtagException:
				c.execute("DELETE FROM ig_hashtags WHERE hashtag='%s'" % (hashtag))
				c.execute("DELETE FROM ig_hashtag_ranges WHERE hashtag='%s'" % (hashtag))
				return
	
	#update last_img_id
	while True: 
		try:
			c.execute("UPDATE ig_hashtags SET last_img_id='%s' WHERE hashtag='%s'" % (max_tag_id, hashtag))
			break
		except Exception as e:
			dbConnect()

	while True:
		try:
			db.commit()
			break
		except Exception as e:
				print(e)
				dbConnect()

	return


def fetch_new_list(hashtag, max_tag):
	"""get a batch of media, given the hashtag and max_tag

		returns the list of medias, and the ID of the next media to be searched
	"""

	global cur_api

	while True:
		try:
			media_list, next = cur_api.api.tag_recent_media(count=COUNT_PER_CHECK, tag_name=hashtag, max_tag_id=max_tag)
			break
		except InstagramAPIError as e:
			print(e)
			if e.status_code == 400:
				raise
			else:
				print("api.tag_recent_media: tag_name=%s, max_tag_id=%s" % (hashtag,max_tag))
				cur_api=cur_api.next
				time.sleep(30)
		except InstagramClientError as e:
			print(e)
			if e.status_code == 502:
				raise
		except:
			print("using new api")
			cur_api = cur_api.next
			time.sleep(30)

	return (media_list, next)

def link_hashtag(hashtag, tag_links):
	"""create/update link between hashtag in ig_hashtags_link"""
	
	global c, db

	try:
		for tag in tag_links:
			if tag.name != hashtag:
				c.execute("SELECT * FROM ig_hashtags_link WHERE hashtag1='%s' AND hashtag2='%s' LIMIT 1" % (hashtag, tag.name))
				db_hashtag = c.fetchone()
				if not db_hashtag:
					c.execute("SELECT * FROM ig_hashtags_link WHERE hashtag1='%s' AND hashtag2='%s' LIMIT 1" % (tag.name, hashtag))
					db_hashtag = c.fetchone()
					if not db_hashtag:
						c.execute("INSERT IGNORE INTO ig_hashtags_link(hashtag1,hashtag2,frequency) VALUES('%s', '%s', '%s')" % (hashtag, tag.name, 1))
						continue
					else:
						c.execute("UPDATE ig_hashtags_link SET frequency=frequency + 1 WHERE hashtag1='%s' AND hashtag2='%s'" % (tag.name, hashtag))
				else:
					c.execute("UPDATE ig_hashtags_link SET frequency=frequency + 1 WHERE hashtag1='%s' AND hashtag2='%s'" % (hashtag, tag.name))
				if int(db_hashtag[2]) > min_freq: #remember to change min_freq in view.py (class search)
					c.execute("INSERT IGNORE INTO ig_hashtags(hashtag) VALUES('%s')" % (tag.name))
			db.commit()
	except Exception as e:
		try:
			db.rollback()
		except:	
			dbConnect()


def get_user(user_id):
	"""retrieve user, given its user_id"""

	global cur_api

	while True:
		try:
			user = cur_api.api.user(user_id)
			break
		except:
			cur_api = cur_api.next
			print("api.user: user_id=%s" % (user_id))
			time.sleep(30)

	return user

def search_and_add(hashtag,max_tag):
	"""Search media with hashtag with given max_tag number. Add media's user if the media meets condition."""

	global cur_api

	try:
		(media_list, next) = fetch_new_list(hashtag, max_tag)
	except:
		raise

	if next == None:
		return max_tag
	
	max_tag=next.split('max_tag_id=')[1]
	for media in media_list:
		if (media.like_count >= MIN_LIKE_COUNT):
			#first, link hashtags
			try:
				link_hashtag(hashtag, media.tags)
			except AttributeError as e:
				#this runs if the media has no tags
				pass

			#get the owner of media
			user = get_user(media.user.id)

			#find whether or not there is email in his bio
			email = re.search(r'[-0-9a-zA-Z.+_]+@[-0-9a-zA-Z.+_]+\.[a-zA-Z]{2,4}', user.bio)

			#if there is email
			if email:
				try:
					username = user.username
					userID = user.id
					try: #find average like of the user
						avgLike = findAvgLike(userID)
					except IgHashtagException:
						continue
					#add/update user to ig_users
					c.execute("SELECT * FROM ig_users WHERE userID='%s' LIMIT 1" % (userID))
					db_user = c.fetchone()
					if not db_user:
						c.execute("INSERT INTO ig_users(username, email, followers, emailScraped, postCount, postAvgLike, userID) \
									VALUES('%s', '%s', '%d', '%s', '%d', '%d', '%s')" % (username, email.group(0), \
									user.counts["followed_by"], time.strftime("%Y-%m-%d", time.gmtime()), \
									user.counts["media"], avgLike, userID))
					else:
						c.execute("UPDATE ig_users SET username='%s',email='%s',followers='%d',emailScraped='%s',postCount='%d', postAvgLike='%d' WHERE userID='%s'" \
							% (username, email.group(0), user.counts["followed_by"], time.strftime("%Y-%m-%d", time.gmtime()), user.counts["media"], avgLike, userID))

					#add/update ig_user_tags
					c.execute("SELECT * FROM ig_user_tags WHERE userID='%s' AND hashtag='%s' LIMIT 1" % (userID, hashtag))
					db_user_tag  = c.fetchone()
					if not db_user_tag:
						c.execute("INSERT INTO ig_user_tags(userID,hashtag,frequency) \
						VALUES('%s', '%s', '%d')" % (userID, hashtag, 1))
					else:
						c.execute("UPDATE ig_user_tags SET frequency=frequency + 1 \
							WHERE userID='%s' AND hashtag='%s'" % (userID, hashtag))
					db.commit()
				except:
					try:
						db.rollback()
					except:
						dbConnect()	
								
	return max_tag


def findAvgLike(user_id):
	"""returns the average like of an Instagram user, given its user_id"""

	global cur_api, db,c

	td = datetime.timedelta(days=1)
	today = datetime.datetime.today()

	# retrieve the 30 most recent medias posted by the user
	while True:
		try:
			(user_media, pag) = cur_api.api.user_recent_media(user_id=user_id, count=30)
			break
		except InstagramAPIError as e:
			print(e)
			if e.status_code == 400:
				raise IgHashtagException()
			else:
				cur_api = cur_api.next
				time.sleep(30)
		except InstagramClientError as e:
			print(e)
			if e.status_code == 502:
				raise IgHashtagException()
			else:
				cur_api = cur_api.next
				time.sleep(30)

	# Check each media, and add them into a list if they are over 1 day old
	media_num = 0
	like_num = []
	for media in user_media:
		created_time = media.created_time
		if (today-created_time) >= td:
			like_num.append(media.like_count)
			media_num += 1

	# find the average like
	if len(like_num) == 0:
		avg_like = 0
	elif len(like_num) >= 10:
		like_num.sort()
		l = like_num[1:-1]
		avg_like = sum(l)/len(l)
	else:
		avg_like = sum(like_num)/len(like_num)

	return avg_like



def main():

	global cur_api, db, c

	# Instagram API is setup
	apiSetup()

	# retrieve all hashtags from database, then process each one.
	while True:
		dbConnect()
		c.execute("SELECT * FROM ig_hashtags")
		rows = c.fetchall()
		for row in rows:
			process_hashtag(row)

		while True:
			try:
				db.close()
				break
			except Exception as e:
					print(e)
					dbConnect()	


if __name__ == '__main__':
	main()
