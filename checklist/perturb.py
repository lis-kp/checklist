import numpy as np
import re
import os
import json
from .editor import recursive_apply

def load_data():
    cur_folder = os.path.dirname(__file__)
    basic = json.load(open(os.path.join(cur_folder, os.pardir, 'data', 'lexicons', 'basic.json')))
    names = json.load(open(os.path.join(cur_folder, os.pardir, 'data', 'names.json')))
    name_set = { x:set(names[x]) for x in names }
    data = {
        'name': names,
        'name_set': name_set,
        'city': basic['city'],
        'country': basic['country'],
    }
    return data

def process_ret(ret, ret_m=None, meta=False, n=10):
    if ret:
        if len(ret) > n:
            idxs = np.random.choice(len(ret), n, replace=False)
            ret = [ret[i] for i in idxs]
            if ret_m:
                ret_m = [ret_m[i] for i in idxs]
        if meta:
            ret = (ret, ret_m)
        return ret
    return None

class Perturb:
    data = load_data()
    @staticmethod
    def perturb(data, perturb_fn, keep_original=True, returns_meta=False, nsamples=None, *args, **kwargs):
        ret = []
        ret_add = []
        order = list(range(len(data)))
        samples = 0
        if nsamples:
            np.random.shuffle(order)
        for i in order:
            d = data[i]
            t = []
            add = []
            if keep_original:
                org = recursive_apply(d, str)
                # tp = type(d)
                # if tp in [list, np.array, tuple]:
                #     org = tp([str(x) for x in d])
                # else:
                #     org = str(d)
                t.append(org)
                add.append({})
            p = perturb_fn(d, *args, **kwargs)
            a = []
            x = []
            if not p:
                continue
            if returns_meta:
                p, a = p
            if type(p) in [np.array, list]:
                t.extend(p)
                add.extend(a)
            else:
                t.append(p)
                add.append(a)
            ret.append(t)
            ret_add.append(add)
            samples += 1
            if nsamples and samples == nsamples:
                break
        if returns_meta:
            return ret, ret_add
        return ret

    @staticmethod
    def strip_punctuation(doc):
        # doc is a spacy doc
        while doc[-1].pos_ == 'PUNCT':
            doc = doc[:-1]
        return doc.text

    @staticmethod
    def punctuation(doc):
        # doc is a spacy doc
        s = Perturb.strip_punctuation(doc)
        ret = []
        if s != doc.text:
            ret.append(s)
        if s + '.' != doc.text:
            ret.append(s + '.')
        return ret


    @staticmethod
    def add_typos(string, typos=1):
        string = list(string)
        swaps = np.random.choice(len(string) - 1, typos)
        for swap in swaps:
            tmp = string[swap]
            string[swap] = string[swap + 1]
            string[swap + 1] = tmp
        return ''.join(string)

    @staticmethod
    def contractions(sentence):
        expanded = [Perturb.expand_contractions(sentence), Perturb.contract(sentence)]
        return [t for t in expanded if t != sentence]

    @staticmethod
    def expand_contractions(sentence):
        contraction_map = {
            "ain't": "is not", "aren't": "are not", "can't": "cannot",
            "can't've": "cannot have", "could've": "could have", "couldn't":
            "could not", "didn't": "did not", "doesn't": "does not", "don't":
            "do not", "hadn't": "had not", "hasn't": "has not", "haven't":
            "have not", "he'd": "he would", "he'd've": "he would have",
            "he'll": "he will", "he's": "he is", "how'd": "how did", "how'd'y":
            "how do you", "how'll": "how will", "how's": "how is",
            "I'd": "I would", "I'll": "I will", "I'm": "I am",
            "I've": "I have", "i'd": "i would", "i'll": "i will",
            "i'm": "i am", "i've": "i have", "isn't": "is not",
            "it'd": "it would", "it'll": "it will", "it's": "it is", "ma'am":
            "madam", "might've": "might have", "mightn't": "might not",
            "must've": "must have", "mustn't": "must not", "needn't":
            "need not", "oughtn't": "ought not", "shan't": "shall not",
            "she'd": "she would", "she'll": "she will", "she's": "she is",
            "should've": "should have", "shouldn't": "should not", "that'd":
            "that would", "that's": "that is", "there'd": "there would",
            "there's": "there is", "they'd": "they would",
            "they'll": "they will", "they're": "they are",
            "they've": "they have", "wasn't": "was not", "we'd": "we would",
            "we'll": "we will", "we're": "we are", "we've": "we have",
            "weren't": "were not", "what're": "what are", "what's": "what is",
            "when's": "when is", "where'd": "where did", "where's": "where is",
            "where've": "where have", "who'll": "who will", "who's": "who is",
            "who've": "who have", "why's": "why is", "won't": "will not",
            "would've": "would have", "wouldn't": "would not",
            "you'd": "you would", "you'd've": "you would have",
            "you'll": "you will", "you're": "you are", "you've": "you have"
            }
        # self.reverse_contraction_map = dict([(y, x) for x, y in self.contraction_map.items()])
        contraction_pattern = re.compile(r'\b({})\b'.format('|'.join(contraction_map.keys())),
            flags=re.IGNORECASE|re.DOTALL)

        def expand_match(contraction):
            match = contraction.group(0)
            first_char = match[0]
            expanded_contraction = contraction_map.get(match, contraction_map.get(match.lower()))
            expanded_contraction = first_char + expanded_contraction[1:]
            return expanded_contraction
        return contraction_pattern.sub(expand_match, sentence)

    @staticmethod
    def contract(sentence):
        reverse_contraction_map = {
            'is not': "isn't", 'are not': "aren't", 'cannot': "can't",
            'could not': "couldn't", 'did not': "didn't", 'does not':
            "doesn't", 'do not': "don't", 'had not': "hadn't", 'has not':
            "hasn't", 'have not': "haven't", 'he is': "he's", 'how did':
            "how'd", 'how is': "how's", 'I would': "I'd", 'I will': "I'll",
            'I am': "I'm", 'i would': "i'd", 'i will': "i'll", 'i am': "i'm",
            'it would': "it'd", 'it will': "it'll", 'it is': "it's",
            'might not': "mightn't", 'must not': "mustn't", 'need not': "needn't",
            'ought not': "oughtn't", 'shall not': "shan't", 'she would': "she'd",
            'she will': "she'll", 'she is': "she's", 'should not': "shouldn't",
            'that would': "that'd", 'that is': "that's", 'there would':
            "there'd", 'there is': "there's", 'they would': "they'd",
            'they will': "they'll", 'they are': "they're", 'was not': "wasn't",
            'we would': "we'd", 'we will': "we'll", 'we are': "we're", 'were not':
            "weren't", 'what are': "what're", 'what is': "what's", 'when is':
            "when's", 'where did': "where'd", 'where is': "where's",
            'who will': "who'll", 'who is': "who's", 'who have': "who've", 'why is':
            "why's", 'will not': "won't", 'would not': "wouldn't", 'you would':
            "you'd", 'you will': "you'll", 'you are': "you're",
        }

        reverse_contraction_pattern = re.compile(r'\b({})\b '.format('|'.join(reverse_contraction_map.keys())),
            flags=re.IGNORECASE|re.DOTALL)
        def cont(possible):
            match = possible.group(1)
            first_char = match[0]
            expanded_contraction = reverse_contraction_map.get(match, reverse_contraction_map.get(match.lower()))
            expanded_contraction = first_char + expanded_contraction[1:] + ' '
            return expanded_contraction
        return reverse_contraction_pattern.sub(cont, sentence)

    @staticmethod
    def change_names(doc, meta=False, n=10, first_only=False, last_only=False):
        ents = [x.text for x in doc.ents if np.all([a.ent_type_ == 'PERSON' for a in x])]
        ret = []
        ret_m = []
        for x in ents:
            f = x.split()[0]
            sex = None
            if f.capitalize() in Perturb.data['name_set']['women']:
                sex = 'women'
            if f.capitalize() in Perturb.data['name_set']['men']:
                sex = 'men'
            if not sex:
                continue
            if len(x.split()) > 1:
                l = x.split()[1]
                if len(l) > 2 and l.capitalize() not in Perturb.data['name_set']['last']:
                    continue
            else:
                if last_only:
                    return None
            names = Perturb.data['name'][sex][:90+n]
            to_use = np.random.choice(names, n)
            if not first_only:
                f = x
                if len(x.split()) > 1:
                    last = Perturb.data['name']['last'][:90+n]
                    last = np.random.choice(last, n)
                    to_use = ['%s %s' % (x, y) for x, y in zip(names, last)]
                    if last_only:
                        to_use = last
                        f = x.split()[1]
            for y in to_use:
                ret.append(re.sub(r'\b%s\b' % re.escape(f), y, doc.text))
                ret_m.append((f, y))
        return process_ret(ret, ret_m=ret_m, n=n, meta=meta)

    @staticmethod
    def change_location(doc, meta=False, n=10):
        ents = [x.text for x in doc.ents if np.all([a.ent_type_ == 'GPE' for a in x])]
        ret = []
        ret_m = []
        for x in ents:
            if x in Perturb.data['city']:
                names = Perturb.data['city']
            elif x in Perturb.data['country']:
                names = Perturb.data['country']
            else:
                continue
            sub_re = re.compile(r'\b%s\b' % re.escape(x))
            to_use = np.random.choice(names, n)
            ret.extend([sub_re.sub(n, doc.text) for n in to_use])
            ret_m.extend([(x, n) for n in to_use])
        return process_ret(ret, ret_m=ret_m, n=n, meta=meta)

    @staticmethod
    def change_number(doc, meta=False, n=10):
        nums = [x.text for x in doc if x.text.isdigit()]
        ret = []
        ret_m = []
        for x in nums:
            # e.g. this is 4 you
            if x == '2' or x == '4':
                continue
            sub_re = re.compile(r'\b%s\b' % x)
            change = int(int(x) * .2) + 1
            to_sub = np.random.randint(-min(change, int(x) - 1), change + 1, n * 3)
            to_sub = ['%s' % str(int(x) + t) for t in to_sub if t != x][:n]
            ret.extend([sub_re.sub(n, doc.text) for n in to_sub])
            ret_m.extend([(x, n) for n in to_sub])
        return process_ret(ret, ret_m=ret_m, n=n, meta=meta)