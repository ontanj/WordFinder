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
    print("Löser dina korsordsbekymmer.\n@ är vokal, $ är konsonant, £ är vilken bokstav som helst.")
    word = input("Vilket ord ska lösas?\n")
    props = prop(word)
    string = "Följande möjligheter finns:\n"
    for p in props:
        string += p + ", "
    print(string)