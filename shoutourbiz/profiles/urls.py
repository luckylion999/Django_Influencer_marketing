from django.conf.urls import url
from django.conf.urls import include
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth import views as auth_views

from . import forms
from . import views

urlpatterns = [
    url(r'^(?P<network>\w{2})/(?P<uid>\d+)/', views.influencer_details, name='influencer_details'),
    url(r'^unlock/(?P<network>\w{2})/(?P<uid>\d+)/$', views.unlock_influencer, name='unlock_influencer'),
    url(r'^charts/age_group/(?P<uid>\d+)/$', views.age_group_chart, name='age_group_chart'),
    url(r'^charts/engagement/(?P<uid>\d+)/$', views.engagement_chart, name='engagement_chart'),
    url(r'^charts/gender/(?P<uid>\d+)/$', views.gender_chart, name='gender_chart'),
    url(r'^charts/trends/(?P<network>\w{2})/(?P<uid>\d+)/$', views.trends_chart, name='trends_chart'),
    url(r'^charts/country/(?P<uid>\d+)/$', views.country_chart, name='country_chart'),
    url(r'^charts/profile_pic/(?P<uid>\d+)/$', views.get_ig_profile_pic, name='ig_profile_pic'),
    url(r'^charts/followers/(?P<uid>\d+)/$', views.followers_trend_chart, name='followers_trend_chart'),
]