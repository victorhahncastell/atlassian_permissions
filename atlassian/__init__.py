from abc import ABCMeta, abstractmethod
from collections import defaultdict
import logging
from urllib.parse import urlsplit, urljoin

from requests import get


__author__ = 'Sýlvan Heuser, Victor Hahn Castell'


class Service(metaclass=ABCMeta):
    """
    Abstract class for services like Confluence, JIRA, Stash, etc
    """

    def __init__(self, url, version=None, selenium_workaround=False):
        """
        :param url: URL of service
        :param version: tuple of version information
        """
        self.l = logging.getLogger('{}.{}'.format(__name__, self.__class__.__name__))
        self.url = url
        self.version = version if version is not None else (0, 1, 0)
        self.selenium_workaround = selenium_workaround
        self.user = None
        self._logged_in = False
        self.server = None
        self._data = {}

    @abstractmethod
    def login(self, user, password):
        """
        Login to service. Will grant access to API.
        :param user: string username
        :param password: string password
        """
        self.user = user
        self._logged_in = True

    @abstractmethod
    def get_projects(self):
        """
        Yield all projects of this service.
        :return: Project
        """
        yield None

    @abstractmethod
    def get_permissions(self, projectkey):
        """
        Yield all permission entries for the project with the specified key
        :param projectkey: string name, key or ID of project
        :return:
        """
        pass

    @abstractmethod
    def logout(self):
        """
        Will terminate the current session. Is automatically called on destruction of this object.
        :return:
        """
        pass

    def __del__(self):
        self.logout()


class Project:
    def __init__(self, data):
        self.data = data

    @property
    def key(self):
        return self.data.get('key', None)


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



class PermissionCollector:
    def __init__(self, services, user, password):
        self.services = services
        self.user = user
        self.password = password

    def get_permissions(self):
        permissions = {}
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
