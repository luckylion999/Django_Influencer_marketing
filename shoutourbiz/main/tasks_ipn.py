from celery import shared_task
from .models import Payment, AuthUser, SubscriptionData, BuyerUses
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from decimal import Decimal
from datetime import datetime, date
from .utils import calcul_new_date
from .utils_helper import dt_to_aware
import time
from django.contrib.auth.models import Group


@shared_task
def add_subscription(usr_id, receipt, timestamp):
    for i in range(3):
        try:
            payment = Payment.objects.get(active=True, receipt=receipt)
        except ObjectDoesNotExist:
            if i == 2:
                return
            time.sleep(30)
        else:
            break
    user = AuthUser.objects.get(id=usr_id)
    try:
        plan = settings.PAYMENT_PLANS[payment.amount]
    except KeyError:
        amount = Decimal(payment.amount)
        plan = None
        for key, value in settings.PAYMENT_PLANS.items():
            if amount > Decimal(key):
                plan = value
            else:
                break
        if not plan:
            print 'No payment plan was found. Payment id: {}'.format(payment.id)
            return
    plan_uses = plan[0]
    plan_period = plan[1]
    completed_bills = Payment.objects.filter(receipt=receipt, recur=True).count()
    paid_months = plan_period + completed_bills
    payment_time = datetime.fromtimestamp(int(timestamp))
    payment_time = dt_to_aware(payment_time)
    end_date = calcul_new_date(payment_time, paid_months)

    try:
        subscr = SubscriptionData.objects.get(user=user)
    except:
        # create subscription here
        subscr = SubscriptionData(user=user, started=payment_time,
                                  end=end_date, month_uses=plan_uses,
                                  payment_perdiod=plan_period, receipt=receipt)
    else:
        subscr.month_uses = plan_uses
        subscr.payment_period = plan_period
        subscr.started = payment_time
        subscr.end = end_date
        subscr.receipt = receipt
    subscr.save()
    uses = BuyerUses.objects.filter(uid=user)
    uses_num = plan_uses
    if uses.exists():
        uses = uses[0]
        uses.uses = uses_num
    else:
        uses = BuyerUses(uid=user, uses=uses_num)
    uses.save()
    buyer_group = Group.objects.get_or_create(name='month_buyer')[0]
    user.groups.add(buyer_group)
    user.save()
    payment.active = False
    payment.save()