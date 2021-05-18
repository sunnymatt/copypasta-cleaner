import pytest
import pickle as pkl
from clean import *
import pkg_resources
from symspellpy.symspellpy import SymSpell

def test_dedup_spaces():
    line = "Hello my Name  is  ABC."
    clean_line = "Hello my Name is ABC."
    assert dedup_spaces(line) == clean_line

    normal_line = "This line has no issues with it whatsoever."
    assert dedup_spaces(normal_line) == normal_line


def test_remove_spaces_around_linebreak():
    line = "this is a    \n\n test."
    clean_line = "this is a\ntest."
    assert remove_spaces_around_linebreak(line) == clean_line
    
    normal_line = "This line has no issues with it whatsoever."
    assert remove_spaces_around_linebreak(normal_line) == normal_line


def test_lastword():
    line = "The last word is grumble"
    assert lastword(line) == "grumble"
    line += "    "
    assert lastword(line) == "grumble"


def test_firstword():
    line = "First word is first."
    assert firstword(line) == "First"
    line = "   " + line
    assert firstword(line) == "First"

def test_forms_word():
    wordset = pkl.load(open('eng_words.pkl', 'rb'))
    assert form_word('hi', 'larious', wordset)
    assert not form_word('jumbo', 'shrimp', wordset)

def test_second_word_split():
    line = "First second"
    assert second_word_split(line) == ("First ", "second")
    
    word = "First"
    assert second_word_split(word) == ("First", "")

def test_remove_line_break():
    text1 = """Two households, both alike in dignity,
    in fair Verona, where we lay our scene,
    from ancient grudge break to new mutiny,
    where civil blood makes civil hands unclean."""
    clean_text = "Two households, both alike in dignity, in fair Verona, where we lay our scene, from ancient grudge break to new mutiny, where civil blood makes civil hands unclean."
    wordset = pkl.load(open('eng_words.pkl', 'rb'))

    assert remove_line_break(text1, wordset) == clean_text
    
    # words across line
    text2 = """Two households, both alike in digni-
    ty, in fair Verona, where we lay our scene,
    from ancient grudge break to new mutiny,
    where civil blood makes civil hands unclean."""
    assert remove_line_break(text2, wordset) == clean_text
    
    # paragraph ends on line, maintain line break
    text3 = """Two households, both alike in digni-
    ty, in fair Verona, where we lay our scene,
    from ancient grudge break.
    
    To new mutiny, where civil blood makes civil
    hands unclean."""

    clean_text = """Two households, both alike in dignity, in fair Verona, where we lay our scene, from ancient grudge break.\n\nTo new mutiny, where civil blood makes civil hands unclean."""
    assert remove_line_break(text3, wordset) == clean_text 

def test_correct_spelling():
    sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
    dictionary_path = "./frequency_dictionary_en_82_765.txt"
    # term_index is the column of the term and count_index is the
    # column of the term frequency
    sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)

    string = "The man's face was orrific"
    assert correct_spelling(string, sym_spell) == "The man's face was horrific"
