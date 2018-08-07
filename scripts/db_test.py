import MySQLdb

user = 'root'
db = 'empty'
host = 'localhost'
pas = 'mysql'
db = MySQLdb.connect(user=user, db=db, host=host, passwd=pas)
c = db.cursor()
c.execute('DROP PROCEDURE IF EXISTS add_version_to_actor;')
# c.execute("""
# CREATE DEFINER=CURRENT_USER PROCEDURE add_version_to_actor ( )
# BEGIN
# DECLARE colName TEXT;
# SELECT column_name INTO colName
# FROM information_schema.columns
# WHERE table_schema = 'empty'
#     AND table_name = 'auth_user_groups'
# AND column_name = 'user_id';
# IF colName is NULL THEN
#     ALTER TABLE `auth_user_groups` CHANGE `user_id` `authuser_id` INTEGER NOT NULL;
# END IF;
# END
# """)
# c.execute('CALL add_version_to_actor;')
print c.fetchone()