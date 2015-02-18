from abc import ABCMeta, abstractmethod
from collections import defaultdict

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

    def __init__(self, permission, type, member_names):
        self.permission = permission
        self._type = None
        self.type = type
        self.member_names = member_names

    @property
    def type(self):
        if self._type == self.USER:
            return 'user'
        elif self._type == self.GROUP:
            return 'group'
        else:
            raise ValueError('"{}" is an illegal value for type'.format(self._type))

    @type.setter
    def type(self, val):
        if val in ('user',):
            self._type = 1
        elif val in ('group',):
            self._type = 2


class PermissionCollector:
    def __init__(self, services, user, password):
        self.services = services
        self.user = user
        self.password = password

    def get_permissions(self):
        permissions = defaultdict(lambda: defaultdict())
        for s in self.services:
            s.login(self.user, self.password)
            for p in s.get_projects():
                permissions[s.name][p.key]['__meta'] = p.data
                permissions[s.name][p.key] = s.get_permissions(p.key)
            s.logout()
        return permissions