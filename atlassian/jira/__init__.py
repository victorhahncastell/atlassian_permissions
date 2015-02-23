from collections import defaultdict
import logging

from .. import HTTPClient

from atlassian import Service, PermissionEntry, Project


__author__ = 'Sýlvan Heuser'
l = logging.getLogger(__name__)


class Jira(Service):
    name = 'Jira'

    @property
    def client(self):
        if 'client' not in self._data:
            raise RuntimeError('Please login')
        return self._data['client']

    def login(self, user, password):
        super().login(user, password)
        self._data['client'] = HTTPClient(self.url, user=user, password=password)

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
            for type, members in types.items():
                yield PermissionEntry(perm, type, members)

    def get_roles(self, projectkey):
        return self.client.get('rest/api/2/project/{}/role'.format(projectkey))