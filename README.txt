Replace the repository root app.py and requirements.txt with these exact files.
Do not paste only part of app.py.

Verification:
- This app.py passes: python -m py_compile app.py
- In this clean file, line 80 begins with: def classify_device(item_name):
- There is no COLUMN_ALIASES variable anywhere in this file.

Expected GitHub structure:
/
  app.py
  requirements.txt
  data/
    2018_매출DB.xlsx
    ...
    2026.08_매출 DB.xlsx
