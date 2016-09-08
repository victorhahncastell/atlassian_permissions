#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod, abstractproperty
import re


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
