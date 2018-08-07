import random
import smtplib
import MySQLdb
from email.mime.text import MIMEText
import time

HOST = "localhost"
USER = "otto"
DB = "shout_out_biz"
PASSWD = "96in236"
sender = 'noreply@shoutour.biz'

def dbConnect():

	global db, c

	while True:
		try:
			db=MySQLdb.connect(host=HOST, user=USER, passwd=PASSWD, db=DB)
			c=db.cursor()
			break
		except:
			print("connection failed; reconnecting to db")
			time.sleep(30)

def sendmail(email, username):
	msg = MIMEText("Hi %s, I have clients interested in buying shoutouts from you. If you could get back to me with pricing by registering on our website below so we can move forward, that would be great.\n \
http://shoutour.biz/members/register/?em=%s \n \
Note: Please don't respond to this email or try to contact us on the website. We don't have time to answer to every request. After registering above, we will send another email when our clients have sent us money." % (username, email))
	
	msg['Subject'] = 'Shoutouts'
	msg['From'] = 'ShoutOur.Biz <noreply@shoutour.biz>'
	msg['To'] = '%s <%s>' %(username, email)
	msg['Reply-To'] = 'noreply@shoutour.biz'
	s = smtplib.SMTP(host='127.0.0.1', port=25, local_hostname='localhost')
	s.sendmail('noreply@shoutour.biz', [email], msg.as_string())
	s.quit()

def main():

	while True:
		dbConnect()
		c.execute("SELECT * FROM ig_users ORDER BY userID")

		users = c.fetchall()
		for user in users:
			emailSent = user[9]
			if emailSent:
				continue
			k = random.randint(0,10)
			if k == 10:
				userID = user[8]
				username = user[0]
				email = user[1]
				c.execute("UPDATE ig_users SET emailSent=1 WHERE userID='%s'" % (userID))
				sendmail(email, username)
				db.commit()
			time.sleep(10)
		db.close()

	# c.execute("SELECT * FROM ig_user_tags WHERE hashtag='%s' ORDER BY frequency DESC" % ('supplement'))
	# user_tags = c.fetchall()

	# for user_tag in user_tags:
	# 	userID = user_tag[0]
	# 	c.execute("SELECT * FROM ig_users WHERE userID='%s'" % (userID))
	# 	user = c.fetchone()
	# 	emailSent = user[9]
	#  	if emailSent:
	#  		continue
	#  	userID = user[8]
	# 	username = user[0]
	# 	email = user[1]
	# 	sendmail(email, username)
	# 	c.execute("UPDATE ig_users SET emailSent=1 WHERE userID='%s'" % (userID))
	# 	db.commit()



if __name__ == '__main__':
	main()

