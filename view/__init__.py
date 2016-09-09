#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from deepdiff import DeepDiff


class TextView(metaclass=ABCMeta):
    """
    Abstract base class for views that can be represented as text.
    I.e., currently all of our views.
    """
    def __init__(self, model, diff=None, cmp=None):
        self.model = model
        """The model this view draws data from. For a global view this should be a MyLittleAtlassian world object."""

        self._output = None

        self._cmp = cmp
        """Another model to compare to if this view should include a diff"""

        # self.diff
        """
        Whether to include a diff in the output (diff="yes"), print only changes (diff="only").
        diff should be "no" otherwise.
        If a diff is requestes, another model to compare to must be passed as cmp.
        Default is "yes" if cmp is set on construction, "no" otherwise.
        """
        if self._cmp is None:
            self._diff = "no"
        else:
            if diff in ("yes", "no", "only"):  # diff set correctly by caller
                self._diff = diff
            else:                              # not set by caller or invalid
                self._diff = "no"

    @property
    def diff(self):
        return self._diff

    @diff.setter
    def diff(self, value):
        self._diff = value
        self._output = None

    @property
    def cmp(self):
        return self._cmp

    @cmp.setter
    def cmp(self, value):
        self._cmp = value
        self._output = None

    @property
    def output(self):
        if self._output is None:
            self.generate()
        return self._output

    @abstractmethod
    def generate(self):
        pass

    def export(self, filename):
        with open(filename, 'w') as file:
            file.write(self.output)

    def print(self):
        print(self.output)

    def _prepare_data_for_generate(self):
        """
        Prepare two dicts that our child class will use to generate the view:
          - pemdata
          - metadata
            - header_messages: error/warning/notice messages to be displayed "on top"
        """
        # TODO: should use this structure for all views / in all child classes
        permdata = self.model.permissions
        metadata = dict()

        contains_change = set()  # for diff only, we collect all containers actually containing changes
        if self.diff == "yes" or self.diff == "only":
            olddata = self.cmp.permissions
            diff = DeepDiff(olddata, permdata, default_view='ref')
            if 'set_item_removed' in diff:
                for change in diff['set_item_removed']:
                    contains_change.add(change.up.up.t2)  # up from string to user/group set, up to PermissionEntry
                    self.add_rem_parse(change)  # subclass implements to mark this item as removed
            if 'set_item_added' in diff:
                for change in diff['set_item_added']:
                    contains_change.add(change.up.up.t2)  # up from string to user/group set, up to PermissionEntry
                    self.add_rem_parse(change)  # subclass implements to mark this item as added

        remove = list()
        if self.diff == "only":
            metadata['title'] = 'Atlassian permission change report'
            metadata['msg_no_data'] = "No changes"
            for service_key, projects in permdata.items():
                for project_key, permissions in projects.items():
                    any_change = False
                    for permission in permissions.values():
                        if permission in contains_change:
                            any_change = True
                    if not any_change:
                        # remove this project if none of its permissions (e.g. User, Developer...) has changes
                        remove.append( (projects, project_key) )
            for remove_from, item in remove:
                del remove_from[item]
        else:
            metadata['title'] = 'Atlassian permissions'

        return permdata, metadata

    @classmethod
    def add_rem_parse(cls, change):
        parentset = change.up.t2

        if change.report_type == 'set_item_added':
            parentset.discard(change.t2)
            parentset.add(cls.format_item_added(change.t2))
        elif change.report_type == 'set_item_removed':
            parentset.add(cls.format_item_removed(change.t1))

    @classmethod
    def msg_compare_partially_unparsable(cls, metadata):
        """
        Call msg_header and write a header message telling the user
        that the provided comparison data is at least partly unparsable.
        """
        cls.msg_header(metadata, 'cmp_partially_unparsable',
                       "Compare data (partially) unparsable. " +
                       "Please ensure the old data was recorded using the same version " +
                       "of this software. Note this software can not currently display " +
                       "added, renamed or removed projects.")


    @classmethod
    def msg_header(cls, metadata, name, text):
        """
        Prepare a metadata message that the specific view should print header notice.
        """
        if 'header_messages' not in metadata:
            metadata['header_messages'] = dict()
        metadata['header_messages'][name] = text
