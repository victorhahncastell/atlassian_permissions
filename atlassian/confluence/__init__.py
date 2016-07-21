import logging

from .. import Service
from .xmlrpc import Confluence as ConfluenceXMLRPC


__author__ = 'Sýlvan Heuser'
l = logging.getLogger(__name__)


class Confluence(Service):
    # TODO: get version from API
    name = 'Confluence'
    space_permissions_supported_from = (5, 5)

    def login(self, user, password):
        if (self.selenium_workaround) and (self.version < self.space_permissions_supported_from):
            from .selenium import Confluence as ConfluenceWebDriver
            self._data['selenium'] = ConfluenceWebDriver(self.url)
            self._data['selenium'].login(user, password)
        self._data['xmlrpc'] = ConfluenceXMLRPC(self.url)
        self._data['xmlrpc'].login(user, password)
        super().login(user, password)

    def get_projects(self):
        yield from self._data['xmlrpc'].get_spaces()

    def get_permissions(self, projectkey):
        if (self.selenium_workaround) and (self.version < self.space_permissions_supported_from):
            yield from self._data['selenium'].get_permissions(projectkey)
        else:
            yield from self._data['xmlrpc'].get_permissions(projectkey)

    def logout(self):
        if 'selenium' in self._data:
            self._data['selenium'].logout()
        self._data['xmlrpc'].logout()