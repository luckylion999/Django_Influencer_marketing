/**
	Generate report to see all influencers which
	have been analyzed.
*/
SELECT
    t3.id as influencer_id, t3.username as influencer_username,
    t3.followers as influencer_followers,
    COUNT(t3.id) as num_followers_evaluated
FROM ig_follower_rating t1
INNER JOIN ig_follower t2
	ON t1.ig_follower_id = t2.id
INNER JOIN ig_users t3
	ON t2.following_id = t3.id
INNER JOIN auth_user t4
	ON t1.assistant_id = t4.id
GROUP BY influencer_id, influencer_username, influencer_followers;