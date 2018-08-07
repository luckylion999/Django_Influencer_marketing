import json

from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.encoding import smart_str
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

import stripe

from . import settings as app_settings
from .forms import PlanForm
from .models import (
    Customer,
    CurrentSubscription,
    Event,
    EventProcessingException
)
from main.models import *
stripe.api_key = settings.STRIPE_SECRET_KEY



class PaymentsContextMixin(object):

    def get_context_data(self, **kwargs):
        context = super(PaymentsContextMixin, self).get_context_data(**kwargs)
        context.update({
            "STRIPE_PUBLIC_KEY": app_settings.STRIPE_PUBLIC_KEY,
            "PLAN_CHOICES": app_settings.PLAN_CHOICES,
            "PAYMENT_PLANS": app_settings.PAYMENTS_PLANS
        })
        return context


def _ajax_response(request, template, **kwargs):
    response = {
        "html": render_to_string(
            template,
            RequestContext(request, kwargs)
        )
    }
    if "location" in kwargs:
        response.update({"location": kwargs["location"]})
    return HttpResponse(response.get('html'))


class SubscribeView(PaymentsContextMixin, TemplateView):
    template_name = "payments/subscribe.html"

    def get_context_data(self, **kwargs):
        context = super(SubscribeView, self).get_context_data(**kwargs)
        customer = None
        auth_user_id = self.request.user.id
        if BuyerCredits.objects.filter(buyer_id=auth_user_id).exists():
            credit_user = BuyerCredits.objects.get(buyer_id=auth_user_id)
            credits = credit_user.buyer_credits
        else:
            credits = 0
        if hasattr(self.request.user, 'customer'):
            customer = self.request.user.customer
        else:
            customer = None
        context.update({
            "customer": customer,
            "form": PlanForm,
            "credits": credits,
        })
        return context


class ChangeCardView(PaymentsContextMixin, TemplateView):
    template_name = "payments/change_card.html"

    def get_context_data(self, **kwargs):
        context = super(ChangeCardView, self).get_context_data(**kwargs)
        auth_user_id = self.request.user.id
        if BuyerCredits.objects.filter(buyer_id=auth_user_id).exists():
            credit_user = BuyerCredits.objects.get(buyer_id=auth_user_id)
            credits = credit_user.buyer_credits
        else:
            credits = 0

        context.update({
            "credits": credits,
        })
        return context


class CancelView(PaymentsContextMixin, TemplateView):
    template_name = "payments/cancel.html"

    def get_context_data(self, **kwargs):
        context = super(CancelView, self).get_context_data(**kwargs)
        auth_user_id = self.request.user.id
        if BuyerCredits.objects.filter(buyer_id=auth_user_id).exists():
            credit_user = BuyerCredits.objects.get(buyer_id=auth_user_id)
            credits = credit_user.buyer_credits
        else:
            credits = 0

        context.update({
            "credits": credits,
        })
        return context


class ChangePlanView(SubscribeView):
    template_name = "payments/change_plan.html"

    def get_context_data(self, **kwargs):
        context = super(ChangePlanView, self).get_context_data(**kwargs)
        auth_user_id = self.request.user.id
        if BuyerCredits.objects.filter(buyer_id=auth_user_id).exists():
            credit_user = BuyerCredits.objects.get(buyer_id=auth_user_id)
            credits = credit_user.buyer_credits
        else:
            credits = 0
        context.update({
            "credits": credits,
        })
        return context


class HistoryView(PaymentsContextMixin, TemplateView):
    template_name = "payments/history.html"

    def get_context_data(self, **kwargs):
        context = super(HistoryView, self).get_context_data(**kwargs)
        auth_user_id = self.request.user.id
        if BuyerCredits.objects.filter(buyer_id=auth_user_id).exists():
            credit_user = BuyerCredits.objects.get(buyer_id=auth_user_id)
            credits = credit_user.buyer_credits
        else:
            credits = 0

        context.update({
            "credits": credits,
        })
        return context


@require_POST
@login_required
def change_card(request):
    auth_user_id = request.user.id
    if BuyerCredits.objects.filter(buyer_id=auth_user_id).exists():
        credit_user = BuyerCredits.objects.get(buyer_id=auth_user_id)
        credits = credit_user.buyer_credits
    else:
        credits = 0
    try:
        customer = request.user.customer
        send_invoice = customer.card_fingerprint == ""
        customer.update_card(
            request.POST.get("stripe_token")
        )
        if send_invoice:
            customer.send_invoice()
        customer.retry_unpaid_invoices()
        data = {}
    except stripe.CardError as e:
        data = {"error": smart_str(e)}
    data["credits"] = credits
    return _ajax_response(request, "payments/change_card.html", **data)


@require_POST
@login_required
def change_plan(request):
    form = PlanForm(request.POST)
    try:
        current_plan = request.user.customer.current_subscription.plan
    except CurrentSubscription.DoesNotExist:
        current_plan = None
    if form.is_valid():
        try:
            request.user.customer.subscribe(form.cleaned_data["plan"])
            if request.user.customer.current_subscription:
                plan = request.user.customer.current_subscription.plan
                buyer_id = request.user.id
                if (plan == 'INTRO'):
                    buyer_credits = 250
                elif (plan == "SILVER"):
                    buyer_credits = 500
                elif (plan == "GOLD"):
                    buyer_credits = 1000
                if BuyerCredits.objects.filter(buyer_id=buyer_id).exists():
                    BuyerCredits.objects.filter(buyer_id=buyer_id).update(buyer_credits=buyer_credits)
                else:
                    buyer = BuyerCredits.objects.create(buyer_id=buyer_id, buyer_credits=buyer_credits, )
            data = {
                "form": PlanForm(initial={"plan": form.cleaned_data["plan"]}),
            }
        except stripe.StripeError as e:
            data = {
                "form": PlanForm(initial={"plan": current_plan}),
                "error": smart_str(e),
            }
    else:
        data = {
            "form": form,
        }
    auth_user_id = request.user.id
    if BuyerCredits.objects.filter(buyer_id=auth_user_id).exists():
        credit_user = BuyerCredits.objects.get(buyer_id=auth_user_id)
        credits = credit_user.buyer_credits
    else:
        credits = 0
    data["credits"] = credits
    return _ajax_response(request, "payments/change_plan.html", **data)


@require_POST
@login_required
def subscribe(request, form_class=PlanForm):

    data = {"plans": settings.PAYMENTS_PLANS}
    form = form_class(request.POST)
    if form.is_valid():
        try:
            try:
                customer = request.user.customer
            except ObjectDoesNotExist:
                customer = Customer.create(request.user)
            if request.POST.get("stripe_token"):
                customer.update_card(request.POST.get("stripe_token"))
            if (request.POST.get("coupon_id") == "JOSH"):
                customer.subscribe(plan=form.cleaned_data["plan"], coupon=request.POST.get("coupon_id"))
            else:
                customer.subscribe(form.cleaned_data["plan"])
            if customer.current_subscription:
                plan = customer.current_subscription.plan
                buyer_id = request.user.id
                if (plan == 'INTRO'):
                    buyer_credits = 250
                elif (plan == "SILVER"):
                    buyer_credits = 500
                elif (plan == "GOLD"):
                    buyer_credits = 1000
                if BuyerCredits.objects.filter(buyer_id=buyer_id).exists():
                    BuyerCredits.objects.filter(buyer_id=buyer_id).update(buyer_credits=buyer_credits)
                else:
                    buyer = BuyerCredits.objects.create(buyer_id=buyer_id, buyer_credits=buyer_credits, )
            data["form"] = form_class()
            if hasattr(request.user, 'customer'):
                customer = request.user.customer
            else:
                customer = None
            data["customer"] = customer
        except stripe.StripeError as e:
            if hasattr(request.user, 'customer'):
                customer = request.user.customer
            else:
                customer = None
            data["customer"] = customer
            data["form"] = form
            data["error"] = smart_str(e) or "Unknown error"
    else:
        if hasattr(request.user, 'customer'):
            customer = request.user.customer
        else:
            customer = None
        data["customer"] = customer
        data["error"] = form.errors
        data["form"] = form
    auth_user_id = request.user.id
    if BuyerCredits.objects.filter(buyer_id=auth_user_id).exists():
        credit_user = BuyerCredits.objects.get(buyer_id=auth_user_id)
        credits = credit_user.buyer_credits
    else:
        credits = 0
    data["credits"] = credits
    return _ajax_response(request, "payments/subscribe.html", **data)


@require_POST
@login_required
def cancel(request):
    auth_user_id = request.user.id
    if BuyerCredits.objects.filter(buyer_id=auth_user_id).exists():
        credit_user = BuyerCredits.objects.get(buyer_id=auth_user_id)
        credits = credit_user.buyer_credits
    else:
        credits = 0
    try:
        request.user.customer.cancel()
        data = {}
    except stripe.StripeError as e:
        data = {"error": smart_str(e)}
    data["credits"] = credits
    return _ajax_response(request, "payments/cancel.html", **data)


@csrf_exempt
@require_POST
def webhook(request):
    data = json.loads(smart_str(request.body))
    if Event.objects.filter(stripe_id=data["id"]).exists():
        EventProcessingException.objects.create(
            data=data,
            message="Duplicate event record",
            traceback=""
        )
    else:
        event = Event.objects.create(
            stripe_id=data["id"],
            kind=data["type"],
            livemode=data["livemode"],
            webhook_message=data
        )
        event.validate()
        event.process()
    return HttpResponse()
