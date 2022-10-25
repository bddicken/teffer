#import shlex
import subprocess
import argparse
import os
import difflib
import sys
import json
sys.setrecursionlimit(2000)

html_begin ='''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>teffer</title>
  <style type="text/css">
    table.diff {font-family:Courier; border:medium;}
    .diff_header {background-color:#e0e0e0}
    td.diff_header {text-align:right}
    .diff_next {background-color:#c0c0c0}
    .diff_add {background-color:#aaffaa}
    .diff_chg {background-color:#ffff77}
    .diff_sub {background-color:#ffaaaa}
  </style>
</head>
<body>
'''
html_end = '''
<table class="diff" summary="Legends">
  <tr> <th colspan="2"> Legends </th> </tr>
  <tr> <td> 
  <table border="" summary="Colors">
    <tr><th> Colors </th> </tr>
    <tr><td class="diff_add">&nbsp;Added&nbsp;</td></tr>
    <tr><td class="diff_chg">Changed</td> </tr>
    <tr><td class="diff_sub">Deleted</td> </tr>
  </table> </td> <td>
  <table border="" summary="Links">
    <tr><th colspan="2"> Links </th> </tr>
    <tr><td>(f)irst change</td> </tr>
    <tr><td>(n)ext change</td> </tr>
    <tr><td>(t)op</td> </tr>
  </table> </td> </tr>
</table>
</body>
</html>
'''
CONFIG   = "config.txt"
EXPECTED = "expected.txt"
ACTUAL   = "actual.txt"
OPTIONS  = "options.txt"

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-f', default='html',
    help='''The formatting of the output. 
    This may be one of two options: html or gradescope. 
    The html option will send the results to an html file, that can be viewed in a browser.
    the gradescope option will send the output to a gradescope-compatabale json file.''')
parser.add_argument('-i', default=True, action='store_false',
    help='''If specified, will not include diff output in results.
         The user will only be told wether or not the test passed''')
parser.add_argument('-o', default='./diff.html',
    help='HTML file to put the diff output into.')
parser.add_argument('-t', default='./tests',
    help='Directory containing test cases (directories) to run.')
parser.add_argument('-s', required=True,
    help='directory to find the program/script that the tests execute.')
parser.add_argument('-m', default='test',
    help='''Mode: 
    test: Run the test suite
    update: update all of the expected.txt files with the actual.txt file contents
    clean: Clean up all of the temporary files and actual.txt files''')
parser.add_argument('-e', default='5',
    help='The timeout length, in seconds. This is a per-test-case timeout.')
parser.add_argument('-c', default=False, action='store_true',
    help='Enable if the program beign tested should be allowed to have a non-zero exit code.')

'''
Array of dictionaries
Each dictionary represents the results of one test case
Each dictionary will have three elements
    * name      (string)
    * pass      (boolean)
    * score     (integer)
    * max_score (integer, <= score)
    * expected  (string)
    * actual    (string)
'''
all_test_results = []
    
def longest_str_in_list(l):
    widest = 0
    for i in range(len(l)):
         if len(l) > i and len(l[i]) > widest:
             widest = len(l[i])
    return widest

def are_lines_same(a, b, ignore_tw=True, ignore_lw=False):
    if ignore_tw:
        a = a.rstrip(' \n\t')
        b = b.rstrip(' \n\t')
    if ignore_lw:
        a = a.lstrip(' \n\t')
        b = b.lstrip(' \n\t')
    return a == b

def are_strings_same(a, b, ignore_tw=True, ignore_lw=False):
    '''
    Return True if strings a and b are the same (other than perhaps ignoring some whitespace).
    Return False otherwise.
    If ignore_tw is set to True, ignore the trailing whitespace when comparing a and b.
    If ignore_lw is set to True, ignore the leading whitespace when comparing a and b.
    '''
    al = a.split('\n')
    bl = b.split('\n')

    if len(al) != len(bl):
        return False
    
    for i in range(len(al)):
        same = are_lines_same(al[i], bl[i])
        if not same:
            return False

    return True

def put_strings_side_by_side(a, b):
    result = ''
    al = a.split('\n')
    bl = b.split('\n')
    
    widest = max(longest_str_in_list(al), longest_str_in_list(bl))
    length = max(len(al), len(bl))
 
    for i in range(length):
         if len(al) > i and len(bl) > i:
             if are_strings_same(al[i], bl[i]):
                 result += ' |'
             else:
                 result += '>|'
         else:
             result += '>|'

         if len(al) > i:
             result += al[i].ljust(widest)
         else:
             result += ''.ljust(widest)

         result += '|'
         
         if len(bl) > i:
             result += bl[i].ljust(widest)
         else:
             result += ''.ljust(widest)
         result += '\n'
    
    return result


def write_to_html(results, out_file_name, include_diff):
    text_file = open(out_file_name, "w")
    text_file.write(html_begin)
    text_file.write('<h1>teffer diff results</h1>')
    text_file.write('<hr>')
    
    for r in results:

        text_file.write('<h2>' + r['name'] + '</h2>')
        if include_diff:
            diff = difflib.HtmlDiff().make_table(
                r['extra_data']['expected'], r['extra_data']['actual'],
                EXPECTED, ACTUAL)
            text_file.write(diff)
        text_file.write('<br>')
        text_file.write('<hr>')

    text_file.write('<br>')
    text_file.write(html_end)
    text_file.close()

def write_to_gradescope_json(results, out_file_name, include_diff):
    text_file = open(out_file_name, "w")
    text_file.write('{ "tests" : [\n')
 
    i = 0
    for r in results:
        i += 1
        text_file.write('  { "name" : ' + json.dumps(r['name']) + '\n')
        if include_diff:
            sbs  = 'Your output on left, expected output on right\n'
            sbs += 'Lines beginning with a \'>\' indicates a line that differs from the expected output\n\n'
            sbs += put_strings_side_by_side('\n'.join(r['extra_data']['actual']), '\n'.join(r['extra_data']['expected']))
            #diff = difflib.ndiff(r['expected'], r['actual'])
            #diff_text = '\n'.join(diff)
            #text_file.write('    "output" : ' + json.dumps(diff_text) + ',\n')
            text_file.write(',"output" : ' + json.dumps(sbs) + '\n')
        for k, v in r.items():
            if k != 'extra_data':
                text_file.write(',"' + k + '" : "' + str(v) + '"\n')
        text_file.write('}')
        if i < len(results):
            text_file.write(',')
        text_file.write('\n')
    
    text_file.write('] }\n')
    text_file.close()

def load_config(config_path):
    '''
    Load up any specific config info for a particular test case.
    Returns a dictionary mapping config setting name (key) to 
    the value for that config setting.
    '''
    config = {}
    config_file = None
    try:
        config_file = open(config_path, 'r')
    except:
        return config
    for line in config_file:
        tokens = line.split(':')
        config[tokens[0]] = tokens[1].strip('\n')
    return config

def main():
    args = parser.parse_args()
    assert(args.m == 'test' or args.m == 'update' or args.m == 'clean')
    assert(args.f == 'html' or args.f == 'gradescope')

    cwd = os.getcwd()
    subdirs = [name for name in sorted(os.listdir(args.t))
        if os.path.isdir(os.path.join(args.t, name))]

    for sdir in subdirs:
        print("TESTING: " + str(sdir))
        os.chdir(cwd)
        full_path = os.path.join(args.t, sdir)
        ex_path = os.path.join(full_path, EXPECTED)
        ac_path = os.path.join(full_path, ACTUAL)
        config_path = os.path.join(full_path, CONFIG)
        
        op_path = ''
        if os.path.exists(full_path + '/' + OPTIONS):
            op_path = os.path.join(full_path, OPTIONS)

        # test mode - run all of the test cases
        if args.m == 'test':
            run_file = open(os.path.join(full_path, 'run.sh'), 'rb')
            script = run_file.read().decode("utf-8") 
            script = script.replace('BASE_DIR', str(os.path.abspath(str(args.s))))
            script = script.replace('TEST_DIR', str(os.path.abspath(str(full_path))))
            
            # Create new temp file with script
            temp = os.path.join(cwd, 'teffer-temp.sh')
            tf = open(temp, 'w')
            tf.write('#!/bin/bash\n')
            tf.write(script)
            tf.close()
            
            decoded = 'DECODED OUPUT PLACEHOLDER'

            # The gradescope problem is somewhere here ish!
            # Either command is not running correctly, or output not being grabbed correctly.
            # Run the script
            subproc_exit_code = 0
            try:
                #result = subprocess.run(['gtimeout', args.e, '/bin/bash', temp], \
                result = subprocess.run(['timeout', args.e, '/bin/bash', temp], \
                                      stdout=subprocess.PIPE, \
                                      stderr=subprocess.PIPE, \
                                      check= not args.c)
                decoded = result.stdout.decode("utf-8")
                decoded += result.stderr.decode("utf-8")
            except subprocess.CalledProcessError as err:
                decoded = 'A problem occurred when trying to decode the output of the program.\n'
                decoded += 'You should debug and test your program more thoroughly.\n'
                decoded += 'Have you considered the various edge cases?\n'
                # Print to stdout for staffs' debugging
                print()
                print('A problem occurred:', err)
                print('Don\'t worry, this should be the student\'s mistake.')
                result = err  # Gathering the stdout and stderr
                subproc_exit_code = err.returncode
            except:
                decoded = 'A problem occurred when trying to decode the output of the program.\n'
                decoded += 'You should debug and test your program more thoroughly.\n'
                decoded += 'Have you considered the various edge cases?\n'
           
            # If the command times out, then exit with status 124.
            # Otherwise, exit with the status of COMMAND. 
            if subproc_exit_code != 0:
                if subproc_exit_code == 124:
                    decoded = 'A problem occurred: Time Limit Exceeded!\n'
                    decoded += 'Your code took too long to run (perhaps an infinite loop?)\n'
                    decoded += 'Please try to address the issue, and submit again.'
                elif args.c != True:
                    decoded_err = result.stderr.decode("utf-8")
                    if decoded_err.strip(' \n\t') == '':
                        decoded = 'A problem occurred!\n'
                        decoded += 'This issue could be one of a number of problems, including:\n'
                        decoded += '  * You named your file incorrectly\n'
                        decoded += '  * Your program produced an unknown error\n'
                        decoded += 'Please try to address the issue, and submit again.'
                    else:
                        decoded = 'A problem occurred: Runtime Error\n'
                        decoded += 'Your program produced an error when it\'s running.\n'
                        decoded += 'You will be able to get more details when debugging on your device.\n'
                        decoded += 'Please try to address the issue, and submit again.\n'
                        if "No such file or directory" in decoded_err or \
                           "ModuleNotFoundError" in decoded_err:
                            decoded += '\nYou may also need to check if you named your files correctly.\n'
                            decoded += 'It should be exactly matched to the filename in the spec.'
                        print('\nRuntime Error Details:\n', decoded_err)
                        

            actual_output_file = open(ac_path, "w")
            actual_output_file.write(decoded)

            actual_output_file.close()
            
            expected_lines = []
            for line in open(ex_path, 'r'):
                expected_lines.append(line.rstrip('\n'))
            actual_lines = []
            for line in open(ac_path, 'r'):
                actual_lines.append(line.rstrip('\n'))
           
            config = load_config(config_path)

            a = '\n'.join(actual_lines)
            e = '\n'.join(expected_lines)
            # Ignore trailing spaces, newlines, and tabs
            # Should this be an option?
            a = a.rstrip(' \n\t')
            e = e.rstrip(' \n\t')
            same = are_strings_same(a, e)
            result = {}
            result['name']      = sdir
            result['pass']      = same
            result['score']     = 1 if same else 0
            result['max_score'] = 1
            for config_name, value in config.items():
                result[config_name] = value
            result['extra_data'] = {}
            result['extra_data']['expected']  = expected_lines
            result['extra_data']['actual']    = actual_lines
            # handle options
            if op_path != '':
                for line in open(op_path, 'r'):
                    sp = line.strip('\n').split('=')
                    result[sp[0]] = sp[1]
            all_test_results.append(result) 
            
            os.remove(temp)
        # update mode - copy contents of expected.txt into actual.txt
        elif args.m == 'update':
            with open(ac_path) as fa:
                lines = fa.readlines()
                lines = [l for l in lines if True]
                with open(ex_path, 'w') as fe:
                    fe.writelines(lines)
        # clean mode - remove all actual.txt files
        elif args.m == 'clean':
            os.remove(ac_path)
        else:
            print('Invalid mode')

    if args.f == 'html':
        write_to_html(all_test_results, args.o, args.i)
    elif args.f == 'gradescope':
        write_to_gradescope_json(all_test_results, args.o, args.i)

main()

