# -*- coding: utf-8 -*-
'''
Utilities for logging metrics.

Author: Wayne Werner <wwerner@saltstack.com>
'''
from __future__ import absolute_import, print_function, unicode_literals

import base64
import datetime
import itertools
import logging
import math
import psutil
import traceback

import requests
import salt.exceptions
import salt.utils.yamlloader as yamlloader
import yaml


log = logging.getLogger(__name__)


def load_beats_info():
    '''
    Search for *beats config files to get elasticsearch credentials.

    Raise SaltConfigurationError if no config file is found.
    '''

    try:
        with open('/etc/filebeat/filebeat.yml') as f:
            return yamlloader.load(f)
    except (IOError, yaml.parser.ParserError):
        pass

    try:
        with open('/etc/journalbeat/journalbeat.yml') as f:
            return yamlloader.load(f)
    except (IOError, yaml.parser.ParserError):
        pass

    try:
        with open('/etc/metricsbeat/metricbeat.yml') as f:
            return yamlloader.load(f)
    except (IOError, yaml.parser.ParserError):
        pass

    raise salt.exceptions.SaltConfigurationError('No valid beats config file found')


def parse_config(beats_info, elastic_port='9243'):
    '''
    Convert beats config into config suitable for posting via requests.

    If the config cannot be parsed, raise InvalidConfigError.
    '''

    raw_auth = beats_info['cloud.auth']
    _, _, raw_url_info = beats_info['cloud.id'].partition(':')
    username, _, password = raw_auth.partition(':')
    decoded_info = base64.b64decode(raw_url_info.encode('utf-8')).decode()
    uri, elastic_subnet, kibana_subnet = decoded_info.split('$')
    elastic_uri = 'https://' + elastic_subnet + '.' + uri + ':' + elastic_port
    return elastic_uri, username, password


def _parse_index(name):
    '''
    Take an elastic search index name, and return a dict of its parts.

    Example:

    >>> _parse_index('filebeat-7.3.0-2019.08.27-000024')
    {'type': 'filebeat', 'version': '7.3.0', 'date': '2019.08.27',
     'index': '000024'}
    '''
    typename, version, date, index = name.split('-')
    return {'type': 'filebeat', 'version': version, 'date': date, 'index': index}


def get_index(
    *, uri, username, password, preference=('filebeat', 'journalbeat', 'metricbeat')
):
    '''
    Select and return the most recent index from elasticsearch, using the
    ``preference`` order. If no index is found, return None. Indexes are
    expected to be in the format of <preference>-<version>-%Y-%m-%d-\d+.

    For example: filebeat-7.3.0-2019.08.27-000024
    '''
    r = requests.get(
        uri.rstrip('/') + '/_cat/indices?v',
        headers={'Accept': 'application/json'},
        auth=(username, password),
    )
    index = None

    def sort_order(element):
        raw_index = element['index']
        name, rest = raw_index.split('-', maxsplit=1)
        try:
            priority = preference.index(name)
        except ValueError:
            # It was missing
            priority = math.inf  # Sort is the thing that goes up
        # Negate priority so we can reverse sort on the rest, but
        # sort forward on the priority
        return -priority, rest

    if r.status_code == 200:
        data = r.json()
        # Because we're swapping priority, we need to reverse the sort here
        data.sort(key=sort_order, reverse=True)
        _, groups = next(itertools.groupby(data, lambda x: _parse_index(x['index'])['type']))
        index = next(groups)["index"]
    return index


def post_metrics(*, metrics, uri, index, username, password):
    '''
    Post provided metrics to the given Elasticsearch uri+index.
    '''
    url = uri.rstrip("/") + '/' + index + '/_doc/'
    log.debug('Posting metrics to %r', url)
    r = requests.post(url, json={
        "message": "{:.2f} MB used.".format(metrics['memory_mb']}),
        "metrics": metrics,
        "@timestamp": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
        auth=(username, password),
    )
    if r.status_code != 201:
        log.error('Failed to post metrics to Elasticsearch: %r', r.json())
    log.warning(r.json())


def get_metrics():
    # Unique Set Size is the memory that will be freed if this process
    # was terminated *right now* - see
    # http://www.pybloggers.com/2016/02/psutil-4-0-0-and-how-to-get-real-process-memory-and-environ-in-python/
    # for more info
    uss_memory = psutil.Process().memory_full_info().uss
    return {
        'memory_mb': uss_memory / 1024 / 1024,  # bytes in kb / kb in mb
        'stack_trace': ''.join(traceback.format_stack()),
    }


def dump_metrics_now():
    metrics = get_metrics()
    uri, username, password = parse_config(load_beats_info())
    index = get_index(uri=uri, username=username, password=password)
    post_metrics(metrics=metrics, index=index, uri=uri, username=username, password=password)


if __name__ == '__main__':
    log.addHandler(logging.StreamHandler())
    dump_metrics_now()
