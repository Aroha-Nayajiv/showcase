import os
import re

docs_dir = "/Users/vijayan/work/devai/devai/projects/PatientIntake/deliverables/docs"

# Fix AES-1 token (including different dashes)
filepath = os.path.join(docs_dir, "inception_stakeholder_needs.md")
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the AES-1¶ completely, or replace with AES-256? The prompt said "Clean AES-1¶ token". I'll replace it with AES-256 or just remove it. Let's just remove it and any trailing spaces/parens.
content = re.sub(r'\(AES[-–]1¶\)', '(AES-256)', content)
content = re.sub(r'AES[-–]1¶', 'AES-256', content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

# Fix section numbering in stakeholder_analysis_scope.md
filepath = os.path.join(docs_dir, "inception_stakeholder_analysis_scope.md")
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find all headings with numbers
headings = re.findall(r'^##\s+(\d+)\.\s+(.*)$', content, flags=re.MULTILINE)

# Rewrite the numbers sequentially
counter = 1
for old_num, title in headings:
    old_heading = f"## {old_num}. {title}"
    new_heading = f"## {counter}. {title}"
    content = content.replace(old_heading, new_heading, 1)
    counter += 1

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done fixing remaining issues.")
