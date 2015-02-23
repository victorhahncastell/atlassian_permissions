from collections import defaultdict
import logging
from urllib.parse import urlsplit
from urllib.parse import urljoin

from atlassian import Service, HTTPClient, Project, PermissionEntry


__author__ = 'Sýlvan Heuser'
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

    def get_projects(self):
        yield Project({'key': self.GLOBALKEY, 'description': 'Global Stash permissions'})
        for proj in self._get_pages('/rest/api/1.0/projects'):
            projectkey = proj['key']
            yield Project(proj)
            for repo in self._get_pages('/rest/api/1.0/projects/{projectKey}/repos'.format(projectKey=projectkey)):
                repo['key'] = '{}{}{}'.format(projectkey, self.REPO_DELIM, repo['slug'])
                yield Project(repo)

    def get_permissions(self, projectkey):
        # permissions = defaultdict(lambda: defaultdict(lambda: list))
        permissions = {}
        # global permissions
        if projectkey is self.GLOBALKEY:
            permissions.update(self._get_permissions('/rest/api/1.0/admin/permissions/{}'))
        elif self.REPO_DELIM in projectkey:
            # repo permissions
            projectkey, repo_slug = projectkey.split(':')
            permissions.update(self._get_permissions(
                '/rest/api/1.0/projects/{projectKey}/repos/{repositorySlug}/permissions/{{}}'.format(
                    projectKey=projectkey, repositorySlug=repo_slug)))
        else:
            # project permissions
            permissions.update(self._get_permissions('/rest/api/1.0/projects/{}/{{}}'.format(projectkey)))
            # TODO personal repo permissions?
        for permission, permission_types in permissions.items():
            for permission_type, members in permission_types.items():
                yield PermissionEntry(permission, permission_type, members)

    def _get_permissions(self, api):
        permissions = defaultdict(lambda: defaultdict(list))
        for api_endpoint, response_key, permission_type in (('groups', 'group', PermissionEntry.GROUP),
                                                            ('users', 'user', PermissionEntry.USER)):
            for value in self._get_pages(api.format(api_endpoint)):
                permissions[value['permission']][permission_type].append(value[response_key]['name'])
        return permissions

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
            if response is None:
                return []
            start = response['size'] - 1
            values += response['values']
        return values