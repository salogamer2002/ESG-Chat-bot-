import os
from collections import Counter

directory = "data/raw_docs"
extension_counts = Counter()

for root, _, files in os.walk(directory):
    for file in files:
        _, ext = os.path.splitext(file)
        if ext:  # Only consider files with an extension
            extension_counts[ext.lower()] += 1  # Normalize to lowercase

print("Document type counts:")
for ext, count in extension_counts.items():
    print(f"{ext}: {count}")