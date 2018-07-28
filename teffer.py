#import shlex
import subprocess
import argparse
import os
import difflib
import sys
import json

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
expected = "expected.txt"
actual   = "actual.txt"

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
    help='Directory to find the program/script that the tests execute.')
parser.add_argument('-m', default='test',
    help='''Mode: 
    test: Run the test suite
    update: update all of the expected.txt files with the actual.txt file contents
    clean: Clean up all of the temporary files and actual.txt files''')

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

def write_to_html(results, out_file_name, include_diff):
    text_file = open(out_file_name, "w")
    text_file.write(html_begin)
    text_file.write('<h1>teffer diff results</h1>')
    text_file.write('<hr>')
    
    for r in results:

        text_file.write('<h2>' + r['name'] + '</h2>')
        if include_diff:
            diff = difflib.HtmlDiff().make_table(
                r['expected'], r['actual'],
                expected, actual)
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
        text_file.write('  { "name" : ' + json.dumps(r['name']) + ',\n')
        if include_diff:
            #diff = difflib.Differ().compare(r['expected'], r['actual'])
            diff = difflib.ndiff(r['expected'], r['actual'])
            diff_text = '\n'.join(diff)
            print('------- expected ------- ')
            print(r['expected'])
            print('------- actual ------- ')
            print(r['actual'])
            print('----------------------')
            print('----------------------')
            print(diff_text)
            print('----------------------')
            print('----------------------')
            print(json.dumps(diff_text))
            text_file.write('    "output" : ' + json.dumps(diff_text) + ',\n')
        text_file.write('    "score" : "' + str(r['score']) + '",\n')
        text_file.write('    "max_score" : "' + str(r['max_score']) + '" }')
        if i < len(results):
            text_file.write(',')
        text_file.write('\n')
    
    text_file.write('] }\n')
    text_file.close()

args = parser.parse_args()
assert(args.m == 'test' or args.m == 'update' or args.m == 'clean')
assert(args.f == 'html' or args.f == 'gradescope')

cwd = os.getcwd()
subdirs = [name for name in os.listdir(args.t)
    if os.path.isdir(os.path.join(args.t, name))]

for sdir in subdirs:
    os.chdir(cwd)
    full_path = os.path.join(args.t, sdir)
    ex_path = os.path.join(full_path, expected)
    ac_path = os.path.join(full_path, actual)

    # test mode - run all of the test cases
    if args.m == 'test':
        run_file = open(os.path.join(full_path, 'run.sh'), 'rb')
        script = run_file.read().decode("utf-8") 
        script = script.replace('BASE_DIR', str(args.s))
        script = script.replace('TEST_DIR', str(full_path))
        
        print('\n\n------- script -------')
        print(script + '\n\n')
        
        # Create new temp file with script
        temp = os.path.join(cwd, 'teffer-temp.sh')
        tf = open(temp, 'w')
        tf.write('#!/bin/bash\n')
        tf.write(script)
        tf.close()

        # Run the script
        result = subprocess.run(['bash', temp], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        actual_output_file = open(ac_path, "w")
        decoded = result.stdout.decode("utf-8") 
        actual_output_file.write(decoded)
        actual_output_file.close()
        
        print('\n\n------- decoded -------')
        print(decoded + '\n\n')
    
        print('\n\n------- ac_path -------')
        print(ac_path + '\n\n')

        expected_lines = []
        for line in open(ex_path, 'r'):
            expected_lines.append(line.rstrip('\n'))
        actual_lines = []
        for line in open(ac_path, 'r'):
            actual_lines.append(line.rstrip('\n'))
        
        result = {}
        result['name']      = sdir
        result['pass']      = True
        result['score']     = 1
        result['max_score'] = 1
        result['expected']  = expected_lines
        result['actual']    = actual_lines
        all_test_results.append(result) 
        
        os.remove('./teffer-temp.sh')
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

