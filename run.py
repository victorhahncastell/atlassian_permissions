#!/usr/bin/env python3
import csv
import logging
from pprint import pprint
from argparse import ArgumentParser
import pickle

from atlassian import PermissionCollector, PermissionEntry
from atlassian.confluence import Confluence
from atlassian.jira import Jira
from atlassian.stash import Stash


__author__ = 'Sýlvan Heuser'
l = logging.getLogger(__name__)


def get_password(passwordarg, filearg):
    password = None
    if passwordarg is not None:
        password = passwordarg
    elif filearg is not None:
        with open(filearg, 'r') as fd:
            password = fd.read()
    else:
        # TODO interactively acquire password
        pass
    assert password is not None, 'Password is empty'
    return password


def get_services(confluence, jira, stash):
    services = []
    for arguments, service in ((confluence, Confluence), (jira, Jira), (stash, Stash)):
        if arguments is not None:
            for uri in arguments:
                version = None
                if ',version=' in uri:
                    versionstr = uri.split(',')[-1]
                    version = tuple(versionstr.split('=')[-1].split('.'))
                    uri = ','.join(uri.split(',')[:-1])
                services.append(service(uri, version=version))
    assert services, 'No services specified'
    return services


class Numberer:
    def __init__(self, start=0):
        self.start = start
        self.elements = []

    def get(self, elem):
        if elem not in self.elements:
            self.elements.append(elem)
        return self.elements.index(elem) + self.start


def main():
    parser = ArgumentParser()
    parser.add_argument('--loglevel', default='WARNING', help="Loglevel", action='store')
    parser.add_argument('user', help='User to log in with')
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--passfile', '-P', help='Password file')
    parser.add_argument('--confluence', '-c', help='Add Confluence instance', action='append')
    parser.add_argument('--jira', '-j', help='Add JIRA instance', action='append')
    parser.add_argument('--stash', '-s', help='Add Stash instance', action='append')
    parser.add_argument('--save', '-S', help='Save to file')
    parser.add_argument('--load', '-l', help='Load from file')
    parser.add_argument('--export', '-e', help='Export CSV data to this file')
    args = parser.parse_args()
    loglevel = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(loglevel, int):
        raise ValueError('Invalid log level: {}'.format(args.loglevel))
    logging.basicConfig(level=loglevel)

    if args.load:
        with open(args.load, 'rb') as fd:
            permissions = pickle.load(fd)
    else:
        password = get_password(args.password, args.passfile)
        services = get_services(args.confluence, args.jira, args.stash)

        pc = PermissionCollector(services, args.user, password)
        permissions = pc.get_permissions()
    if args.export:
        n = Numberer(start=2)
        with open(args.export, 'w', newline='') as fd:
            writer = csv.writer(fd, dialect='unix')
            for service, projects in permissions.items():
                for project, data in projects.items():
                    for permission in data['permissions']:
                        permline = [service, project]
                        if permission.type == PermissionEnty.USER:
                            memberprefix = 'u'
                        elif permission.type == PermissionEntry.GROUP:
                            memberprefix = 'g'
                        for member in permission.members:
                            permline[n.get('{}:{}'.format(memberprefix, member))] = permission.permission
                        permline[n.get(permission.permission)] = ';'.join(permission.members)
                        writer.writerow(permline)
    if args.save:
        with open(args.save, 'wb') as fd:
            pickle.dump(permissions, fd)
    else:
        pprint(permissions)


if __name__ == '__main__':
    main()

