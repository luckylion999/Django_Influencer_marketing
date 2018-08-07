from itertools import chain

from django.shortcuts import render, redirect
from django.contrib.auth.models import Group, Permission
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.contrib import auth

from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache

from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages

from django.http import HttpResponseForbidden, JsonResponse
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied

from django.http import Http404, HttpResponseNotFound
from django.forms.models import model_to_dict
from django.db.models import Avg

from main.forms import LoginForm, RegistrationForm
from main.models import AuthUser, IgFollower, VerifiedUserAccounts, \
	VerifiedUserNiches, IgUsers, TwUsers, IgUserTags, TwUserKeywords, BuyerCredits, UnlockedUsers
from main.decorators import ajax_required
from main import permissions

from internal.models import IgFollowerRating

import random

from . import models
from . import utils
from . import forms

from internal import utils as analyzer_utils

# audience stats available only for instagram users
@ajax_required
def age_group_chart(request, uid):

	ig_user = IgUsers.objects.filter(id=uid).first()
	if not ig_user:
		return JsonResponse({'status': 404, 'mssg': 'User could not be found'})

	ratings = utils.retrieve_follower_ratings_given_ig_user(ig_user)

	if not ratings:
		age_group_stats = None
	else:
		# age group stats
		age_group_stats = utils.calculate_age_group_stats(ratings)

	ig_user_dict = model_to_dict(ig_user)
	if permissions.is_external_user(request.user):
		ig_user_dict['username'] = '*' * len(ig_user_dict['username'])
		ig_user_dict['email'] = '*' * len(ig_user_dict['email'])
		ig_user_dict['userid'] = '*' * len(ig_user_dict['userid'])

	# is_auth_user is always set to True for now
	# this is a patch, and it will be changed back later
	is_auth_user = True

	# if not request.user.is_authenticated():
	# 	is_auth_user = False
	# else:
	# 	is_auth_user = True

	return JsonResponse({
		'is_auth_user': is_auth_user,
		'status': 200,
		'ig_user': ig_user_dict,
		'age_group_stats': age_group_stats,
	})

@ajax_required
def engagement_chart(request, uid):

	ig_user = IgUsers.objects.filter(id=uid).first()
	average_engagement = IgUsers.objects.all().aggregate(Avg('engagement'))['engagement__avg']
	if not ig_user:
		return JsonResponse({'status': 404, 'mssg': 'User could not be found'})

	# engagement stats
	engagement_stats = utils.calculate_engagement_stats(ig_user)

	ig_user_dict = model_to_dict(ig_user)
	if permissions.is_external_user(request.user):
		ig_user_dict['username'] = '*' * len(ig_user_dict['username'])
		ig_user_dict['email'] = '*' * len(ig_user_dict['email'])
		ig_user_dict['userid'] = '*' * len(ig_user_dict['userid'])

	# is_auth_user is always set to True for now
	# this is a patch, and it will be changed back later
	is_auth_user = True

	# if not request.user.is_authenticated():
	# 	is_auth_user = False
	# else:
	# 	is_auth_user = True

	return JsonResponse({
		'is_auth_user': is_auth_user,
		'status': 200,
		'ig_user': ig_user_dict,
		'average_engagement': average_engagement,
		'engagement_stats': engagement_stats,
	})

def randomize_info(info):
	"""
	Method to randomize information (username/email) for safety reasons.
	"""

	return ''.join(random.sample(info,len(info)))

@ajax_required
def gender_chart(request, uid):

	ig_user = IgUsers.objects.filter(id=uid).first()
	if not ig_user:
		return JsonResponse({'status': 404, 'mssg': 'User could not be found'})
	
	ratings = utils.retrieve_follower_ratings_given_ig_user(ig_user)
	# gender stats
	gender_stats = utils.calculate_gender_stats(ratings)

	ig_user_dict = model_to_dict(ig_user)
	if permissions.is_external_user(request.user):
		ig_user_dict['username'] = '*' * len(ig_user_dict['username'])
		ig_user_dict['email'] = '*' * len(ig_user_dict['email'])
		ig_user_dict['userid'] = '*' * len(ig_user_dict['userid'])

	# is_auth_user is always set to True for now
	# this is a patch, and it will be changed back later
	is_auth_user = True

	# if not request.user.is_authenticated():
	# 	is_auth_user = False
	# else:
	# 	is_auth_user = True

	return JsonResponse({
		'is_auth_user': is_auth_user,
		'status': 200,
		'ig_user': ig_user_dict,
		'gender_stats': gender_stats,
	})

@ajax_required
def trends_chart(request, network, uid):

	if network == 'ig':
		user = IgUsers.objects.filter(id=uid).first()
	elif network == 'tw':
		user = TwUsers.objects.filter(id=uid).first()

	if not user:
		return JsonResponse({'status': 404, 'mssg': 'User could not be found'})

	verified_acc = VerifiedUserAccounts.objects.filter(network=network, account_id=uid).first()
	if verified_acc:
		niches = verified_acc.niches.all() or None
	else:
		if network == 'ig':
			niches = user.igusertags_set.all() or None
		elif network == 'tw':
			niches = user.twuserkeywords_set.all() or None

	user_dict = model_to_dict(user)
	if permissions.is_external_user(request.user):
		user_dict['username'] = '*' * len(user_dict['username'])
		user_dict['email'] = '*' * len(user_dict['email'])
		user_dict['userid'] = '*' * len(user_dict['userid'])

	# trends stats
	(trends_headers, trends_values) = utils.calculate_interest_over_time(request.user, user, niches, network)

	# is_auth_user is always set to True for now
	# this is a patch, and it will be changed back later
	is_auth_user = True

	# if not request.user.is_authenticated():
	# 	is_auth_user = False
	# else:
	# 	is_auth_user = True

	return JsonResponse({
		'is_auth_user': is_auth_user,
		'status': 200,
		'user': user_dict,
		'trends_headers': trends_headers,
		'trends_values': trends_values,
	})

@ajax_required
def country_chart(request, uid):

	ig_user = IgUsers.objects.filter(id=uid).first()
	if not ig_user:
		return JsonResponse({'status': 404, 'mssg': 'User could not be found'})

	ratings = utils.retrieve_follower_ratings_given_ig_user(ig_user)
	# country stats
	country_stats = utils.calculate_country_stats(ratings)

	ig_user_dict = model_to_dict(ig_user)
	if permissions.is_external_user(request.user):
		ig_user_dict['username'] = '*' * len(ig_user_dict['username'])
		ig_user_dict['email'] = '*' * len(ig_user_dict['email'])
		ig_user_dict['userid'] = '*' * len(ig_user_dict['userid'])

	# is_auth_user is always set to True for now
	# this is a patch, and it will be changed back later
	is_auth_user = True

	# if not request.user.is_authenticated():
	# 	is_auth_user = False
	# else:
	# 	is_auth_user = True

	return JsonResponse({
		'is_auth_user': is_auth_user,
		'status': 200,
		'ig_user': ig_user_dict,
		'country_stats': country_stats,
	})

@ajax_required
def followers_trend_chart(request, uid):

	ig_user = IgUsers.objects.filter(id=uid).first()
	if not ig_user:
		return JsonResponse({'status': 404, 'mssg': 'User could not be found'})

	followers_trend_stats = utils.calculate_followers_stats(ig_user)

	ig_user_dict = model_to_dict(ig_user)
	if permissions.is_external_user(request.user):
		ig_user_dict['username'] = '*' * len(ig_user_dict['username'])
		ig_user_dict['email'] = '*' * len(ig_user_dict['email'])
		ig_user_dict['userid'] = '*' * len(ig_user_dict['userid'])
	
	# is_auth_user is always set to True for now
	# this is a patch, and it will be changed back later
	is_auth_user = True
	
	# if not request.user.is_authenticated():
	# 	is_auth_user = False
	# else:
	# 	is_auth_user = True

	return JsonResponse({
		'is_auth_user': is_auth_user,
		'status': 200,
		'ig_user': ig_user_dict,
		'followers_trend_stats': followers_trend_stats,
	})

@ajax_required
def get_ig_profile_pic(request, uid):

	try:
		ig_user = IgUsers.objects.get(id=uid)
	except IgUser.DoesNotExist:
		return JsonResponse({'status': 404, 'mssg': 'User not found.'})

	if not permissions.is_unlocked_by_buyer(request.user, ig_user, 'ig') and not (request.user.is_superuser or permissions.is_assistant(request.user)):
		return JsonResponse({'status': 200, 'profile_pic_url': static('img/unknown.png')})

	profile_pic_url = utils.IgProfileParser(uid, ig_user).quick_scrape_ig_profile_picture()
	
	return JsonResponse({
		'status': 200,
		'profile_pic_url': profile_pic_url,
	})

def influencer_details(request, network, uid):

	has_previous = request.GET.get('prev')

	has_network = []
	if network == 'ig':
		has_network.append('ig')
	elif network == 'tw':
		has_network.append('tw')
	else:
		raise PermissionDenied()

	ig_user = tw_user = None

	# get user
	if 'ig' in has_network:
		ig_user = IgUsers.objects.filter(id=uid).first()

		if ig_user and ig_user.related_accs_scraped:
			tw_user = TwUsers.objects.filter(username=ig_user.username).first()
			if tw_user:
				has_network.append('tw')
		else:
			tw_user = None

	else:
		tw_user = TwUsers.objects.filter(id=uid).first()
		if tw_user:
			ig_user = IgUsers.objects.filter(username=tw_user.username).first()
			if ig_user:
				has_network.append('ig')
		else:
			ig_user = None

	if ig_user is None and tw_user is None:
		return HttpResponseNotFound('<h3>Account not found. It does not exist or has been removed.</h3>')

	# key interests
	ig_niches = tw_niches = None
	ig_verified_acc = tw_verified_acc = None
	if 'ig' in has_network:
		ig_verified_acc = VerifiedUserAccounts.objects.filter(network='ig', account_id=ig_user.id).first()
		if ig_verified_acc:
			ig_niches = ig_verified_acc.niches.all() or None
		else:
			ig_niches = ig_user.igusertags_set.all()

	if 'tw' in has_network:
		tw_verified_acc = VerifiedUserAccounts.objects.filter(network='tw', account_id=tw_user.id).first()
		if tw_verified_acc:
			tw_niches = tw_verified_acc.niches.all() or None
		else:
			tw_niches = tw_user.twuserkeywords_set.all()

	# username
	randomized_email = ""
	if ig_user:
		username = ig_user.username
		randomized_email = randomize_info(ig_user.email)
	else:
		username = tw_user.username
		randomized_email = randomize_info(tw_user.email)
	randomized_username = randomize_info(username)
	
	# is assistant
	if request.user.groups.filter(name='assistant').exists():
		is_assistant = True
	else:
		is_assistant = False

	# cpm
	ig_cpm = tw_cpm = None
	if ig_verified_acc:
		ig_cpm = ig_verified_acc.cpm
	if tw_verified_acc:
		tw_cpm = tw_verified_acc.cpm

	# verified
	if ig_verified_acc or tw_verified_acc:
		is_verified = True
	else:
		is_verified = False

	context = {
		'uid': uid,
		'network': network,
		'ig_user': ig_user,
		'ig_verified_acc': ig_verified_acc,
		'tw_user': tw_user,
		'tw_verified_acc': tw_verified_acc,
		'ig_niches': ig_niches,
		'tw_niches': tw_niches,
		'username': username,
		'is_assistant': is_assistant,
		'ig_cpm': ig_cpm,
		'tw_cpm': tw_cpm,
		'has_previous': has_previous,
		'is_verified': is_verified,
		'randomized_username': randomized_username,
		'randomized_email': randomized_email,
	}

	if request.user.groups.filter(name='buyer').exists():
		auth_user_id = request.user.id
		if BuyerCredits.objects.filter(buyer_id=auth_user_id).exists():
			credit_user = BuyerCredits.objects.get(buyer_id=auth_user_id)
			credits = credit_user.buyer_credits
			if int(credits) != 0:
				out_of_credits = False
			else:
				out_of_credits = True

			if UnlockedUsers.objects.filter(buyer_id=auth_user_id, user_id=uid, network=network).exists():
				is_credit_user = True
			else:
				is_credit_user = False
		else:
			credits = 0
			is_credit_user = False
			out_of_credits = True

		# username
		randomized_email = ""
		if ig_user:
			username = ig_user.username
			randomized_email = randomize_info(ig_user.email)
		else:
			username = tw_user.username
			randomized_email = randomize_info(tw_user.email)
		randomized_username = randomize_info(username)

		context = {
			'uid': uid,
			'out_of_credits': out_of_credits,
			'is_credit_user': is_credit_user,
			'network': network,
			'ig_user': ig_user,
			'ig_verified_acc': ig_verified_acc,
			'tw_user': tw_user,
			'tw_verified_acc': tw_verified_acc,
			'ig_niches': ig_niches,
			'tw_niches': tw_niches,
			'username': username,
			'is_assistant': is_assistant,
			'ig_cpm': ig_cpm,
			'tw_cpm': tw_cpm,
			'has_previous': has_previous,
			'is_verified': is_verified,
			'credits': credits,
			'randomized_username': randomized_username,
			'randomized_email': randomized_email,
		}
		return render(request, 'profiles_page.html', context)
	else:
		return render(request, 'profiles_page.html', context)

def unlock_influencer(request, network, uid):

	has_previous = request.GET.get('prev')

	has_network = []
	if network == 'ig':
		has_network.append('ig')
	elif network == 'tw':
		has_network.append('tw')
	else:
		raise PermissionDenied()

	ig_user = tw_user = None

	# get user
	if 'ig' in has_network:
		ig_user = IgUsers.objects.filter(id=uid).first()

		if '@' in ig_user.username:
			ig_user.username = ig_user.username.replace('@', '')

		if ig_user and ig_user.related_accs_scraped:
			tw_user = TwUsers.objects.filter(username=ig_user.username).first()
			if tw_user:
				has_network.append('tw')
		else:
			tw_user = None
	else:
		tw_user = TwUsers.objects.filter(id=uid).first()
		if tw_user:
			ig_user = IgUsers.objects.filter(username=tw_user.username).first()
			if ig_user:
				has_network.append('ig')
		else:
			ig_user = None

	# key interests
	ig_niches = tw_niches = None
	ig_verified_acc = tw_verified_acc = None
	if 'ig' in has_network:
		ig_verified_acc = VerifiedUserAccounts.objects.filter(network='ig', email=ig_user.email).first()
		if ig_verified_acc and ig_verified_acc.niches.all().exists():
			ig_niches = ig_verified_acc.niches.all() or None
		else:
			ig_niches = ig_user.igusertags_set.all()

	if 'tw' in has_network:
		tw_verified_acc = VerifiedUserAccounts.objects.filter(network='tw', email=tw_user.email).first()
		if tw_verified_acc and tw_verified_acc.niches.all().exists():
			tw_niches = tw_verified_acc.niches.all() or None
		else:
			tw_niches = tw_user.twuserkeywords_set.all()

	# username
	if ig_user:
		username = ig_user.username
	else:
		username = tw_user.username

	# is assistant
	if request.user.groups.filter(name='assistant').exists():
		is_assistant = True
	else:
		is_assistant = False

	# cpm
	ig_cpm = tw_cpm = None
	if ig_verified_acc:
		ig_cpm = ig_verified_acc.cpm
	if tw_verified_acc:
		tw_cpm = tw_verified_acc.cpm

	# verified
	if ig_verified_acc or tw_verified_acc:
		is_verified = True
	else:
		is_verified = False

	auth_user_id = request.user.id
	credit_user = BuyerCredits.objects.get(buyer_id=auth_user_id)
	if credit_user.buyer_credits != 0 and credit_user.buyer_credits > 0:
		if not UnlockedUsers.objects.filter(buyer_id=auth_user_id, user_id=uid, network=network).exists():
			credit_user.buyer_credits = int(credit_user.buyer_credits) - 1
			credits = credit_user.buyer_credits
			BuyerCredits.objects.filter(buyer_id=auth_user_id).update(buyer_credits=credits)

			UnlockedUsers.objects.create(buyer_id=auth_user_id, user_id=uid, network=network )
			is_credit_user = True
		else:
			credits = credit_user.buyer_credits
			is_credit_user = True

	else:
		credits = 0
		is_credit_user = False
	context = {
		'uid': uid,
		'network': network,
		'ig_user': ig_user,
		'ig_verified_acc': ig_verified_acc,
		'tw_user': tw_user,
		'tw_verified_acc': tw_verified_acc,
		'ig_niches': ig_niches,
		'tw_niches': tw_niches,
		'username': username,
		'is_assistant': is_assistant,
		'ig_cpm': ig_cpm,
		'tw_cpm': tw_cpm,
		'is_verified': is_verified,
		'has_previous': has_previous,
		'credits': credits,
		'is_credit_user': is_credit_user
	}
	return render(request, 'profiles_page.html', context)
