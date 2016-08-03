#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

import logging
from pprint import pprint
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
        action.add_argument('--csv',
                            help='Export CSV data to this file')
        action.add_argument('--print', action='store_true',
                            help='Pretty-print permissions')
        action.add_argument('--csv-header', help='Include a header line in CSV export', action='store_true')

        optional = self.parser.add_argument_group("optional arguments")
        optional.add_argument('--save', '-S', help='Save to internal file. This allows you to do further analysis with this script without re-crawling everything.')
        optional.add_argument('--load', '-L', help='Load from file. This allows you to do further analysis with this script without re-crawling everything.')
        optional.add_argument('--loglevel', '-l', default='WARNING', help="Loglevel", action='store')
        optional.add_argument('--compare', '-cmp', help="Compare to previous state, show changes only. Will compare to a file previously saved with --save. Provide this file's name here.")

    def parse_arguments(self):
        self.args = self.parser.parse_args()

        if not (self.args.print or self.args.csv or self.args.save):
            self.parser.error("Error: Please specify at least one action. You do want this script to actually do something, right?")

        # Can't output diff as CSV as we're currently using DeepDiff's output format and our CSV exporter doesn't support it.
        # TODO: fix this
        if self.args.csv and self.args.compare:
            self.parser.error("Error: This tool currently can't export comparisons as CSV. Use --print instead.")

        # Set log level
        loglevel = getattr(logging, self.args.loglevel.upper(), None)
        if not isinstance(loglevel, int):
            raise ValueError('Invalid log level: {}'.format(args.loglevel))
        logging.basicConfig(level=loglevel)

        # Create model
        if self.args.load:   # ...or get a ready-made one from disk?
            with open(self.args.load, 'rb') as fd:
                self.world = pickle.load(fd)
        else:
            password = self.get_password()
            self.world = self.create_services(self.args.confluence, self.args.jira, self.args.stash)
            for service in self.world.services:  # TODO beautify
                service.login(self.args.user, password)

    def run_action(self):
        permissions = self.world.permissions  # TODO: get rid of this

        if self.args.compare:
            with open(self.args.compare, 'rb') as fd:
                current_permissions = permissions
                previous_permissions = pickle.load(fd).permissions
                permissions = DeepDiff(previous_permissions, current_permissions, ignore_order=True)

                if self.args.print:
                    pprint(permissions)
                return
                # TODO: beautify (output as well as code)

        if self.args.csv:
            view = WorldCsvView(self.world)
            view.export_csv(self.args.csv, self.args.csv_header)

        if self.args.save:
            with open(self.args.save, 'wb') as fd:
                self.world.logout()
                pickle.dump(self.world, fd)

        if self.args.print:
            view = WorldTextView(self.world)
            view.print()

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
        services = []
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
                    services.append(service(uri, name=name, version=version))
        world = MyLittleAtlassianWorld(services)
        return world
