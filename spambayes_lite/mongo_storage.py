from collections import namedtuple

from pymongo import MongoClient
from . import classifier


STATE_COLLECTION = "save_state"

def copy_collection_js(**kwargs):
    return ("""db["%(old)s"].find().forEach(
    function (doc) {
      db["%(new)s"].update({_id: doc._id}, doc, true);
    })""" % kwargs)

def copy_collection(db, source, target, drop_source=False):
    """Copies a collection with server-side javascript. This is about twice
    as fast as roundtripping python in a forloop. Downside is possible locking.
    Meta data about the state of the collection is also updated.
    If source collection should be deleted after copy, set drop_source = True."""
    db.eval(copy_collection_js(old=source, new=target))
    source_state = db[STATE_COLLECTION].find_one({"collection": source})
    db[STATE_COLLECTION].update({"collection": target}, {
        "collection": target,
        "nham": source_state.get("nham", 0),
        "nspam": source_state.get("nspam", 0),
        "wordinfo": source_state.get("wordinfo", {})}, True)
    if drop_source:
        print "Dropping %s after copy" % (source,)
        db[STATE_COLLECTION].remove({"collection": source})
        db[source].drop()

def move_collection(db, source, target):
    copy_collection(db, source, target, drop_source=True)


def replace_collection(db, collection, rebuild):
    """Rotate in new collection generated from rebuild script."""
    backup = "%s_old" % (collection,)
    if backup in db.collection_names():
        db[backup].drop()
    copy_collection(db, collection, backup)
    if not db[collection].count() == db[backup].count():
        # Bad heuristics, but it's better than nothing.
        raise RuntimeError("collection backup failed for %s (%s)" %
                           (collection, backup))
    # Truncate target collection
    db[collection].remove()
    move_collection(db, rebuild, collection)


class MongoClassifier(object, classifier.Classifier):
    """Classifier with state persisted in MongoDB."""

    def __init__(self, db_url="mongodb://localhost", db_name="spambayes_lite",
                 collection_name="spambayes"):
        classifier.Classifier.__init__(self)
        self.collection_name = collection_name
        self.db_name = db_name
        self.db_url = db_url
        self.load()

    def load(self):
        try:
            self.db = MongoClient(self.db_url)[self.db_name]
        except:
            import pdb; pdb.set_trace()


        state = self.db[STATE_COLLECTION].find_one(
            {"collection": self.collection_name})
        if state is not None:
            self.wordinfo = state.get("wordinfo", {})
            self.nham = state.get("nham", 0)
            self.nspam = state.get("nspam", 0)
        else:
            # Collection of this type does not exist.
            self.wordinfo = {}
            self.nham = 0
            self.nspam = 0
            self.db.create_collection(self.collection_name)
            self.db[STATE_COLLECTION].insert(
                {"collection": self.collection_name,
                 "wordinfo": self.wordinfo,
                 "nspam": self.nspam,
                 "nham": self.nham})
        self.db[self.collection_name].ensure_index("word")

    def __repr__(self):
        return ("MongoClassifier(url=%s, db=%s, collection=%s, nham=%d, nspam=%d)" %
                (self.db_url, self.db_name, self.collection_name, self.nham, self.nspam))

    def close(self):
        self._set_save_state((self.wordinfo, self.nspam, self.nham))


    def _copy_from_base(self, base_collection):
        if base_collection in self.db.collection_names():
            self.db.eval(copy_collection_js(new=self.collection_name, old=base_collection))
            state = self.db[STATE_COLLECTION].find_one(
                {"collection": base_collection}) or {}
            state = (state.get("wordinfo", {}), state.get("nspam", 0), state.get("nham", 0))
            self._set_save_state(state)

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
        row = self._get_row(word)
        if row is not None:
            wi = classifier.WordInfo()
            wi.__setstate__((row["nspam"], row["nham"]))
            return wi

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

    def _set_save_state(self, state):
        self.db[STATE_COLLECTION].update(
            {"collection": self.collection_name},
            {"$set":
             {"collection": self.collection_name,
              "wordinfo": state[0],
              "nspam": state[1],
              "nham": state[2]}}, upsert=True)
        self.wordinfo = state[0]
        self.nspam = state[1]
        self.nham = state[2]
