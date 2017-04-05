#!/usr/bin/env python3
"""Render Rosette API dependency parse trees as SVG via Graphviz"""

import argparse
import os
import re
import subprocess
import sys
import urllib

from operator import itemgetter, methodcaller
from getpass import getpass


EXTERNALS = ('rosette_api',)
try:
    from rosette.api import API, DocumentParameters
except ImportError:
    message = '''This script depends on the following modules:
    {}
If you are missing any of these modules, install them with pip3:
    $ pip3 install {}'''
    print(
        message.format('\n\t'.join(EXTERNALS), ' '.join(EXTERNALS)),
        file=sys.stderr
    )
    sys.exit(1)

DEFAULT_ROSETTE_API_URL = 'https://api.rosette.com/rest/v1/'

ROOT = 'root'
NODE = '{index} [label="{token}"]\n'

EDGE = '{governorTokenIndex} -> {dependencyTokenIndex} [label="{relationship}"]'

STYLE = '''
edge [dir="forward", arrowhead="open", arrowsize=0.5]
node [shape="box", height=0]
'''

def request(content, endpoint, api, language=None, uri=False, **kwargs):
    """Request Rosette API results for the given content and endpoint.

    This method gets the requested results from the Rosette API as JSON.  If
    api's output parameter has been set to "rosette" then the JSON will consist
    of an A(nnotated) D(ata) M(odel) or ADM.  An ADM is a Python dict
    representing document content, annotations of the document content,
    and document metadata.
    
    content:  path or URI of a document for the Rosette API to process
    endpoint: a Rosette API endpoint string (e.g., 'entities')
              (see https://developer.rosette.com/features-and-functions)
    api:      a rosette.api.API instance
              (e.g., API(user_key=<key>, service_url=<url>))
    language: an optional ISO 639-2 T language code
              (the Rosette API will automatically detect the language of the
              content by default)
    uri:      specify that the content is to be treated as a URI and the
              the document content is to be extracted from the URI
    kwargs:   additional keyword arguments
              (e.g., if endpoint is 'morphology' you can specify facet='lemmas';
              see https://developer.rosette.com/features-and-functions for
              complete documentation)
    
    For example:
    
    api = API(user_key=<key>, service_url=DEFAULT_ROSETTE_API_URL)
    
    response = request('This is a sentence.', 'syntax_dependencies', api)
    response['sentences'] -> [
        {
            "startTokenIndex": 0,
            "endTokenIndex": 4,
            "dependencies": [
                {
                    "dependencyType": "nsubj",
                    "governorTokenIndex": 3,
                    "dependentTokenIndex": 0
                },
                {
                    "dependencyType": "cop",
                    "governorTokenIndex": 3,
                    "dependentTokenIndex": 1
                },
                {
                    "dependencyType": "det",
                    "governorTokenIndex": 3,
                    "dependentTokenIndex": 2
                },
                {
                    "dependencyType": "root",
                    "governorTokenIndex": -1,
                    "dependentTokenIndex": 3
                },
                {
                    "dependencyType": "punct",
                    "governorTokenIndex": 3,
                    "dependentTokenIndex": 4
                }
            ]
        }
    ]
    response['tokens'] -> ['This', 'is', 'a', 'sentence', '.']
    
    api.setUrlParameter('output', 'rosette')
    
    response = request('This is a sentence.', 'syntax_dependencies', api)
    response['attributes']['dependency']['items'] -> [
        {
            "relationship": "nsubj",
            "governorTokenIndex": 3,
            "dependencyTokenIndex": 0
        },
        {
            "relationship": "cop",
            "governorTokenIndex": 3,
            "dependencyTokenIndex": 1
        },
        {
            "relationship": "det",
            "governorTokenIndex": 3,
            "dependencyTokenIndex": 2
        },
        {
            "relationship": "root",
            "governorTokenIndex": -1,
            "dependencyTokenIndex": 3
        },
        {
            "relationship": "punct",
            "governorTokenIndex": 3,
            "dependencyTokenIndex": 4
        }
    ]
    
    response['attributes']['token']['items'] -> [
        {
            "startOffset": 0,
            "endOffset": 4,
            "text": "This"
        },
        {
            "startOffset": 5,
            "endOffset": 7,
            "text": "is"
        },
        {
            "startOffset": 8,
            "endOffset": 9,
            "text": "a"
        },
        {
            "startOffset": 10,
            "endOffset": 18,
            "text": "sentence"
        },
        {
            "startOffset": 18,
            "endOffset": 19,
            "text": "."
        }
    ]

    """
    parameters = DocumentParameters()
    if uri:
        parameters['contentUri'] = content
    else:
        parameters['content'] = content
    parameters['language'] = language
    adm = methodcaller(endpoint, parameters, **kwargs)(api)
    return adm

def escape(token):
    """Escape characters that have special semantics within GraphViz"""
    pattern = re.compile(r'([\[\]()"\\])')
    return pattern.sub(r'\\\1', token)

def extent(obj):
    """Get the start and end offset attributes of a dict-like object"""
    return obj.get('startOffset', -1), obj.get('endOffset', -1)

def tokens(adm):
    """Get a sorted list of tokens from the ADM"""
    return sorted(adm['attributes']['token']['items'], key=extent)

def dependencies(adm):
    """Get a sorted list of dependency edges from the ADM"""
    return sorted(
        adm['attributes']['dependency']['items'],
        key=itemgetter('governorTokenIndex', 'dependencyTokenIndex')
    )

def deps_to_graph(adm, index_labels=False):
    """Create a digraph whose nodes are tokens and edges are dependencies"""
    sentence_index = -1
    digraph = 'digraph G{{{}'.format(STYLE)
    for i, token in enumerate(tokens(adm)):
        index_label = '({}) '.format(i) if index_labels else ''
        token_text = '{}{}'.format(index_label, escape(token['text']))
        digraph += NODE.format(index=i, token=token_text)
    for edge in dependencies(adm):
        if edge['relationship'] == ROOT:
            digraph += '{} [label="S{}"]'.format(sentence_index, -sentence_index)
            edge['governorTokenIndex'] = sentence_index
            sentence_index -= 1
        digraph += EDGE.format(**edge) + '\n'
    digraph += '}\n'
    return digraph

def make_svg(digraph):
    """Get an SVG from a digraph string (relies on GraphViz)"""
    try:
        process = subprocess.Popen(
            ['dot', '-Tsvg'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
    except OSError:
        message = '''Cannot find dot which is required to create the SVG.
(You can install dot from the Graphviz package: http://graphviz.org/)'''
        raise Exception(message)
    svg, stderr = process.communicate(digraph)
    if stderr:
        print(stderr, file=sys.stderr)
        message = 'Failed to create an svg representation from string: {}'
        raise Exception(message.format(digraph))
    return svg

def get_content(content, uri=False):
    """Load content from file or stdin"""
    if content is None:
        content = sys.stdin.read()
    elif os.path.isfile(content):
        with open(content, mode='r') as f:
            content = f.read()
    # Rosette API may balk at non-Latin characters in a URI so we can get urllib
    # to %-escape the URI for us
    if uri:
        unquoted = urllib.parse.unquote(content)
        content = urllib.parse.quote(unquoted, '/:')
    return content

def dump(data, filename):
    if filename is None:
        print(data, file=sys.stdout)
    else:
        with open(filename, mode='w') as f:
            print(data, file=f)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument(
        '-i', '--input',
        help=(
            'Path to a file containing input data (if not specified data is '
            'read from stdin)'
        ),
        default=None
    )
    parser.add_argument(
        '-u',
        '--content-uri',
        action='store_true',
        help='Specify that the input is a URI (otherwise load text from file)'
    )
    parser.add_argument(
        '-o', '--output',
        help=(
            'Path to a file where SVG will be written (if not specified data '
            'is written to stdout)'
        ),
        default=None
    )
    parser.add_argument(
        '-k', '--key',
        help='Rosette API Key',
        default=None
    )
    parser.add_argument(
        '-a', '--api-url',
        help='Alternative Rosette API URL',
        default=DEFAULT_ROSETTE_API_URL
    )
    parser.add_argument(
        '-l', '--language',
        help=(
            'A three-letter (ISO 639-2 T) code that will override automatic '
            'language detection'
        ),
        default=None
    )
    parser.add_argument(
        '-b', '--label-indices',
        action='store_true',
        help=(
            'Add token index labels to show the original token order; '
            'this can help in reading the trees, but it adds visual clutter'
        )
    )
    args = parser.parse_args()
    # Get the user's Rosette API key
    key = (
        os.environ.get('ROSETTE_USER_KEY') or
        args.key or
        getpass(prompt='Enter your Rosette API key: ')
    )
    # Instantiate the Rosette API
    api = API(user_key=key, service_url=args.api_url)
    api.setUrlParameter('output', 'rosette')
    content = get_content(args.input, args.content_uri)
    adm = request(
        content,
        'syntax_dependencies',
        api,
        language=args.language,
        uri=args.content_uri
    )
    dump(make_svg(deps_to_graph(adm, args.label_indices)), args.output)
