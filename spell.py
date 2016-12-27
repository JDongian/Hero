"""Statistical spell checker
See http://norvig.com/spell-correct.html for more details.

TODO: numpy, pickle, restructure for full documents
"""

import string
import re
from collections import Counter
import glob, os
import string

CORPUS_DIR = "./corpus"

def _words(text):
    return re.findall(r'\w+', text.lower())


def _get_corpus():
    corpus = []
    with open('big.txt', 'r') as fp:
        corpus.append(fp.read())

    # use all files in the directory
    for fname in glob.iglob(os.path.join(CORPUS_DIR, '**/*'), recursive=True):
        if os.path.isfile(fname):
            with open(fname, 'rb') as fp:
                # logging.debug("adding to corpus: {}".format(fname))
                corpus.append(fp.read().decode(errors='ignore'))

    return ''.join(corpus)

WORDS = Counter(_words(_get_corpus()))


def update_corpus(text):
    WORDS.update(_words(text))


def _P(word, N=sum(WORDS.values())):
    "Probability of `word`."
    return WORDS[word] / N


def _candidates(word):
    "Generate possible spelling corrections for word."
    return (_known([word]) or
            _known(_edits1(word)) or
            _known(_edits2(word)) or
            [word])


def _known(words):
    "The subset of `words` that appear in the dictionary of WORDS."
    return set(w for w in words if w in WORDS)


def _edits1(word):
    "All edits that are one edit away from `word`."
    letters    = 'abcdefghijklmnopqrstuvwxyz'
    splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
    deletes    = [L + R[1:]               for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]
    replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
    inserts    = [L + c + R               for L, R in splits for c in letters]
    return set(deletes + transposes + replaces + inserts)


def _edits2(word):
    "All edits that are two edits away from `word`."
    return (e2 for e1 in _edits1(word) for e2 in _edits1(e1))


def _correction(word):
    "Most probable spelling correction for word."
    return max(_candidates(word), key=_P)


def _case_match(raw, ref):
    # if first letter is uppercase
    if ref[0] in string.ascii_uppercase:
        raw = raw[0].upper() + raw[1:]

    # if all uppercase
    if ref[-1] in string.ascii_uppercase:
        raw = raw.upper()

    return raw


def _hil(new, original):
    u_in = input("{}->{}? ".format(original, new))
    return u_in and u_in[0] == 'y'


def correct(doc):
    replacements = dict()
    # naiive word iteration
    parts = re.split('(\s+)', doc)
    # sort for debug only
    for word in sorted(list(set(parts))):
        # only work with easy words
        if re.match('^[A-Za-z]+$', word):
            new_word = _case_match(_correction(word.lower()), word)
            if new_word != word and _hil(new_word, word):
                replacements[word] = new_word

    # TODO: very inefficient
    for i in range(len(parts)):
        part = parts[i]
        part = replacements.get(part, part)
        parts[i] = part

    return ''.join(parts)


def spellcheck(filename):
    with open(filename, 'rb') as fp:
        doc = fp.read().decode(errors='ignore')

    logging.debug("spell-checking file{}".format(filename))
    return spell.correct(doc)
