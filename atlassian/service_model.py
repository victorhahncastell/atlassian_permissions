#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
import logging

from .permission_data import *


class MyLittleAtlassianWorld():
    def __init__(self, services=[]):
        self.services = services
        """List of all Configured Atlassian services"""

    @property
    # TODO: move to view? We only use this for deepdiff comparison output.
    # alternatively, move comparison to model
    def permissions(self):
        """
        :return: Permissions from all configured services
        :rtype: dict
        """
        result = dict()
        for service in self.services:
            result[service.name] = service.permissions
        return result

    @property
    def flat_permissions(self):
        """
        Yield a flat representation of all permissions in first normal form.
        Convert this to a list and you get a nested list with a consistent depth of 2
        containing exactly one user-permission assignment per entry.

        Contains permissions sorted alphabetically by project, then permission.
        Note that "permission" means Role in Case of Jira.

        We use this for CSV export.

        This aggregates the PermissionDict.flatten() results for all permissions in all of my projects.

        Example:
        ['Confluence', 'Demospace', 'VIEWSPACE',  'Group', 'confluence-users']
        ['Jira',       'DEMO',      'Developers', 'User',  'Alice']
        """
        # TODO: entities below project?!
        for service in self.services:
            for space, permission_name, type, assignee in service.flat_permissions:
                yield service.name, space, permission_name, type, assignee

    def logout(self):
        for service in self.services:
            service.logout()


class Service(metaclass=ABCMeta):
    """
    Abstract class for services like Confluence, JIRA, Stash, etc
    Methods starting in load perform actually talk via network and perform API requests.
    There's normally no need to call those manually.
    You'll probably just need to access the projects and permissions properties.
    """
    def __init__(self, url, name=None, version=None):
        """
        :param url: URL of service
        :param name: any name to that might help you recognize this service
        :param version: tuple of version information
        """
        self.l = logging.getLogger('{}.{}'.format(__name__, self.__class__.__name__))

        if name:
            self.name = name
        else:
            self.name = url

        self.url = url

        # TODO why default 0.1.0?
        self.version = version if version is not None else (0, 1, 0)

        self.user = None
        self._logged_in = False
        self.server = None

        self._projects = None
        """Cached list of projects so we don't need to get them via network every single time"""

        self._data = {}
        """Raw API data"""

    @abstractmethod
    def login(self, user, password):
        """
        Login to service. Will grant access to API.
        :param user: string username
        :param password: string password
        """
        self.user = user
        self._logged_in = True

    @property
    def projects(self):
        if not self._projects:
            self.refresh_projects()
        return self._projects

    def refresh_projects(self):
        self._projects = list(self.load_projects())

    @abstractmethod
    def load_projects(self):
        """
        Freshly load get all projects via network.
        Yield all projects of this service.
        :return: Project
        """
        yield None

    @property
    def permissions(self):
        """
        :return A dict of all permissions for this service.
                Example:
                {
                    'KEY1': [permission1 <PermissionEntry>, permission2 <PermissionEntry>],
                    'KEY2': [permission1 <PermissionEntry>, permission2 <PermissionEntry>]
                }
        :rtype: dict
        """
        result = dict()
        for project in self.projects:
            result[project.key] = project.permissions
        return result

    @property
    def flat_permissions(self):
        """
        Yield a flat representation of all permissions in first normal form.
        Convert this to a list and you get a nested list with a consistent depth of 2
        containing exactly one user-permission assignment per entry.

        Contains permissions sorted alphabetically by project, then permission.
        Note that "permission" means Role in Case of Jira.

        We use this for CSV export.

        This aggregates the PermissionDict.flatten() results for all permissions in all of my projects.

        Example:
        ['DEMO', 'Developers', 'User',  'Alice']
        """
        for project in self.projects:
            for permission_name, type, assignee in project.permissions.flatten():
                yield project.key, permission_name, type, assignee

    def refresh_permissions(self):
        """
        Reloads all permissions via the API.
        Afterwards, accessing the permissions property should get you up to date information.
        :rtype: None
        """
        for project in self.projects:
            project.refresh_permissions()


    @abstractmethod
    def load_permissions_for_project(self, project_key):
        """
        Freshly load permissions for a specific project via network.
        Yield all permission entries for the project with the specified key

        Yield type is Permission Entry.
        These permission entries are not required to be complete, i.e. there may be additional assignees that
        are not mentioned in the returned objects. For our local copy (property permissions) we will merge those.
        :param project_key: string name, key or ID of project
        :return:
        """
        pass

    @abstractmethod
    def logout(self):
        """
        Will terminate the current session. Is automatically called on destruction of this object.
        """
        pass

    def __del__(self):
        #self.logout()
        pass
        # TODO fix (Confluence throws SSL socket already gone exception)


class Project:
    def __init__(self, service, data):
        self.service = service
        """
        The Service object this project belongs to.
        This is necessary because API calls for project data are implemented in Service, not here.
        """
        self.data = data

        self._permissions = None
        """
        A PermissionDict() mapping permission names to permission objects.
        """

    @property
    def key(self):
        return self.data.get('key', None)

    @property
    def permissions(self):
        """
        :return: A dictionary of all permissions for this project
        :rtype: dict
        """
        if not self._permissions:
            self.refresh_permissions()
        return self._permissions

    def refresh_permissions(self):
        """
        :rtype None
        """
        self._permissions = PermissionDict()

        for permission in self.service.load_permissions_for_project(self.key):
            self._permissions.add_permission(permission)
