import os
import sys
import django
sys.path.insert(0, '../shoutourbiz')
os.environ['DJANGO_SETTINGS_MODULE'] = 'local_settings'
django.setup()

from main.models import VerifiedUserAccounts, VerifiedUserNiches, IgUsers, TwUsers

va = VerifiedUserAccounts.objects.all()


def test_verified_accounts_correspond_to_soc_network_accs():
    attrs_map = {'ig': 'ig_user', 'tw': 'tw_user'}
    models_map = {'ig': IgUsers, 'tw': TwUsers}
    accs = VerifiedUserAccounts.objects.all()
    for acc in accs:
        attr = attrs_map[acc.network]
        Model = models_map[acc.network]
        try:
            network_acc = getattr(acc, attr)
            print network_acc.id, acc.account_id
            assert str(network_acc.id) == acc.account_id
        except Model.DoesNotExist:
            print 'bla'

test_verified_accounts_correspond_to_soc_network_accs()


# print fail_count
# print topfails
# print not_exist

# def forwards_func(apps, schema_editor):
#     IgUsers = apps.get_model('main', 'IgUsers')
#     TwUsers = apps.get_model('main', 'TwUsers')
#     models_map = {'tw': TwUsers, 'ig': IgUsers}
#     attr_map = {'tw': 'tw_user', 'ig': 'ig_user'}
#     VerifiedUserAccounts = apps.get_model('main', 'VerifiedUserAccounts')
#     Niches = apps.get_model('main', 'VerifiedUserNiches')
#     accs = VerifiedUserAccounts.objects.all()
#     count = 0
#     for obj in accs:
#         Model = models_map[obj.network]
#         # niches = Niches.objects.filter(verified_accounts__id__in=[obj.id])
#         # for niche in niches:
#         #     niche.verified_accounts.remove(obj)
#         #     print('ok')
#         acc = Model.objects.filter(email=obj.email)
#             # count += 1
#             # print count
#         if not acc.exists():
#             print 'deleting'
#             niches = Niches.objects.filter(verified_accounts__id__in=[obj.id])
#             print niches
#             for niche in niches:
#                 niche.verified_accounts.remove(obj)
#             obj.delete()
