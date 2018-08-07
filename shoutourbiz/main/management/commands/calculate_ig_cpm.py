"""
This module stores the calculate_cpm command, which 
calculates the CPM of all verified users and stores that
value in the IgUsersCPM model.
"""

import os
import sys
import time

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from main.models import IgUsers, VerifiedUserAccounts
from main.utils import _calculate_cpm

def _add():
	all_verified_accounts = VerifiedUserAccounts.objects.filter(network='ig')

	for verified in all_verified_accounts:

		print 'current: ' + verified.email
		
		try:
			tmp_user = IgUsers.objects.filter(verified_acc_id=verified.id)[0]
		except Exception as e:
			print e
			import pdb; pdb.set_trace()

		tmp_cpm = _calculate_cpm(tmp_user)
		verified.cpm = tmp_cpm
		verified.save()

def _update_format():
	all_verified_accounts = VerifiedUserAccounts.objects.filter(network='ig')

	for verified in all_verified_accounts:

		print 'current: ' + verified.email
		
		try:
			tmp_user = IgUsers.objects.filter(verified_acc_id=verified.id)[0]
		except Exception as e:
			print e
			import pdb; pdb.set_trace()

		verified.cpm = round(verified.cpm, 2)
		verified.save()

class Command(BaseCommand):

	def add_arguments(self, parser):

		parser.add_argument(
			'--add',
			default=False,
			help='Add cpm'
		)
		parser.add_argument(
			'--update',
			default=False,
			help='Update cpm values'
		)

	def handle(self, *args, **options):
		if options['add']:
			_add()
		elif options['update']:
			_update_format()