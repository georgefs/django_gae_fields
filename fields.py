#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2013 george 
#
# Distributed under terms of the MIT license.

from django.db import models
import json
from cStringIO import StringIO
import blob
from django import forms


class GFile(models.FileField):
    _key=None
    _content_type=None
    _f=None
    def __init__(self, value):
        data = dict()
        if isinstance(value, basestring):
            data = json.loads(value)
            self.key = data['key']
            self.content_type = data['content_type']
        else:
            self._f = value.file
            self._content_type = value.content_type
    
    def save_datastore(self):
        self._key = blob.save(self.file.read())

    def get_datastore(self):
        self._f = StringIO(blob.get(self.key))

    @property
    def file(self):
        if not self._f:
            self.get_datastore()
        return self._f

    @property
    def content_type(self):
        return self._content_type
    
    @property
    def key(self):
        if not self._key:
            self.save_datastore()
        return self._key

    @property
    def content(self):
        data = dict()
        data['key'] = self.key
        data['content_type'] = self.content_type
        return json.dumps(data)


class GFileField(models.Field):
    def to_python(self, value):
        return GFile(value)

    def get_prep_value(self, value):
        value = self.to_python(value)
        return value.content

    def db_type(self, connection):
        return 'TEXT'

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.FileField, 'max_length': self.max_length}
        if 'initial' in kwargs:
            defaults['required'] = False

        defaults.update(kwargs)
        return super(GFileField, self).formfield(**defaults)

