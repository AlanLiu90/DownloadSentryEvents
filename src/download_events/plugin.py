# coding: utf-8

from sentry.plugins.base.v2 import Plugin2
from django.conf.urls import url
from .endpoints.project_events import SimpleProjectEventsEndpoint

VERSION = "0.0.1"

class DownloadEventsPlugin(Plugin2):
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

    def get_url_module(self):
        self.logger.info("DownloadEventsPlugin.get_url_module")
        return "download_events.urls"

    def get_project_urls(self):
        self.logger.info("DownloadEventsPlugin.get_project_urls")
        return [url(
            r"^simple-events/$",
            SimpleProjectEventsEndpoint.as_view(),
        )]
