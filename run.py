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
    parser.add_argument('--csv-users', help='Enable CSV users', action='store_true')
    parser.add_argument('--csv-permissions', help='Enable CSV permissions', action='store_true')
    parser.add_argument('--print', help='Pretty-print permissions', action='store_true')
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
        perms = []
        permission_names = set()
        member_names = set()
        for service, projects in permissions.items():
            for project, data in projects.items():
                for permission in data['permissions']:
                    prefix_members = set()
                    permission_names.add(permission.permission)
                    if permission.type == PermissionEntry.USER:
                        prefix = 'u'
                    elif permission.type == PermissionEntry.GROUP:
                        prefix = 'g'

                    for member in permission.member_names:
                        name = '{}:{}'.format(prefix, member)
                        member_names.add(name)
                        prefix_members.add(name)
                    perms.append({'service': service, 'project': project, 'permission': permission.permission, 'members': permission.member_names, 'member_type': permission.type, 'prefix_members': list(prefix_members)})

        with open(args.export, 'w', newline='') as fd:
            permline = []
            writer = csv.writer(fd, dialect='unix')
            permline.append('service')
            permline.append('project')
            permline.append('type')
            if args.csv_permissions:
                for p in permission_names:
                    permline.append(p)
            if args.csv_users:
                for m in member_names:
                    permline.append(m)
            writer.writerow(permline)

            for permission in perms:
                permline = []
                permline.append(permission['service'])
                permline.append(permission['project'])
                permline.append(permission['member_type'])
                if args.csv_permissions:
                    for p in permission_names:
                        if permission['permission'] == p:
                            permline.append(';'.join(permission['prefix_members']))
                        else:
                            permline.append(None)
                if args.csv_users:
                    for m in member_names:
                        if m in permission['prefix_members']:
                            permline.append(permission['permission'])
                        else:
                            permline.append(None)
                writer.writerow(permline)

    if args.save:
        with open(args.save, 'wb') as fd:
            pickle.dump(permissions, fd)
    if args.print:
        pprint(permissions)


if __name__ == '__main__':
    main()

