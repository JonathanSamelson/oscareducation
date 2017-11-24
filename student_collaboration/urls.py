from django.conf.urls import url

from forum.views import thread
from . import views

urlpatterns = [
    # View example : views.update_settings
    # Url Example : url(r'^dashboard/$', views.dashboard, name='student_dashboard'),
    url(r'^$', views.collaborative_home, name='collaborative_home'),
    url(r'^notifications/$', views.collaborative_notifications, name='notifications'),
    url(r'^settings/$', views.update_settings, name='settings'),
    url(r'^request_help/$', views.submit_help_request, name='request_help'),
    url(r'^provide_help/$', views.OpenHelpRequestsListView.as_view(), name='provide_help'),
    url('^provide_help/([0-9]+)$', views.open_help_request, name='reply_help'),
    url(r'^help_request_history/$', views.help_request_hist, name='help_request_history'),
    url(r'^help_request_history/thread/(?P<id>\d+)$', thread, name='view_thread')
]
