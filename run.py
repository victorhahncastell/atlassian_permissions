#!/usr/bin/env python3
import csv
import logging
from pprint import pprint
from argparse import ArgumentParser
import pickle
import sys

from atlassian import PermissionCollector, PermissionEntry
from atlassian.confluence import Confluence
from atlassian.jira import Jira
from atlassian.stash import Stash


__author__ = 'Sýlvan Heuser, Victor Hahn'
l = logging.getLogger(__name__)


def main():
    parser = ArgumentParser()

    auth = parser.add_argument_group("Authentication",
                                     "Please provide administrative credentials so this script can access your Atlassian services.")
    auth.add_argument('--user', '-u', help='User to log in with', required=True)
    passwordargs = auth.add_mutually_exclusive_group(required=True)
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
    action.add_argument('--export', '-e',
                        help='Export CSV data to this file')
    action.add_argument('--print', action='store_true',
                        help='Pretty-print permissions')
    action.add_argument('--csv-users', help='For CSV export, include users', action='store_true')
    action.add_argument('--csv-permissions', help='For CSV export, include permissions', action='store_true')
    action.add_argument('--csv-merged', help='For CSV export, merge entries together per project', action='store_true')

    optional = parser.add_argument_group("optional arguments")
    optional.add_argument('--save', '-S', help='Save to internal file. This allows you to do further analysis with this script without re-crawling everything.')
    optional.add_argument('--load', '-l', help='Load from file. This allows you to do further analysis with this script without re-crawling everything.')
    optional.add_argument('--loglevel', default='WARNING', help="Loglevel", action='store')

    # Parse arguments and provide further validation
    args = parser.parse_args()

    if not (args.print or args.export or args.save):
      parser.error("Error: Please specify at least one action. You do want this script to actually do something, right?")

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
        services = get_services(args.confluence, args.jira, args.stash, parser)

        pc = PermissionCollector(services, args.user, password)
        permissions = pc.get_permissions()

    if args.export:
      export_csv(permissions, args.export, args.csv_permissions, args.csv_users, args.csv_merged)

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
    else:
        # TODO interactively acquire password
        pass
    assert password is not None, 'Password is empty'
    if password:
        return password
    else:
        parser.error("Please provide a valid password.")


def get_services(confluence, jira, stash, parser):
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
                services.append(service(uri, version=version))
    return services


def export_csv(permissions, filename, csv_permissions, csv_users, csv_merged):
    perms = []
    merged_perms = []
    permission_names = set()
    member_names = set()
    for service, projects in permissions.items():
        for project, data in projects.items():
            project_perms = []
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
                perm = {'service': service, 'project': project, 'permission': permission.permission, 'members': permission.member_names, 'member_type': permission.type, 'prefix_members': list(prefix_members)}
                perms.append(perm)
                project_perms.append(perm)
            project_perm = {'service': service, 'project': project}
            for perm in project_perms:
                if perm['permission'] in project_perm:
                    project_perm[perm['permission']] += perm['prefix_members']
                else:
                    project_perm[perm['permission']] = perm['prefix_members']
                for member in perm['prefix_members']:
                    if member in project_perm:
                        project_perm[member] += [perm['permission']]
                    else:
                        project_perm[member] = [perm['permission']]
            merged_perms.append(project_perm)

    with open(filename, 'w', newline='') as fd:
        permline = []
        writer = csv.writer(fd, dialect='unix')
        permline.append('service')
        permline.append('project')
        if csv_permissions:
            for p in permission_names:
                permline.append(p)
        if csv_users:
            for m in member_names:
                permline.append(m)
        writer.writerow(permline)

        if csv_merged:
            for permission in merged_perms:
                permline = []
                permline.append(permission['service'])
                permline.append(permission['project'])
                if csv_permissions:
                    for p in permission_names:
                        if p in permission:
                            permline.append(';'.join(permission[p]))
                        else:
                            permline.append(None)
                if csv_users:
                    for m in member_names:
                        if m in permission:
                            permline.append(';'.join(permission[m]))
                        else:
                            permline.append(None)
                writer.writerow(permline)
        else:
            for permission in perms:
                permline = []
                permline.append(permission['service'])
                permline.append(permission['project'])
                if csv_permissions:
                    for p in permission_names:
                        if permission['permission'] == p:
                            permline.append(';'.join(permission['prefix_members']))
                        else:
                            permline.append(None)
                if csv_users:
                    for m in member_names:
                        if m in permission['prefix_members']:
                            permline.append(permission['permission'])
                        else:
                            permline.append(None)
                writer.writerow(permline)


if __name__ == '__main__':
    main()
