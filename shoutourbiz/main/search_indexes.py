import datetime

from haystack import indexes
from main.models import IgUsers, TwUsers, VerifiedUserAccounts, IgHashtags, TwKeywords
from main.utils_helper import calculate_engagement_stats_2, calculate_engagement_stats_for_verified_users

class IgUsersIndex(indexes.SearchIndex, indexes.Indexable):
	text = indexes.CharField(document=True)
	username = indexes.CharField(model_attr='username')
	followers = indexes.IntegerField(model_attr='followers')
	email = indexes.CharField(model_attr='email')
	userid = indexes.CharField(model_attr='userid')
	verified = indexes.IntegerField()
	iid = indexes.IntegerField()
	cpm = indexes.FloatField()
	network = indexes.CharField()
	engagement = indexes.FloatField()

	def get_model(self):
		return IgUsers

	def prepare_text(self, obj):
	 	return [niche.hashtag for niche in obj.igusertags_set.all()]

	def prepare_verified(self, obj):
		verified_acc = VerifiedUserAccounts.objects.filter(account_id=obj.id, network='ig')
		exists = verified_acc.exists()

		if exists:
			return 1
		else:
			return 0

	def prepare_iid(self, obj):
		return obj.pk

	def prepare_cpm(self, obj):
		verified_acc = VerifiedUserAccounts.objects.filter(account_id=obj.id, network='ig')
		exists = verified_acc.exists()

		if exists:
			return verified_acc.first().cpm
		else:
			return -1

	def prepare_engagement(self, obj):
		return calculate_engagement_stats_2(obj)

	def prepare_network(self, obj):
		return 'ig'

class TwUsersIndex(indexes.SearchIndex, indexes.Indexable):
	text = indexes.CharField(document=True)
	username = indexes.CharField(model_attr='username')
	email = indexes.CharField(model_attr='email')
	followers = indexes.IntegerField(model_attr='followers')
	statusescount = indexes.IntegerField(model_attr='statusescount')
	avgretweet = indexes.IntegerField(model_attr='avgretweet')
	avgfav = indexes.IntegerField(model_attr='avgfav')
	userid = indexes.CharField(model_attr='userid')
	verified = indexes.IntegerField()
	iid = indexes.IntegerField()
	cpm = indexes.FloatField()
	network = indexes.CharField()

	def get_model(self):
		return TwUsers

	def prepare_text(self, obj):
	 	return [niche.keyword for niche in obj.twuserkeywords_set.all()]

	def prepare_verified(self, obj):
		verified_acc = VerifiedUserAccounts.objects.filter(account_id=obj.id, network='tw').exists()
		if verified_acc:
			return 1
		else:
			return 0

	def prepare_iid(self, obj):
		return obj.pk

	def prepare_cpm(self, obj):
		verified_acc = VerifiedUserAccounts.objects.filter(account_id=obj.id, network='tw')
		exists = verified_acc.exists()

		if exists:
			return verified_acc.first().cpm
		else:
			return -1

	def prepare_network(self, obj):
		return 'tw'

class VerifiedUserAccountsIndex(indexes.SearchIndex, indexes.Indexable):
	text = indexes.CharField(document=True)
	username = indexes.CharField()
	email = indexes.CharField(model_attr='email')
	network = indexes.CharField(model_attr='network')
	account_id = indexes.IntegerField(model_attr='account_id')
	price = indexes.DecimalField(model_attr='price')
	cpm = indexes.FloatField(model_attr='cpm')
	followers = indexes.IntegerField()
	verified = indexes.IntegerField()
	iid = indexes.IntegerField()
	engagement = indexes.FloatField()

	def get_model(self):
		return VerifiedUserAccounts

	def prepare_text(self, obj):
		return [niche.niche for niche in obj.niches.all()]

	def prepare_followers(self, obj):

		try:
			if obj.network == 'ig':
				ig_user = IgUsers.objects.filter(id=obj.account_id)
				if ig_user.exists():
					return ig_user.first().followers
			elif obj.network == 'tw':
				tw_user = TwUsers.objects.filter(id=obj.account_id)
				if tw_user.exists():
					return tw_user.first().followers
		except Exception as e:
			return -1

	def prepare_verified(self, obj):
		return 1

	def prepare_iid(self, obj):
		return obj.account_id

	def prepare_username(self, obj):

		try:

			if obj.network == 'ig':
				ig_user = IgUsers.objects.filter(id=obj.account_id)
				if ig_user.exists():
					return ig_user.first().username
			elif obj.network == 'tw':
				tw_user = TwUsers.objects.filter(id=obj.account_id)
				if tw_user.exists():
					return tw_user.first().username

		except Exception as e:
			print e
			return None

	def prepare_engagement(self, obj):
		return calculate_engagement_stats_for_verified_users(obj)

class IgHashtagsIndex(indexes.SearchIndex, indexes.Indexable):
	text = indexes.EdgeNgramField(document=True, model_attr='hashtag')

	def get_model(self):
		return IgHashtags
	
class TwKeywordsIndex(indexes.SearchIndex, indexes.Indexable):
	text = indexes.EdgeNgramField(document=True, model_attr='keyword')

	def get_model(self):
		return TwKeywords