import logging
from urllib.parse import urlsplit, urljoin
from requests import get

#TODO: move this somewhere sensible
#TODO: useful error handling (CLI...)
class HTTPClient:
    def __init__(self, base, user=None, password=None):
        self.base = base
        self.user = user
        self.password = password

    def get(self, url):
        urlparts = urlsplit(url)
        request_url = urljoin(self.base, urlparts.path)
        if urlparts.query is not None:
            request_url += "?" + urlparts.query

        if self.user is not None:
            response = get(request_url, auth=(self.user, self.password))
        else:
            response = get(request_url)
        assert response.status_code is 200, 'Error when requesting {}.'.format(request_url)
        return response.json()
