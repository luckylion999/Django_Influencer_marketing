import pytz
import models as main_models

from decimal import Decimal

def dt_to_aware(dtobj):
    localtz = pytz.timezone('UTC')
    return localtz.localize(dtobj)

def calculate_engagement_stats_2(ig_user):
    """ avg likes per photo / num of follower """
    if ig_user.postavglike != None and ig_user.followers != None:
        if ig_user.postavglike == 0:
            return 0
        else:
            if ig_user.followers == 0:
                return -1
            else:
                stat = float(ig_user.postavglike) / float(ig_user.followers)
                return stat
    else:
        return None

def calculate_engagement_stats_for_verified_users(verified_user):

    if verified_user.network != 'ig':
        return -2
        
    ig_user = main_models.IgUsers.objects.filter(id=verified_user.account_id).first()

    if not ig_user:
        return -2

    if ig_user.postavglike != None and ig_user.followers != None:
        if ig_user.postavglike == 0:
            return 0
        else:
            if ig_user.followers == 0:
                return -1
            else:
                stat = float(ig_user.postavglike) / float(ig_user.followers)
                return stat
    else:
        return None

def calculate_cpm_before_save(verified_account):

    if not isinstance(verified_account, main_models.VerifiedUserAccounts):
        return -1

    if verified_account.network == 'ig':
        account = main_models.IgUsers.objects.filter(id=verified_account.account_id).first()
    elif verified_account.network == 'tw':
        account = main_models.TwUsers.objects.filter(id=verified_account.account_id).first()

    if account.followers > 0 and account.followers < 1000:
        ratio = 6.262
    elif account.followers >= 1000 and account.followers < 10000:
        ratio = 15
    elif account.followers >= 10000 and account.followers < 20000:
        ratio = 24.5
    elif account.followers >= 20000 and account.followers < 100000:
        ratio = 4.86
    elif account.followers >= 100000 and account.followers < 1000000:
        ratio = 21.06
    elif account.followers >= 1000000 and account.followers < 10000000:
        ratio = 10.64
    elif account.followers >= 10000000 and account.followers < 50000000:
        ratio = 25.6
    elif account.followers >= 50000000:
        ratio = 10
    else:
        return -1

    num_views_per_thousand = (Decimal(account.followers) / Decimal(ratio)) / 1000

    # get price of running add
    price = Decimal(verified_account.price)

    # calculate cpm
    cpm = price / Decimal(num_views_per_thousand)

    return cpm