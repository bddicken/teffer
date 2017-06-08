# Teffer

Teffer (TEst diFFER) is a python-based tool used for autometed testing.
The tool runs an input program against a set of textual tests.
For each test, teffer generates a diff.
All of the diffs are combined and inserted into an html output, which can be viewed in your browser of choice.


## Writing Tests

Teffer test-cases are made by creating a single directory full of subdirectories.
Each subdirectory represents a single teffer test case.
Each individual test directory should contain the following files:

* `run.sh` : A bash scrip which will be executed by teffer, with the current working directors as the execution directory.
             `run.sh` may use the token `COMMAND_BASE_DIR`, and teffer will replace this with the directory specified to the `-s` option of teffer.
* `expected.txt` : A text file containing the expected output of this particular execution of your program.

Each test directory should also contain any necessary resource files needed for the test, such as input files.

A top-level test directory will have a structure that looks similar to this:

```
$ tree tests/
tests/
├── some-test
│   ├── resource-1.txt
|   ├── resource-2.txt
│   ├── run.sh
│   └── expected.txt
├── another-test
│   ├── resource-X.txt
│   ├── run.sh
│   └── expected.txt
└── cool-test
    ├── run.sh
    └── expected.txt
```

Teffer will generate an `actual.txt` alongside each `expected.txt` after being executed.
The `actual.txt` is the captured stdout from running the command in `run.sh`.
Teffer will diff `actual.txt` and `expected.txt`.
Teffer will generate an HTML file containing all of the diffs from the test run.
This HTML file can be viewed in a web-browser.

See the `teffer/tests` directory for a few example test cases.


## Command-line arguments

See `teffer.sh -h` for details of command-line options.


## Testing

Teffer has a default test suite, located in the `./tests`.
Since teffer itself is a testing framework, we use teffer to test itself.
To run the teffer tests, just execute:

```
./teffer.sh
```


## Walkthrough

Below is a step-by-step guide to running teffer on some test cases.
The test-cases used are from a programming assignment given in CS 110 at the UofA.

1) Use or create a set of test cases to run teffer on.
   Show below is a screenshow of the contents of a `tests` directory.
   
   ![files](./images/files.png)
   
   The test directory contains many tests, each with a `run.sh` and an `expected.txt` file.
   Below are the contents of these two files in the `bat-5` directory:

    ```
sed -i '' -e 's/^BAT_WIDTH.*/BAT_WIDTH = 5/g' BASE_DIR/bat.py
python3 BASE_DIR/bat.py
    ```

    ```
\****\_____      /\_/\      _____/****/
 \    *****\_____|* *|_____/*****    / 
  \         *****| - |*****         /  
   \_______ *****||*||***** _______/   
                 {   }
    ```

