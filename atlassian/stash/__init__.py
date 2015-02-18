import logging

from atlassian import Service


__author__ = 'Sýlvan Heuser'
l = logging.getLogger(__name__)


class Stash(Service):
    def login(self, user, password):
        pass  # FIXME login to stash

    def logout(self):
        pass  # TODO logout of stash

    def get_projects(self):
        pass  # FIXME get stash projects

    def get_permissions(self, projectkey):
        pass  # FIXME get stash permissions