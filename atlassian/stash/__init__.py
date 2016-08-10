from collections import defaultdict
import logging
from urllib.parse import urlsplit
from urllib.parse import urljoin

from ..service_model import Service, Project
from ..permission_data import PermissionEntry
from .. import HTTPClient


l = logging.getLogger(__name__)


class Stash(Service):
    GLOBALKEY = 'STASH-GLOBAL'
    REPO_DELIM = ':'
    name = 'Stash'

    @property
    def client(self):
        if 'client' not in self._data:
            raise RuntimeError('Please login')
        return self._data['client']

    def login(self, user, password):
        super().login(user, password)
        self._data['client'] = HTTPClient(self.url, user=user, password=password)

    def logout(self):
        pass  # TODO logout of stash

    def load_projects(self):
        yield Project(self, {'key': self.GLOBALKEY, 'description': 'Global Stash permissions'})
        for proj in self._get_pages('/rest/api/1.0/projects'):
            projectkey = proj['key']
            yield Project(self, proj)
            for repo in self._get_pages('/rest/api/1.0/projects/{projectKey}/repos'.format(projectKey=projectkey)):
                repo['key'] = '{}{}{}'.format(projectkey, self.REPO_DELIM, repo['slug'])
                #del repo['cloneUrl']  # TODO: why did these two lines exist?
                #del repo['links']['clone']
                yield Project(self, repo) # TODO repo!=project

    def load_permissions_for_project(self, project_key):
        # global permissions
        if project_key is self.GLOBALKEY:
            result = self._get_permissions('/rest/api/1.0/admin/permissions/{}')
            return result
        elif self.REPO_DELIM in project_key:
            # repo permissions
            project_key, repo_slug = project_key.split(':')
            result = self._get_permissions('/rest/api/1.0/projects/{projectKey}/repos/{repositorySlug}/permissions/{{}}'.format(projectKey=project_key, repositorySlug=repo_slug))
            return result
        else:
            # project permissions
            result = self._get_permissions('/rest/api/1.0/projects/{}/permissions/{{}}'.format(project_key))
            return result
            # TODO personal repo permissions?

    def _get_permissions(self, api):
        for api_endpoint, response_key in (('groups', 'group'),
                                                            ('users', 'user')):
            for value in self._get_pages(api.format(api_endpoint)):
                if api_endpoint == 'users':
                    yield PermissionEntry(value['permission'], value[response_key]['name'], None)
                elif api_endpoint == 'groups':
                    yield PermissionEntry(value['permission'], None, value[response_key]['name'])

    def _get_pages(self, url):
        query_args = []
        split_url = urlsplit(url)
        if len(split_url.query) > 0:
            query_args.append(split_url.query)
        query_args.append('start={}')
        url = urljoin(url, '?' + '&'.join(query_args))
        response = {'isLastPage': False}
        values = []
        start = 0
        while not response['isLastPage']:
            response = self.client.get(url.format(start))
            start = response['size'] - 1
            values += response['values']
        return values