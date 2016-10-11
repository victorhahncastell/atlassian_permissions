import logging
from urllib.parse import urlsplit, urljoin
from requests import get

l = logging.getLogger(__name__)

#TODO: move this somewhere sensible
#TODO: useful error handling (CLI...)
class HTTPClient:
    def __init__(self, base, user=None, password=None):
        self.base = base
        self.user = user
        self.password = password

    def get(self, url):
        request_url =  self.base + url

        l.debug("Will now get: " + str(request_url))

        if self.user is not None:
            response = get(request_url, auth=(self.user, self.password))
        else:
            response = get(request_url)

        assert response.status_code is 200, 'Error when requesting {}, response code {}.'.format(request_url, response.status_code)
        # TODO: Need better error handling

        return response.json()
