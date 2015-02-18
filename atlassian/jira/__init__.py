from collections import defaultdict
import logging
from urllib.parse import urljoin, urlsplit

from requests import get

from atlassian import Service, PermissionEntry, Project


__author__ = 'Sýlvan Heuser'
l = logging.getLogger(__name__)


class HTTPClient:
    def __init__(self, base, user=None, password=None):
        self.base = base
        self.user = user
        self.password = password

    def get(self, url):
        url = urlsplit(url)
        url = url[2:]
        request_url = urljoin(self.base, url)
        if self.user is not None:
            response = get(request_url, auth=(self.user, self.password))
        else:
            response = get(request_url)
        assert response.status_code is 200, 'Error when requesting {}.'.format(request_url)
        return response.json()


class Jira(Service):
    @property
    def client(self):
        if 'client' not in self._data:
            raise RuntimeError('Please login')
        return self._data['client']

    def login(self, user, password):
        self._data['client'] = HTTPClient(self.url, user=self.user, password=self.password)

    def logout(self):
        pass  # TODO logout of jira

    def get_projects(self):
        for project in self.client.get('rest/api/2/project'):
            yield Project(project)

    def get_permissions(self, projectkey):
        permissions = defaultdict(lambda: defaultdict(lambda: list()))
        for name, url in self.get_roles(projectkey).items():
            role = self.client.get(url)
            for actor in role.get('actors', ()):
                if actor['type'] is 'atlassian-group-role-actor':
                    permissions[name][PermissionEntry.GROUP].append(actor['name'])
                elif actor['type'] in 'atlassian-user-role-actor':
                    permissions[name][PermissionEntry.USER].append(actor['name'])
                else:
                    self.l.error('Could not match type "{}" to user or group'.format(actor['type']),
                                 extra={'actor': actor})
        for perm, types in permissions.items():
            for type, members in types:
                yield PermissionEntry(perm, type, members)

    def get_roles(self, projectkey):
        return self.client.get('rest/api/2/project/{}/role'.format(projectkey))