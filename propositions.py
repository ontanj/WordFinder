from selenium import webdriver
import os
import time
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, ElementNotVisibleException
import re
import sys
import getopt

class SAOLReader(webdriver.Chrome):

    def __init__(self, headless=True):
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
        self.get("https://svenska.se/tre/?sok=" + word)

    def saol_text(self):
        try:
            return self._saol_element_text()
        except NoSuchElementException:
            time.sleep(1)
            return self._saol_element_text()

    def _saol_element_text(self):
        return self.find_element_by_id("saol-1").find_element_by_class_name("cshow").text

    def _saol_lexems(self):
        return self.find_element_by_id("saol-1").find_elements_by_class_name("lexem")

    def _saol_digs(self):
        digs = self.find_element_by_id("saol-1").find_element_by_class_name("cshow").find_elements_by_class_name("dig")
        for i in range(len(digs)):
            time.sleep(0.5)
            not_stale_digs = self.find_element_by_id("saol-1").find_element_by_class_name("cshow").find_elements_by_class_name("dig")
            yield not_stale_digs[i]

    def _do_lexems(self, lexems):
        all_lexems = []
        for lexem in lexems:
            try:
                text = lexem.find_element_by_class_name("def").text
            except NoSuchElementException:
                continue
            text = text.replace("\u00AD", "")
            all_lexems.append(text)
        return all_lexems

    def _saol_dig_back(self):
        try:
            self.find_element_by_id("saol-1").find_element_by_class_name("pback").find_element_by_tag_name("a").click()
        except NoSuchElementException:
            time.sleep(0.5)
            self.find_element_by_id("saol-1").find_element_by_class_name("pback").find_element_by_tag_name("a").click()

    def check(self, word):
        self.goto(word)
        text = self.saol_text()
        if "inga svar" in text:
            return False
        lexems = self._saol_lexems()
        defs = []
        if lexems:
            defs.extend(self._do_lexems(lexems))
        else:
            digs = self._saol_digs()
            lexems_1 = []
            for d in digs:
                try:
                    d.click()
                except ElementNotVisibleException:
                    continue
                try:
                    lexems = self._saol_lexems()
                except NoSuchElementException:
                    time.sleep(0.5)
                    lexems = self._saol_lexems()
                lexems_2 = self._do_lexems(lexems)
                if lexems_1 != lexems_2:
                    defs.extend(lexems_2)
                lexems_1 = lexems_2
                self._saol_dig_back()
        return defs
        
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

def instantiate_browser(headless=True):
    return SAOLReader(headless)

if __name__ == "__main__":
    headless = True
    word = None
    saol = False
    for opt in sys.argv[1:]:
        if opt == "-i":
            headless = False
        elif opt == "-s":
            saol = True
        elif opt[0] != "-":
            word = opt
    
    if word == None:
        print("Löser dina korsordsbekymmer.\n@ är vokal, $ är konsonant, £ är vilken bokstav som helst.")
        word = input("Vilket ord ska lösas?\n")
    else:
        print(f"Löser dina korsordsbekymmer.\n{word}")
    props = prop(word)
    string = f"Följande {len(props)} möjligheter finns:\n"
    for p in props:
        string += p + ", "
    print(string[0:-2]) #remove last comma

    if saol:
        do_check = "Y"
    else:
        do_check = input("Vill du kolla mot SAOL? [Y/n]\n")
    if do_check != "n":
        wd = instantiate_browser(headless=headless)
        saol_props = []
        for p in props:
            expls = wd.check(p)
            if expls != False:
                saol_props.append((p, expls))
        no_saol_props = len(saol_props)
        if no_saol_props == 0:
            print("Inga möjligheter hittades.")
        else:
            saol_prop_string = f"Följande {len(saol_props)} möjligheter hittades:\n"
            for saol_prop in saol_props:
                saol_prop_string += "\n" + saol_prop[0] + ": "
                saol_prop_word_string = ""
                for expl in saol_prop[1]:
                    saol_prop_word_string += expl + "; "
                saol_prop_string += saol_prop_word_string[0:-2]
            print(saol_prop_string) #remove last comma
        wd.close()