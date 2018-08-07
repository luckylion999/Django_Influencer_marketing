"""
This module contains models relevant
to the demographics analyzer.
"""

from django.db import models
from django_countries.fields import CountryField
from django_countries import Countries
from django.contrib.auth.models import User

from datetime import date

from main.models import AuthUser, IgFollower

class IgFollowerRating(models.Model):
	"""
	Stores the ratings that assistants give
	to the Instagram account.
	"""

	AGE_GROUP_CHOICES = [
		('U', 'Unknown'),
		('0-17', '0-17'),
		('18-24', '18-24'),
		('25-34', '25-34'),
		('35-44', '35-44'),
		('45-54', '45-54'),
		('55+', '55+')
	]

	GENDER_CHOICES = [
		('U', 'Unknown'),
		('M', 'Male'),
		('F', 'Female')
	]

	ig_follower = models.ForeignKey(IgFollower, null=True, on_delete=models.CASCADE)
	assistant = models.ForeignKey(AuthUser, null=True, on_delete=models.CASCADE)

	age_group = models.CharField(max_length=10, choices=AGE_GROUP_CHOICES)
	country = CountryField(blank_label='Unknown', blank=True)
	gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
	date_created = models.DateField(auto_now_add=True, null=True)

	class Meta:
		db_table = 'ig_follower_rating'