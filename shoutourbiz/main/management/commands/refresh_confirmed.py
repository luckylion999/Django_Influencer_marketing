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

logging.basicConfig(level=logging.DEBUG, filename="refresh_confirmed.log", 
	filemode="a+", format="%(asctime)-15s %(message)s")

NUM_STEPS = 100

class Command(BaseCommand):

	def refresh(self, start_ndx):
		global NUM_STEPS

		all_count = VerifiedUserAccounts.objects.all().count()
		current_ndx = start_ndx

		while current_ndx < all_count:
			
			verified_accounts = VerifiedUserAccounts.objects.all()[current_ndx: current_ndx + NUM_STEPS]

			for user in verified_accounts:
				# saving IgUsers will automatically save the verified account as well
				ig_user = IgUsers.objects.filter(id=user.account_id)
				if not ig_user.exists():
					user.save()
				else:
					ig_user.first().save()

				if current_ndx % 5 == 0:
					print '-- #{0} {1}'.format(user.id, user.email)
					logging.error('-- #{0} {1}'.format(user.id, user.email))
					
				current_ndx += 1

	def add_arguments(self, parser):

		parser.add_argument(
			'--ndx',
			default=False,
			help='Start index'
		)

	def handle(self, *args, **options):

		if options['ndx'] is not None:
			self.refresh(int(options['ndx']))