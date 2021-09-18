import pickle as pkl
import re
import pyperclip
import pkg_resources
from symspellpy.symspellpy import SymSpell, Verbosity

def dedup_spaces(text):
    """
    Deduplicate spaces
    i.e., "the  lazy fox  jumped" -> "the lazy fox jumped"
    """
    return re.sub(r'[^\S\n]+', ' ', text)

def remove_spaces_around_linebreak(text):
    """
    Remove spaces "around" line breaks
    "they went to the \n store" -> "they went to the\nstore"
    """
    # dedup spaces across line breaks as well
    # [^\S\n] = non-newline spaces
    return re.sub(r'[^\S\n]*\n+[^\S\n]*', '\n', text)

def remove_punctuation(line):
    """
    Remove all non whitespace/alphanumeric
    characters from the line.
    """
    allowed = [c for c in line if c.isalnum() or c.isspace()]
    return "".join(allowed)

def lastword(line):
    """
    Extract last word from line
    """
    clean_line = remove_punctuation(line)
    lastword = re.search(r'\s*(\w+)\s*$', clean_line)
    if lastword:
        return lastword.group(1)
    return ''

def firstword(line):
    """
    Extract first word from line
    """
    clean_line = remove_punctuation(line)
    firstword = re.search(r'^\s*(\w+)', clean_line)
    if firstword:
        return firstword.group(1)
    return ''

def second_word_split(line):
    """
    Return everything before the second word and the rest of the string.
    "I'm happy" -> ("I'm "), "happy"
    """
    matches = list(re.finditer(r'[^\s]+', line))
    if len(matches) < 2:
        return line, ''
    second_word_index = matches[1].start()
    return line[:second_word_index], line[second_word_index:]

def form_word(tok1, tok2, wordset):
    if (tok1 + tok2).lower() in wordset:
        return True
    return False

def remove_line_break(text, wordset):
    """
    Remove line break
    i.e., "the lazy\nfox jumped" -> "the lazy fox jumped"
    """
    text = remove_spaces_around_linebreak(text)
    lines = text.split('\n')
    new_text = ''
    i = 0

    while i < len(lines) - 1:
        if not lines[i]:
            # if this is an empty line, just keep the newline and go
            new_text += '\n'
            i += 1
            continue

        to_increment = 1 # by default, increment to the next line after iteration
        # decide whether to merge line i, i+1
        sub_char = ' ' # by default, replace the newlines with a space
        lastchar = lines[i][-1]
        if re.match('[—-]', lastchar):
            # check if last character is a dash
            # extract last token of this line
            # and first token of next line,
            # see if they combine to make a word
            last_tok = lastword(lines[i][:-1])
            first_tok = firstword(lines[i+1])
            if form_word(last_tok, first_tok, wordset):
                # merge the lines
                first_line = lines[i][:-(len(last_tok) + 1)]
                to_append, rest_of_line = second_word_split(lines[i+1])
                lines[i] = first_line + last_tok + to_append
                lines[i+1] = rest_of_line
                sub_char = '' # no character substitution needed

        elif re.match('[.?!"”’\']', lastchar):
            # keep the line break if the length of this line
            # is much shorter than the next (rough heuristic for
            # the end of a praagraph)
            if i > 0 and len(lines[i]) <= 0.7 * len(lines[i-1]):
                sub_char = '\n'

        # check next line
        new_text += lines[i] + sub_char
        i += to_increment

    # remember to add the last line!
    new_text += lines[-1]

    return new_text

def dehyphenate(text, wordset):
    """
    Remove hyphenated words that shouldn't be hyphenated
    i.e., "she was a doc-tor" -> "she was a doctor"
    """
    corrected_text = ''
    last_match_index = 0
    for match in re.finditer(r'(\w+[—-]\w+)', text):
        # add everything in between the words
        corrected_text += text[last_match_index:match.start()]
        last_match_index = match.end()
        token = text[match.start():match.end()]
        loc = re.search(r'[—-]', token).start()
        # remove hyphen
        first_half, end_half = token[:loc], token[loc+1:]
        if form_word(first_half, end_half, wordset):
            corrected_text += first_half + end_half
        else:
            corrected_text += token
    # don't forget rest of the text
    corrected_text += text[last_match_index:]
    return corrected_text


def clean(text, wordset):
    """
    Clean text copied and pasted from PDFs
    """
    # step 0: remove trailing whitespace
    text = text.strip()
    # step 1: clean spaces
    clean_text = dedup_spaces(text)

    # step 2: dedup line breaks
    clean_text = remove_line_break(clean_text, wordset)

    # step 3: combine remaining hyphenated terms that should be one word
    clean_text = dehyphenate(clean_text, wordset)

    return clean_text

def refine_correction(old_word, corrected_word):
    """
    Horribly specialized method that keeps the original case
    pattern of (1st letter capitalized, rest of word uncapitalized)
    """
    if len(old_word) < 1:
        return corrected_word
    if len(corrected_word) < len(old_word):
        return old_word
    if re.match(r'[A-Z]', old_word) and old_word[1:].lower() == old_word[1:]:
        return corrected_word[0].upper() + corrected_word[1:].lower()
    return corrected_word

def correct_spelling(text, sym_spell):
    corrected_text = ''
    last_match_index = 0
    for match in re.finditer(r'([^\s]+)', text):
        # add everything in between the words
        corrected_text += text[last_match_index:match.start()]
        last_match_index = match.end()

        # correct word
        token = text[match.start():match.end()]
        term = re.search(r'(\w+)', token) # extract just the term (e.g., "cat" in "cat's")
        if not term:
            corrected_text += token
            continue

        input_word = token[term.start():term.end()]
        suggestions = sym_spell.lookup(input_word, Verbosity.CLOSEST, max_edit_distance=1, transfer_casing=True)
        if len(suggestions) == 0:
            # if no possible misspellings, then we assume that the word actually needs to be segmented
            corrected_term = sym_spell.word_segmentation(input_word).corrected_string
            corrected_text += corrected_term
            continue

        corrected_term = refine_correction(input_word, suggestions[0].term)
        corrected_text += token[:term.start()] + corrected_term + token[term.end():]

        # update last match index
        last_match_index = match.end()

    corrected_text += text[last_match_index:]
    return corrected_text

if __name__ == "__main__":
    # extract text from clipboard and replace with cleaned text
    raw_text = pyperclip.paste()
    wordset = pkl.load(open("eng_words.pkl", "rb"))
    clean_text = clean(raw_text, wordset)
    # correct spelling
    sym_spell = SymSpell(max_dictionary_edit_distance=1, prefix_length=7)
    dictionary_path = "./frequency_dictionary_en_82_765.txt"
    sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)
    clean_text = correct_spelling(clean_text, sym_spell)

    pyperclip.copy(clean_text)
    print("Cleaned text:")
    print(pyperclip.paste())
