import sys
from collections import namedtuple

from pymongo import MongoClient

from .Options import options
from .classifier import Classifier

class WordInfo(namedtuple("WordInfo", ("spamcount", "hamcount"))):
    def __new__(_cls, spamcount, hamcount, *args):
        """Create a new instance of WordInfo(spamcount, hamcount)"""
        return _tuple.__new__(_cls, (spamcount, hamcount))

class MongoClassifierState(namedtuple("MongoClassifierState", ("wordinfo", "nspam", "nham"))):
    def __new__(_cls, wordinfo, nspam, nham, *args):
        """Create a new instance of MongoClassifierState(wordinfo, nspam, nham)"""
        return _tuple.__new__(_cls, (wordinfo, nspam, nham))

class MongoClassifier(object, Classifier):
    """Classifier with state persisted in MongoDB."""

    STATE_COLLECTION = "save_state"

    def __init__(self, db_url="mongodb://localhost", db_name="spambayes_lite",
                 collection_name="spambayes"):
        classifier.Classifier.__init__(self)
        self.collection_name = collection_name
        self.db_name = db_name
        self.db_url = db_url
        self.load()

    def load(self):
        try:
            self.db = pymongo.MongoClient(self.db_url)[self.db_name]
        except:
            import pdb; pdb.set_trace()


        state = self.db[self.STATE_COLLECTION].find_one(
            {"collection": self.collection_name}, as_class=MongoClassifierState)
        if state is not None:
            self.wordinfo = state.wordinfo
            self.nham = state.nham
            self.nspam = state.nspam
        else:
            # Collection of this type does not exist.
            self.wordinfo = {}
            self.nham = 0
            self.nspam = 0
            self.db.create_collection(self.collection_names)
            self.db[self.STATE_COLLECTION].insert(
                {"collection": self.collection_name,
                 "wordinfo": self.wordinfo,
                 "nspam": self.nspam,
                 "nham": self.nham})


    def _get_row(self, word, retclass=dict):
        return self.db[self.collection_name].find_one(
            {"word": word}, as_class=retclass)

    def _set_row(self, word, nspam, nham):
        self.db[self.collection_name].update(
            {"word": word}, {"$set": {"nspam": nspam, "nham": nham}},
            upsert=True)

    def _delete_row(self, word):
        self.db[self.collection_name].remove({"word": word})

    def _has_key(self, key):
        return self.db[self.collection_name].find_one({"word": word}) is not None

    def _wordinfoget(self, word):
        if isinstance(word, unicode):
            word = word.encode("utf-8")

        row = self._get_row(word, retclass=WordInfo)
        if row is not None:
            return row
        else:
            return WordInfo(0, 0)

    def _wordinfoset(self, word, record):
        if isinstance(word, unicode):
            word = word.encode("utf-8")
        self._set_row(word, record.spamcount, record.hamcount)

    def _wordinfodel(self, word):
        if isinstance(word, unicode):
            word = word.encode("utf-8")
        self._delete_row(word)

    def _wordinfokeys(self):
        return [r["word"] for r in self.db[self.collection_name].find()
                if "word" in r]


    def close(self):
        pass
