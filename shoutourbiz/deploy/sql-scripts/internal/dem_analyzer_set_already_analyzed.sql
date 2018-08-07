/**
	For all rows that have been analyzed,
	set analyzed = 1 and retrieved = 1.
*/

UPDATE (
	SELECT *
	FROM ig_follower
	INNER JOIN ig_follower_rating
		ON ig_follower_rating.ig_follower_id = ig_follower.id
) t1 SET t1.analyzed = 1, t1.retrieved = 1;

/**
	Select followers that have been retrieved, but not yet analyzed.
*/
SELECT * FROM ig_follower WHERE retrieved = 1 AND analyzed = 0;