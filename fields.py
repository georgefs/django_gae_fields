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
from Crypto.Cipher import AES
import base64



class GFile(models.FileField):
    _key=None
    _content_type=None
    _f=None
    def __init__(self, value):
        data = dict()
        if isinstance(value, basestring):
            data = json.loads(value)
            self._key = data['key']
            self._content_type = data['content_type']
        else:
            self._f = value.file
            self._content_type = value.content_type
    
    def save_datastore(self):
        if self._key:
            return
        self._key = blob.save(self.file.read())

    def get_datastore(self):
        if self._f:
            return
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


import logging
class AESGFile(GFile):
    def __init__(self, key="", iv="",  *args, **kwargs):
        self.key = smart_str(key).rjust(16)
        self.iv = smart_str(iv).rjust(16)
        self.aes_prefix = aes_prefix
        assert len(self.key) == 16, 'key must less then 16 byte string'
        assert len(self.iv) == 16, 'iv must less then 16 byte string'
        return super(AESGFile, self).__init__(self, *args, **kwargs)

    def save_datastore(self):
        if self._key:
            return
        value = base64.b64encode(value)
        value = value + " " * (16 - len(value) % 16)
        value = self.aes.encrypt(value)
        self._key = blob.save(value)
        
    def get_datastore(self):
        if self._f:
            return
        value = self.aes.decrypt(value).strip()
        value = base64.b64decode(value)
        self._f = StringIO(value)

    @property
    def aes(self):
        return AES.new(self.key, AES.MODE_CBC, self.iv)



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

class AESGFileField(GFileField):
    def to_python(self, value):
        return AESGFile(value)


