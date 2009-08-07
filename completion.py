#
# Functions useful for completing:
#    1) names of files and directories
#    2) names of environment variables
#

import sys, os
from common import parse_line, expand_env_vars, has_exec_extension, strip_extension
from common import contains_special_char, starts_with_special_char

def complete_file(line):
    """
    Complete names of files or directories
    This function tokenizes the line and computes file and directory
    completions starting with the last token.
    
    It returns a pair:
      - the line expanded up to the longest common sequence among the
        completions
      - the list of all possible completions (first dirs, then files)
    """

    tokens = parse_line(line)
    token = tokens[-1].replace('"', '')
    
    (path_to_complete, _, prefix) = token.rpartition('\\')
    if path_to_complete == '' and token != '' and token[0] == '\\':
        path_to_complete = '\\'

    # print '\n\n', path_to_complete, '---', prefix, '\n\n'

    if path_to_complete == '':
        dir_to_complete = os.getcwd()
    elif path_to_complete == '\\':
        dir_to_complete = os.getcwd()[0:3]
    else:
        dir_to_complete = expand_env_vars(path_to_complete) + '\\'

    completions = []
    if os.path.isdir(dir_to_complete):
        try:
            completions = [elem for elem in os.listdir(dir_to_complete) if elem.lower().startswith(prefix.lower())]
        except OSError:
            # Cannot complete, probably access denied
            pass
        

    # Sort directories first, also append '\'; then, files
    completions_dirs = [elem + '\\' for elem in completions if os.path.isdir(dir_to_complete + '\\' + elem)]
    completions_files = [elem for elem in completions if os.path.isfile(dir_to_complete + '\\' + elem)]
    completions = completions_dirs + completions_files

    if (len(tokens) == 1 or tokens[-2] in ['|', '||', '&', '&&']) and path_to_complete == '':
        # We are at the beginning of a command ==> also complete from the path
        completions_path = []
        for elem_in_path in os.environ['PATH'].split(';'):
            dir_to_complete = expand_env_vars(elem_in_path) + '\\'
            try:                
                completions_path += [elem for elem in os.listdir(dir_to_complete) 
                                     if elem.lower().startswith(prefix.lower())
                                     and os.path.isfile(dir_to_complete + '\\' + elem)
                                     and has_exec_extension(elem)
                                     and not elem in completions
                                     and not elem in completions_path]
            except OSError:
                # Cannot complete, probably access denied
                pass

        # Add internal commands
        internal_commands = ['assoc',
                             'call', 'cd', 'cls', 'color', 'copy',
                             'date', 'del', 'dir',
                             'echo', 'endlocal', 'erase', 'exit',
                             'for', 'ftype',
                             'goto',
                             'if',
                             'md', 'mkdir', 'move',
                             'path', 'pause', 'popd', 'prompt', 'pushd',
                             'rem', 'ren', 'rd', 'rmdir',
                             'set', 'setlocal', 'shift', 'start',
                             'time', 'title', 'type',
                             'ver', 'verify', 'vol']
        completions_path += [elem for elem in internal_commands
                             if elem.lower().startswith(prefix.lower())
                             and not elem in completions
                             and not elem in completions_path]


        # Sort in lexical order (case ignored)
        completions_path.sort(key=str.lower)

        # Remove .com, .exe or .bat extension where possible
        completions_path_no_ext = [strip_extension(elem) for elem in completions_path]
        completions_path_nice = []
        for i in range(0, len(completions_path_no_ext)):
            similar = [elem for elem in completions_path_no_ext if elem == completions_path_no_ext[i]]
            similar += [elem for elem in completions if strip_extension(elem) == completions_path_no_ext[i]]
            if len(similar) == 1 and has_exec_extension(completions_path[i]) and len(prefix) < len(completions_path[i]) - 3:
                # No similar executables, don't use extension
                completions_path_nice.append(completions_path_no_ext[i])
            else:
                # Similar executables found, keep extension
                completions_path_nice.append(completions_path[i])
        completions += completions_path_nice

    if completions != []:
        # Find the longest common sequence
        common_string = find_common_prefix(prefix, completions)
            
        if path_to_complete == '':
            completed_file = common_string
        elif path_to_complete == '\\':
            completed_file = '\\' + common_string
        else:
            completed_file = path_to_complete + '\\' + common_string

        if expand_env_vars(completed_file).find(' ') >= 0 or \
               (prefix != '' and [elem for elem in completions if contains_special_char(elem)] != []) or \
               (prefix == '' and [elem for elem in completions if starts_with_special_char(elem)] != []):
            # We add quotes if one of the following holds:
            #   * the (env-expanded) completed string contains whitespace
            #   * there is a prefix and at least one of the valid completions contains whitespace
            #   * there is no prefix and at least one completion _starts_ with whitespace
            start_quote = '"'
        else:
            start_quote = ''

        # Build the result
        result = line[0 : len(line) - len(tokens[-1])] + start_quote + completed_file

        if len(completions) == 1:
            # We can close the quotes if we have completed to a unique filename
            if start_quote == '"':
                end_quote = '"'
            else:
                end_quote = ''
                
            if result[-1] == '\\':
                # Directory -- we want the backslash (if any) AFTER the closing quote
                result = result[ : -1] + end_quote + '\\'
            else:
                # File -- add space if the completion is unique
                result += end_quote
                result += ' '

        if len(completions) == 1:
            return (result, [])
        else:
            return (result, completions)
    else:
        # No expansion was made, return original line
        return (line, [])


def complete_env_var(line):
    """
    Complete names of environment variables
    This function tokenizez the line and computes completions
    based on environment variables starting with the last token
    
    It returns a pair:
      - the line expanded up to the longest common sequence among the
        completions
      - the list of all possible completions
    """

    token_orig = parse_line(line)[-1]
    if token_orig.count('%') % 2 == 0 and token_orig.strip('"').endswith('%'):
        [lead, prefix] = token_orig.strip('"').rstrip('%').rsplit('%', 2)
    else:
        [lead, prefix] = token_orig.strip('"').rsplit('%', 1)

    if token_orig.strip('"').endswith('%') and prefix != '':
        completions = [prefix]
    else:
        completions = [var for var in os.environ if var.lower().startswith(prefix.lower())]

    completions.sort()

    if completions != []:
        # Find longest prefix
        common_string = find_common_prefix(prefix, completions)
        
        quote = ''  # Assume no quoting needed by default, then check for spaces
        for completion in completions:
            if contains_special_char(os.environ[completion]):
                quote = '"'
                break
            
        result = line[0 : len(line) - len(token_orig)] + quote + lead + '%' + common_string
        
        if len(completions) == 1:
            result += '%' + quote
            return (result, [])
        else:
            return (result, completions)
    else:
        # No completion possible, return original line
        return (line, [])



def find_common_prefix(original, completions):
    """
    Search for the longest common prefix in a list of strings
    Returns the longest common prefix
    """
    
    common_len = 0
    common_string = None
    mismatch = False
    perfect = True
    while common_len < len(completions[0]) and not mismatch:
        common_len += 1
        common_string = completions[0][0:common_len]
        for completion in completions[1 : ]:
            if completion[0:common_len].lower() != common_string.lower():
                mismatch = True
            elif completion[0:common_len] != common_string:
                perfect = False
    if mismatch:
        common_string = common_string[:-1]
        common_len -= 1

    # Try to take a good guess wrt letter casing
    if not perfect:
        for i in range(len(original)):
            case_match = [c for c in completions if c.startswith(original[:i + 1])]
            if len(case_match) > 0:
                common_string = case_match[0][:common_len]
            else:
                break

    return common_string

