/* get the assistant from ID */
SELECT *
FROM (
	auth_user a
    LEFT JOIN auth_user_groups b
		ON a.id = b.authuser_id
	LEFT JOIN auth_group c
		ON b.group_id = c.id
) WHERE c.name='assistant' AND a.id=2225;

/**
	Retrieve follower for analysis.

	OLD.
**/
SELECT * 
FROM ig_follower_num_evals t1
RIGHT JOIN (
		SELECT a.id as FOLLOWER_ID, a.username as FOLLOWER_USRNAME, 
			d.username as BASE_USRNAME, d.followers as BASE_NUM_FOLLOWERS
		FROM ig_follower a
		LEFT JOIN ig_users d
		ON d.id = a.following_id
		WHERE a.id NOT IN (
			SELECT ig_follower_id
			FROM ig_follower b 
			RIGHT JOIN ig_follower_rating c 
			ON b.id = c.ig_follower_id
			WHERE c.assistant_id=2230
		)
) t2 
ON t1.ig_follower_id = t2.FOLLOWER_ID
WHERE t1.num_evals < 25
ORDER BY t1.num_evals DESC;

/**
	Retrieve follower for analysis.

	NEW.
*/
SELECT t2.id as FOLLOWER_ID, t2.username as FOLLOWER_USRNAME, 
			t1.username as BASE_USRNAME, t1.followers as BASE_NUM_FOLLOWERS
FROM ig_users t1
RIGHT JOIN (
	SELECT *
	FROM ig_follower a
	WHERE a.id NOT IN (
		SELECT ig_follower_id FROM ig_follower_rating
    )
) t2 
ON t1.id = t2.following_id
ORDER BY t1.followers DESC
LIMIT 1;