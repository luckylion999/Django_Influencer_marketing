"""
This module contains views for staff and 
admin actions. It also contains view relevant
to the demographics analyzer, which allows assistants
to evaluate and categorize social media users.
"""

import csv

import json

from django.shortcuts import render, redirect
from django.contrib.auth.models import Group, Permission
from django.contrib import auth

from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from django.views.generic.edit import DeleteView


from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import permission_required

from django.contrib import messages

from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.paginator import Paginator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.http import Http404, HttpResponseNotFound
from django.forms.models import model_to_dict
from django.db.models import Count
from django.db import models

from django.utils.decorators import method_decorator

from main.forms import LoginForm, RegistrationForm
from main.models import AuthUser, IgFollower, VerifiedUserAccounts, VerifiedUserNiches, \
	IgUsers, TwUsers, IgUserTags, TwUserKeywords, IgUsersSocialAccounts
from main.decorators import ajax_required

from internal.forms import AssistantEditInfluencerForm, AssistantEditInfluencerTwitterForm, \
	AssistantEditInfluencerFacebookForm, AssistantEditInfluencerYoutubeForm, \
	AssistantEditInfluencerFullnameForm, AssistantEditInfluencerUsernameForm

from profiles.utils import IgProfileParser

from . import models
from . import utils
from . import forms
from . import mixins

def is_assistant(user):
	"""
	Return true if user is an assistant, False otherwise
	"""

	if user.groups.filter(name='assistant').exists():
		return True
	return False

def _is_superuser(user):
	"""
	Return true if user is superuser (admin)
	"""

	return user.is_superuser

def _validate_perms(user):
	"""
	Return True if user is authenticated (logged in)
	"""

	return user.is_authenticated()


@sensitive_post_parameters()
@csrf_protect
@never_cache
def analyzer_signup(request):
	"""
	Sign up for an assistant account.
	"""

	if request.user.is_authenticated():
		return redirect('internal:profile')
	if request.method == 'POST':
		post = request.POST.copy()
		request.POST = post

		form = RegistrationForm(request.POST)
		if form.is_valid():
			cd = form.cleaned_data
			password = cd['password1']
			user = form.save()
			g, created = Group.objects.get_or_create(name='assistant')
			g.user_set.add(user)
			g.save()
			user = auth.authenticate(username=user.email, password=password)
			auth.login(request, user)
			return redirect('internal:profile')
		return render(request, 'analyzer_signup.html', {'form': form})
	else:
		form = RegistrationForm()
		return render(request, 'analyzer_signup.html', {'form': form})

@sensitive_post_parameters()
@csrf_protect
@never_cache
def analyzer_login(request):
	"""
	Log into assistant account.
	"""

	form = LoginForm(request)

	if request.user.is_authenticated():
		return redirect('internal:profile')
	if request.method == "POST":
		form = LoginForm(request, data=request.POST)
		if form.is_valid():
			# security check complete. Log the user in.
			auth.login(request, form.get_user())
			return redirect('internal:profile')
	else:
		form = LoginForm(request)

	return render(request, 'analyzer_login.html', {'form': form})

@login_required()
def analyzer_logout(request):
	"""
	Log out of the analyzer panel.
	"""

	auth.logout(request)
	return redirect('internal:login')

@login_required()
def analyzer_profile(request):
	"""
	View for assistant profile page, which contains info
	about the assistant, such as email, name, and a list of
	all social media accounts that they evaluated.
	"""

	if not (_validate_perms(request.user) and
			_is_superuser(request.user) or is_assistant(request.user)):
		return redirect('main:perm_denied')

	user_id = int(request.user.id)
	if request.GET.get('page'):
		page_num = int(request.GET.get('page'))
	else:
		page_num = 1

	# get assistant profile info
	if _is_superuser(request.user):
		ratings = None
		(num_ratings, all_assistants_stats) = utils.get_all_assistant_info()
		stats = None
	else:
		ratings = utils.get_assistant_info(user_id)
		num_ratings = len(ratings)
		all_assistants_stats = None

		paginator = Paginator(ratings, 10)

		try:
			stats = paginator.page(page_num)
		except PageNotAnInteger:
			stats = paginator.page(1)
		except EmptyPage:
			stats = paginator.page(paginator.num_pages)

	return render(request, 'analyzer_assistant_profile.html', {
			'ratings': ratings,
			'num_ratings': num_ratings,
			'all_assistants_stats': all_assistants_stats,
			'stats': stats,

		})

@login_required()
def analyzer_instructions(request):
	"""
	View shows instructions to assistants.
	"""

	if not (_validate_perms(request.user) and
			_is_superuser(request.user) or is_assistant(request.user)):
		return redirect('main:perm_denied')

	return render(request, 'analyzer_dem_instructions_page.html', {})

@login_required()
def analyzer_evaluate_ui(request):
	"""
	View shows the actual UI for assistants to evaluate.
	"""

	if not (_validate_perms(request.user) and
			_is_superuser(request.user) or is_assistant(request.user)):
		return redirect('main:perm_denied')

	if request.method == 'POST':
		form = forms.IgFollowerRatingForm(request.POST)
		if form.is_valid():

			form2 = form.save(commit=False)

			# assign follower id
			follower_id = request.POST.get('follower_id')
			ig_follower = IgFollower.objects.get(id=follower_id)
			form2.ig_follower = ig_follower

			# assign assistant id
			user_id = request.user.id
			assistant = AuthUser.objects.filter(id=user_id)[0]
			form2.assistant = assistant

			form.save()

			# mark ig follower as ANALYZED
			follower_obj = IgFollower.objects.filter(id=follower_id)
			if follower_obj.exists():
				follower_obj = follower_obj.first()
				follower_obj.analyzed = 1
				follower_obj.save()

			return redirect('internal:evaluate_ui')
		else:
			return render(request, 'analyzer_dem_ui_page.html',
				{'form': form})
	elif request.method == 'GET':

		current_user = request.user
		follower = utils.getBatch(current_user)
		form = forms.IgFollowerRatingForm()

 		# mark ig follower as RETRIEVED
		follower_obj = IgFollower.objects.filter(id=follower['FOLLOWER_ID'])
		if follower_obj.exists():
			follower_obj = follower_obj.first()
			follower_obj.retrieved = 1
			follower_obj.save()

		ig_user = follower_obj.following
		follows_a_confirmed_influencer = VerifiedUserAccounts.objects.filter(account_id=ig_user.id).exists()

 		return render(request, 'analyzer_dem_ui_page.html',
			{'follower': follower, 'form': form, 
			'follows_a_confirmed_influencer': follows_a_confirmed_influencer})

def index_model(request):

	email = request.GET.get('email')
	uid = int(request.GET.get('uid'))
	network = request.GET.get('network')
	verified = request.GET.get('verified')

	if verified and verified != 'False':
		if network == 'ig':
			acc = VerifiedUserAccounts.objects.filter(network='ig', account_id=uid)
		elif network == 'tw':
			acc = VerifiedUserAccounts.objects.filter(network='tw', account_id=uid)
	else:
		if network == 'ig':
			acc = IgUsers.objects.filter(id=uid)
		elif network == 'tw':
			acc = TwUsers.objects.filter(id=uid)

	if acc.exists():
		acc.first().save()

	return HttpResponse(status=200)

@login_required()
def assistant_edit_influencer_add_remove_niches(request):
	"""
	Add/remove niches.

	Pseudocode:
	1) If confirmed (verified) niches exist, edit the confirmed niches
	2) Else if only unconfirmed (unverified) are available, edit only the unconfirmed niches
	"""

	social_flag = None
	if not (_validate_perms(request.user) and
			_is_superuser(request.user) or is_assistant(request.user)):
		return redirect('main:perm_denied')

	if request.method != 'POST':
		raise Http404

	usr_id = request.POST.get('usr_id')
	network = request.POST.get('network')
	username = request.POST.get('username')
	user_name = request.POST.get('user_name_field')

	#start new social account's username add
	fullname = request.POST.get('fullname')
	account_id = request.POST.get('account_id')
	tw_username = request.POST.get('twitter_username')
	fb_username = request.POST.get('facebook_username')
	yt_username = request.POST.get('youtube_username')

	if network == 'ig':
		ig_user = IgUsers.objects.filter(id=account_id).first()
		ig_user.username = user_name
		ig_user.save()
	elif network == 'tw':
		tw_user = TwUsers.objects.filter(id=account_id).first()
		tw_user.username = user_name
		tw_user.save()

	user_name_field = AssistantEditInfluencerUsernameForm({'user_name_field': user_name})
	if fullname == '' and tw_username == '' and yt_username == '' and fb_username == '':
		social_flag = False

	ig_user_social = IgUsersSocialAccounts.objects.filter(ig_userid=account_id)
	if ig_user_social.exists():
		ig_user_account = IgUsersSocialAccounts.objects.get(ig_userid=account_id)

		ig_user_account.fullname = fullname
		ig_user_account.tw_username = tw_username
		ig_user_account.fb_username = fb_username
		ig_user_account.yt_username = yt_username

		ig_user_account.save()
	else:
		if social_flag != False:
			IgUsersSocialAccounts.objects.create(fullname=fullname, tw_username=tw_username, fb_username=fb_username, yt_username=yt_username, ig_userid=account_id)

	fullname_form = AssistantEditInfluencerFullnameForm({'fullname': fullname})
	twitter_username_form = AssistantEditInfluencerTwitterForm({'twitter_username': tw_username})
	facebook_username_form = AssistantEditInfluencerFacebookForm({'facebook_username': fb_username})
	youtube_username_form = AssistantEditInfluencerYoutubeForm({'youtube_username': yt_username})
	#end new social account's username add

	acc = VerifiedUserAccounts.objects.filter(network=network, account_id=account_id). \
		prefetch_related('niches').first()

	# if account is verified, save only to verified niches
	# else if account is not verified, save as IgUserNiches and TwUserKeywords

	if not acc:
		if network == 'ig':
			acc = IgUsers.objects.filter(id=account_id).first()
		elif network == 'tw':
			acc = TwUsers.objects.filter(id=account_id).first()
		is_verified = False
	else:
		is_verified = True

	form = AssistantEditInfluencerForm(request.POST)
	if form.is_valid():
		# parse through niches and save
		new_niches = [x.strip() for x in form.cleaned_data['niches'].split(',')]

		if is_verified:
			# get all VerifiedUserNiches
			existing = [niche.niche for niche in acc.niches.all()]
		else:
			if network == 'ig':
				existing = [niche.hashtag for niche in acc.igusertags_set.all()]
			elif network == 'tw':
				existing = [niche.keyword for niche in acc.twuserkeywords_set.all()]

		# add niches
		for niche in new_niches:

			if not niche or niche in existing:
				continue

			if is_verified:
				try:
					new_niche = VerifiedUserNiches.objects.get(network=network, niche=niche)
				except ObjectDoesNotExist:
					new_niche = VerifiedUserNiches(niche=niche, network=network)
					new_niche.save()

				new_niche.verified_accounts.add(acc)
			else:
				if network == 'ig':
					try:
						new_niche = IgUserTags.objects.get(iguser=acc, hashtag=niche)
					except ObjectDoesNotExist:
						new_niche = IgUserTags(iguser=acc, hashtag=niche, userid=acc.userid, frequency=0)
						new_niche.save()
				elif network == 'tw':
					try:
						new_niche = TwUserKeywords.objects.get(twuser=acc, keyword=niche)
					except ObjectDoesNotExist:
						new_niche = TwUserKeywords(twuser=acc, keyword=niche, userid=acc.userid)
						new_niche.save()

		# remove niches
		for niche in existing:

			if niche not in new_niches:
				if is_verified:
					results = VerifiedUserNiches.objects.filter(network=network).filter(niche=niche).\
						filter(verified_accounts__id=acc.id)
				else:
					if network == 'ig':
						results = IgUserTags.objects.filter(iguser=acc, hashtag=niche)
					elif network == 'tw':
						results = TwUserKeywords.objects.filter(twuser=acc, keyword=niche)

				for result_niche in results:
					result_niche.delete()

		# return niches
		if '' != new_niches[0]:
			if is_verified:
				niches = utils.make_niches_str(utils.get_niches(acc))
			else:
				niches = utils.make_niches_str_unverified(utils.get_niches_unverified(acc, network), network)
		else:
			niches = ''

		new_niches = ','.join(new_niches)
		form.niches = new_niches

		# return email
		email = acc.email

		context = {
			'edit_infl_form': form,
			'fullname_form': fullname_form,
			'edit_twitter_username_form': twitter_username_form,
			'edit_facebook_username_form': facebook_username_form,
			'edit_youtube_username_form': youtube_username_form,
			'usr_id': account_id,
			'is_successful': True,
			'acc': model_to_dict(acc),
			'niches': new_niches,
			'username': user_name,
			'user_name_field': user_name_field,
			'email': email,
			'network': network,
			'is_verified': is_verified,
			'success': True
		}

		if niches == '':
			messages.success(request, 'Successfully saved niches to the database. To reflect these changes on the profile, please refresh the page.')
		else:
			messages.success(request, 'Successfully saved niches ({0}). To reflect these changes on the profile, please refresh the page.'.format(new_niches))
		return render(request, 'assistant_edit_influencer.html', context)

	# form not valid
	niches = utils.make_niches_str(utils.get_niches(acc, network, email))
	context = {
		'edit_infl_form': form,
		'fullname_form': fullname_form,
		'edit_twitter_username_form': twitter_username_form,
		'edit_facebook_username_form': facebook_username_form,
		'edit_youtube_username_form': youtube_username_form,
		'usr_id': account_id,
		'is_successful': True,
		'acc': model_to_dict(acc),
		'niches': niches,
		'username': user_name,
		'user_name_field': user_name_field,
		'email': email,
		'network': network,
		'success': False
	}
	messages.error(request, 'ERROR: Could not save niches!')
	return render(request, 'assistant_edit_influencer.html', context)

def get_most_popular_niches(num):
	"""
	Helper function that extracts the num most popular niches from the model
	IgUserTags.
	"""
	#Counting the number of times a niche is used at least once by a user.
	hashtag_count = IgUserTags.objects.values("hashtag").annotate(Count("id"))
	len_hasht_count = len(hashtag_count)
	niche_count_as_list = list(hashtag_count)
	sorted_niches_by_freq = []
	#Finding the most common niche.
	for ind in range(num):
		max_key = 0
		for i in range(len_hasht_count - ind):
			if niche_count_as_list[i]["id__count"] > niche_count_as_list[max_key]["id__count"]:
				max_key = i
		sorted_niches_by_freq.append(hashtag_count[max_key]["hashtag"])
		niche_count_as_list[max_key], niche_count_as_list[len_hasht_count-1-ind] = niche_count_as_list[len_hasht_count-num-1], niche_count_as_list[max_key]
		niche_count_as_list.pop(-1)

	return sorted_niches_by_freq

@login_required()
def assistant_edit_influencer(request, network, uid):
	"""
	GET method.

	Render a page for internal users to edit influencer info.
	"""

	if not (_validate_perms(request.user) and
			_is_superuser(request.user) or is_assistant(request.user)):
		return redirect('main:perm_denied')

	if not network:
		return HttpResponseNotFound('<h3>Please specify a social media network for this account.</h3>')
	if not uid:
		return HttpResponseNotFound('<h3>Please specify a valid account ID number.</h3>')

	usr_id = uid
	username = request.GET.get('username')
	most_popular_niches = get_most_popular_niches(50)

	user_name_field = AssistantEditInfluencerUsernameForm({'user_name_field': username})

	acc = VerifiedUserAccounts.objects.filter(network=network, account_id=usr_id).\
			prefetch_related('niches').first()

	if acc:
		is_verified = True
	else:
		if network == 'ig':
			acc = IgUsers.objects.filter(id=usr_id).first()
		elif network == 'tw':
			acc = TwUsers.objects.filter(id=usr_id).first()

		is_verified = False

	if not acc:
		return HttpResponseNotFound('<h3>Account not found.</h3>')

	try:
		if is_verified:
			m_niches = utils.make_niches_str(utils.get_niches(acc))
		else:
			m_niches = utils.make_niches_str_unverified(utils.get_niches_unverified(acc, network), network)

		m_niches = m_niches.lower()
		form = AssistantEditInfluencerForm({'niches': m_niches})

		#check other social account exist
		social_account = IgUsersSocialAccounts.objects.filter(ig_userid=usr_id)
		if social_account.exists():
			social_account = IgUsersSocialAccounts.objects.get(ig_userid=usr_id)
			twitter_username_form = AssistantEditInfluencerTwitterForm({'twitter_username': social_account.tw_username})
			facebook_username_form = AssistantEditInfluencerFacebookForm({'facebook_username': social_account.fb_username})
			youtube_username_form = AssistantEditInfluencerYoutubeForm({'youtube_username': social_account.yt_username})
			fullname_form = AssistantEditInfluencerFullnameForm({'fullname': social_account.fullname})
		else:
			twitter_username_form = AssistantEditInfluencerTwitterForm({'twitter_username': ''})
			facebook_username_form = AssistantEditInfluencerFacebookForm({'facebook_username': ''})
			youtube_username_form = AssistantEditInfluencerYoutubeForm({'youtube_username': ''})
			fullname_form = AssistantEditInfluencerFullnameForm({'fullname': ''})

	except Exception:
		m_niches = []
		form = AssistantEditInfluencerForm({'niches': ''})
		twitter_username_form = AssistantEditInfluencerTwitterForm({'twitter_username': ''})
		facebook_username_form = AssistantEditInfluencerFacebookForm({'facebook_username': ''})
		youtube_username_form = AssistantEditInfluencerYoutubeForm({'youtube_username': ''})
		fullname_form = AssistantEditInfluencerFullnameForm({'fullname': ''})

	# return email
	email = acc.email

	context = {
		'edit_infl_form': form,
		'edit_twitter_username_form': twitter_username_form,
		'edit_facebook_username_form': facebook_username_form,
		'edit_youtube_username_form': youtube_username_form,
		'fullname_form': fullname_form,
		'usr_id': usr_id,
		'acc': acc,
		'niches': m_niches,
		'username': username,
		'user_name_field': user_name_field,
		'most_popular_niches': most_popular_niches,
		'is_verified': is_verified,
		'network': network,
		'email': email,
	}

	return render(request, 'assistant_edit_influencer.html', context)

def scrape_pic_and_bio(request, username):
	"""
	Scrape Instagram profile pic and their bio
	"""

	if not (_validate_perms(request.user) and 
			_is_superuser(request.user) or is_assistant(request.user)):
		return redirect('main:perm_denied')

	if not username:
		raise PermissionDenied()

	data = json.dumps(IgProfileParser(username).\
			quick_scrape_ig_profile_picture_and_bio())

	return JsonResponse(data, safe=False)

class RetrieveInfluencersAlreadyAnalyzed(TemplateView):
	"""
	Retrieve a report for a list of influencers that have already
	been analyzed and also display how many followers were analyzed
	by assistants for those influencers.
	"""

	@method_decorator(permission_required('is_superuser'))
	def dispatch(self, request):
		return super(RetrieveInfluencersAlreadyAnalyzed, self).dispatch(request)

	def get(self, request, *args, **kwargs):

		data = self.get_finished_influencers()
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment;filename=report.csv'
		writer = csv.writer(response)
		writer.writerow(['ID', 'Username', 'Num followers', 'Num followers evaluated',])
		for cdr in data:
			writer.writerow([cdr['influencer_id'], cdr['influencer_username'], cdr['influencer_followers'], cdr['num_followers_evaluated'], ])

		return response

	def get_finished_influencers(self):
		"""
		Retrieve a list of users that have been analyzed
		by assistants.
		"""
		data = utils.get_finished_influencers()
		return data

class DeleteInfluencer(TemplateView):
	"""
	Delete an influencer.
	"""
	def get(self, request, *args, **kwargs):
		return HttpResponseForbidden('GET not allowed')

	def post(self, request, *args, **kwargs):
		
		if not (_validate_perms(request.user) and
				_is_superuser(request.user) or is_assistant(request.user)):
			return redirect('main:perm_denied')

		if not request.POST.get('unconfirmed_id') and \
				not request.POST.get('network'):
			raise HttpResponseForbidden('You did not provide enough info to perform this action')

		unconfirmed_id = int(request.POST.get('unconfirmed_id'))
		network = request.POST.get('network')

		# delete unconfirmed account
		if network == 'ig':
			acc = IgUsers.objects.filter(id=unconfirmed_id)
		elif network == 'tw':
			acc = TwUsers.objects.filter(id=unconfirmed_id)

		if acc.exists():
			try:
				acc.first().delete()
			except Exception as e:
				return HttpResponse(status=400, content=e)

		# delete confirmed account if exists
		verified = VerifiedUserAccounts.objects.filter(network=network, account_id=unconfirmed_id)
		if verified.exists():
			try:
				verified.first().delete()
			except Exception as e:
				return HttpResponse(status=400, content=e)

		return HttpResponse(status=200, content='Account successfully deleted.')