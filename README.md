# copypasta-cleaner

I copy and paste text from PDFs a lot, and this utility helps do some basic cleaning of the copied text to make it more palatable! Just copy the text section from the PDF, run `python clean.py`, and the new clean text will be in your clipboard and printed out to the terminal.

## Installation
Clone the repo and then run `pip install -r requirements.txt`
*Recommended workflow*: add an alias in `.bashrc` that changes the directory to this repo, (optionally activates a conda environment), and then runs `python clean.py`. Currently I can open a terminal, run the alias, and get the cleaned text in about 5-6 seconds.

## Todos
- Have it run in the background so that you don't have to wait for the dictionary to load every time
- Call from command line (improve workflow)
- Throw onto a website
- Just use one dictionary (currently it uses two different wordsets)

## Some acknowledgments
I use the [English words repo](https://github.com/dwyl/english-words) for one dictionary and [pyspellchecker](https://github.com/barrust/pyspellchecker) for another.
