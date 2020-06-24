# coding: utf-8

from sentry.plugins.base.v2 import Plugin2

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
        return "download_events.urls"
