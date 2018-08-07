from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.decorators import login_required, permission_required

from . import views

urlpatterns = [
	url(r'^login/$', views.analyzer_login, name='login'),
	url(r'^logout/$', views.analyzer_logout, name='logout'),
	url(r'^signup/$', views.analyzer_signup, name='signup'),
	url(r'^profile/$', views.analyzer_profile, name='profile'),
	url(r'^dem/$', views.analyzer_instructions, name='dem'),
	url(r'^dem/evaluate_ui/$', views.analyzer_evaluate_ui, name='evaluate_ui'),
	url(r'^dem/evaluate_ui/scrape_pic_and_bio/(?P<username>.+)/$', views.scrape_pic_and_bio, name='scrape_pic_and_bio'),
	url(r'^influencer/edit/(?P<network>\w{2})/(?P<uid>\d+)/', views.assistant_edit_influencer, name='assistant_edit_influencer'),
	url(r'^influencer/edit_post/', views.assistant_edit_influencer_add_remove_niches, name='assistant_edit_influencer_post'),
	url(r'^retrieve_influencers_already_analyzed/$', views.RetrieveInfluencersAlreadyAnalyzed.as_view(), name='retrieve_influencers_already_analyzed'),
	url(r'^index_model/$', views.index_model, name='index_model'),
	url(r'^influencer/delete/$', views.DeleteInfluencer.as_view(), name='delete_influencer'),
]