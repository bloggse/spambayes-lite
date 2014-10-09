# Copyright 2014, Daniel Brandt <me@dbrandt.se>.
# Distributable under the same terms as the Python programming language.

import dns.resolver
import dns.exception
import dns.reversename


class NSCache(object):
    "Cached DNS resolver and cache singleton"

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(NSCache, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "resolver"):
            self.resolver = dns.resolver.Resolver()
            self.resolver.cache = dns.resolver.LRUCache()

    def lookup(self, name, qtype="A"):
        qtype = qtype.upper()
        if qtype == "PTR":
            return self.reverse_lookup(name)
        elif qtype != "A":
            raise RuntimeError("Only A and PTR requests allowed (you tried %s)." %
                               (qtype,))
        try:
            name = name.decode("utf8")
        except UnicodeError:
            pass
        try:
            res = self.resolver.query(name, "A")
        except dns.exception.DNSException:
            return []
        return [x.address for x in res.rrset.items]

    def reverse_lookup(self, ip):
        try:
            rname = dns.reversename.from_address(ip)
        except AttributeError, SyntaxError:
            # Malformed in-data in some way or another.
            return ""
        try:
            res = self.resolver.query(rname, "PTR")
        except dns.exception.DNSException:
            return ""
        if len(res.rrset.items):
            res = res.rrset.items[0].target.to_text()
            if res.endswith("."):
                return res[:-1]
