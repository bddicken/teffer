import shlex
import subprocess
import argparse
import os
import difflib
import sys

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

args = parser.parse_args()
assert(args.m == 'test' or args.m == 'update' or args.m == 'clean')

cwd = os.getcwd()
subdirs = [name for name in os.listdir(args.t)
    if os.path.isdir(os.path.join(args.t, name))]

text_file = open(args.o, "w")
text_file.write(html_begin)
text_file.write('<h1>teffer diff results</h1>')
text_file.write('<hr>')

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
        
        # Create new temp file with script
        tf = open('teffer-temp.sh', 'w')
        tf.write(script)
        tf.close()

        # Run the script
        result = subprocess.run(['bash', './teffer-temp.sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        af = open(os.path.join(full_path, "actual.txt"), "w")
        decoded = result.stdout.decode("utf-8") 
        af.write(decoded)
        af.close()
        expected_lines = open(ex_path, 'U').readlines()
        actual_lines   = open(ac_path, 'U').readlines()
        diff = difflib.HtmlDiff().make_table(
            expected_lines, actual_lines,
            expected, actual)
        text_file.write('<h2>' + sdir + '</h2>')
        text_file.write(diff)
        text_file.write('<br>')
        text_file.write('<hr>')
        
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

text_file.write('<br>')
text_file.write(html_end)
text_file.close()

