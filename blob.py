#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2013 george
#
# Distributed under terms of the MIT license.

from google.appengine.ext import ndb


class Blob(ndb.Model):
    data = ndb.BlobProperty()

def save(blobdata):
    result = Blob(data=blobdata)
    result.put()
    return result.key.id()


def get(blobkey):
    file = ndb.Key(Blob, int(blobkey)).get()
    return file.data

