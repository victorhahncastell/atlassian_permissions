#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pprint, csv


class PermissionData(dict):
    """
    Complete representation of our collected Atlassian service data.
    See data_structure_example.txt for the general idea of it.
    """

    def export_csv(self, filename, csv_permissions, csv_users, csv_merged):
        perms = []
        merged_perms = []
        permission_names = set()
        member_names = set()
        for service, projects in self.items():
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
                    perm = {'service': service, 'project': project, 'permission': permission.permission,
                            'members': permission.member_names, 'member_type': permission.type,
                            'prefix_members': list(prefix_members)}
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

    def export_text(self):
        return pprint.pformat(self)  # TODO: beautify


class PermissionDict(dict):
    def __missing__(self, key):
        return None

    def add_permission(self, permission: str, users=[], groups=[]):
        """Same syntax as PermissionEntry constructor. Creates a new permission entry or amends and existing one."""
        if self[permission]:
            self[permission].additional(users, groups)
        else:
            self[permission] = PermissionEntry(permission, users, groups)


class PermissionEntry:
    def __init__(self, permission, users = None, groups = None):
        self.permission = permission
        self.users = set()
        self.groups = set()
        self.additional(users, groups)

    def __repr__(self):
        prefix = self.permission + ": "
        user_strng = None
        group_strng = None

        if len(self.users):
            user_strng = 'USERS({})'
            user_strng = user_strng.format(', '.join(self.users))
        if len(self.groups):
            group_strng = 'GROUPS({})'
            group_strng = group_strng.format(', '.join(self.groups))
        if user_strng:
            if group_strng:
                return prefix + user_strng + ", " + group_strng
            else:
                return prefix + user_strng
        elif group_strng:
            return group_strng
        else:
            return prefix + "None"

    def additional(self, users = None, groups = None):
        """Extend this privilege to the specified users and groups"""
        if users:
            if not isinstance(users, set):
                users = {users}
            self.users = self.users | users
        if groups:
            if not isinstance(groups, set):
                groups = {groups}
            self.groups = self.groups | groups


