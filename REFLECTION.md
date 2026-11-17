# Reflection

## Decisions

- The CLI and the Streamlit UI run the same code path: load, profile, chart, then write Markdown and JSON. All outputs are staged and moved into place together, so a failed run leaves no half-written report.
- Each profiling step and quality rule is a small function that I could test alone.
- CSV is read with pyarrow's streaming reader, which rejects ragged rows, unclosed quotes and invalid UTF-8. JSON arrays are streamed with ijson. JSON Lines and Parquet are also supported.
- Missing-value markers must match exactly, including case, so `Na` (sodium) stays a value while `NA` becomes missing. The report counts every conversion.

## Demonstrations

- The supplied CSV (3,322 rows) and the supplied nested JSON, read with `--flatten-json` (3,317 rows, 18 columns).
- A flat JSON built from the supplied structures, with problems added on purpose: missing values, text in a numeric column, an extreme value and a duplicate row.
- A Parquet copy of the CSV.

## Limitations

- The whole table is held in memory, and profiling checks values one at a time in Python. A 200k × 18 CSV takes about 17 s and 0.8 GB.
- Type and date detection are heuristics. Only ISO-style dates are parsed.
- In streamed `.json` files, an invalid escape such as `\ud800` becomes `?`.
- The tool does not check units, domain rules or causality. I tested it on macOS only.

## AI assistance and verification

- I used Claude Code for design review, implementation, refactoring and tests. [AUTHOR: add other tools.]
- I verified the result with 444 automated tests and end-to-end CLI runs on CSV, JSON and Parquet. I also checked the UI in headless Chrome, installed the wheel outside the repository, and timed a 200k-row file.

## Time spent

[AUTHOR: enter actual time.]

## Personal review

[AUTHOR: describe your own review before submission.]
