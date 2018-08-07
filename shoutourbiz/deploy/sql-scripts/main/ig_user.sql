/**
	Deletes an IgUsers record.
*/
DELETE FROM ig_follower_rating WHERE ig_follower_id IN (
	SELECT id FROM ig_follower WHERE following_id = <ID>
);
DELETE FROM ig_follower WHERE following_id = <ID>;
DELETE FROM ig_user_tags WHERE iguser_id = <ID>;
DELETE FROM ig_follower_trend WHERE ig_user_id = <ID>;
DELETE FROM ig_users WHERE id = <ID>;
/**
	Deletes an TwUsers record.
*/
DELETE FROM tw_user_keywords WHERE twuser_id >= 5000;
DELETE FROM tw_users WHERE id >= 5000;
/**
	Select all IgUsers that have '@' in the username
*/
SELECT a.id,a.username,a.email,a.followers, b.id,b.username,b.email,b.followers
FROM ig_users a
INNER JOIN ig_users b ON REPLACE(a.username, '@', '') = b.username
WHERE a.username LIKE '@%';
/**
	Delete all IgUsers that have '@' in the username
*/
SELECT * FROM ig_users WHERE username LIKE '@%';
DELETE FROM ig_users WHERE username LIKE '@%';
