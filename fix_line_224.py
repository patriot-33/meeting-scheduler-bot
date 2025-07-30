#!/usr/bin/env python3
"""Fix the specific syntax error on line 224"""

# Read the file
with open('src/handlers/manager.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Fix the broken string
content = content.replace(
    '                ">7\nB # 20A =5B 70?;0=8@>20==KE 2AB@5G.\\n\\n"\n                "06<8B5 /schedule 4;O =07=0G5=8O =>2>9 2AB@5G8."',
    '                "📅 У вас нет запланированных встреч.\\n\\n"\n                "Нажмите /schedule для назначения новой встречи."'
)

# Write back
with open('src/handlers/manager.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed syntax error on line 224")

# Test syntax
import subprocess
result = subprocess.run(['python3', '-m', 'py_compile', 'src/handlers/manager.py'], capture_output=True)
if result.returncode == 0:
    print("✅ Syntax check passed!")
else:
    print(f"❌ Syntax error: {result.stderr.decode()}")