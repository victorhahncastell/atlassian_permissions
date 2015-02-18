from collections import defaultdict
import logging

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from .. import PermissionEntry


__author__ = 'Sýlvan Heuser'
l = logging.getLogger(__name__)


class Confluence:
    def __init__(self, uri):
        self.l = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        self.uri = uri
        self.user = None
        self.profile = webdriver.FirefoxProfile()
        self.driver = webdriver.Firefox(firefox_profile=self.profile)
        self.driver.implicitly_wait(10)
        self.logged_in = False

    def __del__(self):
        self.driver.quit()

    def login(self, user, password):
        self.l.info('Logging in')
        self.user = user
        d = self.driver
        d.get(self.uri)
        d.delete_all_cookies()
        d.get(self.uri + '/login.action')
        d.find_element_by_id('os_username').send_keys(user)
        d.find_element_by_id('os_password').send_keys(password)
        d.find_element_by_id('os_cookie').click()
        d.find_element_by_id('loginButton').click()
        try:
            # TODO Use a more general approach to check if login was successful
            WebDriverWait(d, 10).until(ec.title_contains('Dashboard'))
        except TimeoutException as e:
            self.l.exception(e)
            self.logged_in = False
            raise e
        self.logged_in = True
        self.l.info('Logged in successfully')
        return True

    def logout(self):
        # TODO maybe implement a logout process?
        pass

    def get_space_permissions(self, key):
        assert self.logged_in, 'Not logged in.'
        self.l.info('Getting permissions for space {}'.format(key))
        d = self.driver
        d.get(self.uri + '/spaces/spacepermissions.action?key={}'.format(key))
        permissions = defaultdict(lambda: defaultdict(lambda: defaultdict()))
        newpermissions = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: list())))
        for elem in d.find_elements_by_css_selector('td.permissionCell'):
            perm = elem.get_attribute('data-permission')
            group = elem.get_attribute('data-permission-group')
            user = elem.get_attribute('data-permission-user')
            enabled = elem.get_attribute('data-permission-set') == 'true'
            if group is None:
                if user is None:
                    permissions['anonymous'][perm] = enabled
                    if enabled:
                        newpermissions[perm]['user'].append('anonymous')
                else:
                    permissions['user'][user][perm] = enabled
                    if enabled:
                        newpermissions[perm]['user'].append(user)
            else:
                permissions['groups'][group][perm] = enabled
                if enabled:
                    newpermissions[perm]['groups'].append(group)
        self.l.info('Completed space {}'.format(key))
        permissions['new'] = newpermissions
        return permissions

    def get_permissions(self, key):
        permissions = self.get_space_permissions(key).get('new')
        for perm, members in permissions.items():
            if 'user' in members:
                yield PermissionEntry(perm, PermissionEntry.USER, members['user'])
            if 'groups' in members:
                yield PermissionEntry(perm, PermissionEntry.GROUP, members['groups'])

