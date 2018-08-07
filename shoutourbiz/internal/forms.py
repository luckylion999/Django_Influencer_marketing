"""
This module contains forms relevant to the
demographics analyzer.
"""

from django import forms
from .models import IgFollowerRating

from django_countries.widgets import CountrySelectWidget

class IgFollowerRatingForm(forms.ModelForm):
	"""
	Form stores ratings for Instagram users.
	"""

	class Meta:
		model = IgFollowerRating
		fields = ['age_group', 'country', 'gender']
		widgets = {'country': CountrySelectWidget()}
		exclude = ('ig_follower', 'assistant',)

class AssistantEditInfluencerForm(forms.Form):
    niches = forms.CharField(help_text='Separate each niche with a comma.',
                       required=False,
                       widget=forms.Textarea);

class AssistantEditInfluencerTwitterForm(forms.Form):
	twitter_username = forms.CharField(required=False,
							 widget=forms.TextInput);

class AssistantEditInfluencerFacebookForm(forms.Form):
	facebook_username = forms.CharField(required=False,
							 widget=forms.TextInput);

class AssistantEditInfluencerYoutubeForm(forms.Form):
	youtube_username = forms.CharField(required=False,
							 widget=forms.TextInput);

class AssistantEditInfluencerFullnameForm(forms.Form):
	fullname = forms.CharField(required=False,
							 widget=forms.TextInput);

class AssistantEditInfluencerUsernameForm(forms.Form):
	user_name_field = forms.CharField(required=False,
							widget=forms.TextInput);