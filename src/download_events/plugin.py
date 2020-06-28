# coding: utf-8

from __future__ import absolute_import

from sentry.plugins.base.v1 import Plugin
from django.conf.urls import url
from download_events.endpoints.project_events import SimpleProjectEventsEndpoint

VERSION = "0.0.1"

class DownloadEventsPlugin(Plugin):
    """
    A plugin for downloading necessary event data only.
    """
    author = 'Alan Liu'
    author_url = 'https://github.com/AlanLiu90/DownloadSentryEvents'
    version = VERSION
    description = 'A plugin for downloading necessary event data only.'
    resource_links = [
        ('Source', 'https://github.com/AlanLiu90/DownloadSentryEvents'),
        ('Bug Tracker', 'https://github.com/AlanLiu90/DownloadSentryEvents/issues'),
        ('README', 'https://github.com/AlanLiu90/DownloadSentryEvents/blob/master/README.md'),
    ]

    slug = 'DownloadEvents'
    title = 'DownloadEvents'
    conf_key = slug
    conf_title = title
    project_default_enabled = True

    def get_project_urls(self):
        return [url(
            r"^simple-events/$",
            SimpleProjectEventsEndpoint.as_view(),
        )]
