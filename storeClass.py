from google.appengine.ext import ndb

class WStore2(ndb.Model):
    """Weather data daily entries."""
    cur_date = ndb.DateTimeProperty()
    data_date= ndb.DateTimeProperty()
    idx=ndb.IntegerProperty(indexed=True)
    content= ndb.PickleProperty()
    src=ndb.StringProperty()