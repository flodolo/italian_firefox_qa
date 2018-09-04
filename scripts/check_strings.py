#!/usr/bin/python3

import argparse
import logging
import os
import re
import sys
from html.parser import HTMLParser
import hunspell
import nltk
import string

logging.basicConfig()

# Import libraries
try:
    from compare_locales import parser
except ImportError as e:
    print('FATAL: make sure that dependencies are installed')
    print(e)
    sys.exit(1)


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


class CheckStrings():

    excluded_folders = (
        'calendar',
        'chat',
        'editor',
        'extensions',
        'mail',
        'other-licenses',
        'suite'
    )

    def __init__(self, script_path, repository_path):
        '''Initialize object'''

        # Set defaults
        self.supported_formats = [
            '.dtd',
            '.ftl',
            '.inc',
            '.ini',
            '.properties',
        ]
        self.file_list = []
        self.strings = {}
        self.script_path = script_path
        self.repository_path = repository_path.rstrip(os.path.sep)

        # Extract strings
        self.extractStrings()

        # Run checks
        self.quotesChecks()
        self.checkSpelling()

    def extractStrings(self):
        '''Extract strings in files'''

        # Create a list of files to analyze
        self.extractFileList()

        for file_path in self.file_list:
            file_extension = os.path.splitext(file_path)[1]
            file_name = self.getRelativePath(file_path)

            # Ignore folders unrelated to Firefox Desktop or Fennec
            if file_name.startswith(self.excluded_folders):
                continue
            if file_name.endswith('region.properties'):
                continue

            file_parser = parser.getParser(file_extension)
            file_parser.readFile(file_path)
            try:
                entities = file_parser.parse()
                for entity in entities:
                    # Ignore Junk
                    if isinstance(entity, parser.Junk):
                        continue

                    string_id = '{}:{}'.format(
                        file_name, entity)
                    if file_extension == '.ftl':
                        if entity.raw_val != '':
                            self.strings[string_id] = entity.raw_val
                        # Store attributes
                        for attribute in entity.attributes:
                            attr_string_id = '{0}:{1}.{2}'.format(
                                file_name, entity, attribute)
                            self.strings[attr_string_id] = attribute.raw_val
                    else:
                        self.strings[string_id] = entity.raw_val
            except Exception as e:
                print('Error parsing file: {}'.format(file_path))
                print(e)

    def extractFileList(self):
        '''Extract the list of supported files'''

        for root, dirs, files in os.walk(
                self.repository_path, followlinks=True):
            for f in files:
                for supported_format in self.supported_formats:
                    if f.endswith(supported_format):
                        self.file_list.append(os.path.join(root, f))
        self.file_list.sort()

    def getRelativePath(self, file_name):
        '''Get the relative path of a filename'''

        relative_path = file_name[len(self.repository_path) + 1:]

        return relative_path

    def strip_tags(self, text):
        html_stripper = MLStripper()
        html_stripper.feed(text)

        return html_stripper.get_data()

    def quotesChecks(self):
        '''Check quotes'''

        # Load exceptions
        exceptions = []
        file_name = os.path.join(
            self.script_path, os.path.pardir, 'exceptions', 'quotes.txt')
        with open(file_name, 'r') as f:
            exceptions = []
            for l in f:
                exceptions.append(l.rstrip())

        straight_quotes = re.compile(r'\'|"')
        for message_id, message in self.strings.items():
            if message_id in exceptions:
                continue
            if message and straight_quotes.findall(message):
                if not straight_quotes.findall(self.strip_tags(message)):
                    # Message is clean after stripping HTML
                    continue
                print('{}: wrong quotes\n{}'.format(message_id, message))

    def checkSpelling(self):
        '''Check for spelling mistakes'''

        # Load exceptions
        exceptions = []
        file_name = os.path.join(
            self.script_path, os.path.pardir, 'exceptions', 'spelling.txt')
        with open(file_name, 'r') as f:
            exceptions = []
            for line in f:
                exceptions.append(line.rstrip())

        # Load hunspell dictionaries
        dictionary_path = os.path.join(
            self.script_path, os.path.pardir, 'dictionaries')
        spellchecker = hunspell.HunSpell(
            os.path.join(dictionary_path, 'it_IT.dic'),
            os.path.join(dictionary_path, 'it_IT.aff'),
        )
        # Add extra dictionary
        # This doesn't seem to work, so doing a silly workaround for now
        # https://github.com/blatinier/pyhunspell/issues/73
        '''
        spellchecker.add_dic(
            os.path.join(dictionary_path, 'additional_words.dic'))
        '''
        with open(os.path.join(dictionary_path, 'additional_words.dic'), 'r') as f:
            for line in f:
                spellchecker.add(line.rstrip())

        punctuation = list(string.punctuation)

        placeables = {
            '.ftl':
                [
                    # Message references, variables, terms
                    re.compile(r'(?<!\{)\{\s*([\$|-]?[A-Za-z0-9._-]+)(?:[\[(]?[A-Za-z0-9_\-, :"]+[\])])*\s*\}'),
                    # DATETIME()
                    re.compile(r'\{\s*DATETIME\(.*\)\s*\}'),
                    # Variants
                    re.compile(r'\{\s*\$[a-zA-Z]+\s*->'),
                ],
            '.properties':
                [
                    re.compile(r'(?<!\{)\{\s*[A-Za-z0-9_-]+\s*\}'),
                ],
            '.dtd':
                [
                    re.compile(r'&([A-Za-z0-9\.]+);'),
                ],
        }

        # Some files should be completely excluded
        excluded_files = [
            'browser/defines.inc',
            'toolkit/toolkit/intl/regionNames.ftl',
            'toolkit/toolkit/intl/languageNames.ftl',
        ]

        for message_id, message in self.strings.items():
            filename, extension = os.path.splitext(message_id.split(':')[0])
            if message_id.split(':')[0] in excluded_files:
                continue
            if message_id in exceptions:
                continue
            if extension == '.ftl' and '.style' in message_id:
                continue
            if not message:
                continue

            # Strip HTML
            cleaned_message = self.strip_tags(message)

            # Replace apostrophes and quotes
            cleaned_message = cleaned_message.replace('’', '\'')
            cleaned_message = cleaned_message.replace('“', ' ')
            cleaned_message = cleaned_message.replace('”', ' ')

            # Remove ellipsis, newlines
            cleaned_message = cleaned_message.replace('…', '')
            cleaned_message = cleaned_message.replace(r'\n', ' ')

            # Replace other characters to reduce errors
            cleaned_message = cleaned_message.replace('/', ' ')
            cleaned_message = cleaned_message.replace('=', ' = ')

            # Remove placeables from FTL and properties strings
            if extension in placeables:
                try:
                    for pattern in placeables[extension]:
                        cleaned_message = pattern.sub(
                            ' ', cleaned_message)
                except Exception as e:
                    print('Error removing placeables')
                    print(message_id)
                    print(e)

            # Tokenize sentence
            tokens = nltk.word_tokenize(cleaned_message)
            errors = []
            for token in tokens:
                if token not in punctuation and not spellchecker.spell(token):
                    errors.append(token)

            if errors:
                print('{}: spelling error'.format(message_id))
                for e in errors:
                    print('Original: {}'.format(message))
                    print('Cleaned: {}'.format(cleaned_message))
                    print('  {}'.format(e))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('repo_path', help='Path to locale files')
    args = parser.parse_args()

    CheckStrings(
        os.path.abspath(os.path.dirname(__file__)),
        args.repo_path)


if __name__ == '__main__':
    main()
