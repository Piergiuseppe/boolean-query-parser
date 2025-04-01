# Boolean Query Parser

A Python package for parsing and evaluating complex boolean text queries with support for AND, OR, NOT operations, parentheses for nesting, and regular expression pattern matching.

## Features

- Boolean operators: `AND`, `OR`, `NOT`
- Parentheses for grouping and complex nested expressions
- Regular expression pattern matching with support for:
  - Regular expression flags (`i` for case-insensitive, `m` for multiline, `s` for dotall, `x` for verbose)
  - Complex patterns including capture groups, lookaheads, and lookbehinds
  - Special character escaping
- Simple, intuitive query syntax
- Comprehensive error handling

## Installation

### From PyPI

```bash
pip install boolean-query-parser
```

### From Source

Clone the repository and install using pip:

```bash
git clone https://github.com/yourusername/boolean_query_parser.git
cd boolean_query_parser
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

### `parse_query(query_str: str) -> Union[dict, str]`

Parses a boolean query string into a structured representation.

**Parameters:**
- `query_str` (str): The boolean query string to parse.

**Returns:**
- A nested dictionary structure representing the parsed query.

**Raises:**
- `SyntaxError`: If the query has invalid syntax or mismatched parentheses.

**Query Syntax:**
- Boolean operators: `AND`, `OR`, `NOT`
- Terms can be wrapped in quotes for exact matching: `"exact phrase"`
- Regular expressions can be specified with forward slashes: `/pattern/`
- Regular expressions can include flags: `/pattern/i` (i=case-insensitive, m=multiline, s=dotall, x=verbose)
- Parentheses can be used for grouping expressions

### `apply_query(parsed_query: Union[dict, str], text: str) -> bool`

Applies a parsed query to a text string and returns whether the text matches the query.

**Parameters:**
- `parsed_query` (Union[dict, str]): The parsed query structure from `parse_query`.
- `text` (str): The text to match against the query.

**Returns:**
- `bool`: True if the text matches the query, False otherwise.

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

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
