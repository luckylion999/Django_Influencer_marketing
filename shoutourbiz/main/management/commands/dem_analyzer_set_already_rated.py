"""
This module resets the demographic analyzer.
For any instagram followers that are retrieved (retrieved=1)
but not analyzed (analyzed=0), it resets retrieved=0.
"""

import os
import sys
import time
import logging

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from main.models import IgFollower
from internal.models import IgFollowerRating

def _reset():
	print('............ SET ALREADY RATED ............')

	ratings = IgFollowerRating.objects.all()
	for rating in ratings:
		print 'Rating: {0}'.format(rating.id)
		follower = rating.ig_follower
		print 'Setting follower {0}:{1}'.format(follower.id, follower.username)
		follower.retrieved = 1
		follower.analyzed = 1
		follower.save()

class Command(BaseCommand):

	def handle(self, *args, **options):
		try:
			_reset()
		except Exception as e:
			print e