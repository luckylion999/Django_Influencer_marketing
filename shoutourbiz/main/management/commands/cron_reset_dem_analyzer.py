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

logging.basicConfig(level=logging.DEBUG, filename="cron_reset_dem_analyzer.log", 
	filemode="a+", format="%(asctime)-15s %(message)s")

def _reset():
	logging.debug('............ RESETTING THE DEM ANALYZER ............')

	followers = IgFollower.objects.filter(analyzed=0, retrieved=1)

	for follower in followers:
		logging.debug('Resetting {0}:{1}'.format(follower.id, follower.username))
		follower.retrieved = 0
		follower.analyzed = 0
		follower.save()

class Command(BaseCommand):

	def handle(self, *args, **options):
		try:
			_reset()
		except Exception as e:
			logging.debug(e)