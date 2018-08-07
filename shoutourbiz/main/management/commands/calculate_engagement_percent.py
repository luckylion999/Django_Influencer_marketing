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

logging.basicConfig(level=logging.DEBUG, filename="calculate_engagement_percent.log", 
	filemode="a+", format="%(asctime)-15s %(message)s")

NUM_STEPS = 100

class Command(BaseCommand):

	def refresh(self, start_ndx):
		global NUM_STEPS

		all_count = IgUsers.objects.all().count()
		current_ndx = start_ndx

		while current_ndx < all_count:

			ig_users = IgUsers.objects.all()[current_ndx: current_ndx + NUM_STEPS]

			for user in ig_users:
				user.save()

				if current_ndx % 5 == 0:
					print '-- #{0} {1} {2}'.format(user.id, user.username, user.engagement)
					logging.error('-- #{0} {1} {2}'.format(user.id, user.username, user.engagement))
					
				current_ndx += 1

	def add_arguments(self, parser):

		parser.add_argument(
			'--ig',
			default=False,
			help='Calculate engagement for ig'
		)

	def handle(self, *args, **options):

		if options['ig'][0] is not None:
			self.refresh(int(options['ig']))