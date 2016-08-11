#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

import logging
from pprint import pprint, pformat
from argparse import ArgumentParser
from getpass import getpass

import dill as pickle
from deepdiff import DeepDiff

from atlassian.service_model import MyLittleAtlassianWorld
from atlassian.confluence import Confluence
from atlassian.jira import Jira
from atlassian.stash import Stash

from view.csv import WorldCsvView
from view.text import WorldTextView
from view.html import WorldHtmlView

l = logging.getLogger(__name__)

class CliController:
    @staticmethod
    def run():
        controller = CliController()
        controller.prepare_arguments()
        controller.parse_arguments()
        controller.run_action()
        return controller

    def __init__(self):
        self.parser = ArgumentParser()
        self.args = None

        """A MyLittleAtlassianWold object serving as root of our model"""
        self.world = None

    def prepare_arguments(self):
        auth = self.parser.add_argument_group("Authentication",
                                         "Please provide administrative credentials so this script can access your Atlassian services.")
        auth.add_argument('--user', '-u', help='User to log in with')
        passwordargs = auth.add_mutually_exclusive_group()
        passwordargs.add_argument('--password', '-p', help='Password')
        passwordargs.add_argument('--passfile', '-P', help='Password file')

        services = self.parser.add_argument_group("Services",
                                             '''\
                                             Add at least one Atlassian service to check. You can provide multiple instances of each kind.
                                             Please provide the complete URL including either http:// or https://, e.g. https://confluence.myserver.example.com.
                                             You can add a hint telling us the Confluence version you're running like this:
                                             https://confluence.myserver.example.com,version=5.8.14''')
        services.add_argument('--confluence', '-c', help='Add Confluence instance.', action='append')
        services.add_argument('--jira', '-j', help='Add JIRA instance.', action='append')
        services.add_argument('--stash', '-s', help='Add Bitbucket Server instance, formerly known as Stash.', action='append')

        action = self.parser.add_argument_group("Action", "What do you actually want to do?")
        action.add_argument('--csv', action='store_true', help='Export permissions as CSV')
        action.add_argument('--print', action='store_true', help='Pretty-Print permissions (plain text)')
        action.add_argument('--html', action='store_true', help='Export permissions as HTML')

        optional = self.parser.add_argument_group("optional arguments")
        optional.add_argument('--compare', '-cmp',
                              help="Compare to previous state, show changes only." +
                                   "Will compare to a file previously saved with --save." +
                                   "Provide this file's name here.")
        optional.add_argument('--diff', action='store_true', help="Use together with cmp and an output action to show changes only.")
        optional.add_argument('--save', '-S', help='Save to internal file. This allows you to do further analysis with this script without re-crawling everything.')
        optional.add_argument('--load', '-L', help='Load from file. This allows you to do further analysis with this script without re-crawling everything.')
        optional.add_argument('--output', '-o', help='Write output to this file. Will print to console if omitted.')
        optional.add_argument('--loglevel', '-l', default='WARNING', help="Loglevel", action='store')
        optional.add_argument('--header', help='For CSV export, include a header line', action='store_true')

    def parse_arguments(self):
        self.args = self.parser.parse_args()

        if not (self.args.print or self.args.csv or self.args.save or self.args.html):
            self.parser.error("Please specify at least one action. You do want this script to actually do something, right?")

        if not (self.args.load or self.args.user):
            self.parser.error("Please specify a user name.")

        # Can't output diff as CSV as we're currently using DeepDiff's output format and our CSV exporter doesn't support it.
        # TODO: fix this
        if self.args.compare and (self.args.csv):
            self.parser.error("Error: This tool currently can't export comparisons as CSV. --html or --print should work.")

        # Set log level
        loglevel = getattr(logging, self.args.loglevel.upper(), None)
        if not isinstance(loglevel, int):
            raise ValueError('Invalid log level: {}'.format(self.args.loglevel))
        logging.basicConfig(level=loglevel)

        # Create model
        if self.args.load:   # ...or get a ready-made one from disk?
            with open(self.args.load, 'rb') as fd:
                self.world = pickle.load(fd)
        else:
            password = self.get_password()
            self.world = self.create_services(self.args.confluence, self.args.jira, self.args.stash)
            for service in self.world.services.values():  # TODO beautify
                service.login(self.args.user, password)
            self.world.refresh()

    def run_action(self):
        if self.args.compare:  # special case, we prevented any other output than plain text in parse_arguments()
            self.run_compare()
        else:
            self.run_listperms()

        if self.args.save:  # Save model as pickle. Independent of any other action.
            self.run_save()

    def run_compare(self):
        """
        Runs a compare action. Triggers a view based on user commands
        (e.g. --html for an HTML or --print for a plain text view).
        """
        if self.args.diff:
            diff = 'only'
        else:
            diff = 'yes'

        if self.args.print:
            with open(self.args.compare, 'rb') as pickle_file:
                current_permissions = self.world.permissions
                previous_world = pickle.load(pickle_file)
                previous_permissions = previous_world.permissions
                permissions = DeepDiff(previous_permissions, current_permissions, ignore_order=True)
                if self.args.output:
                    with open(self.args.output, 'w') as out_file:
                        out_file.write(pformat(permissions))
                else:
                    pprint(permissions)
                # TODO: use model-level diff, remove view implementation from this controller
        else:  # TODO remove redundant code
            with open(self.args.compare, 'rb') as pickle_file:
                current_permissions = self.world.permissions
                previous_world = pickle.load(pickle_file)
                previous_permissions = previous_world.permissions
                permissions = DeepDiff(previous_permissions, current_permissions, ignore_order=True)

                view_map = (
                    (self.args.csv, WorldCsvView),
                    (self.args.print, WorldTextView),
                    (self.args.html, WorldHtmlView))
                for arg, view_class in view_map:
                    if arg:
                        view = view_class(self.world, cmp=previous_world, diff=diff)
                        if self.args.output:
                            view.export(self.args.output)
                        else:
                            view.print()

    def run_listperms(self):
        """
        Runs an action listing current permissions. Triggers a view based on user commands
        (e.g. --html for an HTML or --print for a plain text view).
        """
        view_map = (
            (self.args.csv, WorldCsvView),
            (self.args.print, WorldTextView),
            (self.args.html, WorldHtmlView))
        for arg, view_class in view_map:
            if arg:
                view = view_class(self.world)
                if self.args.output:
                    view.export(self.args.output)
                else:
                    view.print()

    def run_save(self):
        """
        Saves current state to a pickle file.
        """
        with open(self.args.save, 'wb') as fd:
            self.world.logout()
            pickle.dump(self.world, fd)

    def get_password(self):
        password = None
        if self.args.password is not None:
            password = self.args.password
        elif self.args.passfile is not None:
            with open(self.args.passfile, 'r') as fd:
                password = fd.read()
        else:  # get it interactively
            password = getpass()
        if password:
            return password
        else:
            self.parser.error("Please provide a valid password.")

    def create_services(self, confluence, jira, stash):
        """
        :rtype MyLittleAtlassianWorld
        :return An object representing an ecosystem of Atlassian services
        """
        services = dict()
        for arguments, service, name in ((confluence, Confluence, "Confluence"), (jira, Jira, "Jira"), (stash, Stash, "Stash")):
            # TODO: support custom names
            if arguments is not None:
                for uri in arguments:
                    # validate URL:
                    if not (uri.startswith("http://") or uri.startswith("https://")):
                        self.parser.error("Please provide the complete URLs of your Atlassian instances, starting either in http:// or https://.")

                    #TODO: remove? this version stuff is rather quirky and currently unused. We should get the version from API anyway
                    version = None
                    if ',version=' in uri:
                        versionstr = uri.split(',')[-1]
                        version = tuple(versionstr.split('=')[-1].split('.'))
                        uri = ','.join(uri.split(',')[:-1])
                    services[service.name] = service(uri, name=name, version=version)
        world = MyLittleAtlassianWorld(services)
        return world
