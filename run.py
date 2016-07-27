#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

import sys
if sys.version_info < (3, 4):
    raise RuntimeError("must use python 3.4 or greater")
    # TODO: maybe 3.2 works as well...

import csv
import logging
from pprint import pprint
from argparse import ArgumentParser
from getpass import getpass
import pickle
from deepdiff import DeepDiff

from atlassian import PermissionCollector
from atlassian.permission_data import PermissionEntry
from atlassian.confluence import Confluence
from atlassian.jira import Jira
from atlassian.stash import Stash


l = logging.getLogger(__name__)


def main():
    parser = ArgumentParser()

    auth = parser.add_argument_group("Authentication",
                                     "Please provide administrative credentials so this script can access your Atlassian services.")
    auth.add_argument('--user', '-u', help='User to log in with')
    passwordargs = auth.add_mutually_exclusive_group()
    passwordargs.add_argument('--password', '-p', help='Password')
    passwordargs.add_argument('--passfile', '-P', help='Password file')

    services = parser.add_argument_group("Services",
                                         '''\
                                         Add at least one Atlassian service to check. You can provide multiple instances of each kind.
                                         Please provide the complete URL including either http:// or https://, e.g. https://confluence.myserver.example.com.
                                         You can add a hint telling us the Confluence version you're running like this:
                                         https://confluence.myserver.example.com,version=5.8.14''')
    services.add_argument('--confluence', '-c', help='Add Confluence instance.', action='append')
    services.add_argument('--jira', '-j', help='Add JIRA instance.', action='append')
    services.add_argument('--stash', '-s', help='Add Bitbucket Server instance, formerly known as Stash.', action='append')

    action = parser.add_argument_group("Action", "What do you actually want to do?")
    action.add_argument('--csv',
                        help='Export CSV data to this file')
    action.add_argument('--print', action='store_true',
                        help='Pretty-print permissions')
    action.add_argument('--csv-header', help='Include a header line in CSV export', action='store_true')

    optional = parser.add_argument_group("optional arguments")
    optional.add_argument('--save', '-S', help='Save to internal file. This allows you to do further analysis with this script without re-crawling everything.')
    optional.add_argument('--load', '-L', help='Load from file. This allows you to do further analysis with this script without re-crawling everything.')
    optional.add_argument('--loglevel', '-l', default='WARNING', help="Loglevel", action='store')
    optional.add_argument('--compare', '-cmp', help="Compare to previous state, show changes only. Will compare to a file previously saved with --save. Provide this file's name here.")
    optional.add_argument('--selenium',
                          help="Try to use outdated and probably broken Selenium workaround for old Confluence versions (< 5.5). " +
                               "This will try to start your browser and fetch data from the web interface.")

    # Parse arguments and provide further validation
    args = parser.parse_args()

    if not (args.print or args.csv or args.save):
      parser.error("Error: Please specify at least one action. You do want this script to actually do something, right?")

    # Can't output diff as CSV as we're currently using DeepDiff's output format and our CSV exporter doesn't support it.
    # TODO: fix this
    if (args.csv and args.compare):
      parser.error("Error: This tool currently can't export comparisons as CSV. Use --print instead.")

    # Set log level
    loglevel = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(loglevel, int):
        raise ValueError('Invalid log level: {}'.format(args.loglevel))
    logging.basicConfig(level=loglevel)


    # All set, now to the actual work...
    if args.load:
        with open(args.load, 'rb') as fd:
            permissions = pickle.load(fd)
    else:
        password = get_password(args.password, args.passfile, parser)
        services = get_services(args.confluence, args.jira, args.stash, parser, args.selenium)

        pc = PermissionCollector(services, args.user, password)
        permissions = pc.get_permissions()

    if args.compare:
        with open(args.compare, 'rb') as fd:
            current_permissions = permissions
            previous_permissions = pickle.load(fd)
            permissions = DeepDiff(previous_permissions, current_permissions, ignore_order=True)

    if args.csv:
      permissions.export_csv(args.csv, args.csv_header)

    if args.save:
        with open(args.save, 'wb') as fd:
            pickle.dump(permissions, fd)
    if args.print:
        pprint(permissions)


def get_password(passwordarg, filearg, parser):
    password = None
    if passwordarg is not None:
        password = passwordarg
    elif filearg is not None:
        with open(filearg, 'r') as fd:
            password = fd.read()
    else: # get it interactively
        password = getpass()
    if password:
        return password
    else:
        parser.error("Please provide a valid password.")


def get_services(confluence, jira, stash, parser, selenium_workaround):
    services = []
    for arguments, service in ((confluence, Confluence), (jira, Jira), (stash, Stash)):
        if arguments is not None:
            for uri in arguments:
                # validate URL:
                if not (uri.startswith("http://") or uri.startswith("https://")):
                  parser.error("Please provide the complete URLs of your Atlassian instances, starting either in http:// or https://.")

                version = None
                if ',version=' in uri:
                    versionstr = uri.split(',')[-1]
                    version = tuple(versionstr.split('=')[-1].split('.'))
                    uri = ','.join(uri.split(',')[:-1])
                services.append(service(uri, version=version, selenium_workaround = selenium_workaround))
    return services


if __name__ == '__main__':
    main()
