#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pprint, csv
from typing import Generator

# TODO: raw permissions / scheme settings for JIRA?!
# TODO: Confluence protected pages?!
# TODO: Jira issue visibility?
# TODO: Stash!!

class PermissionData(dict):
    # TODO DEPRECATED

    def flatten(self): # TODO -> Generator[str, str, str, str, str]:
        """
        A flat representation of this permission entry in first normal form,
        i.e. a nested list with a consistent depth of 2 containing exactly one user-permission assignment per entry.

        Contains permissions sorted alphabetically by product, then project, then permission.
        Note that "permission" means Role in Case of Jira.

        We use this for CSV export.

        This aggregates the PermissionDict.flatten() results for all permissions in this set.

        Example:
        [
            ['Confluence', 'Demospace', 'VIEWSPACE',  'Group', 'confluence-users']
            ['Jira',       'DEMO',      'Developers', 'User',  'Alice']
        ]
        """
        # each product
        product_names = sorted(self.keys())
        for product_name in product_names:
            product = self[product_name]

            # each project
            project_names = sorted(product.keys())
            for project_name in project_names:
                project = product[project_name]

                # each permission
                permissions = project["permissions"]
                for permission, permtype, assignee in permissions.flatten():
                    yield (product_name, project_name, permission, permtype, assignee)

    def export_csv(self, filename, header=True):
        # TODO: entities below project?!
        with open(filename, 'w', newline='') as fd:
            writer = csv.writer(fd, dialect='unix')
            if header:  # first CSV line shall contain column headers
                writer.writerow(["Product", "Project", "Permission", "Type", "Assignee"])
            for line in self.flatten():
                writer.writerow(line)

    def export_text(self):
        return pprint.pformat(self)  # TODO: beautify


class PermissionDict(dict):
    """
    Represents all permissions present that exist on a specific level,
    e.g. all project-level permissions for a specific Jira project
    or all page-level permissions for a protected Confluence page.
    """

    def add_permission(self, permission: str, users=[], groups=[]):
        """Same syntax as PermissionEntry constructor. Creates a new permission entry or amends and existing one."""
        if permission in self:
            self[permission].additional(users, groups)
        else:
            self[permission] = PermissionEntry(permission, users, groups)

    def flatten(self) -> Generator[str, str, str]:
        """
        A flat representation of this permission entry in first normal form,
        i.e. a nested list with a consistent depth of 2 containing exactly one user-permission assignment per entry.

        Contains permissions sorted alphabetically.

        We use this for CSV export.

        This aggregates the PermissionEntry.flatten() results for all permissions in this set.

        Example:
        [
            ['VIEWSPACE', 'Group', 'confluence-users']
            ['VIEWSPACE', 'User', 'Alice'],
            ['VIEWSPACE', 'User, 'Bob'],
        ]
        """
        for permission_name in sorted(self.keys()):
            yield from self[permission_name].flatten()


class PermissionEntry:
    """
    Represents a single permission no matter on which level, e.g. browse privileges to a Jira project,
    or writing privileges to a protected Confluence page.
    Knows all users and groups who have this specific permission.
    """

    def __init__(self, permission, users=None, groups=None):
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

    def flatten(self) -> Generator[str, str, str]:
        """
        A flat representation of this permission entry in first normal form,
        i.e. a sequence of tuples containing exactly one user-permission assignment per entry.
        Lists groups first, then users; both sorted alphabetically.
        We use this for CSV export.

        Example:
        ('VIEWSPACE', 'Group', 'confluence-users'),
        ('VIEWSPACE', 'User', 'Alice'),
        ('VIEWSPACE', 'User, 'Bob')
        """
        for group in sorted(self.groups):
            yield (str(self.permission), 'Group', str(group))
        for user in sorted(self.users):
            yield (str(self.permission), 'User', str(user))

    def additional(self, users=None, groups=None):
        """Extend this privilege to the specified users and groups"""
        if users:
            if not isinstance(users, set):
                users = {users}
            self.users = self.users | users
        if groups:
            if not isinstance(groups, set):
                groups = {groups}
            self.groups = self.groups | groups
