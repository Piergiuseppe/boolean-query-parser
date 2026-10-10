# Boolean Query Parser

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/boolean-query-parser?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pypi.org/project/boolean-query-parser/)

**[▶ Try it live in your browser](https://piergiuseppe.github.io/boolean-query-parser/)** — no install needed, runs via WebAssembly

A lightweight, **zero-dependency** Python package for parsing and evaluating complex boolean queries over text and records. Supports `AND`, `OR`, `NOT`, parentheses, wildcards, regular expressions, comparisons for numbers, dates, durations and sizes found in the text, field-scoped terms for dictionaries, explanations of why something matched, and a grep-like command line tool — built entirely on the Python standard library.

## Features

- **Zero external dependencies** — uses only the Python standard library (`re`), so it installs instantly and adds no weight to your project
- Boolean operators: `AND`, `OR`, `NOT`
- Implicit AND: adjacent terms without an operator are treated as AND (e.g. `python flask` equals `python AND flask`)
- Parentheses for grouping and complex nested expressions
- Quoted strings for exact phrase matching (`"exact phrase"`)
- Bare words may contain `_ . - + # @` after the first character, so `node.js`, `e-mail`, `C++` and `C#` need no quotes
- Wildcards in bare words: `pyth*` matches `python` and `pythonic`
- Query-wide options: `ignore_case=True`, `whole_words=True`, and `allow_regex=False` for queries typed by untrusted users
- Regular expression pattern matching with support for:
  - Regular expression flags (`i` for case-insensitive, `m` for multiline, `s` for dotall, `x` for verbose)
  - Complex patterns including capture groups, lookaheads, and lookbehinds
  - Special character escaping
- Comparison operators for values found in natural text:
  - `num:>5` — finds any number in the text and checks if it's > 5
  - `date:>2023-01-01` — finds any date (YYYY-MM-DD, YYYY/MM/DD, optionally with a time) in the text and checks if it's after 2023-01-01
  - `dur:>1.5s` — finds durations such as `250ms`, `2 min` or `3h`
  - `size:>10MB` — finds sizes such as `512KiB` or `3 GB`
  - Supported operators: `>`, `<`, `>=`, `<=`, `=`
  - Combine with boolean operators for range queries (e.g. `num:>=5 AND num:<=10`)
- Positional templates with `{num:op}` / `{date:op}` placeholders inside quoted strings:
  - `"evaluated in {num:<50} ms"` — matches text like `"evaluated in 12 ms"` while respecting order
  - Comparisons only apply to the number/date at the placeholder position, not elsewhere in the text
  - Supports multiple placeholders in a single template
- Field-scoped terms for dictionaries and JSON records: `title:python AND meta.views:num:>100`
- Filters any iterable of strings or of mappings (list, tuple, generator, ...)
- `explain_query` tells you which terms matched and where, and highlights them
- `bqp`, a grep-like command line tool for logs and JSON lines
- Clear syntax errors that carry the position of the offending term

## Installation

### From PyPI

```bash
pip install boolean-query-parser
```

### From Source

Clone the repository and install using pip:

```bash
git clone https://github.com/Piergiuseppe/boolean-query-parser.git
cd boolean-query-parser
pip install .
```

## Usage

### Basic Example

```python
from boolean_query_parser import parse_query, apply_query

# Define some sample text data
documents = [
    "The quick brown fox jumps over the lazy dog",
    "Python is a programming language",
    "The Python programming language is powerful and easy to learn",
    "Regular expressions can be complex but useful"
]

# Parse a query
query = 'Python AND programming AND NOT complex'
parsed_query = parse_query(query)

# Apply the query to filter documents
matching_documents = [doc for doc in documents if apply_query(parsed_query, doc)]

# Print results
for doc in matching_documents:
    print(doc)
```

Output:
```
Python is a programming language
The Python programming language is powerful and easy to learn
```

### Advanced Example with Nested Expressions

```python
from boolean_query_parser import parse_query, apply_query

# Parse a complex query with parentheses and multiple operations
query = '(Python OR programming) AND (language OR easy) AND NOT (complex OR difficult)'
parsed_query = parse_query(query)

# Sample text data
documents = [
    "Python is a great language for beginners",
    "Programming can be complex and difficult at times",
    "Python makes programming tasks easy to accomplish",
    "This text has nothing relevant"
]

# Apply the query
for doc in documents:
    if apply_query(parsed_query, doc):
        print(f"Match: {doc}")
    else:
        print(f"No match: {doc}")
```

### Using Regular Expressions

```python
from boolean_query_parser import parse_query, apply_query

# Parse a query with regex patterns
query = '/py.*on/i AND NOT /difficult/'
parsed_query = parse_query(query)

documents = [
    "Python is easy to learn",
    "python programming is fun",
    "This is difficult Python code",
    "PyThOn is case-insensitive in this example"
]

# Apply the query
for doc in documents:
    if apply_query(parsed_query, doc):
        print(f"Match: {doc}")
```

### Using Regular Expression Flags

```python
from boolean_query_parser import parse_query, apply_query

# Case-insensitive matching with 'i' flag
query = '/python/i'
parsed_query = parse_query(query)
print(apply_query(parsed_query, "This contains PYTHON"))  # True

# Multiline matching with 'm' flag
multiline_text = "First line\nSecond line with python\nThird line"
query = '/^Second.*python$/m'
parsed_query = parse_query(query)
print(apply_query(parsed_query, multiline_text))  # True

# Dot-all mode with 's' flag (dot matches newlines)
text_with_newlines = "Start\nMiddle\nEnd"
query = '/Start.*End/s'
parsed_query = parse_query(query)
print(apply_query(parsed_query, text_with_newlines))  # True
```

### Using Comparisons

Comparison operators scan your text for numbers or dates and compare them against a threshold. The text stays natural — no special markup needed.

- `num:` scans for any number (integer or float) in the text. A minus right after a word character is read as a hyphen, so `pages 3-7` contains 3 and 7, not -7. Numbers that are part of a date or time are skipped, and so are digits after a dot (`v1.2.3` contains 1.2 only).
- `date:` scans for any date (`YYYY-MM-DD` or `YYYY/MM/DD`), optionally followed by a time (`THH:MM[:SS]` or ` HH:MM[:SS]`).
- Dates compare at the precision of the threshold: `date:=2024-01-01` matches `2024-01-01T10:30:00`, `date:=2024-01-01T10:30` matches any second of that minute, and `date:>2024-01-01T10:30:00` compares down to the second.

```python
from boolean_query_parser import parse_query, apply_query

# Find texts where any number is greater than 3
query = parse_query("num:>3")
print(apply_query(query, "found 5 errors"))    # True  (5 > 3)
print(apply_query(query, "found 2 errors"))    # False (2 is not > 3)

# Float threshold
query = parse_query("num:<=9.99")
print(apply_query(query, "price is 5.00"))     # True
print(apply_query(query, "price is 15.50"))    # False

# Date comparison on natural text
query = parse_query("date:>2023-01-01")
print(apply_query(query, "deployed on 2023-06-15"))  # True
print(apply_query(query, "deployed on 2022-12-31"))  # False

# Date range
query = parse_query("date:>=2023-01-01 AND date:<=2023-12-31")
print(apply_query(query, "published 2023-06-15"))    # True
print(apply_query(query, "published 2024-01-01"))    # False

# Combine comparisons with text matching and regex
query = parse_query('(/error/i OR /warn/i) AND num:>=3')
logs = [
    "ERROR severity 5 occurred",
    "WARN level 3 detected",
    "ERROR minor level 1",
    "INFO level 5 ok",
]
print(apply_query(query, logs))
# ['ERROR severity 5 occurred', 'WARN level 3 detected']
```

### Using Positional Templates

When you need comparisons to apply **only to a specific position** in the text rather than scanning everywhere, wrap the query in quotes and use `{num:op value}` or `{date:op value}` placeholders:

```python
from boolean_query_parser import parse_query, apply_query

# Without template: num:<50 matches ANY number, including the "1" in "test 1"
# With template: only the number between "in" and "ms" is checked
query = parse_query('"test 1 Success evaluated in {num:<50} ms"')
print(apply_query(query, "test 1 Success evaluated in 12 ms"))  # True  (12 < 50)
print(apply_query(query, "test 1 Success evaluated in 80 ms"))  # False (80 >= 50)
print(apply_query(query, "test 2 Success evaluated in 12 ms"))  # False ("test 1" ≠ "test 2")

# Multiple placeholders: each is checked at its position
query = parse_query('"test {num:>0} completed in {num:<100} ms"')
print(apply_query(query, "test 5 completed in 42 ms"))   # True  (5>0, 42<100)
print(apply_query(query, "test 0 completed in 42 ms"))   # False (0 is not > 0)
print(apply_query(query, "test 5 completed in 150 ms"))  # False (150 >= 100)

# Date placeholder
query = parse_query('"deployed on {date:>2023-01-01} successfully"')
print(apply_query(query, "deployed on 2024-03-15 successfully"))  # True
print(apply_query(query, "deployed on 2022-12-01 successfully"))  # False

# Combine templates with boolean operators
query = parse_query('"took {num:<50} ms" AND Success')
print(apply_query(query, "Success took 12 ms"))  # True
print(apply_query(query, "Failure took 12 ms"))  # False
```

### Case-insensitive Queries

```python
from boolean_query_parser import parse_query, apply_query

query = parse_query('Python AND "took {num:<50} MS" NOT /timeout/', ignore_case=True)
print(apply_query(query, "python job took 12 ms"))          # True
print(apply_query(query, "PYTHON job took 12 ms TIMEOUT"))  # False
```

`ignore_case=True` applies to text terms, quoted phrases, templates and regexes alike.

### Whole Words and Wildcards

By default a term matches anywhere, so `python` is found in `pythonic`. Pass `whole_words=True` to match whole words only, and use `*` in a bare word to match any run of letters, digits or underscores:

```python
from boolean_query_parser import parse_query, apply_query

print(apply_query(parse_query("python"), "pythonic code"))                    # True
print(apply_query(parse_query("python", whole_words=True), "pythonic code"))  # False
print(apply_query(parse_query("pyth*", whole_words=True), "pythonic code"))   # True
print(apply_query(parse_query("*thon", whole_words=True), "jython"))          # True
```

A quoted `"py*"` is a literal asterisk.

### Durations and Sizes

```python
from boolean_query_parser import parse_query, apply_query

slow = parse_query("ERROR AND (dur:>1s OR size:>10MB)")
print(apply_query(slow, "ERROR request took 1500ms"))   # True
print(apply_query(slow, "ERROR upload of 12 MB"))       # True
print(apply_query(slow, "ERROR request took 300ms"))    # False
print(apply_query(parse_query('"took {dur:<1s}"'), "request took 250ms"))  # True
```

Durations understand `us`, `ms`, `s`/`sec`/`seconds`, `m`/`min`/`minutes`, `h`/`hr`/`hours` and `d`/`days`. Sizes understand `B`/`bytes`, decimal `kB`/`MB`/`GB`/`TB` (powers of 1000) and binary `KiB`/`MiB`/`GiB`/`TiB` (powers of 1024), in any case. A space between amount and unit is allowed in the text; in a query, quote it: `dur:>"1.5 s"`.

### Searching Records

Pass dictionaries instead of strings and scope terms to fields with `field:term`. Unscoped terms search all the values of the record.

```python
from boolean_query_parser import parse_query, apply_query

articles = [
    {"title": "Python tips", "meta": {"author": "ann", "views": 1500}, "tags": ["web", "py"]},
    {"title": "Rust", "body": "python is slow", "meta": {"author": "bob", "views": 20}},
]

query = parse_query("title:python AND meta.views:num:>100", ignore_case=True)
print(apply_query(query, articles))                            # [the "Python tips" record]
print(apply_query(parse_query("tags:web"), articles[0]))       # True
print(len(apply_query(parse_query("python", ignore_case=True), articles)))  # 2
```

- A field can scope any term: `title:"exact phrase"`, `title:/^py/i`, `title:(rust OR go)`, `title:pyth*`, `price:num:>5`.
- Dotted names reach into nested mappings (`meta.author`), unless a literal `"meta.author"` key exists.
- Lists are searched item by item; numbers and booleans are read as text (`true`/`false`).
- A missing field never matches, so `NOT title:x` selects records without a title too.
- `name:` followed by an operator is a comparison, so write `views:num:>100`, not `views:>100`.

### Explaining Matches

```python
from boolean_query_parser import parse_query, explain_query

text = "python with flask and 150 users"
explanation = explain_query(parse_query("python NOT java (flask OR num:>100)"), text)

print(explanation.matched)            # True
print(explanation.highlight(text))    # [python] with [flask] and [150] users
print(explanation)
# ✓ AND
#   ✓ Text('python')  at 0-6
#   ✓ NOT
#     ✗ Text('java')
#   ✓ OR
#     ✓ Text('flask')  at 12-17
#     ✓ Comparison(num:>100)  at 22-25
```

`explanation.hits()` lists the `Hit(field, start, end)` positions that made the query match; terms under `NOT` never count. On records, each hit names its field (`None` for unscoped terms).

### Queries from Untrusted Users

A regular expression can be written to take exponential time on some inputs. When the query comes from someone you do not trust, disable regexes; every other feature keeps working, and wildcards are matched without backtracking, so they stay fast on any input:

```python
from boolean_query_parser import QuerySyntaxError, parse_query

try:
    parse_query("error /(a+)+$/", allow_regex=False)
except QuerySyntaxError as error:
    print(error.position, error)  # 6 Error parsing query: Regular expressions are disabled ...
```

### Command Line

Installing the package adds `bqp`, which prints the lines that match a query, like `grep`:

```bash
bqp 'ERROR AND (dur:>1s OR size:>10MB) NOT healthcheck' app.log
bqp -i -n --color always 'timeout OR refused' *.log
tail -f app.log | bqp 'num:>=500'
bqp --json 'level:error AND ms:num:>500' app.jsonl   # one JSON object per line
bqp --explain 'error NOT healthcheck' app.log         # show why each line matched
```

Options: `-i` ignore case, `-w` whole words, `--no-regex`, `-v` invert, `-c` count, `-l` files with matches, `-n` line numbers, `-H`/`--no-filename`, `--json`, `--explain`, `--color auto|always|never`. The exit status is 0 when a line was selected, 1 when none was, 2 on errors. `python -m boolean_query_parser` works too.

### Complex Regex Patterns

```python
from boolean_query_parser import parse_query, apply_query

# Email validation with regex
email_pattern = '/([A-Za-z0-9]+[._-])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\\.[A-Za-z]{2,})/'
email_query = parse_query(email_pattern)

# HTML tag matching with capture groups and backreferences
html_pattern = '/\\<([a-z][a-z0-9]*)(\\s[^\\>]*)?\\>([^\\<]*)\\<\\/\\1\\>/i'
html_query = parse_query(html_pattern)

# Password validation with lookaheads
password_pattern = '/^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).{8,}$/'
password_query = parse_query(password_pattern)

# Test them
print(apply_query(email_query, "Contact us at info@example.com"))  # True
print(apply_query(html_query, "<div>Content</div>"))  # True
print(apply_query(password_query, "Password123"))  # True
```

## API Documentation

### `parse_query(query_str, *, ignore_case=False, whole_words=False, allow_regex=True) -> Node`

Parses a boolean query string into an abstract syntax tree (AST).

**Parameters:**
- `query_str` (str): The boolean query string to parse.
- `ignore_case` (bool): Match every term regardless of case.
- `whole_words` (bool): Match text terms and phrases only as whole words.
- `allow_regex` (bool): When `False`, `/regex/` terms are a syntax error.

**Returns:**
- `Node`: The root node of the parsed AST. Parse once and reuse it: the tree compiles itself on first use.

**Raises:**
- `QuerySyntaxError` (a subclass of both `QueryError` and `ValueError`): if the query is malformed. Its `position` attribute holds the offset of the offending term.
- `TypeError`: if `query_str` is not a string.

**Query Syntax:**
- Boolean operators: `AND`, `OR`, `NOT`
- Implicit AND: adjacent terms without an operator are treated as AND (e.g. `python flask` equals `python AND flask`)
- Terms can be wrapped in quotes for exact matching: `"exact phrase"`
- Regular expressions can be specified with forward slashes: `/pattern/`
- Regular expressions can include flags: `/pattern/i` (i=case-insensitive, m=multiline, s=dotall, x=verbose). Any other flag, such as JavaScript's `g`, is a syntax error.
- Wildcards: `*` inside a bare word matches any run of word characters (`pyth*`, `*thon`, `py*n`)
- Fields: `name:term` scopes a term (or a parenthesized group) to one field of a record; dotted names reach nested mappings
- Comparisons: `num:>value`, `date:>value`, `dur:>value` and `size:>value` (operators: `>`, `<`, `>=`, `<=`, `=`)
  - `num:` scans text for numbers (integers, floats, negatives) and compares each against the threshold
  - `date:` scans text for date patterns (`YYYY-MM-DD`, `YYYY/MM/DD`, with an optional `THH:MM[:SS]` or ` HH:MM[:SS]` time) and compares at the precision of the threshold
  - Values can be quoted: `date:>"2023-01-01 10:00"`
- Positional templates: `"literal text {num:<50} more text"` — quoted strings with `{num:op value}`, `{date:op value}`, `{dur:op value}` or `{size:op value}` placeholders. Literal text must match in order, and comparisons apply only at the placeholder position.
- Parentheses can be used for grouping expressions, up to 100 levels deep

### `apply_query(parsed_query, text_data) -> bool | list`

Applies a parsed query to one text or record, or filters many.

**Parameters:**
- `parsed_query` (Node): The parsed query AST from `parse_query`.
- `text_data`: A string or a mapping to evaluate, or any iterable of strings, or of mappings, to filter.

**Returns:**
- For a single string or mapping: `bool`.
- Otherwise: a `list` of the items that match, in their original order.

**Raises:**
- `TypeError`: if `text_data` is none of the above, mixes strings and mappings, or is `bytes`.
- `QueryError`: if a query with `field:` terms is applied to plain strings.

### `explain_query(parsed_query, data) -> Explanation`

Explains why a string or a mapping does or does not match. The `Explanation` has `matched`, `hits()`, `highlight(text, before="[", after="]")`, and renders as a tree with `str()`.

## Real-World Use Cases

### Log Analysis

Parse through server logs to find specific error patterns:

```python
from boolean_query_parser import parse_query, apply_query
import glob

# Query to find critical errors related to database but not connection timeouts
query = '(ERROR OR CRITICAL) AND database AND NOT "connection timeout"'
parsed_query = parse_query(query)

# Process log files
matching_logs = []
for log_file in glob.glob('/var/log/application/*.log'):
    with open(log_file, 'r') as f:
        for line in f:
            if apply_query(parsed_query, line):
                matching_logs.append(line.strip())

print(f"Found {len(matching_logs)} matching log entries")
```

### Document Classification

Categorize documents based on their content:

```python
from boolean_query_parser import parse_query, apply_query

# Define category queries
categories = {
    'finance': parse_query('(banking OR investment OR financial) AND NOT (gaming OR entertainment)'),
    'technology': parse_query('(programming OR software OR hardware OR "machine learning") AND NOT financial'),
    'health': parse_query('(medical OR health OR doctor OR patient) AND NOT (technology OR finance)')
}

# Function to classify a document
def classify_document(text):
    results = []
    for category, query in categories.items():
        if apply_query(query, text):
            results.append(category)
    return results or ['uncategorized']
```

### Monitoring & Alerting

Filter log entries using comparisons on numbers and dates:

```python
from boolean_query_parser import parse_query, apply_query

# Alert on errors with severity >= 3 from March 2025 onwards
query = parse_query(
    '(/error/i OR /fatal/i) AND num:>=3 AND date:>=2025-03-01'
)

log_entries = [
    "2025-03-15 ERROR severity 5 — Database connection timeout",
    "2025-03-14 FATAL severity 4 — Out of memory",
    "2025-03-15 ERROR severity 2 — Minor validation failure",
    "2025-03-15 INFO severity 1 — Server started",
    "2025-02-28 ERROR severity 3 — Old disk space warning",
]

alerts = apply_query(query, log_entries)
print(f"Found {len(alerts)} alerts requiring attention")
for alert in alerts:
    print(f"  🚨 {alert}")
```

Output:
```
Found 2 alerts requiring attention
  🚨 2025-03-15 ERROR severity 5 — Database connection timeout
  🚨 2025-03-14 FATAL severity 4 — Out of memory
```

### Email Filtering example

Filter emails based on complex patterns:

```python
from boolean_query_parser import parse_query, apply_query

# Query to find emails that:
# 1. Have attachments (mention .pdf, .doc, etc.)
# 2. Are not from known domains
# 3. Contain specific keywords in the subject
query = parse_query('(/\\.pdf/i OR /\\.doc/i OR /\\.docx/i) AND NOT /from:.*@(company\\.com|trusted\\.org)/ AND /subject:.*urgent/i')

# Apply to email bodies
def filter_suspicious_emails(emails):
    return [email for email in emails if apply_query(query, email)]
```

## Project Layout

```
boolean_query_parser/
├── api.py          parse_query / apply_query / explain_query, thin wrappers over the services
├── services/       ParsingService, MatchingService (texts and records), ExplanationService
├── syntax/         tokens, Lexer and the recursive descent Parser
├── nodes/          the tree: Text, Regex, Comparison, Template, Field, And/Or/Not
├── values/         value kinds (num, date, dur, size), their scanners and comparison operators
├── options.py      QueryOptions
├── records.py      how a mapping is read: field lookup and full text
├── explanation.py  Explanation and Hit
├── cli/            the bqp command
├── exceptions.py   QueryError, QuerySyntaxError
└── parser.py       the 1.0 import path, kept for compatibility
```

Adding a new comparable kind means adding a `ValueKind` to the registry in `values/kinds.py`: comparisons and templates pick it up from there.

## Development

```bash
python -m unittest discover -s tests -t .
python scripts/sync_docs.py   # after changing the package: refreshes the copy the playground in docs/ runs
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
