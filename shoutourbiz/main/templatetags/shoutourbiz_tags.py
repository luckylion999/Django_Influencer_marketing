import ast
import random

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.exceptions import ObjectDoesNotExist

from decimal import Decimal

from main.models import VerifiedUserNiches, IgUserTags, TwUserKeywords, IgUsers, TwUsers, VerifiedUserAccounts
from main.utils import _calculate_cpm

register = template.Library()

@register.filter
def round_to_thouthands(value):
    if value > 1000:
        float_val = value / 100.0
        float_val = round(float_val)
        value = int(float_val * 100)
    return value

@register.filter
def get_niches(obj):

    try:
        if not obj.verified_acc:
            return []
    except ObjectDoesNotExist as e:
        return None

    niches = [niche.niche for niche in obj.verified_acc.niches.all()]
    niches = ', '.join(niches)
    return niches

def _get_unverified_niches(network, obj):
    if network == 'ig':
        niches = [x.hashtag for x in obj.igusertags_set.all()]
    elif network == 'tw':
        niches = [x.keyword for x in obj.twuserkeywords_set.all()]
    return niches

@register.filter
def get_niches_arr(obj):
    if isinstance(obj, IgUsers):
        network = 'ig'
    elif isinstance(obj, TwUsers):
        network = 'tw'

    try:
        if obj.verified_acc:
            niches = [niche.niche for niche in obj.verified_acc.niches.all()]
            if not niches:
                niches = _get_unverified_niches(network, obj)
            return niches[:5]
        else:
            return _get_unverified_niches(network, obj)[:5]

    except Exception as e:
        return []

@register.filter
def get_niches_arr_top_5(niches, network):

    if not niches:
        return ''

    try:
        niches = [niche.niche for niche in niches][:5]
    except Exception as e:
        if network == 'ig':
            niches = [niche.hashtag for niche in niches][:5]
        elif network == 'tw':
            niches = [niche.keyword for niche in niches][:5]

    return ','.join(niches)

@register.filter
def get_niches_str(arr):
    return arr.join(',')

@register.filter
def starred(value):

    if not value:
        return ''
        
    new_val = '*' * len(value)
    return new_val

@register.filter
def currency(dollars):
    dollars = round(float(str(dollars)), 2)
    return "%s%s" % (intcomma(int(dollars)), ("%0.2f" % dollars)[-3:])

@register.filter
def calculate_cpm(account):
    return _calculate_cpm(account)

@register.filter
def is_assistant_tag(user):
    if user.groups.filter(name='assistant').exists():
        return True
    return False

@register.filter
def subtract(value, arg):
    return value - arg

@register.filter
def convert_text_to_array(n_str):
    try:
        arr = [n.strip() for n in ast.literal_eval(n_str)][:5]
    except (SyntaxError, ValueError) as e:
        arr = n_str.split(' ')[:5]
    return arr

@register.filter
def get_obj_from_index(index_obj):

    if index_obj.verified > 0:
        if index_obj.network == 'ig':
            obj = VerifiedUserAccounts.objects.filter(network='ig', email=index_obj.email, account_id=index_obj.iid)
            if obj.exists():
                return obj.first()
            else:
                return None
        elif index_obj.network == 'tw':
            obj = VerifiedUserAccounts.objects.filter(network='tw', email=index_obj.email, account_id=index_obj.iid)
            if obj.exists():
                return obj.first()
            else:
                return None
    else:
        if index_obj.network == 'ig':
            obj = IgUsers.objects.filter(network='ig', id=index_obj.iid)
            if obj.exists():
                return obj.first()
            else:
                return None
        elif index_obj.network == 'tw':
            obj = TwUsers.objects.filter(network='tw', id=index_obj.iid)
            if obj.exists():
                return obj.first()
            else:
                return None

@register.filter
def get_verified_niches_arr(verified_acc):
    
    if not verified_acc:
        return []
    
    return [niche.niche for niche in verified_acc.niches.all()]

@register.filter
def first_five(arr):

    if not arr:
        return []
        
    return arr[:5]

@register.filter
def percentage(value):
    if value is None or value < 0:
        return -1
        
    return str(round(value * 100, 2))

@register.filter
def exists(obj):
    return True if obj else False

@register.filter
def randomize(word):
    """
    Randomize a word.
    """
    if not word:
        return ''
    return ''.join(random.sample(word, len(word)))