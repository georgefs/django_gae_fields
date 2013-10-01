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
from django.utils.encoding import smart_str



class GFile(models.FileField):
    _key=None
    _content_type=None
    _f=None
    def __init__(self, value, *args, **kwargs):
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
        self.file.seek(0)
        self._key = blob.save(self.file.read())

    def get_datastore(self):
        if self._f:
            return
        self._f = StringIO(blob.get(self.key))

    @property
    def file(self):
        if not self._f:
            self.get_datastore()
        self._f.seek(0)
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
    aes_key = None
    aes_iv = None
    def __init__(self, value, key="", iv="",  *args, **kwargs):
        if isinstance(value, basestring):
            data = json.loads(value)
            self._key = data['key']
            self._content_type = data['content_type']
        else:
            self._f = value.file
            self._content_type = value.content_type
        self.aes_key = smart_str(key).rjust(16)
        self.aes_iv = smart_str(iv).rjust(16)
        assert len(self.aes_key) == 16, 'key must less then 16 byte string'
        assert len(self.aes_iv) == 16, 'iv must less then 16 byte string'

    def save_datastore(self):
        if self._key:
            return
        value = self._f.read()
        value = base64.b64encode(value)
        value = value + " " * (16 - len(value) % 16)
        value = self.aes.encrypt(value)
        self._key = blob.save(value)
        
    def get_datastore(self):
        if self._f:
            return
        value = blob.get(self._key)
        value = self.aes.decrypt(value).strip()
        value = base64.b64decode(value)
        self._f = StringIO(value)

    @property
    def aes(self):
        return AES.new(self.aes_key, AES.MODE_CBC, self.aes_iv)



class GFileField(models.Field):
    def to_python(self, value):
        if not value:
            return value
        return GFile(value)

    def get_prep_value(self, value):
        if not value:
            return value
        value = self.to_python(value)
        return value.content

    def db_type(self, connection):
        return 'TEXT'

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.FileField}
        if 'initial' in kwargs:
            defaults['required'] = False

        defaults.update(kwargs)
        return super(GFileField, self).formfield(**defaults)

class AESGFileField(GFileField):
    key = None
    iv = None
    def __init__(self, key="", iv="", *args, **kwargs):
        self.key = key
        self.iv = iv
        super(AESGFileField, self).__init__(self, *args, **kwargs)

    def to_python(self, value):
        if not value:
            return value
        return AESGFile(value, key=self.key, iv=self.iv)

    def contribute_to_class(self, cls, name):
        super(AESGFileField, self).contribute_to_class(cls, name)
        setattr(cls, name, self)


try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^django_gae\.fields\.GFileField"])
    add_introspection_rules([], ["^django_gae\.fields\.AESGFileField"])
except:
    pass

