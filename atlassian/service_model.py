#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from collections import defaultdict
import logging


class MyLittleAtlassianWorld():
    """
    - Services
      - Projects
    - Permission Data
      - (a large dict containing collected data, see permission_data.py and data_structure_example.txt for details)
    YET UNUSED
    """
    pass


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
