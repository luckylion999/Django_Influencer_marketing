from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import auth, sessions
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden,\
	JsonResponse, Http404
from django.contrib.auth import views, get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
import MySQLdb
from django.conf import settings
from copy import copy
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from django.core.mail import EmailMessage
import urllib, urllib2
from django.core.urlresolvers import resolve, reverse
import json
import time
import datetime
from instagram.client import InstagramAPI
from instagram.bind import InstagramAPIError, InstagramClientError
import tweepy
from tweepy import OAuthHandler
import smtplib
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

from django.views.generic.base import TemplateView, View
from django.views.generic.detail import BaseDetailView

from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import requests
from django.contrib import messages
from .decorators import ajax_required
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from itertools import chain
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth import views as auth_views
from django.core.exceptions import ObjectDoesNotExist
import hashlib
from django.utils import timezone
from decimal import Decimal
import operator

from haystack.query import SearchQuerySet

from . import mixins
from . import utils
from .models import *
from .tasks import main_process
from .tasks_ipn import add_subscription
from .forms import RegistrationForm, SellerRegistrationForm, NewAccountForm,\
	EditAccountForm, IgSearchForm, TwSearchForm, LoginForm

import logging
logger = logging.getLogger(__name__)

def is_seller(user):
	if user.groups.filter(name='seller').exists():
		return True

def is_buyer(user):
	if user.groups.filter(name='buyer').exists():
		return True

def is_active_month_buyer(user):
	if user.groups.filter(name='month_buyer').exists() and user.is_active:
		return True
	else:
		return False

def home(request, network='ig'):

	if request.user.groups.filter(name='seller').exists():
		email = request.user.email
		user_accounts = VerifiedUserAccounts.objects.filter(email=email).\
			prefetch_related('niches').select_related('ig_user', 'tw_user')
		niches = []
		ig_accounts = []
		tw_accounts = []
		for acc in user_accounts:
			try:
				ig_accounts.append(acc.ig_user)
			except IgUsers.DoesNotExist:
				pass
			try:
				tw_accounts.append(acc.tw_user)
			except TwUsers.DoesNotExist:
				pass
			niches += list(acc.niches.all())
		niches = set(niche.niche for niche in niches)
		niches = ', '.join(niches)

		context = {'email': email, 'ig_accounts': ig_accounts,
				   'tw_accounts': tw_accounts, 'niches': niches}

		return render(request, 'new/home_seller.html', context)
	else:
		user = request.user
		if user.is_authenticated():
			email = user.email
		else:
			email = None
		ig_form = IgSearchForm()
		tw_form = TwSearchForm()

		user_subscribed = is_active_month_buyer(user)
		prev = request.GET.get('prev') or None

		context = {
			'email': email, 
			'subscribed': user_subscribed, 
			'ig_form': ig_form,
			'tw_form': tw_form,
			'prev': prev
		}
		if request.user.groups.filter(name='buyer').exists():
			auth_user_id = request.user.id
			if BuyerCredits.objects.filter(buyer_id=auth_user_id).exists():
				credit_user = BuyerCredits.objects.get(buyer_id=auth_user_id)
				credits = credit_user.buyer_credits
			else:
				credits = 0

			context = {
				'email': email,
				'subscribed': user_subscribed,
				'ig_form': ig_form,
				'tw_form': tw_form,
				'prev': prev,
				'credits': credits
			}
			return render(request, 'new/home_buyer.html', context)
		else:
			return render(request, 'new/home_buyer.html', context)

@ajax_required
def accounts_page(request, network):

	models_map = {'ig': IgUsers, 'tw': TwUsers}

	min_followers = max_followers = ''
	min_cpm = max_cpm = ''
	min_engagement = max_engagement = ''
	num_page = request.GET.get('page')
	niches = request.GET.get('niches', '')
	search_unverified = request.GET.get('unverified', False)

	# initialize search engine
	search_engine = utils.ES_SobSearchEngine(network, search_unverified)

	# search by niches
	if niches:
		search_engine.search_niches(niches)
	else:
		search_engine.search_niches('match_all')

	# filter by followers
	if (request.GET.get('min_followers') != None and request.GET.get('min_followers') != '') \
			and (request.GET.get('max_followers') != None and request.GET.get('max_followers') != ''):
		min_followers = int(request.GET.get('min_followers'))
		max_followers = int(request.GET.get('max_followers'))
		search_engine.filter_by_followers(min_followers, max_followers)

	# filter by cpm values
	if request.GET.get('min_cpm') and request.GET.get('max_cpm'):
		min_cpm = float(request.GET.get('min_cpm'))
		max_cpm = float(request.GET.get('max_cpm'))
		search_engine.filter_by_cpm(min_cpm, max_cpm)

	# filter by engagement percent
	if request.GET.get('min_engagement') and request.GET.get('max_engagement'):
		min_engagement = float(request.GET.get('min_engagement'))
		max_engagement = float(request.GET.get('max_engagement'))
		search_engine.filter_by_engagement(min_engagement, max_engagement)

	# Sort results
	order_by = request.GET.get('order_by') 
	if order_by:
		search_engine.sort(order_by)

	accs_list = search_engine.get_results()
	
	# TODO: Paginate directly from Elasticsearch to be efficient and save RAM
	paginator = Paginator(accs_list, settings.ACCS_PER_PAGE)

	try:
		page = paginator.page(int(num_page))
	except (PageNotAnInteger, ValueError) as e:
		page = paginator.page(1)
	except EmptyPage:
		page = paginator.page(paginator.num_pages)
	page_range = paginator.page_range
	page_num = page.number
	neg_index = page_num - 3
	neg_index = 0 if neg_index < 0 else neg_index
	page_range = list(page_range)
	page_range = page_range[neg_index:page_num + 2]
	user_subscribed = is_active_month_buyer(request.user)
	is_assistant = request.user.groups.filter(name='assistant').exists()

	unlocked_users = UnlockedUsers.objects.filter(buyer_id=request.user.id).values_list('user_id', flat=True)

	context = {
		'page': page, 
		'page_range': page_range, 
		'paginator': paginator,
		'network': network, 
		'subscribed': user_subscribed,
		'niches': niches, 
		'min_followers': min_followers, 
		'max_followers': max_followers,
		'min_cpm': min_cpm,
		'max_cpm': max_cpm,
		'min_engagement': min_engagement,
		'max_engagement': max_engagement,
		'is_assistant': is_assistant,
		'has_unverified': search_unverified,
		'order_by': order_by,
		'unlocked_users': unlocked_users,
	}

	return render(request, 'new/accounts.html', context)

@ajax_required
def search_autocomplete(request):

	input_niche = request.GET.get('term', '')
	network = request.GET.get('network', 'ig')

	sqs = SearchQuerySet().models(IgHashtags, TwKeywords).autocomplete(text=input_niche)[:5]
	
	suggestions = []
	for sug in sqs:
		suggestions.append({'value': sug.text, 'label': sug.text})

	return JsonResponse(suggestions, safe=False)

@ajax_required
def account_detail(request):
	# this is no longer used since we
	# move to the centralized profile page

	network = request.GET.get('network')
	id = request.GET.get('id')
	models_map = {'ig': IgUsers, 'tw': TwUsers}
	templates_map = {'ig': 'new/ig_account_detail.html', 'tw': 'new/tw_account_detail.html'}
	Model = models_map.get(network)
	if not Model:
		raise Http404
	template = templates_map[network]
	obj = get_object_or_404(Model, id=id)
	user = request.user

	try:
		acc_opened = user.is_authenticated() and obj.verified_acc in user.opened_accounts.all()
	except ObjectDoesNotExist:
		acc_opened = None

	user_subscribed = is_active_month_buyer(user)
	is_assistant = request.user.groups.filter(name='assistant').exists()

	context = {
		'obj': obj, 
		'acc_opened': acc_opened, 
		'subscribed': user_subscribed, 
		'is_assistant': is_assistant
	}
	return render(request, template, context)

@user_passes_test(is_active_month_buyer)
@login_required
@ajax_required
def open_account(request):
	user = request.user
	network = request.POST.get('network')
	id = request.POST.get('id')
	models_map = {'ig': IgUsers, 'tw': TwUsers}
	Model = models_map.get(network)
	if not Model:
		raise Http404
	instance = get_object_or_404(Model, id=id)
	uses = user.buyeruses_set.all()[0]
	uses_num, status = utils.check_uses_active(user)
	resp = {
		'status': status,
		'uses': uses_num
	}
	if uses.uses > 0:
		verified_acc = instance.verified_acc
		uses.uses -= 1
		uses.save()
		user.opened_accounts.add(verified_acc)
		user.save()
		resp['credentials'] = {
			    'username': instance.username, 'email': verified_acc.email,
				'id': instance.id,
		}
		resp['uses'] = uses.uses

	else:
		resp['status'] = 'not enough'
	return JsonResponse(resp)

@user_passes_test(is_buyer)
@login_required
@ajax_required
def get_uses(request):
	uses_num, resp = utils.check_uses_active(request.user)
	return JsonResponse({'uses': uses_num, 'resp': resp})

@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request):

	redirect_to = request.POST.get('next_',
								   request.GET.get('next', 'main:home'))
	if request.user.is_authenticated():
		return redirect(redirect_to)
	if request.method == "POST":
		
		form = LoginForm(request, data=request.POST)
		if form.is_valid():
			# Okay, security check complete. Log the user in.
			auth.login(request, form.get_user())
			return redirect(redirect_to)
	else:
		form = LoginForm(request, initial={'next_': redirect_to})

	return render(request, 'new/login.html', {'form': form})

@login_required
def logout(request):

	auth.logout(request)
	return redirect('main:home')

def register_buyer(request):
	if request.user.is_authenticated():
		return redirect('main:home')
	if request.method == 'POST':
		form = RegistrationForm(request.POST)
		if form.is_valid():
			cd = form.cleaned_data
			password = cd['password1']
			user = form.save()
			g, created = Group.objects.get_or_create(name='buyer')
			g.user_set.add(user)
			g.save()
			user = auth.authenticate(username=user.email, password=password)
			auth.login(request, user)

			if cd['coupon'] and cd['coupon'].lower() == 'josh':
				BuyerCredits.objects.create(buyer_id=request.user.id, buyer_credits = 20 + settings.DEFAULT_FREE_CREDITS)
			else:
				BuyerCredits.objects.create(buyer_id=request.user.id, buyer_credits=settings.DEFAULT_FREE_CREDITS)

			return redirect('main:home')
		return render(request, 'new/registration.html', {'type': 'buyer', 'form': form})
	else:
		form = RegistrationForm()
		return render(request, 'new/registration.html', {'type': 'buyer', 'form': form})

def register_publisher(request):
	if request.user.is_authenticated():
		return redirect('main:home')
	if request.method == 'POST':
		#note: check username not already exist
		form = SellerRegistrationForm(request.POST)
		if form.is_valid():
			cd = form.cleaned_data
			password = cd['password1']
			user = form.save()
			g, created = Group.objects.get_or_create(name='seller')
			g.user_set.add(user)
			g.save()

			user = auth.authenticate(username=user.email, password=password)
			auth.login(request, user)
			return redirect('main:home')
		return render(request, 'new/registration.html', {'type': 'publisher', 'form': form})
	else:
		form = SellerRegistrationForm()
		return render(request, 'new/registration.html', {'type': 'publisher', 'form': form})

@user_passes_test(is_seller)
@login_required
def new_account(request, network):
	network_map = {'ig': 'Instagram', 'tw': 'Twitter'}
	if network not in network_map:
		raise Http404
	try:
		if network == 'ig':
			user = request.session['ig']
			id_ = user['id']
			username = user['username']
			u = IgUsers.objects.filter(username=username)
		else:
			key, secret = request.session['tw']['access_token'], \
					      request.session['tw']['access_token_secret']
			auth = tweepy.OAuthHandler(settings.TW_KEY, settings.TW_SECRET)
			auth.set_access_token(key, secret)
			api = tweepy.API(auth)
			me = api.me()
			username = me.screen_name
			id_ = me.id
			u = TwUsers.objects.filter(username=username)
	except KeyError:
		msg = 'You are not authenticated with {}. Please try again to add new account'.\
			format(network_map[network])
		messages.error(request, msg)
		return redirect('main:home')
	except tweepy.TweepError:
		msg = 'Cannot connect to Twitter API. Please try to authenticate again.'
		messages.error(request, msg)
		return redirect('main:home')
	except tweepy.RateLimitError:
		msg = 'Too many requests. Please try again later.'
		messages.error(request, msg)
		return redirect('main:home')
	else:
		try:
			user_instance = u[0]
			v = user_instance.verified_acc
			if v:
				messages.warning(request, 'This account has already been registered!')
				return redirect('main:home')
		except IndexError:
			user_instance = None
	if request.method == 'POST':
		form = NewAccountForm(request.POST, session_username=username, network=network)
		if form.is_valid():
			emailScraped = time.strftime("%Y-%m-%d", time.gmtime())
			email = request.user.email
			error = False
			if network == 'ig':
				try:
					post_num, follower_num, avg_like = utils.get_user_info_ig(id_, user['token'])
				except utils.IgException:
					form.add_error(None, 'Cannot retrieve data from Instagram.'
										 ' Please try again or re-authenticate with Instagram.')
					error = True
				else:
					data = {
						'username': username, 'email': email, 'followers': follower_num,
						'emailscraped': emailScraped, 'postcount': post_num,
						'postavglike': avg_like, 'userid': id_, 'verified': 2,
						'emailsent': 1,
					}
					if user_instance:
						for key, value in data.items():
							setattr(user_instance, key, value)
					else:
						user_instance = IgUsers(**data)
					user_instance.save()
					main_process.delay(user)
			else:
				try:
					data = utils.get_user_info_tw(api)
					data2 = {
						'email': email, 'emailscraped': emailScraped,
						'verified': 2, 'emailsent': 1,
					}
					data.update(data2)
				except tweepy.TweepError:
					form.add_error(None, 'Cannot retrieve data from Twitter.'
										 ' Please try again or re-authenticate with Twitter.')
					error = True
				else:
					if user_instance:
						for key, value in data.items():
							setattr(user_instance, key, value)
					else:
						user_instance = TwUsers(**data)
					user_instance.save()
			if not error:
				cd = form.cleaned_data
				verified_acc = VerifiedUserAccounts(email=email, network=network,
													price=cd['price'], note=cd['note'])
				verified_acc.save()
				user_instance.verified_acc = verified_acc
				user_instance.save()
				niches = cd['niches']
				if niches:
					niches_list = niches.split(',')
					niches_list = set(niche.strip().lower() for niche in niches_list)
					for niche in niches_list:
						try:
							n = VerifiedUserNiches.objects.get(niche=niche, network=network)
						except ObjectDoesNotExist:
							n = VerifiedUserNiches(niche=niche, network=network)
							n.save()
						n.verified_accounts.add(verified_acc)
				messages.success(request, 'Account {} has been added!'.format(username))
				return redirect('main:home')
	else:
		n = []
		follower_count = 0
		if network == 'ig':
			if user_instance:
				niches = IgUserTags.objects.filter(userid=user_instance.id, frequency__gte=3).order_by('-frequency')
				follower_count = user_instance.followers
				n = [niche.hashtag for niche in niches]
		else:
			if user_instance:
				niches = TwUserKeywords.objects.filter(userid=user_instance.id)
				follower_count = user_instance.followerscount
				n = [niche.keyword for niche in niches]
		niches = ', '.join(n)
		if follower_count == 0:
			price = 0
		elif follower_count < 50000:
			price = 5
		elif follower_count < 100000:
			price = 10
		else:
			price = 10 + follower_count // 20000
		form = NewAccountForm(initial={'niches': niches, 'price': price, 'username': username},
							  session_username=username, network=network)
	network_full = network_map[network]
	context = {'form': form, 'username': username, 'network': network,
			   'network_full': network_full}
	return render(request, 'new/new_account.html', context)

@user_passes_test(is_seller)
@login_required
@ajax_required
def oauth_redirect(request, network):
	redirect_uri = '{}://{}{}'.format(request.scheme, request.get_host(),
									  reverse('main:authenticate_successful', args=(network,)))
	next = request.GET.get('next')
	if next:
		redirect_uri += '?next={}'.format(next)
	if network == 'ig':
		redirect_url = """
		https://api.instagram.com/oauth/authorize/?client_id={}&redirect_uri={}
		&response_type=code&scope=basic+public_content+follower_list
		"""
		redirect_url = redirect_url.format(settings.IG_ID, redirect_uri)
		network = 'Instagram'
	elif network == 'tw':
		auth = tweepy.OAuthHandler(settings.TW_KEY, settings.TW_SECRET, redirect_uri)
		try:
			redirect_url = auth.get_authorization_url()
		except tweepy.TweepError:
			messages.error(request, 'Cannot obtain Twitter authorization token. Please try again later.')
			return redirect('main:home')
		request.session['tw'] = {'request_token': auth.request_token}
		network = 'Twitter'
	else:
		raise Http404
	return render(request, 'new/modal_oauth.html', {'network': network, 'link': redirect_url})

@user_passes_test(is_seller)
@login_required
def authenticate_successful(request, network):
	next = request.GET.get('next')
	if network == 'ig':
		code = request.GET.get('code')
		if code:
			ig_url = 'https://api.instagram.com/oauth/access_token'
			redirect_uri = '{}://{}{}'.format(request.scheme, request.get_host(),
                                      reverse('main:authenticate_successful', args=('ig', )))
			if next:
				redirect_uri += '?next={}'.format(next)
			params = {
				'client_id': settings.IG_ID, 'client_secret': settings.IG_SECRET,
				'grant_type': 'authorization_code', 'redirect_uri': redirect_uri,
				'code': code
			}
			resp = requests.post(ig_url, data=params)
			if resp.status_code == 200:
				userdata = utils.create_ig_user(resp.json())
				request.session['ig'] = userdata
				if next:
					url = reverse('main:{}'.format(next.strip()), args=('ig',))
					return redirect(url)
				else:
					return redirect('main:home')
		messages.error(request, 'Cannot obtain Instagram authorization token. Please try again later.')
	if network == 'tw':
		code = request.GET.get('oauth_verifier')
		if code:
			auth = tweepy.OAuthHandler(settings.TW_KEY, settings.TW_SECRET)
			try:
				token = request.session['tw']['request_token']
				del request.session['tw']
				auth.request_token = token
				auth.get_access_token(code)
				tokens_dict = {
					'access_token': auth.access_token,
					'access_token_secret': auth.access_token_secret
				}
				request.session['tw'] = tokens_dict
				if next:
					url = reverse('main:{}'.format(next.strip()), args=('tw',))
					return redirect(url)
				else:
					return redirect('main:home')
			except KeyError, tweepy.TweepError:
				pass
		messages.error(request, 'Cannot obtain Twitter authorization token. Please try again later.')
	for key in ['ig', 'tw']:
		if key in request.session:
			del request.session[key]
	return redirect('main:home')

# MAKE AJAX
@user_passes_test(is_seller)
@login_required
def account_overview(request, network, model_id):
	models_map = {'tw': TwUsers, 'ig': IgUsers}
	Model = models_map.get(network)
	if not Model:
		raise Http404
	account = get_object_or_404(Model, id=model_id)
	verified_acc = account.verified_acc
	if not verified_acc:
		raise Http404
	# change this so that it returns permission error
	email = request.user.email
	if verified_acc.email != email:
		return HttpResponseForbidden('You don\'t have permission!')
	if network == 'ig':
		username = account.username
		network_full = 'Instagram'
	else:
		username = account.username
		network_full = 'Twitter'
	niches = verified_acc.niches.filter(network=network).values_list('niche', flat=True)
	niches = ', '.join(niches)
	context = {'username': username, 'network': network, 'network_full': network_full,
			   'niches': niches, 'instance': verified_acc, 'model_id': model_id}
	return render(request, 'new/account_overview.html', context)

@user_passes_test(is_seller)
@login_required
def edit_account(request, network, model_id):
	models_map = {'tw': TwUsers, 'ig': IgUsers}
	Model = models_map.get(network)
	if not Model:
		raise Http404
	account = get_object_or_404(Model, id=model_id)
	verified_acc = account.verified_acc
	if not verified_acc:
		raise Http404
	email = request.user.email
	# change this so that it returns permission error
	if verified_acc.email != email:
		return HttpResponseForbidden('You don\'t have permission!')
	acc_niches = verified_acc.niches.filter(network=network)
	if request.method == 'POST':
		form = EditAccountForm(request.POST)
		if form.is_valid():
			cd = form.cleaned_data
			verified_acc.price = cd['price']
			verified_acc.note = cd['note']
			verified_acc.save()
			niches = cd['niches'].split(',')
			verified_acc.niches.remove(*acc_niches)
			for n in niches:
				n = n.strip().lower()
				try:
					niche = VerifiedUserNiches.objects.get(network=network, niche=n)
				except ObjectDoesNotExist:
					niche = VerifiedUserNiches(network=network, niche=n)
					niche.save()
				verified_acc.niches.add(niche)
			messages.success(request, 'Form edit success!')
			return redirect('main:home')
	else:
		niches = acc_niches.values_list('niche', flat=True)
		niches = ', '.join(niches)
		initial_data = {
			'niches': niches, 'price': verified_acc.price,
			'note': verified_acc.note,
		}
		form = EditAccountForm(initial=initial_data)
	if network == 'ig':
		username = account.username
		network_full = 'Instagram'
	else:
		username = account.username
		network_full = 'Twitter'

	context = {'username': username, 'network': network, 'network_full': network_full,
			   'form': form, 'model_id': model_id}
	return render(request, 'new/edit_account.html', context)

def tos(request):
	return render(request, 'pages/tos.html')

def permission_denied(request):
	return render(request, 'pages/403.html')

def gen_pdf_ig(request):

	if 'tag' not in request.GET:
		return render(request, 'gen_pdf_ig.html')

	tag = request.GET.get('tag', False)
	if tag == False:
		return render(request, 'gen_pdf_ig.html')

	PASSWD = "96in236"
	HOST = "localhost"
	USER = "otto"
	DB = "shout_out_biz"

	db=MySQLdb.connect(host=HOST, user=USER, passwd=PASSWD, db=DB)
	c=db.cursor()

	c.execute("INSERT IGNORE INTO ig_hashtags(hashtag) VALUES('%s')" % (tag))

	c.execute("SELECT ig_users.id, ig_users.followers, ig_users.postCount, ig_users.username, ig_users.userID \
			  FROM (SELECT * FROM ig_user_tags WHERE hashtag='%s') as newtable \
			  INNER JOIN ig_users \
			  WHERE newtable.userID=ig_users.userID \
			  ORDER BY ig_users.followers DESC" % (tag))

	users = c.fetchall()

	doc = SimpleDocTemplate("/var/www/shoutour.biz/shoutourbiz/main/media/pdf_ig/shout_our_biz_%s.pdf" % (tag), pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
	styleSheet = getSampleStyleSheet()
	elements = []

	title = Paragraph('SHOUT OUT BIZ CATALOGUE(IG) FOR "%s"<br/><br/>' % (tag.upper()), styleSheet['Title'])

	headerStyle = copy(styleSheet["Title"])
	headerStyle.__dict__['fontSize'] = 12

	userID = Paragraph('<b>ID</b>',headerStyle)
	followerNum = Paragraph('<b>NUMBER OF FOLLOWERS</b>',headerStyle)
	postNum = Paragraph('<b>NUMBER OF POSTS</b>',headerStyle)
	hashtag = Paragraph('<b>CATEGORIES</b>',headerStyle)

	data= [[userID, followerNum, postNum, hashtag]]
	user_count = 0
	first_page = True
	doc.userCount = 0

	for user in users:

		doc.userCount += 1

		if user_count == 18 or (first_page and user_count == 17):
			t = Table(data,1*[1*inch]+1*[2.4*inch]+1*[1.8*inch]+1*[3*inch], (len(data))*[0.5*inch])
			t.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
								   ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
								   ('TEXTCOLOR',(0,-1),(-1,-1),colors.black),
								   ]))
			#elements.append(t)
			elements.append(PageBreak())
			data = [[userID, followerNum, postNum, hashtag]]
			user_count = 0
			first_page = False

		c.execute("SELECT ig_user_tags.hashtag \
			  FROM ig_user_tags \
			  WHERE userID='%s' \
			  ORDER BY frequency \
			  LIMIT 3" % (user[4]))
		most_used_tags = c.fetchall()
		tag_list =[]
		for mt in most_used_tags:
			tag_list.append(mt[0])
		tag_str = ', '.join(tag_list)
		data.append([user[0], user[1], user[2], tag_str])
		user_count += 1

	t=Table(data,1*[1*inch]+1*[2.4*inch]+1*[1.8*inch]+1*[3*inch], (len(data))*[0.5*inch])
	t.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
						   ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
						   ('TEXTCOLOR',(0,-1),(-1,-1),colors.black),
						   ]))

	elements.append(PageBreak())

	def FirstPageSetup(canvas, doc):

		canvas.saveState()
		canvas.drawImage('/var/www/shoutour.biz/shoutourbiz/main/media/invoice/invoice-header.png',20,595, width=575,height=180)
		canvas.drawImage('/var/www/shoutour.biz/shoutourbiz/main/media/invoice/invoice-information.png',20,530, width=575,height=35)
		if doc.userCount < 18:
			canvas.drawImage('/var/www/shoutour.biz/shoutourbiz/main/media/invoice/invoice-footer.png',20, 20, width=575,height=25)
		else:
			doc.pageCount = 1
		canvas.restoreState()

	def LaterPageSetup(canvas, doc):

		canvas.saveState()
		canvas.drawImage('/var/www/shoutour.biz/shoutourbiz/main/media/invoice/invoice-information.png',20,730, width=575,height=35)
		if (doc.userCount - 17 - 18 * doc.pageCount) <= 0:
			canvas.drawImage('/var/www/shoutour.biz/shoutourbiz/main/media/invoice/invoice-footer.png',20, 20, width=575,height=25)
		else:
			doc.pageCount += 1
		canvas.restoreState()

	doc.build(elements, onFirstPage=FirstPageSetup,onLaterPages=LaterPageSetup)
	db.close()

	if 'email' in request.GET:
		email = request.GET['email']
		subject = "Shout Our Biz - %s (IG)" % (tag)
		body = "Hello, \n\n \
				Thank you for choosing Shout Our Biz. \
				Please see attachment for your requested catalogue for %s (IG)" % (tag)
		to = email.replace(" ","").split(";")
		if to[-1] == '':
			to.pop()
		em = EmailMessage(subject, body, to=to)
		em.attach_file('/var/www/shoutour.biz/shoutourbiz/main/media/pdf_ig/shout_our_biz_%s.pdf' % (tag))
		em.send()

	return HttpResponseRedirect('/members/media/pdf_ig/shout_our_biz_%s.pdf' % (tag))


def gen_pdf_tw(request):

	if 'kw' not in request.GET:
		return render(request, 'gen_pdf_tw.html')

	kw = request.GET.get('kw', False)
	if kw == False:
		return render(request, 'gen_pdf_tw.html')

	PASSWD = "96in236"
	HOST = "localhost"
	USER = "otto"
	DB = "shout_out_biz"

	db=MySQLdb.connect(host=HOST, user=USER, passwd=PASSWD, db=DB)
	c=db.cursor()

	c.execute("INSERT IGNORE INTO tw_keywords(keyword) VALUES('%s')" % (kw))

	c.execute("SELECT tw_users.id, tw_users.followersCount, tw_users.statusesCount, tw_users.screenName \
			  FROM (SELECT * FROM tw_user_keywords WHERE keyword='%s') as newtable \
			  INNER JOIN tw_users \
			  WHERE newtable.screenName=tw_users.screenName \
			  ORDER BY tw_users.followersCount DESC" % (kw))

	users = c.fetchall()

	doc = SimpleDocTemplate("/var/www/shoutour.biz/shoutourbiz/main/media/pdf_tw/shout_our_biz_%s.pdf" % (kw), pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
	styleSheet = getSampleStyleSheet()
	elements = []

	title = Paragraph('SHOUT OUT BIZ CATALOGUE(TW) FOR "%s"<br/><br/>' % (kw.upper()), styleSheet['Title'])
	elements.append(title)

	headerStyle = copy(styleSheet["Title"])
	headerStyle.__dict__['fontSize'] = 12

	userID = Paragraph('<b>ID</b>',headerStyle)
	followerNum = Paragraph('<b>NUMBER OF FOLLOWERS</b>',headerStyle)
	postNum = Paragraph('<b>NUMBER OF TWEETS</b>',headerStyle)


	data= [[userID, followerNum, postNum]]
	user_count = 0
	first_page = True

	for user in users:

		if user_count == 18 or (first_page and user_count == 17):
			t = Table(data,1*[1*inch]+1*[2.4*inch]+1*[1.8*inch], (len(data))*[0.5*inch])
			t.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
								   ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
								   ('TEXTCOLOR',(0,-1),(-1,-1),colors.black),
								   ]))
			elements.append(t)
			elements.append(PageBreak())
			data = [[userID, followerNum, postNum]]
			user_count = 0
			first_page = False

		data.append([user[0], user[1], user[2]])
		user_count += 1

	t=Table(data,1*[1*inch]+1*[2.4*inch]+1*[1.8*inch], (len(data))*[0.5*inch])
	t.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
						   ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
						   ('TEXTCOLOR',(0,-1),(-1,-1),colors.black),
						   ]))

	elements.append(t)
	doc.build(elements)
	db.close()

	if 'email' in request.GET:
		email = request.GET['email']
		subject = "Shout Our Biz - %s (TW)" % (kw)
		body = "Hello, \n\n \
				Thank you for choosing Shout Our Biz. \
				Please see attachment for your requested catalogue for %s (TW)" % (kw)
		to = email.replace(" ","").split(";")
		if to[-1] == '':
			to.pop()
		em = EmailMessage(subject, body, to=to)
		em.attach_file('/var/www/shoutour.biz/shoutourbiz/main/media/pdf_tw/shout_our_biz_%s.pdf' % (kw))
		em.send()

	return HttpResponseRedirect('/members/media/pdf_tw/shout_our_biz_%s.pdf' % (kw))


def gen_pdf_ig_new(request):

	if 'tag' not in request.GET:
		return render(request, 'gen_pdf_ig_new.html')

	try:
		tag = request.GET.get('tag', False)
		phone = request.GET.get('phone', False)
		email = request.GET.get('email', False)
		addr = request.GET.get('addr', False)
		budget = request.GET.get('budget', False)
		if tag == False:
			return render(request, 'gen_pdf_ig_new.html')

		user_tags =IgUserTags.objects.filter(hashtag=tag)
		verified = VerifiedUserNiches.objects.filter(niche=tag, network='ig')

		doc = SimpleDocTemplate("/var/www/shoutour.biz/shoutourbiz/main/media/pdf_ig/shout_our_biz_%s.pdf" % (tag), pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
		styleSheet = getSampleStyleSheet()
		elements = []
		doc.phone = phone
		doc.email = email
		doc.addr = addr

		data= [['', '', '', '', '', '','']]
		user_count = 0
		first_page = True
		accounts = []
		account_id_included = []
		doc.userCount = 0
		doc.totalPrice = 0

		for niche in verified:
			verified_account = VerifiedUserAccounts.objects.filter(id=niche.verified_account_id)[0]
			user = IgUsers.objects.filter(id=verified_account.account_id)[0]
			uid = AuthUser.objects.filter(email=verified_account.email)[0].id
			p = verified_account.price * 13 / 10
			folNum = user.followers
			likesPPost = user.postavglike
			folPDollar = folNum / p
			likesPDollar = likesPPost / p

			userTags = IgUserTags.objects.filter(userid=user.userid).order_by('-frequency')
			tag_list =[]
			tag_len = 0
			for t in userTags:
				if tag_len + len(t.hashtag) + 1 > 15:
					break
				tag_list.append(t.hashtag)
				tag_len += len(t.hashtag) + 1
			if len(tag_list) == 0:
				tag_list.append('unknown')
			tag_str = ', '.join(tag_list)

			accounts.append([uid,tag_str, folNum, likesPPost,folPDollar,p,likesPDollar])
			account_id_included.append(verified_account.account_id)


		for user_tag in user_tags:

			user = IgUsers.objects.filter(userid=user_tag.userid)
			if not user.exists():
				user_tag.delete()
				continue
			elif user[0].verified == 0:
				continue
			else:
				user = user[0]
				verified_account = VerifiedUserAccounts.objects.filter(network='ig', account_id=user.id)[0]
				uid = AuthUser.objects.filter(email=verified_account.email)[0].id
				p = verified_account.price * 13 / 10
				folNum = user.followers
				likesPPost = user.postavglike
				folPDollar = folNum / p
				likesPDollar = likesPPost / p
				userTags = IgUserTags.objects.filter(userid=user.userid).order_by('-frequency')
				tag_list =[]
				tag_len = 0
				for t in userTags:
					if tag_len + len(t.hashtag) + 1 > 15:
						break
					tag_list.append(t.hashtag)
					tag_len += len(t.hashtag) + 1
				if len(tag_list) == 0:
					tag_list.append('unknown')
				tag_str = ', '.join(tag_list)

				if verified_account.account_id not in account_id_included:
					accounts.append([uid,tag_str, folNum, likesPPost,folPDollar,p,likesPDollar])
					account_id_included.append(verified_account.account_id)

		accounts.sort(key=lambda x:x[6], reverse=True) #4 is fol/$, 6 is likes/$

		if budget:
			remain = int(budget) * 11 / 10 + 10	# 1.1 time the max budget and plus 10

		for account in accounts:

			if budget:
				if (remain - account[-2]) < 0:
					break

				remain -= account[-2]

			if user_count == 18 or (first_page and user_count == 13):

				if first_page:
					t = Table(data,7*[1.15*inch], 1*[3.2*inch]+(len(data)-1)*[0.5*inch])
				else:
					t = Table(data,7*[1.15*inch], 1*[1*inch]+(len(data)-1)*[0.5*inch])
				t.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
									   ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
									   ('TEXTCOLOR',(0,-1),(-1,-1),colors.black),
									   ]))
				elements.append(t)
				elements.append(PageBreak())
				data = [['','', '', '', '', '','']]
				user_count = 0
				first_page = False

			doc.userCount += 1
			doc.totalPrice += account[5]
			data.append(account)
			user_count += 1

		if first_page:
			t = Table(data,7*[1.15*inch], 1*[3.2*inch]+(len(data)-1)*[0.5*inch])
		else:
			t = Table(data,7*[1.15*inch], 1*[1*inch]+(len(data)-1)*[0.5*inch])
		t.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
							   ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
							   ('TEXTCOLOR',(0,-1),(-1,-1),colors.black),
							   ]))

		elements.append(t)
		elements.append(PageBreak())

		#add invoice to db
		try:
			buyer = BuyerInfo.objects.get(email=email)
		except:
			buyer = BuyerInfo(email=email)
		buyer.phone = phone
		buyer.address = addr
		buyer.save()
		doc.bid = buyer.bid
		doc.date = datetime.date.today()
		if budget == '':
			invoice = Invoice(bid=buyer, price=doc.totalPrice, date=datetime.datetime.now())
		else:
			invoice = Invoice(bid=buyer, budget=budget, price=doc.totalPrice, date=doc.date)
		invoice.save()
		doc.iid = invoice.iid


		def FirstPageSetup(canvas, doc):

			canvas.saveState()
			canvas.drawImage('/var/www/shoutour.biz/shoutourbiz/main/media/invoice/invoice-header.png',20,595, width=575,height=180)
			canvas.drawImage('/var/www/shoutour.biz/shoutourbiz/main/media/invoice/invoice-information.png',20,530, width=575,height=35)
			canvas.setFillColorRGB(255,255,255)
			canvas.setFont('Helvetica-Bold', 14)
			canvas.drawString(60, 752, doc.phone)
			canvas.setFont('Helvetica-Bold', 9)
			canvas.drawString(198, 755, doc.email)
			canvas.setFont('Helvetica-Bold', 12)
			canvas.drawString(60, 710, doc.addr)
			bid = str(doc.bid)
			iid = str(doc.iid)
			while len(bid) < 5:
				bid = '0' + bid
			while len(iid) < 5:
				iid = '0' + iid
			canvas.setFont('Helvetica-Bold', 15)
			canvas.drawString(120, 658, iid)
			canvas.setFont('Helvetica-Bold', 12)
			canvas.drawString(405, 659, bid)
			canvas.drawString(505, 659, str(doc.date))
			if doc.userCount < 14:
				canvas.drawImage('/var/www/shoutour.biz/shoutourbiz/main/media/invoice/invoice-footer.png',20, 20, width=575,height=25)
				canvas.setFillColorRGB(255,255,255)
				canvas.setFont('Helvetica-Bold', 19)
				canvas.drawString(85, 25.5, '$'+str(doc.totalPrice)+'.00')
				link = 'https://www.paypal.com/cgi-bin/webscr?business=macdonjo3@hotmail.com&cmd=_xclick&currency_code=USD&amount=%d&item_name=ShoutOut(ID=%d)&invoice=%d&no_shipping=1' % (doc.totalPrice, doc.iid,doc.iid)
				canvas.linkURL(link, (510, 22, 593, 44), relative=1)
			else:
				doc.pageCount = 1
			canvas.restoreState()

		def LaterPageSetup(canvas, doc):

			canvas.saveState()
			canvas.drawImage('/var/www/shoutour.biz/shoutourbiz/main/media/invoice/invoice-information.png',20,730, width=575,height=35)
			if (doc.userCount - 13 - 18 * doc.pageCount) <= 0:
				canvas.drawImage('/var/www/shoutour.biz/shoutourbiz/main/media/invoice/invoice-footer.png',20, 20, width=575,height=25)
				canvas.setFillColorRGB(255,255,255)
				canvas.setFont('Helvetica-Bold', 20)
				canvas.drawString(85, 25.5, str(doc.totalPrice)+'.00')
				link = 'https://www.paypal.com/cgi-bin/webscr?business=macdonjo3@hotmail.com&cmd=_xclick&currency_code=USD&amount=%d&item_name=ShoutOut(ID=%d)&invoice=%d&no_shipping=1' % (doc.totalPrice, doc.iid,doc.iid)
				canvas.linkURL(link, (510, 22, 593, 44), relative=1)
			doc.pageCount += 1
			canvas.restoreState()

		doc.build(elements, onFirstPage=FirstPageSetup,onLaterPages=LaterPageSetup)

		return HttpResponseRedirect('/members/media/pdf_ig/shout_our_biz_%s.pdf' % (tag))
	except Exception as e:
		return render(request, 'gen_pdf_ig_new.html', {'msg': e})

def buy_subscription(request):
	return render(request, 'new/subscribe.html')

@user_passes_test(is_buyer)
@login_required
def payment_success(request):
	"""
	Subscription will be activated from the date on which payment was made.
	Regardless of the time when this view was accessed.
	:param request:
	:return:
	"""
	for key, value in request.GET.items():
		print key, value
	rcpt = request.GET.get('cbreceipt', '')
	timestamp = request.GET.get('time', '')
	item = request.GET.get('item', '')
	cbpop = request.GET.get('cbpop', '')
	value_str = '|'.join([settings.JVZ_SECRET_KEY, rcpt, timestamp, item])
	new_hash = hashlib.sha1(value_str).hexdigest()
	new_hash = new_hash[:8].upper()
	if new_hash != cbpop:
		return HttpResponseForbidden('forbidden')
	usr_id = request.user.id
	add_subscription.delay(usr_id, rcpt, timestamp)
	return render(request, 'new/thank_you_page.html')

@csrf_exempt
@require_http_methods(['POST'])
def jvzipn(request):
	for key, value in request.POST.items():
		print key, value
	key_list = [key for key in request.POST if key != 'cverify']
	ciphered_key = request.POST.get('cverify')
	key_list.sort()
	value_list = [request.POST.get(key) for key in key_list]
	value_list.append(settings.JVZ_SECRET_KEY)
	value_str = '|'.join(value_list)
	new_hash = hashlib.sha1(value_str).hexdigest()
	new_hash = new_hash[:8].upper()
	if new_hash != ciphered_key:
		return HttpResponseForbidden('')
	payment_type = request.POST.get('ctransaction')
	receipt = request.POST.get('ctransreceipt')
	email = request.POST.get('ccustemail')
	timestamp = request.POST.get('ccustemail')
	amount = request.POST.get('ctransamount')
	cust_name = request.POST.get('ccustname')
	if payment_type == 'SALE':
		# Payment.objects.filter(receipt__exact=receipt).update(active=False)
		new_payment = Payment(email=email, timestamp=timestamp, receipt=receipt,
							  amount=amount, customer_name=cust_name)
		new_payment.save()
	# if recurring is handled this way, recurring payments are saved,
	#  and then duration of subscription calculated:
	#  p = Payment.objects.filter(recur=True, receipt=receipt).count()
	# months = 1 + p
	# if subscription is activated after some time

	elif payment_type == 'BILL':
		new_recur = Payment(email=email, timestamp=timestamp, receipt=receipt,
							amount=amount, customer_name=cust_name, active=False,
							recur=True)
		new_recur.save()
		try:
			subscription = SubscriptionData.objects.get(receipt=receipt)
		except ObjectDoesNotExist:
			pass
		else:
			ended = subscription.end
			pmnt_period = subscription.payment_period
			subscription.end = utils.calcul_new_date(ended, pmnt_period)
			subscription.save()
			uses = subscription.user.buyeruses_set.all()[0]
			uses.uses = subscription.month_uses
			uses.save()
	return render(request, 'new/ipn_response.html')

class IPN(TemplateView): #paypal
	def get(self, request, *args, **kwargs):
		return HttpResponseForbidden('')

	def post(self, request, *args, **kwargs):
		originalParameters = self.request.POST
		logger.info(originalParameters)
		newParameteres = 'cmd=_notify-validate&' + self.request.POST.urlencode()
		req = urllib2.Request("http://www.paypal.com/cgi-bin/webscr", newParameteres)
		response = urllib2.urlopen(req)
		result = response.read()
		logger.info(result)
		if result == "VERIFIED": #notification is not hacked/faked
			logger.info('verified!!')
			logger.info(originalParameters['receiver_email'])
			if originalParameters.get('receiver_email') != "macdonjo3@hotmail.com":
				logger.info("not valid receiving email!")
				return HttpResponse('200 OK')

			# You need to check 'payment_status' of the IPN
			email = originalParameters['payer_email']

			if originalParameters['txn_type'] == "subscr_cancel": #do nothing, wait for subscr_eot
				logger.info("subscr_cancel", email)
			elif originalParameters.get('payment_status') == "Refunded": #refunded so
				logger.info("payment_status = Refunded")
				try:
					myuser = User.objects.get(email=email)
					myuser.groups.clear()
					myuser.delete()
				except ObjectDoesNotExist:
					logger.info("not deleted: can't find email: " + email)
			#create account, but delete when payment failed (subscr_cancel)
			elif (originalParameters['txn_type'] == "subscr_payment" and originalParameters['payment_status'] == "Completed") or originalParameters['txn_type'] == "subscr_signup":
				logger.info("subscr_signup/payment")
				subscr_id = originalParameters['subscr_id']
				first_name = originalParameters['first_name']
				last_name = originalParameters['last_name']
				if User.objects.filter(username=email).count() == 0: #new subscription
					logger.info("new subscription")
					myuser = User.objects.create_user(email, email, subscr_id, first_name=first_name, last_name=last_name)
					myuser.save()
					g, created = Group.objects.get_or_create(name='month_buyer')
					g.user_set.add(myuser)
					g.save()
					logger.info("new user saved")
					#send email
					emailMessage = """ Hi %s,

Login URL: http://shoutour.biz/members/login/
Username: %s,
Password: %s

Thanks!""" %(first_name,email,subscr_id)
					msg = EmailMessage('ShoutOuts', emailMessage, to = [email])
					logger.info("sending email ....")
					emailSent = False
					for x in range(10):
						try:
							msg.send()
							logger.info("email sent!")
							emailSent = True
							break
						except:
							logger.info("email not sent. retrying!")
							time.sleep(30)
					if emailSent == False:
						logger.error("cannot send email to: " + email)

			elif originalParameters['txn_type'] == "subscr_eot": #end of subscription
				logger.info("subscr_eot")
				try:
					myuser = User.objects.get(email=email)
					myuser.groups.clear()
					myuser.delete()
				except ObjectDoesNotExist:
					logger.info("ObjectDoesNotExist", email)

		return HttpResponse('200 OK')


def instagram_invoice(request):

	if 'tag' not in request.GET:
		return render(request, 'instagram_invoice.html')

	if request.method == "GET":

		try:
			t = request.GET.get('tag', False)
			tags = t.replace(' ', '').split(',')

			cur_user = []
			for tag in tags:
				user_tags = IgUserTags.objects.filter(hashtag__icontains=tag)
				for user_tag in user_tags:
					if user_tag.frequency > 5:
						cur_user.append(user_tag.userid)

			for tag in tags:
				user_tags = VerifiedUserNiches.objects.filter(niche__icontains=tag,network='ig')
				for user_tag in user_tags:
					user = IgUsers.objects.get(id=user_tag.verified_account.account_id)
					cur_user.append(user.userid)

			userid_set = set(cur_user)

			class user_detail(object):

				def __init__(self, username, uid, tag_str, email, price, fol, lpp, fpd, lpd):
					self.username = username
					self.uid = uid
					self.tag_str = tag_str
					self.email = email
					self.price = price
					self.fol = fol
					self.lpp = lpp
					self.fpd = fpd
					self.lpd = lpd

			verifiedUserList = []
			unverifiedUserList = []

			for userid in userid_set:
				user = IgUsers.objects.filter(userid=userid)[0]

				username = user.username
				uid = user.id
				fol = user.followers
				lpp = user.postavglike

				userTags = IgUserTags.objects.filter(userid=user.userid).order_by('-frequency')
				tag_list =[]
				tag_len = 0
				for t in userTags:
					if tag_len + len(t.hashtag) + 1 > 15:
						break
					tag_list.append(t.hashtag)
					tag_len += len(t.hashtag) + 1
				if len(tag_list) == 0:
					tag_list.append('unknown')
				tag_str = ', '.join(tag_list)

				aid = user.id
				vua = VerifiedUserAccounts.objects.filter(account_id=aid)
				# if account is verified
				if vua.exists():
					vua = vua[0]
					email =  vua.email
					if vua.price < 0:
						vua.price = 1
						vua.save()
					price = vua.price
					fpd = int(fol / price)
					lpd = int(lpp / price)
					verifiedUserList.append(user_detail(username, uid, tag_str, email, price, fol, lpp, fpd, lpd))
				else: #if account is not verified
					email = user.email
					price = None
					fpd = None
					lpd = None
					unverifiedUserList.append(user_detail(username, uid, tag_str, email, price, fol, lpp, fpd, lpd))

			# Sort the List by follower count 
			verifiedUserList.sort(key=lambda x:x.fol, reverse=True)
			unverifiedUserList.sort(key=lambda x:x.fol, reverse=True)

			return render(request, 'instagram_invoice_result.html', {'VerUserList': verifiedUserList, 'UnverUserList':unverifiedUserList})

		except Exception as e:
			return render(request, 'instagram_invoice.html', {'msg': e})


	elif request.method == "POST":
		pass

	return render(request, 'instagram_invoice.html')

def generate_instagram_invoice(request):

	try:
		phone = request.POST.get('phone')
		email = request.POST.get('email')
		addr = request.POST.get('addr')
		budget = request.POST.get('budget', False)
		markup = request.POST.get('markup')

		verUsers = request.POST.getlist('verCheckbox')
		unverUsers = request.POST.getlist('unverCheckbox')
		prices = request.POST.getlist('price')

		doc = SimpleDocTemplate("/var/www/shoutour.biz/shoutourbiz/main/media/pdf_ig/shout_our_biz_%s.pdf" % (email), pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
		styleSheet = getSampleStyleSheet()
		elements = []
		doc.phone = phone
		doc.email = email
		doc.addr = addr

		data= [['', '', '', '', '', '','']]
		user_count = 0
		first_page = True
		accounts = []
		doc.userCount = 0
		doc.totalPrice = 0

		for uid in verUsers:
			verified_account = VerifiedUserAccounts.objects.filter(account_id=uid)[0]
			user = IgUsers.objects.filter(id=verified_account.account_id)[0]
			p = float("%.2f" % (verified_account.price * (1+int(markup)/float(100))))
			folNum = user.followers
			likesPPost = user.postavglike
			folPDollar = float("%.2f" % (folNum / p))
			likesPDollar = float("%.2f" % (likesPPost / p))

			userTags = IgUserTags.objects.filter(userid=user.userid).order_by('-frequency')
			tag_list =[]
			tag_len = 0
			for t in userTags:
				if tag_len + len(t.hashtag) + 1 > 15:
					break
				tag_list.append(t.hashtag)
				tag_len += len(t.hashtag) + 1
			if len(tag_list) == 0:
				tag_list.append('unknown')
			tag_str = ', '.join(tag_list)

			accounts.append([uid,tag_str, folNum, likesPPost,folPDollar,p,likesPDollar])

		for i in range(len(unverUsers)):
			uid = unverUsers[i]
			p = float("%.2f" % (float(prices[i]) * (1+int(markup)/float(100))))
			user = IgUsers.objects.filter(id=uid)[0]
			folNum = user.followers
			likesPPost = user.postavglike
			folPDollar = float("%.2f" % (folNum / p))
			likesPDollar = float("%.2f" % (likesPPost / p))

			userTags = IgUserTags.objects.filter(userid=user.userid).order_by('-frequency')
			tag_list =[]
			tag_len = 0
			for t in userTags:
				if tag_len + len(t.hashtag) + 1 > 15:
					break
				tag_list.append(t.hashtag)
				tag_len += len(t.hashtag) + 1
			if len(tag_list) == 0:
				tag_list.append('unknown')
			tag_str = ', '.join(tag_list)

			accounts.append([uid,tag_str, folNum, likesPPost,folPDollar,p,likesPDollar])

		accounts.sort(key=lambda x:x[6], reverse=True) #4 is fol/$, 6 is likes/$

		for account in accounts:

			if user_count == 18 or (first_page and user_count == 13):

				if first_page:
					t = Table(data,7*[1.15*inch], 1*[3.2*inch]+(len(data)-1)*[0.5*inch])
				else:
					t = Table(data,7*[1.15*inch], 1*[0.5*inch]+(len(data)-1)*[0.5*inch])
				t.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
									   ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
									   ('TEXTCOLOR',(0,-1),(-1,-1),colors.black),
									   #('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
									   #('BOX', (0,0), (-1,-1), 0.25, colors.black),
									   ]))
				elements.append(t)
				elements.append(PageBreak())
				data = [['','', '', '', '', '','']]
				user_count = 0
				first_page = False

			doc.userCount += 1
			doc.totalPrice += account[5]
			data.append(account)
			user_count += 1

		if first_page:
			t = Table(data,7*[1.15*inch], 1*[3.2*inch]+(len(data)-1)*[0.5*inch])
		else:
			t = Table(data,7*[1.15*inch], 1*[0.5*inch]+(len(data)-1)*[0.5*inch])
		t.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
							   ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
							   ('TEXTCOLOR',(0,-1),(-1,-1),colors.black),
							   #('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
							   #('BOX', (0,0), (-1,-1), 0.25, colors.black),
							   ]))

		elements.append(t)
		elements.append(PageBreak())

		#add invoice to db
		try:
			buyer = BuyerInfo.objects.get(email=email)
		except:
			buyer = BuyerInfo(email=email)
		buyer.phone = phone
		buyer.address = addr
		buyer.save()
		doc.bid = buyer.bid
		doc.date = datetime.date.today()
		if not budget:
			invoice = Invoice(bid=buyer, price=doc.totalPrice, date=datetime.datetime.now())
		else:
			invoice = Invoice(bid=buyer, budget=budget, price=doc.totalPrice, date=doc.date)
		invoice.save()
		doc.iid = invoice.iid


		def FirstPageSetup(canvas, doc):

			canvas.saveState()
			canvas.drawImage('/var/www/shoutour.biz/shoutourbiz/main/media/invoice/invoice-header.png',20,595, width=575,height=180)
			canvas.drawImage('/var/www/shoutour.biz/shoutourbiz/main/media/invoice/invoice-information.png',20,530, width=575,height=35)
			canvas.setFillColorRGB(255,255,255)
			canvas.setFont('Helvetica-Bold', 14)
			canvas.drawString(60, 752, doc.phone)
			canvas.setFont('Helvetica-Bold', 9)
			canvas.drawString(198, 755, doc.email)
			canvas.setFont('Helvetica-Bold', 12)
			canvas.drawString(60, 710, doc.addr)
			bid = str(doc.bid)
			iid = str(doc.iid)
			while len(bid) < 5:
				bid = '0' + bid
			while len(iid) < 5:
				iid = '0' + iid
			canvas.setFont('Helvetica-Bold', 15)
			canvas.drawString(120, 658, iid)
			canvas.setFont('Helvetica-Bold', 12)
			canvas.drawString(405, 659, bid)
			canvas.drawString(505, 659, str(doc.date))
			if doc.userCount < 14:
				canvas.drawImage('/var/www/shoutour.biz/shoutourbiz/main/media/invoice/invoice-footer.png',20, 20, width=575,height=25)
				canvas.setFillColorRGB(255,255,255)
				canvas.setFont('Helvetica-Bold', 19)
				canvas.drawString(85, 25.5, '$'+'%0.2f' % doc.totalPrice)
				link = 'https://www.paypal.com/cgi-bin/webscr?business=macdonjo3@hotmail.com&cmd=_xclick&currency_code=USD&amount=%d&item_name=ShoutOut(ID=%d)&invoice=%d&no_shipping=1' % (doc.totalPrice, doc.iid,doc.iid)
				canvas.linkURL(link, (510, 22, 593, 44), relative=1)
			else:
				doc.pageCount = 1
			canvas.restoreState()

		def LaterPageSetup(canvas, doc):

			canvas.saveState()
			canvas.drawImage('/var/www/shoutour.biz/shoutourbiz/main/media/invoice/invoice-information.png',20,720, width=575,height=35)
			if (doc.userCount - 13 - 18 * doc.pageCount) <= 0:
				canvas.drawImage('/var/www/shoutour.biz/shoutourbiz/main/media/invoice/invoice-footer.png',20, 20, width=575,height=25)
				canvas.setFillColorRGB(255,255,255)
				canvas.setFont('Helvetica-Bold', 20)
				canvas.drawString(85, 25.5, '$'+'%0.2f' % doc.totalPrice)
				link = 'https://www.paypal.com/cgi-bin/webscr?business=macdonjo3@hotmail.com&cmd=_xclick&currency_code=USD&amount=%d&item_name=ShoutOut(ID=%d)&invoice=%d&no_shipping=1' % (doc.totalPrice, doc.iid,doc.iid)
				canvas.linkURL(link, (510, 22, 593, 44), relative=1)
			doc.pageCount += 1
			canvas.restoreState()

		doc.build(elements, onFirstPage=FirstPageSetup,onLaterPages=LaterPageSetup)

		return HttpResponseRedirect('/members/media/pdf_ig/shout_our_biz_%s.pdf' % (email))

	except Exception as e:
		return render(request, 'instagram_invoice.html', {'msg': e})