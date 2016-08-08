#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# TODO: raw permissions / scheme settings for JIRA?!
# TODO: Confluence protected pages?!
# TODO: Jira issue visibility?
# TODO: Stash!!


class PermissionDict(dict):
    """
    Represents all permissions present that exist on a specific level,
    e.g. all project-level permissions for a specific Jira project
    or all page-level permissions for a protected Confluence page.
    """

    def __str__(self):
        result = ""
        first = True
        for permission_key in sorted(self.keys()):
            if first:
                first = False
            else:
                result += "\n"
            result += str(self[permission_key])
        return result

    def add_permission(self, permission, users=[], groups=[]):
        """
        Can accept a PermissionsEntry object or the raw permission data
        (in that case, same syntax as PermissionEntry constructor).
        Adds a new permission entry to this PermissionDict or amends and existing one.
        """
        if not isinstance(permission, PermissionEntry):
            permission = PermissionEntry(permission, users, groups)

        if permission.name in self:
            self[permission.name].merge(permission)
        else:
            self[permission.name] = permission

    def flatten(self):
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

    def __init__(self, name, users=None, groups=None):
        self.name = name
        """The name of this privilege. Note: For Jira, these are roles."""

        self.users = set()
        self.groups = set()
        self.additional(users, groups)

    def __str__(self):
        prefix = self.name + ": "
        #prefix = "" # we're really only using this to print who PermissionDicts and this doubles the name. TODO: find better solution
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
            return prefix + group_strng
        else:
            return prefix + "None"

    def flatten(self):
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
            yield (str(self.name), 'Group', str(group))
        for user in sorted(self.users):
            yield (str(self.name), 'User', str(user))

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

    def merge(self, other_permission_entry):
        if other_permission_entry.name != self.name:
            raise ValueError("Can only merge permission entries w/ identical permission name")
        self.additional(other_permission_entry.users, other_permission_entry.groups)
