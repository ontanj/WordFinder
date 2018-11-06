from selenium import webdriver
import os
from selenium.common.exceptions import NoSuchElementException
import sys
import re

class SAOLWordFinder(webdriver.Chrome):

    def __init__(self, pattern, verbose=False, headless=True):
        self.first_finder = re.compile(r'^(\w*)([$|@|£])')
        self.pattern = pattern
        self.words = []
        self.consonants = "bcdfghjklmnpqrstvwxz"
        self.vocals = "aeiouyåäö"
        self.letters = "abcdefghijklmnopqrstuvwxyzåäö"
        self.compile_regex(pattern)
        if headless:
            chromeOptions = webdriver.ChromeOptions()
            chromeOptions.add_argument("headless")
            prefs = {"profile.managed_default_content_settings.images":2}
            chromeOptions.add_experimental_option("prefs",prefs)
        else:
            chromeOptions = None
        dir_path = os.path.dirname(os.path.realpath(__file__))
        super().__init__(executable_path=dir_path+"/chromedriver", chrome_options=chromeOptions)

    def goto(self, word):
        self.get("https://svenska.se/tri/f_saol.php?sok=" + word)

    def saol_text(self):
        return self.find_element_by_class_name("cshow").text

    def fit(self, lemma):
        all_forms = lemma.find_elements_by_class_name("bform")
        if all_forms == []:
            return None
        for form in all_forms:
            form_text = form.text
            if self.regex_pattern.match(form_text) != None:
                return form_text
        return False

    def _saol_lemmas(self):
        lemmas = self.find_elements_by_class_name("lemma")
        if not lemmas:
            return None
        defs = []
        for lemma in lemmas:
            word_fit = self.fit(lemma)
            if word_fit == False:
                continue
            elif word_fit == None:
                try:
                    word_fit = lemma.find_element_by_class_name("grundform").text
                except NoSuchElementException:
                    continue
            try:
                found_defs = lemma.find_elements_by_class_name("def")
            except NoSuchElementException:
                found_defs = []
            found_defs_text = []
            for defi in found_defs:
                found_defs_text.append(defi.text.replace("\u00AD", ""))
            defs.append((word_fit, found_defs_text))
        return defs

    def _saol_digs(self):
        digs = self.find_elements_by_tag_name("a")
        for i in range(len(digs)):
            not_stale_digs = self.find_elements_by_tag_name("a")
            yield not_stale_digs[i]

    def _click_dig(self, dig):
        link = dig.get_attribute("onclick")[26:-2]
        self.get("https://svenska.se" + link)

    def search(self):
        self.look_for(self.pattern)

    def compile_regex(self, pattern):
        pattern = pattern.replace('@',f'[{self.vocals}]').replace('£',f'[{self.letters}]').replace('$',f'[{self.consonants}]')
        pattern = "^" + pattern + "$"
        self.regex_pattern = re.compile(pattern)

    def from_pattern(self, pattern):
        return pattern.replace('@','?').replace('£','?').replace('$','?')

    def new_search_array(self, pattern, last):
        pos, letters_after = self.find_first(pattern, last)
        n = [pattern[0:pos] + letter + pattern[pos+1:] for letter in letters_after]
        return n

    def find_first(self, pattern, last):
        match = self.first_finder.search(pattern)
        pos = len(match.group(1))
        sign = match.group(2)
        if sign == "@":
            letters = self.vocals
        elif sign == "$":
            letters = self.consonants
        else:
            letters = self.letters
        letters_after = letters[letters.index(last[pos]):]
        return pos, letters_after

    def look_for(self, pattern):
        search_word = self.from_pattern(pattern)
        last = self.check(search_word)
        if last == True:
            return
        new_props = self.new_search_array(pattern, last)
        for prop in new_props:
            self.look_for(prop)

    def check(self, word):
        self.goto(word)
        text = self.saol_text()
        if "inga svar" in text:
            return True
        lemmas = self._saol_lemmas()
        if lemmas or lemmas == []:
            self.words.extend(lemmas)
            return True
        else:
            digs = self._saol_digs()
            lemmas_1 = []
            for d in digs:
                self._click_dig(d)
                lemmas_2 = self._saol_lemmas()
                if lemmas_1 != lemmas_2:
                    self.words.extend(lemmas_2)
                lemmas_1 = lemmas_2
                self.back()
        if "..." in text and lemmas_2:
            last = lemmas_2[-1][0]
            return last
        else:
            return True
        
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
    if print_props:
        props = prop(word)
        string = f"Följande möjligheter finns:\n"
        for p in props:
            string += p + ", "
        print(string[0:-2]) #remove last comma
        print(f"\n{len(props)} stycken.\n")

    if saol:
        do_check = "Y"
    else:
        do_check = input("Vill du kolla mot SAOL? [Y/n]\n")
    if do_check != "n":
        wd = SAOLWordFinder(word, verbose=True, headless=True)
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
        wd.close()