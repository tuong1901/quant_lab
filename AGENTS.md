# AI Dev Rules — Small Personal Project

## 1. At the start of every new session
Before touching any file, read in this order:
- README.md at the repo root (if present)
- PROJECT_STATUS.md (if present)
- The README.md of the folder relevant to the task
- The source code directly relevant to the task

Never assume architecture or business logic — if unsure, ask instead of guessing.

## 2. While writing code
Keep functions small, one responsibility per function (SRP); avoid a giant main() or deeply nested logic.
Every important function must have a docstring in this format:

```python
def calculate_candlestick_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    [PURPOSE]: Compute body_size, upper_wick, lower_wick, body_ratio from OHLC data.
    [DEPENDENCIES]: Called by preprocessor.prepare_features();
                    output feeds into models/tcn_lstm.forward().
    [ARGS]: df — DataFrame with columns ['Open','High','Low','Close'].
    [RETURNS]: DataFrame with 4 new candlestick feature columns added.
    [SIDE EFFECTS]: None (pure function).
    """
```

Name variables/functions clearly, avoid cryptic abbreviations.
For non-trivial algorithms (e.g. scoring logic, feature engineering, matching logic), add 2-3 lines of comments explaining why it's done this way, not just what it does.

## 3. After finishing a change
If a file/module exceeds ~150-200 lines or gains a significant new feature → update that folder's README.md (purpose, main functions, dependencies).
If the change affects overall architecture → update the root README.md.
Briefly update PROJECT_STATUS.md: what's being worked on, what's done, what's next, any open issues. A few lines is enough, no long format needed.

## 4. General principles
Code is the final source of truth — if README and code disagree, trust the code, then fix the README.
Don't silently make large architectural changes — a heads-up is 1 sentence.
Before a large change, briefly explain: what's changing, why, which files are affected — 3-4 lines is enough.

## 5. File access restrictions (STRICT)
The agent is ONLY allowed to freely read/edit:
- Source code files directly relevant to the task (.py, .ts, .js, etc.)
- Its own log/status files it creates for debugging (e.g. debug_log.md, fix_notes.md)

The agent is NEVER allowed to read, open, parse, or edit any other file type (.txt, .csv, .json data files, .xlsx, .pdf, images, or any file containing data) WITHOUT explicitly asking for permission first — EVERY SINGLE TIME, no exceptions.
    