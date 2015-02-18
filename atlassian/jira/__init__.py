import logging

from atlassian import Service


__author__ = 'Sýlvan Heuser'
l = logging.getLogger(__name__)


class HTTPClient:
    def __init__(self, base):
        self.base = base

    def get(self, url):
        pass  # FIXME


class Jira(Service):
    @property
    def client(self):
        if 'client' not in self._data:
            self._data['client'] = HTTPClient(self.url)
        return self._data['client']

    def login(self, user, password):
        pass  # FIXME login to jira

    def logout(self):
        pass  # TODO logout of jira

    def get_projects(self):
        pass  # FIXME get jira projects

    def get_permissions(self, projectkey):
        pass  # FIXME get jira permissions