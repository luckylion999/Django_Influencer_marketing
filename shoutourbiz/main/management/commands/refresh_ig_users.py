"""
Calculates (or recalculates) the engagement percent
for IgUsers, TwUsers, and VerifiedUserAccounts
"""

import os
import sys
import time
import logging

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from main.models import IgUsers, TwUsers, VerifiedUserAccounts

logging.basicConfig(level=logging.DEBUG, filename="refresh_ig_users.log", 
	filemode="a+", format="%(asctime)-15s %(message)s")

NUM_STEPS = 100

class Command(BaseCommand):

	def refresh(self, start_ndx):
		global NUM_STEPS

		print 'Start ndx: {0}'.format(start_ndx)

		all_count = IgUsers.objects.all().count()
		current_ndx = start_ndx

		while current_ndx < all_count:

			accs = IgUsers.objects.all()[current_ndx: current_ndx + NUM_STEPS]

			for user in accs:
				user.save()

				if current_ndx % 5 == 0:
					print '-- #{0} {1} {2}'.format(user.id, user.email, user.engagement)
					logging.error('-- #{0} {1} {2}'.format(user.id, user.email, user.engagement))
					
				current_ndx += 1

	def refresh_zeroes(self, start_ndx):
		global NUM_STEPS

		print 'refresh zeroes'
		print 'Start ndx: {0}'.format(start_ndx)

		all_count = IgUsers.objects.all().count()
		current_ndx = start_ndx

		while current_ndx < all_count:

			accs = IgUsers.objects.filter(engagement=0)[current_ndx: current_ndx + NUM_STEPS]

			for user in accs:
				user.save()

				if current_ndx % 5 == 0:
					print '-- #{0} {1} {2}'.format(user.id, user.email, user.engagement)
					logging.error('-- #{0} {1} {2}'.format(user.id, user.email, user.engagement))
					
				current_ndx += 1

	def add_arguments(self, parser):

		parser.add_argument(
			'--all',
			default=False,
		)

		parser.add_argument(
			'--ndx',
			default=False,
			help='Start index'
		)

	def handle(self, *args, **options):

		if options['ndx'] is not None:
			if options['all'] is not None:
				self.refresh(int(options['ndx']))
			else:
				self.refresh_zeroes(int(options['ndx']))