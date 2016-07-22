from collections import defaultdict
import logging
from xmlrpc.client import Server

from .. import PermissionEntry, Project


__author__ = 'Sýlvan Heuser, Victor Hahn Castell'
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

    def logout(self):
        pass  # TODO logout from Confluence via XMLRPC

    def get_spaces(self):
        spaces = self.server.confluence1.getSpaces(self.token)
        self.l.debug('get_spaces', extra={'spaces': spaces})
        for s in spaces:
            yield Project(s)

    def get_permissions_for_space(self, key):
        """
        Get permissions from Confluence API
        """
        permissions = self.server.confluence1.getSpacePermissionSets(self.token, key)
        self.l.debug('get_permissions_for_space', extra={'key': key, 'permissions': permissions})
        for p in permissions:
            yield dict(p)

    def get_permissions(self, key):
        """
        Convert raw data to our internal permission data format
        """
        for permission_set in self.get_permissions_for_space(key):
            if 'spacePermissions' in permission_set:
                for permission in permission_set['spacePermissions']:
                    if 'type' in permission:
                        type = permission['type']
                    else:
                        pass # TODO error

                    if 'userName' in permission:
                        user = permission['userName']
                    else:
                        user = None

                    if 'groupName' in permission:
                        group = permission['groupName']
                    else:
                        group = None

                    yield permission['type'], user, group
            else:
                pass #TODO
