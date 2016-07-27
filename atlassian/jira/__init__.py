from collections import defaultdict
import logging

from .. import HTTPClient

from ..service_model import Service, Project
from ..permission_data import PermissionEntry


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
        # TODO logout of jira
        del self._data['client']

    def load_projects(self):
        for project in self.client.get('rest/api/2/project'):
            yield Project(self, project)

    def load_permissions_for_project(self, project_key):
        roles = self.get_roles(project_key)
        for name, url in roles.items():
            role = self.client.get(url)
            for actor in role.get('actors', ()):
                if actor['type'] in 'atlassian-group-role-actor':
                    yield PermissionEntry(name, None, actor['name'])
                elif actor['type'] in 'atlassian-user-role-actor':
                    yield PermissionEntry(name, actor['name'], None)
                else:
                    self.l.error('Could not match type "{}" to user or group'.format(actor['type']),
                                 extra={'actor': actor})

    def get_roles(self, projectkey):
        return self.client.get('rest/api/2/project/{}/role'.format(projectkey))