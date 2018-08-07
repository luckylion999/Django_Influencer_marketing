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

class Command(BaseCommand):

	def remove(self):
		
		accs = IgUsers.objects.filter(username__contains='@')

		for acc in accs:
			print '{0} - {1}'.format(acc.id, acc.username)

			# if @ account has a corresponding account without the '@'
			acc2 = IgUsers.objects.filter(username=acc.username.replace('@', ''))
			if not acc2.exists():
				continue

			acc2 = acc2.first()

			# if '@' account connects to a corresponding verified account
			verified_accs = VerifiedUserAccounts.objects.filter(network='ig', account_id=acc.id)

			# if '' account connects to a corresponding verified account
			verified_accs_wo =  VerifiedUserAccounts.objects.filter(network='ig', account_id=acc2.id)
			if verified_accs_wo.exists():
				if verified_accs.exists():
					verified_accs.delete()
					continue

			if verified_accs.exists():

				if len(verified_accs) > 1:
					print 'Verified user {0} registered more than once ({1}'.format(verified_accs.first().id, len(verified_accs))
					for ndx in range(len(verified_accs)):
						if ndx == 0:
							continue
						print 'Deleting {1}'.format(ndx)
						verified_accs[ndx].delete()

				else:
					verified = verified_accs.first()
					# connect the verified account to the account without the '@'
					verified.account_id = acc2.id
					verified.save()

				print 'Verified {0} now connected with {1} - {2}'.format(verified.id, acc2.id, acc2.username)

		print 'Initial total: {0}'.format(len(accs))

	def handle(self, *args, **options):
		self.remove()