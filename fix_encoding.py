import os
import glob

# Fix all Python files with encoding issues
files_to_check = glob.glob('src/**/*.py', recursive=True)

for filepath in files_to_check:
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Check if content needs fixing
        needs_fix = False
        for line in content.split('\n'):
            if '"' in line and any(ord(c) > 127 and ord(c) < 256 for c in line):
                needs_fix = True
                break
        
        if needs_fix:
            print(f"File {filepath} needs fixing, but skipping to avoid corruption")
            
    except Exception as e:
        print(f"Error checking {filepath}: {e}")

print("\nFor now, let's just fix the critical error in registration.py")
