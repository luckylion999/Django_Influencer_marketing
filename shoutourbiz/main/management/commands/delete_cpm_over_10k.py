"""
Deletes any user with CPM over $10,000.
"""

import os
import sys
import time
import logging

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from main.models import IgUsers, VerifiedUserAccounts

class Command(BaseCommand):

	def handle(self, *args, **options):

		verified_accounts = VerifiedUserAccounts.objects.all()

		for user in verified_accounts:
			
			if user.cpm >= 10000:

				# find corresponding IG account and delete
				ig_account = IgUsers.objects.filter(id=user.account_id)
				if ig_account.exists():
					ig_account = ig_account.first()
					ig_account.delete()

					# finally, delete the verified account also
					user.delete()

					print '-- Deleted verified {0} | IG {1} | email {2} | cpm {3}'.format(user.id, ig_account.id, user.email, user.cpm)

				else:
					print '-- Deleted verified {0} | IG not found | email {1} | cpm {2}'.format(user.id, user.email, user.cpm)