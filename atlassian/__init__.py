import logging
from urllib.parse import urlsplit, urljoin
from requests import get

from .permission_data import PermissionData, PermissionDict


class PermissionCollector:
    def __init__(self, services, user, password):
        self.services = services
        self.user = user
        self.password = password

    def get_permissions(self):
        permissions = PermissionData()  # dict w/ custom methods
        for s in self.services:                        # Get permissions from all configured services, e.g. Jira...
            s.login(self.user, self.password)

            for p in s.get_projects():                 # ... for all projects in those services.
                if s.name not in permissions:
                    permissions[s.name] = {} # initialize service entry
                if p.key not in permissions[s.name]:
                    permissions[s.name][p.key] = p.data # get project meta data. TODO: normalize
                    permissions[s.name][p.key]['permissions'] = PermissionDict() # initialize permission entry for this project
                for permission, users, groups in s.get_permissions(p.key):
                    permissions[s.name][p.key]['permissions'].add_permission(permission, users, groups)
            s.logout()
        return permissions


class HTTPClient:
    def __init__(self, base, user=None, password=None):
        self.base = base
        self.user = user
        self.password = password

    def get(self, url):
        url = urlsplit(url)
        url = url[2:]
        request_url = urljoin(self.base, url[0])
        if self.user is not None:
            response = get(request_url, auth=(self.user, self.password))
        else:
            response = get(request_url)
        assert response.status_code is 200, 'Error when requesting {}.'.format(request_url)
        return response.json()
