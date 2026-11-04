# Synthetic account-export fixtures

Invented, fictitious data only (example.com, com.example.*). The record shape imitates
a Takeout-style activity list for testing; it is NOT a verified provider schema.

- `activity.json`: pretty-printed list with valid records and deliberate defects
  (invalid time, missing title, non-list products, non-object element, negative
  duration, unknown field).
- `activity_reformatted_copy.json`: same content with different formatting and key order,
  to test repeated-import detection.

Do not place real participant exports here.
