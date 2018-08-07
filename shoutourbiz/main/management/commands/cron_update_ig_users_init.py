from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

import requests
import re
import os
import time
import json
import datetime
import random
import logging

from main.models import IgUsers, IgFollowerTrend

NUM_STEPS = 100

class Command(BaseCommand):

	def add_arguments(self, parser):
		parser.add_argument('startndx', nargs=1, type=int)

	def _get_data(self, ndx):
		global NUM_STEPS
		return IgUsers.objects.all()[ndx : ndx + NUM_STEPS]

	def handle(self, *args, **options):
		global current_ndx, timekeeper, total_inserted, half_hour_timer

		if options['startndx'][0] is not None:
			current_ndx = options['startndx'][0]

		while current_ndx < IgUsers.objects.all().count():

			users = self._get_data(current_ndx)
			for user in users:

				if current_ndx % 10 == 0:
					print '--- {0}: {1} ---'.format(current_ndx, user.username)

				if not IgFollowerTrend.objects.filter(ig_user=user).exists():
					trend = IgFollowerTrend()
					trend.ig_user = user
					trend.num_followers = user.followers
					trend.save()

				current_ndx += 1