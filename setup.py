#!/usr/bin/env python
from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="DownloadSentryEvents",
    version='0.0.1',
    author='Alan Liu',
    author_email='alanliu21@hotmail.com',
    url='https://github.com/AlanLiu90/DownloadSentryEvents',
    description='A plugin for downloading necessary event data only',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    keywords='sentry',
    include_package_data=True,
    zip_safe=False,
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=[
        'sentry>=10.0.0',
    ],
    entry_points={
        'sentry.plugins': [
            'download_sentry_events = download_sentry_events.plugin:DownloadEventsPlugin'
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 2.7',
        "License :: OSI Approved :: MIT License",
    ]
)
