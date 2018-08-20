from datetime import datetime
import os
#import platform
import sys

from pycmd_public import appearance, behavior, color


def original_like_prompt():
    path = os.getcwd().decode(sys.getfilesystemencoding())
    #import win32api
    #path = win32api.GetShortPathName(path)
    return color.Fore.DEFAULT + path + '>'


quiet_mode = ['/Q', '-Q']
switches = [arg.upper() for arg in sys.argv]
if not any(switch in quiet_mode for switch in switches):
    #print 'Microsoft Windows [Version %s]' % platform
    print 'Microsoft Windows [Version 10.0.15063]'
    print '(c) %s Microsoft Corporation. All rights reserved.' % datetime.now().year

appearance.simple_prompt = original_like_prompt
behavior.quiet_mode = True
