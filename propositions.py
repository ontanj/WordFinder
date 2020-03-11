# -*- coding: utf-8 -*-

import sys
import re
import urllib.request as urlr
import urllib
from html.parser import HTMLParser

class SAOLWordFinder:

    def __init__(self, pattern, verbose=False):
        self.first_finder = re.compile(r'^(\w*)([$|@|£])')
        self.find_def = re.compile(r'class="def".*?>(.*?)(?:<span.*?>(.*?)</span>(.*?))?</span>', re.S)
        self.find_links = re.compile(r"onclick=\"return loadDiv\('#saol-1','(/tri/f_saol\.php\?id=.*?)'\)\"><span class=\"dig\">(?: &nbsp|1)")
        self.pattern = pattern
        self.words = []
        self.consonants = "bcdfghjklmnpqrstvwxz"
        self.vocals = "aeiouyåäö"
        self.letters = "abcdefghijklmnopqrstuvwxyzåäö"
        self.compile_regex(pattern)
        self.no_of_props = self.find_no_of_props(pattern)
        self.verbose = verbose
        self.get_wild_numbers()
        self.find_grundform = re.compile(r'<span class="grundform">(.*?)</span>')

    def find_no_of_props(self, pattern):
        self.wild_sequence = re.findall(r'[@£$]', pattern)
        no = 1
        for sign in self.wild_sequence:
            if sign == "@":
                no *= 9
            elif sign == "£":
                no *= 29
            else:
                no *= 20
        return no

    def goto(self, word):
        word = urllib.parse.quote(word)
        return self.get("tri/f_saol.php?sok=" + word)

    def get(self, link):
        req = urlr.Request("https://svenska.se/" + link, headers={"Referer": "https://svenska.se/"})
        with urlr.urlopen(req) as resp:
            html = resp.read().decode("utf-8")
        return html

    def fit(self, lemma):
        match = self.class_pattern.search(lemma) # TODO: matcha grundform
        if match == None:
            return None
        else:
            return match.group(1)

    def search(self):
        self.look_for(self.pattern)
        if self.verbose:
            print("\r                                 ")

    def look_for(self, pattern):
        search_word = self.from_pattern(pattern)
        last = self.check(search_word)
        if last == True:
            return
        new_props = self.new_search_array(pattern, last)
        for prop in new_props:
            self.look_for(prop)

    def check(self, word):
        html = self.goto(word)
        if "inga svar" in html:
            return True
        lemmas = html.split('class="lemma"')
        if len(lemmas) >= 2:
            self._saol_lemmas(lemmas[1:])
            return True
        else:
            more = False
            if "..." in html:
                more = True
            links = self.find_links.findall(html)
            for link in links:
                html = self.get(link)
                lemmas = html.split('class="lemma"')
                last_word = self._saol_lemmas(lemmas[1:])
            if more:
                return last_word
            else:
                return True

    def _saol_lemmas(self, lemmas):
        
        defs = []
        for lemma in lemmas:
            defs_text = []
            word_fit = self.fit(lemma)
            if word_fit == None:
                continue
            matches = self.find_def.findall(lemma)
            for match in matches:
                meaning = ""
                for segment in match:
                    meaning += segment
                defs_text.append(meaning.replace("\u00AD", ""))
            defs.append((word_fit, defs_text))
        self.add_words(defs)
        if not defs:
            match = self.find_grundform.search(lemmas[0])
            return match.group(1)
        return defs[-1][0]

    def compile_regex(self, pattern):
        pattern = pattern.replace('@',f'([{self.vocals}])').replace('£',f'([{self.letters}])').replace('$',f'([{self.consonants}])')
        class_pattern = 'class="bform"[^<>]*>(' + pattern + ')</span>'
        self.word_pattern = re.compile(pattern)
        self.class_pattern = re.compile(class_pattern)

    def from_pattern(self, pattern):
        return pattern.replace('@','?').replace('£','?').replace('$','?')

    def new_search_array(self, pattern, last):
        pos, sign = self.find_first(pattern, last)
        letter = last[pos]
        if sign == "@":
            letters = self.vocals
        elif sign == "$":
            letters = self.consonants
        else:
            letters = self.letters
        letters_after = letters[letters.index(letter):]
        new_patterns = [pattern[0:pos] + letter + pattern[pos+1:] for letter in letters_after]
        if letter == "a":
            extra_patterns = self.new_search_array(new_patterns[0], last)
            new_patterns = extra_patterns + new_patterns[1:]
        return new_patterns

    def find_first(self, pattern, last):
        match = self.first_finder.search(pattern)
        pos = len(match.group(1))
        sign = match.group(2)
        return pos, sign

    def past_words(self, numbers):
        no = 1
        for n in numbers:
            no *= n
        return no

    def get_wild_numbers(self):
        wild_numbers = []
        for sign in self.wild_sequence:
            if sign == "@":
                wild_numbers.append(9)
            elif sign == "£":
                wild_numbers.append(29)
            else:
                wild_numbers.append(20)
        self.wild_numbers = wild_numbers

    def calculate_progress(self, current):
        if not self.verbose:
            return
        matches = self.word_pattern.fullmatch(current)
        matches = matches.groups()
        progress = 0
        for index in range(len(matches)):
            if self.wild_sequence[index] == "@":
                progress += self.vocals.find(matches[index]) * self.past_words(self.wild_numbers[index+1:])
            elif self.wild_sequence[index] == "£":
                progress += self.letters.find(matches[index]) * self.past_words(self.wild_numbers[index+1:])
            else:
                progress += self.consonants.find(matches[index]) * self.past_words(self.wild_numbers[index+1:])
        print(f'\r{progress} / {self.no_of_props}', end="")

    def add_words(self, words):
        for word in words:
            if word not in self.words:
                self.calculate_progress(word[0])
                self.words.append(word)

def prop(word):
    consonants = "bcdfghjklmnpqrstvwxz"
    vocals = "aeiouyåäö"
    letters = "abcdefghijklmnopqrstuvwxyzåäö"
    propositions = [""]
    for letter in word:
        if letter == '@':
            propositions = [former + new for former in propositions for new in vocals]
        elif letter == '$':
            propositions = [former + new for former in propositions for new in consonants]
        elif letter == '£':
            propositions = [former + new for former in propositions for new in letters]
        else:
            propositions = [former + letter for former in propositions]
    return propositions

if __name__ == "__main__":
    headless = True
    word = None
    saol = False
    print_props = True
    for opt in sys.argv[1:]:
        if opt[0] == "-":
            if "i" in opt:
                headless = False
            if "s" in opt:
                saol = True
            if "np" in opt:
                print_props = False
        else:
            word = opt
    
    if word == None:
        print("Löser dina korsordsbekymmer.\n@ är vokal, $ är konsonant, £ är vilken bokstav som helst.")
        word = input("Vilket ord ska lösas?\n")
    else:
        print(f"Löser dina korsordsbekymmer.\n")
        
    wd = SAOLWordFinder(word, verbose=True)
    if print_props:
        dont_print = "n"
        if wd.no_of_props >= 1000:
            print(f'Det finns {wd.no_of_props} möjligheter.\n')
            dont_print = input("Vill du skippa att skriva ut dem? [Y/n]")
        if dont_print == "n":
            props = prop(word)
            string = f"Följande möjligheter finns:\n"
            for p in props:
                string += p + ", "
            print(string[0:-2]) #remove last comma
            print(f"\n{len(props)} stycken.\n")

    if saol:
        do_check = "Y"
    else:
        do_check = input("Vill du kolla mot SAOL? [Y/n]")
    if do_check != "n":
        saol_props = wd.search()
        no_saol_props = len(wd.words)
        if no_saol_props == 0:
            print("Inga möjligheter hittades.")
        else:
            saol_prop_string = f"Följande {len(wd.words)} möjligheter hittades:\n"
            for saol_prop in wd.words:
                def_string = ""
                for defs in saol_prop[1]:
                    def_string += defs + "; "
                saol_prop_string += "\n" + saol_prop[0] + ": " + def_string[0:-2]
            print(saol_prop_string) #remove last comma
