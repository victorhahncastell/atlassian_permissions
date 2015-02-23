from abc import ABCMeta, abstractmethod
from collections import defaultdict
import logging
from urllib.parse import urlsplit, urljoin

from requests import get


__author__ = 'Sýlvan Heuser'


class Service(metaclass=ABCMeta):
    """
    Abstract class for services like Confluence, JIRA, Stash, etc
    """

    def __init__(self, url, version=None):
        """
        :param url: URL of service
        :param version: tuple of version information
        """
        self.l = logging.getLogger('{}.{}'.format(__name__, self.__class__.__name__))
        self.url = url
        self.version = version if version is not None else (0, 1, 0)
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


class PermissionEntry:
    USER, GROUP = range(2)

    def __repr__(self):
        strng = None
        if self.type is self.USER:
            strng = '{}→USERS({})'
        elif self.type is self.GROUP:
            strng = '{}→GROUPS({})'
        return strng.format(self.permission, ', '.join(self.member_names))

    def __init__(self, permission, type, member_names):
        self.permission = permission
        self.type = type
        self.member_names = member_names


class PermissionCollector:
    def __init__(self, services, user, password):
        self.services = services
        self.user = user
        self.password = password

    def get_permissions(self):
        permissions = {}
        for s in self.services:
            s.login(self.user, self.password)
            for p in s.get_projects():
                if s.name not in permissions:
                    permissions[s.name] = {}
                if p.key not in permissions[s.name]:
                    permissions[s.name][p.key] = p.data
                permissions[s.name][p.key]['permissions'] = list(s.get_permissions(p.key))
            s.logout()
        return permissions


class HTTPClient:
    def __init__(self, base, user=None, password=None):
        self.l = logging.getLogger('{}.{}'.format(__name__, self.__class__.__name__))
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
        assert response.status_code in (200, 404), 'Error when requesting {}.'.format(request_url)
        if response.status_code == 404:
            self.l.warn('404 response for "{}"'.format(request_url))
            return None
        else:
            return response.json()
