from collections import defaultdict
import logging
from xmlrpc.client import Server

from ..service_model import Project
from ..permission_data import PermissionEntry

#TODO: THIS API IS DEPRECATED

l = logging.getLogger(__name__)


class ConfluenceXMLRPC():

    def __init__(self, generic):
        self.generic = generic
        self.token = None
        self.server = None

    def login(self, user, password):
        self.server = Server(self.generic.url + '/rpc/xmlrpc')
        self.token = self.server.confluence1.login(user, password)
        assert self.token is not None, 'Login failed'
        return self.token

    def logout(self):
        """Return True on sucessful logout, False otherwise"""
        if self.token:
            success = self.server.confluence1.logout(self.token)
        else:
            success = False
        self.token = None
        self.server = None
        return success

    def load_projects(self):
        spaces = self.server.confluence1.getSpaces(self.token)
        l.debug('get_spaces', extra={'spaces': spaces})
        for s in spaces:
            yield Project(self.generic, s)

    def get_permissions_for_space(self, key):
        """
        Get permissions from Confluence API
        """
        permissions = self.server.confluence1.getSpacePermissionSets(self.token, key)
        l.debug('get_permissions_for_space', extra={'key': key, 'permissions': permissions})
        for p in permissions:
            yield dict(p)

    def load_permissions_for_project(self, project_key):
        """
        Convert raw data to our internal permission data format
        """
        for permission_set in self.get_permissions_for_space(project_key):
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
                    yield PermissionEntry(permission['type'], user, group)
            if set(permission_set.keys()) != {'spacePermissions', 'type'}:
                l.debug('Got Confluence permission data that does not just include "spacePermissions": ' +
                             str(permission_set))

