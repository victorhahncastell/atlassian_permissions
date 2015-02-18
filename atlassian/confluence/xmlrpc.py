from collections import defaultdict
import logging
from xmlrpc.client import Server

from .. import PermissionEntry, Project


__author__ = 'Sýlvan Heuser'
l = logging.getLogger(__name__)


class Confluence:
    def __init__(self, uri):
        self.l = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        self.uri = uri
        self.server = Server(uri + '/rpc/xmlrpc')
        self.token = None

    def login(self, user, password):
        self.token = self.server.confluence1.login(user, password)
        assert self.token is not None, 'Login failed'
        return self.token

    def get_spaces(self):
        spaces = self.server.confluence1.getSpaces(self.token)
        self.l.debug('get_spaces', extra={'spaces': spaces})
        for s in spaces:
            yield Project(s)

    def get_permissions_for_space(self, key):
        """
        Not tested.
        """
        permissions = self.server.confluence1.getSpacePermissionSets(self.token, key)
        self.l.debug('get_permissions_for_space', extra={'key': key, 'permissions': permissions})
        for p in permissions:
            yield dict(p)

    def get_permissions(self, key):
        """
        Not tested.
        """
        permissions = list(self.get_permissions_for_space(key))
        new_permissions = defaultdict(lambda: defaultdict(lambda: list()))
        for perm in permissions['contentPermissions']:
            if perm['userName'] is not None:
                new_permissions[perm['type']]['users'].append(perm['userName'])
            if perm['groupName'] is not None:
                new_permissions[perm['type']]['groups'].append(perm['groupName'])
        for type, members in new_permissions.items():
            if 'users' in members:
                yield PermissionEntry(type, PermissionEntry.USER, members['users'])
            if 'groups' in members:
                yield PermissionEntry(type, PermissionEntry.GROUP, members['groups'])