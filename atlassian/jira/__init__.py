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
        pass  # TODO logout of jira

    def get_projects(self):
        for project in self.client.get('rest/api/2/project'):
            yield Project(project)

    def get_permissions(self, projectkey):
        roles = self.get_roles(projectkey)
        for name, url in roles.items():
            role = self.client.get(url)
            for actor in role.get('actors', ()):
                if actor['type'] in 'atlassian-group-role-actor':
                    yield name, None, actor['name']
                elif actor['type'] in 'atlassian-user-role-actor':
                    yield name, actor['name'], None
                else:
                    self.l.error('Could not match type "{}" to user or group'.format(actor['type']),
                                 extra={'actor': actor})

    def get_roles(self, projectkey):
        return self.client.get('rest/api/2/project/{}/role'.format(projectkey))