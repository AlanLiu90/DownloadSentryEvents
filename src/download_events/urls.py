# coding: utf-8

from __future__ import absolute_import

from django.conf.urls import url
from .endpoints.project_events import SimpleProjectEventsEndpoint

urlpatterns = [
    url(
        r"^(?P<organization_slug>[^\/]+)/(?P<project_slug>[^\/]+)/simple-events/$",
        SimpleProjectEventsEndpoint.as_view(),
    ),
]
