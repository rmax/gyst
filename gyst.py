#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""My gist command line tool"""

__author__ = 'Rolando Espinoza La fuente <darkrho@gmail.com>'
__version__ = '0.1'
__all__ = ['']

import itertools
import fileinput
import logging
import os
import re
import subprocess
import sys
import urllib
import urllib2
from optparse import OptionParser, make_option

GIST_URL = 'http://gist.github.com/'

def github_user_token():
    """Retrieves user & token from git"""
    # TODO: handle exceptions
    usercmd = 'git config --global github.user'.split()
    tokencmd = 'git config --global github.token'.split()
    proc1 = subprocess.Popen(usercmd, stdout=subprocess.PIPE)
    proc2 = subprocess.Popen(tokencmd, stdout=subprocess.PIPE)
    output1 = proc1.communicate()[0]
    output2 = proc2.communicate()[0]
    return output1.strip(), output2.strip()

def gist_txt_url(gistid):
    """Returns gist's text url"""
    return GIST_URL + gistid + '.txt'

def main():
    """
    main program
    """
    #TODO: extend usage examples
    usage = """%prog [options] [files]

    %prog -r 1 -o gist.txt
    %prog -r 737db156ce0ac2388902
    %prog models.py tests.py
    %prog -p secret.txt"""
    option_list = [
        make_option('-d', '--debug', action='store_true',
                help='Enable debug mode',
                dest='debug', default=False),
        make_option('-r', '--read', action='store',
                help='Download gist', metavar='id',
                dest='gistread', type='string'),
        make_option('-o', '--output', action='store',
                help='Destination file', metavar='file',
                dest='gistout', type='string'),
        make_option('-e', '--extension', action='store',
                help='File extension. Default .txt',
                metavar='.ext', dest='gistext', type='string'),
        make_option('-p', '--private', action='store_true',
                help='Publish private gist',
                dest='private', default=False),
        ]

    parser = OptionParser(usage, option_list=option_list,
            version=__version__)

    options, args = parser.parse_args()

    if options.debug:
        logging.basicConfig(level=logging.DEBUG)

    # parse input
    #TODO: allow username token by command line?
    username, token = github_user_token()

    logging.debug('options: %s', options)
    logging.debug('args: %s', args)
    logging.debug('username: %s', username)
    logging.debug('token: %s', token)

    # Read gist
    if options.gistread is not None:
        if len(args) > 0:
            parser.error('-r does not allow extra arguments')

        elif not re.match(r'^\w+$', options.gistread):
            parser.error('-r invalid gist ID')

        else:
            gist_url = gist_txt_url(options.gistread)
            logging.debug('fetching %s', gist_url)

            # TODO: git clone option

            if options.gistout:
                if os.path.exists(options.gistout):
                    parser.error('-o file exists')
                out = file(options.gistout, 'w')
            else:
                out = sys.stdout

            count = 0
            # TODO: maybe handle multiple files in gist
            for line in urllib2.urlopen(gist_url):
                out.write(line)
                count += 1

            if options.gistout:
                out.close()
                logging.debug('%d lines written', count)

            # TODO: better way to known if gist exists
            if count == 0:
                main_msg('Unknown Gist or has been deleted', error=True)

    # Post gist 
    else:
        # gistfile key generator
        gistfile_key = ('gistfile'+str(i) for i in itertools.count(1))

        default_ext = '.txt'
        if options.gistext:
            override_ext = options.gistext
        else:
            override_ext = None

        # post data with login & token
        postdata = dict(login=username, token=token)

        # post initial values
        if options.private:
            postdata['private'] = 'on'
            logging.debug('Private gist')

        # loop over all files
        for line in fileinput.input(args):

            ## setup per-file values
            if fileinput.isfirstline():
                gist_current = gistfile_key.next()
                file_name = 'file_name[%s]' % gist_current
                file_ext = 'file_ext[%s]' % gist_current
                file_contents = 'file_contents[%s]' % gist_current

                if fileinput.isstdin():
                    # standard input
                    logging.debug('Processing STDIN')
                    postdata[file_name] = ''
                    postdata[file_contents] = ''
                    if override_ext:
                        postdata[file_ext] = override_ext
                    else:
                        postdata[file_ext] = default_ext
                else:
                    # real file
                    name, ext = os.path.splitext(fileinput.filename())
                    logging.debug('Processing %s%s', name, ext)
                    postdata[file_name] = name
                    postdata[file_contents] = ''
                    if override_ext:
                        postdata[file_ext] = override_ext
                    elif ext is not None:
                        postdata[file_ext] = ext
                    else:
                        postdata[file_ext] = default_ext

            # append line to current content
            postdata[file_contents] += line

        logging.debug('Post data\n%s', postdata)

        # do the post
        url = GIST_URL + 'gists'
        data = urllib.urlencode(postdata)

        request = urllib2.Request(url, data)
        logging.debug('Request: %s', request)

        # TODO: handle response errors
        response = urllib2.urlopen(request)
        logging.debug('Response: %s', response)

        main_msg('Here is your gist: %s' % response.geturl())

    # finish program
    main_exit()

# helpers
def main_msg(msg, error=False):
    """Display program messages"""
    if error:
        print >> sys.stderr, msg
    else:
        print >> sys.stdout, msg
    
def main_exit(msg=None, code=0):
    """Exit with exit code"""
    if msg:
        main_msg(msg, not code == 0)
    sys.exit(code)


if __name__ == '__main__':
    #TODO: tests
    main()
