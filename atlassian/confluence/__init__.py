import logging

from ..service_model import Service, Project
from .xmlrpc import ConfluenceXMLRPC


l = logging.getLogger(__name__)


class Confluence(Service):
    # TODO: get version from API
    name = 'Confluence'
    space_permissions_supported_from = (5, 5) #TODO

    def __init__(self, url, name=None, version=None):
        super().__init__(url, name, version)
        self.api = ConfluenceXMLRPC(self)

    def login(self, user, password):
        self.api.login(user, password)
        super().login(user, password)

    def load_projects(self):
        return self.api.load_projects()

    def load_permissions_for_project(self, project_key):
        return self.api.load_permissions_for_project(project_key)

    def logout(self):
        self.api.logout()
        super().logout()