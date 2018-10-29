from selenium import webdriver
import os
import time
from selenium.common.exceptions import NoSuchElementException

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

def check(wd, word):
    wd.get("https://svenska.se/tre/?sok=" + word)
    try:
        text = wd.find_element_by_id("saol-1").find_element_by_class_name("cshow").text
    except NoSuchElementException:
        time.sleep(1)
        text = wd.find_element_by_id("saol-1").find_element_by_class_name("cshow").text
    if "inga svar" in text:
        return False
    else:
        return True


def instantiate_browser(headless=False):
    if headless:
        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.add_argument("headless")
        prefs = {"profile.managed_default_content_settings.images":2}
        chromeOptions.add_experimental_option("prefs",prefs)
    else:
        chromeOptions = None
        import os 
    dir_path = os.path.dirname(os.path.realpath(__file__))
    return webdriver.Chrome(executable_path=dir_path+"/chromedriver", chrome_options=chromeOptions)

if __name__ == "__main__":
    print("Löser dina korsordsbekymmer.\n@ är vokal, $ är konsonant, £ är vilken bokstav som helst.")
    word = input("Vilket ord ska lösas?\n")
    props = prop(word)
    string = f"Följande {len(props)} möjligheter finns:\n"
    for p in props:
        string += p + ", "
    print(string[0:-2]) #remove last comma

    do_check = input("Vill du kolla mot SAOL? [Y/n]\n")
    if do_check != "n":
        wd = instantiate_browser()
        saol_props = []
        for p in props:
            if check(wd, p):
                saol_props.append(p)
        sp_st = f"Följande {len(saol_props)} möjligheter hittades:\n"
        for sp in saol_props:
            sp_st += sp + ", "
        print(sp_st[0:-2]) #remove last comma