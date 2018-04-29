# coding=utf-8
import codecs
import click
import collections
import re

from cdli_mpa_tool.morph_dict import *


class CONLChecker:
    def __init__(self, pathname, verbose):
        self.inputFileName = pathname
        self.verbose = verbose
        self.iscorrect = True
        self.__reset__()

    def __reset__(self):
        self.surfaceMode = ''
        self.inEnvelope = ''
        self.column = ''
        self.IDlist = []

    def check(self):
        if self.verbose:
            click.echo('\nInfo: Checking file {0}.'.format(self.inputFileName))
        with codecs.open(self.inputFileName, 'r', 'utf-8') as openedFile:
            total_lines = 0
            for (i, line) in enumerate(openedFile):
                self.__parse(i, line.strip())
                total_lines += 1
            if total_lines < 2:
                click.echo(
                    '\nError: The first 2 lines of the file {0} are not present.'.format(
                        self.inputFileName))
                self.iscorrect = False
            if len(self.IDlist) != len(set(self.IDlist)):
                click.echo(
                    '\nError: File {0} : IDs generated are not unique'.format(
                        self.inputFileName))
                duplicates = [item for item, count in
                              collections.Counter(self.IDlist).items() if
                              count > 1]
                click.echo('\n Duplicate IDs : {0}.'.format(duplicates))
                self.iscorrect = False
            if self.iscorrect:
                click.echo('\nInfo: The file {0} has correct format.'.format(
                    self.inputFileName))

    def __check_segm_xpostag(self, segm, xpostag, linenumber):
        count_dash = segm.count('-')
        count_dot = xpostag.count('.')
        if count_dot != count_dash:
            click.echo(
                '\nError: The xpostag dot count {0} in line number {1} in file {2} does not match with segm dash count {3}.'
                    .format(count_dot, linenumber, self.inputFileName, count_dash))
            self.iscorrect = False
        xpostag_pattern = r"^(([A-Z0-9]+)(\-([A-Z0-9]+))*)(\.([A-Z0-9]+)(\-([A-Z0-9]+))*)+|[A-Z]+$"
        # check xpostag
        if not re.compile(xpostag_pattern).match(xpostag):
            click.echo(
                '\nError: The xpostag {0} in line number {1} in file {2} does not follow the format "{3}".'
                    .format(xpostag, linenumber, self.inputFileName,
                            xpostag_pattern))
            self.iscorrect = False
        xpostag_splitted = xpostag.split(".")
        xpostag_part_len = len(xpostag_splitted)
        postag_pos = -1
        for i in range(xpostag_part_len):
            if xpostag_splitted[i] in ALL_POSTAGS:
                postag_pos = i
                break
        if postag_pos == -1:
            click.echo(
                '\nError: The xpostag {0} in line number {1} in file {2} does not have a base postag out of "{3}".'
                    .format(xpostag, linenumber, self.inputFileName,
                            ALL_POSTAGS))
            self.iscorrect = False
        elif postag_pos != 0 and (
                xpostag_splitted[postag_pos] not in SPECIAL_POSTAGS):
            click.echo(
                '\nError: The xpostag {0} in line number {1} in file {2} has a prefix without {3} not being verb postag.'
                    .format(xpostag, linenumber, self.inputFileName,
                            xpostag_splitted[postag_pos]))
            self.iscorrect = False
        else:
            isVerb = False
            if xpostag_splitted[postag_pos] in SPECIAL_POSTAGS:
                isVerb = True
            prefix_list = xpostag_splitted[:postag_pos]
            suffix_list = xpostag_splitted[(postag_pos + 1):]
            if isVerb:
                for p in prefix_list:
                    if p not in VERB_PREFIX:
                        click.echo(
                            '\nError: The xpostag {0} in line number {1} in file {2} has a prefix not in verb postag prefix list {3}.'
                                .format(xpostag, linenumber,
                                        self.inputFileName,
                                        VERB_PREFIX))
                        self.iscorrect = False
                for s in suffix_list:
                    if s not in VERB_SUFFIX:
                        click.echo(
                            '\nError: The xpostag {0} in line number {1} in file {2} has a suffix not in verb postag suffix list {3}.'
                                .format(xpostag, linenumber,
                                        self.inputFileName,
                                        VERB_SUFFIX))
                        self.iscorrect = False
            else:
                for s in suffix_list:
                    if s not in NOUN_MORPHS:
                        click.echo(
                            '\nError: The xpostag {0} in line number {1} in file {2} has a suffix not in noun postag suffix list {3}.'
                                .format(xpostag, linenumber,
                                        self.inputFileName,
                                        NOUN_MORPHS))
                        self.iscorrect = False
        # check segm
        segm_pattern = r"^(([a-z0-9]+)((\-[a-z0-9]+)|(\[\-[a-z0-9]+\]))*\-)?[A-Za-z0-9\(\)]+\[[a-z0-9]*\]((\-[a-z0-9]+)|(\[\-[a-z0-9]+\])|(\[\-ø\]))*$"
        # check xpostag
        if not re.compile(segm_pattern).match(segm):
            click.echo(
                '\nError: The segm {0} in line number {1} in file {2} does not follow the format "{3}".'
                    .format(segm, linenumber, self.inputFileName,
                            segm_pattern))
            self.iscorrect = False

    def check_line(self, linenumber, line):
        line_splitted = line.split('\t')
        if len(line_splitted) < 4:
            click.echo(
                "\nError: No field should be empty in file {0} linenumber {1} (An underscore should be added in fields where we can't add something)."
                    .format(self.inputFileName, linenumber))
            self.iscorrect = False
        else:
            segm = line_splitted[2]
            xpostag = line_splitted[3]
            self.__check_segm_xpostag(segm, xpostag, linenumber)
        if len(line_splitted) > 0:
            id_form = line_splitted[0]
            id_pattern = r"^e?(o|r|t|b|l|ri|(s?[a-z]?[0-9]?))\.((col|b)[0-9]'?\.)?[0-9]+'?\.[0-9]+$"
            if not re.compile(id_pattern).match(id_form):
                click.echo(
                    '\nError: The id {0} in line number {1} in file {2} does not follow the Conll format "{3}".'
                        .format(id_form, linenumber, self.inputFileName,
                                id_pattern))
                self.iscorrect = False
            self.IDlist.append(id_form)

    def __parse(self, linenumber, line):
        p_pattern = r"^#new_text=[a-zA-Z0-9]+\s*$"
        heading_pattern = r"#\s+ID\s+FORM\s+SEGM\s+XPOSTAG\s+HEAD\s+DEPREL\s+MISC\s*"
        if linenumber == 0 and not re.compile(p_pattern).match(line):
            click.echo(
                '\nError: The line number {0} in file {1} does not follow the Conll format "{2}".'
                    .format(linenumber, self.inputFileName, p_pattern))
            self.iscorrect = False
        elif linenumber == 1 and not re.compile(heading_pattern).match(line):
            click.echo(
                '\nError: The line number {0} in file {1} does not follow the Conll format "{2}".'
                    .format(linenumber, self.inputFileName, heading_pattern))
            self.iscorrect = False
        elif linenumber > 1:
            self.check_line(linenumber, line)
        else:
            pass
