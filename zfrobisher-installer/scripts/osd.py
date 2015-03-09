#!/usr/bin/env python

#
# This is and On Screen Display that helps to show build stages collored
#

import sys

#
# Constants and definitions
#
COLORTABLE = {
    'default': '\033[1;m',
    'red': '\033[1;31m',
    'green': '\033[1;32m',
    'blue': '\033[1;34m',
    'yellow': '\033[1;33m',
}

TERMWIDTH=80

def _print_line(char = '*', color='default'):
    print COLORTABLE[color] + char * TERMWIDTH + COLORTABLE['default']
# _print_line()

def _print_bordered_line(content = '', border = '*', color='default'):
    free_spc = TERMWIDTH - 2 * len(border) - len(content)
    before_spc = free_spc / 2
    after_spc = free_spc - before_spc
    print COLORTABLE[color] + border + ' ' * before_spc + content + ' ' * after_spc + border + COLORTABLE['default']
# _print_bordered_line ()

def print_title(title):
    _print_line(color='red')
    _print_bordered_line(color='red')
    lines = []
    words = title.split(' ')
    line = ''
    for word in words:
        if len(line) <= TERMWIDTH / 2:
            if len(line) > 0:
                line += ' '
            line += word
        else:
            lines.append(line)
            line = word
    lines.append(line)

    for line in lines:
        _print_bordered_line(content = line, color = 'red')

    _print_bordered_line(color='red')
    _print_line(color='red')
# print_title()

def print_subtitle(title):
    _print_line(char = '=', color='blue')
    freespc = (TERMWIDTH - len(title)) / 2
    print COLORTABLE['blue'] + ' ' * freespc + title + COLORTABLE['default']
    _print_line(char = '=', color='blue')
# print_subtitle()

def print_info(info):
    print COLORTABLE['yellow'] + info + COLORTABLE['default']
# print_info()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "Usage: osd.py COMMAND string"
        sys.exit(-1)
    
    command = sys.argv[1].upper()
    string = ' '.join(sys.argv[2:])

    if command == 'TITLE':
        print_title(string)
    elif command == 'SUBTITLE':
        print_subtitle(string)
    elif command == 'INFO':
        print_info(string)
    else:
        print "Valid commands: TITLE SUBTITLE INFO"
        sys.exit(-1)
     

