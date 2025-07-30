#!/usr/bin/env python3
"""Final fix for manager.py"""

# Read the file
with open('src/handlers/manager.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Fix specific lines
for i, line in enumerate(lines):
    # Fix line 224 (index 223)
    if i == 223 and '>7B # 20A =5B' in line:
        lines[i] = '                "У вас нет запланированных встреч.\\n\\n"\n'
    # Fix line 225 (index 224)
    elif i == 224 and '06<8B5 /schedule' in line:
        lines[i] = '                "Нажмите /schedule для назначения новой встречи."\n'

# Write back
with open('src/handlers/manager.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed manager.py")

# Test
import subprocess
result = subprocess.run(['python3', '-m', 'py_compile', 'src/handlers/manager.py'], capture_output=True)
if result.returncode == 0:
    print("✅ Syntax check passed!")
else:
    print(f"❌ Syntax error: {result.stderr.decode()}")