# -*- coding: utf-8 -*-
#
"""
BigramSplitter.py

Created by Mikio Hokari, CMScom and Manabu Terada, CMScom on 2009-09-30.
"""
import unicodedata
import pythai

# from zope.interface import implements
from Products.ZCTextIndex.ISplitter import ISplitter
from Products.ZCTextIndex.PipelineFactory import element_factory
from Products.CMFPlone.utils import classImplements
# from Products.CMFPlone.utils import getSiteEncoding

from Products.BigramSplitter.config import rx_U, rxGlob_U, \
            rx_L, rxGlob_L, rx_all, pattern, pattern_g


def bigram(u, limit=1):
    """ Split into bi-gram.
    limit arg describes ending process.
    If limit = 0 then
        日本人-> [日本,本人, 人]
        金 -> [金]
    If limit = 1 then
        日本人-> [日本,本人]
        金 -> []
    """
    return [u[i:i+2] for i in xrange(len(u) - limit)]

 
# An ugly hack for Benar Thai site
# Using the split function in pythai: https://pypi.org/project/pythai/
# Make it work with Thai language in Plone (Not bi-gram anymore though)
def pythai_split(u, limit=1):
    """ 
    Using PyThai to split thai words
    """
    return pythai.split(u)


def process_str_post(s, enc):
    """Receive str, remove ? and *, then return str.
    If decode gets successful, process str as unicode.
    If decode gets failed, process str as ASCII.
    """
    try:
        if not isinstance(s, unicode):
            uni = s.decode(enc, "strict")
        else:
            uni = s
    except UnicodeDecodeError, e:
        return s.replace("?", "").replace("*", "")
    try:
        return uni.replace(u"?", u"").replace(u"*", u"").encode(enc, "strict")
    except UnicodeEncodeError, e:
        return s.replace("?", "").replace("*", "")


def process_str(s, enc):
    """Receive str and encoding, then return the list 
    of str as bi-grammed result.
    Decode str into unicode and pass it to process_unicode.
    When decode failed, return the result splitted per word.
    Splitting depends on locale specified by rx_L.
    """
    try:
        if not isinstance(s, unicode):
            uni = s.decode(enc, "strict")
        else:
            uni = s
    except UnicodeDecodeError, e:
        return rx_L.findall(s)
    bigrams = process_unicode(uni)
    return [x.encode(enc, "strict") for x in bigrams]


def process_str_glob(s, enc):
    """Receive str and encoding, then return the list
    of str considering glob processing.
    Decode str into unicode and pass it to process_unicode_glob.
    When decode failed, return the result splitted per word.
    Splitting depends on locale specified by rxGlob_L.
    """
    try:
        if not isinstance(s, unicode):
            uni = s.decode(enc, "strict")
        else:
            uni = s
    except UnicodeDecodeError, e:
        return rxGlob_L.findall(s)
    bigrams = process_unicode_glob(uni)
    return [x.encode(enc, "strict") for x in bigrams]


def process_unicode(uni):
    """Receive unicode string, then return a list of unicode
    as bi-grammed result.
    """
    normalized = unicodedata.normalize('NFKC', uni)
    for word in rx_U.findall(normalized):
        swords = [g.group() for g in pattern.finditer(word)]
        for sword in swords:
            if not rx_all.match(sword[0]):
                yield sword
            else:
                for x in pythai_split(sword, 0):
                    yield x


def process_unicode_glob(uni):
    """Receive unicode string, then return a list of unicode
    as bi-grammed result.  Considering globbing.
    """
    normalized = unicodedata.normalize('NFKC', uni)
    for word in rxGlob_U.findall(normalized):
        swords = [g.group() for g in pattern_g.finditer(word)
                  if g.group() not in u"*?"]
        for i, sword in enumerate(swords):
            if not rx_all.match(sword[0]):
                yield sword
            else:
                if i == len(swords) - 1:
                    limit = 1
                else:
                    limit = 0
                if len(sword) == 1:
                    bigramed = [sword + u"*"]
                else:
                    bigramed = pythai_split(sword, limit)
                for x in bigramed:
                    yield x

class BigramSplitter(object):
    meta_type = 'BigramSplitter'
    __implements__ = ISplitter

    def process(self, lst):
        """ Will be called when indexing.
        Receive list of str, make it bi-grammed, then return
        the list of str.
        """
        # XXX: Hanno says we only support utf-8 getSiteEncoding won't
        # work from here without some nasty tricks
        enc = 'utf-8'
        result = [x for s in lst for x in process_str(s, enc)]
        return result

    def processGlob(self, lst):
        """ Will be called once when searching.
        Receive list of str, make it bi-grammed considering
        globbing, then return the list of str.
        """
        enc = 'utf-8'
        result = [x for s in lst for x in process_str_glob(s, enc)]
        return result

    def process_post_glob(self, lst):
        """ Will be called twice when searching.
        Receive list of str, Remove ? and *, then return
        the list of str.
        """
        enc = 'utf-8'
        result = [process_str_post(s, enc) for s in lst]
        return result

classImplements(BigramSplitter, BigramSplitter.__implements__)

try:
    element_factory.registerFactory('Word Splitter',
        'Bigram Splitter', BigramSplitter)
except ValueError:
    # In case the splitter is already registered, ValueError is raised
    pass


class BigramCaseNormalizer(object):

    def process(self, lst):
        enc = 'utf-8'
        result = []
        for s in lst:
            # This is a hack to get the normalizer working with
            # non-unicode text.
            try:
                if not isinstance(s, unicode):
                    s = unicode(s, enc)
            except (UnicodeDecodeError, TypeError):
                result.append(s.lower())
            else:
                result.append(s.lower().encode(enc))
        return result

try:
    element_factory.registerFactory('Case Normalizer',
        'Bigram Case Normalizer', BigramCaseNormalizer)
except ValueError:
    # In case the normalizer is already registered, ValueError is raised
    pass

