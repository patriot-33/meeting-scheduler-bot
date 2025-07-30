#!/usr/bin/env python3
"""Final fix for manager.py encoding issues."""

import re

# Read the file
with open('src/handlers/manager.py', 'rb') as f:
    content = f.read()

# Replace problematic lines
# Line 224-225 issue
content = content.replace(b'>7\nB\x0f # 20A =5B 70?;0=8@>20==KE 2AB@5G.', b'\xd0\x9d\xd0\xb5\xd1\x82 \xd0\xb7\xd0\xb0\xd0\xbf\xd0\xbb\xd0\xb0\xd0\xbd\xd0\xb8\xd1\x80\xd0\xbe\xd0\xb2\xd0\xb0\xd0\xbd\xd0\xbd\xd1\x8b\xd1\x85 \xd0\xb2\xd1\x81\xd1\x82\xd1\x80\xd0\xb5\xd1\x87.')

# Write back
with open('src/handlers/manager.py', 'wb') as f:
    f.write(content)

# Now fix remaining encoding issues
with open('src/handlers/manager.py', 'r', encoding='utf-8', errors='replace') as f:
    text = f.read()

# Fix all remaining corrupted text
replacements = {
    '>7\nB\x0f # 20A =5B 70?;0=8@>20==KE 2AB@5G.': '📅 У вас нет запланированных встреч.',
    '\x1d\u041d': 'Н',
    '� K =0E>48B5AL =0': '❌ Вы находитесь в статусе',
    '=  A>60;5=8N, =0 1;8609H85 4 =545;8 =5B A2>1>4=KE A;>B>2.': '😔 К сожалению, на ближайшие 4 недели нет свободных слотов.',
    '📅 >ABC?=K5 A;>BK 4;O 2AB@5G': '📅 Доступные слоты для встреч',
    '� @>87>H;0 >H81:0 ?@8 ?>;CG5=88 4>ABC?=KE A;>B>2. >?@>1C9B5 ?>765.': '❌ Произошла ошибка при получении доступных слотов. Попробуйте позже.',
    '� 5;L7O =07=0G8BL 2AB@5GC': '❌ Нельзя назначить встречу',
    '� # 20A C65 5ABL 70?;0=8@>20==0O 2AB@5G0.': '❌ У вас уже есть запланированная встреча.',
    '�  A>60;5=8N, MB>B A;>B C65 70=OB. >?@>1C9B5 2K1@0BL 4@C3>5 2@5<O.': '❌ К сожалению, этот слот уже занят. Попробуйте выбрать другое время.',
    '📅 >20O 2AB@5G0': '📅 Новая встреча',
    ' AB@5G0 CA?5H=> =07=0G5=0!': '✅ Встреча успешно назначена!',
    '📅 0B0:': '📅 Дата:',
    '� @5<O:': '🕐 Время:',
    '= K ?>;CG8B5 =0?><8=0=85 70 1 G0A 4> 2AB@5G8.': '💡 Вы получите напоминание за 1 час до встречи.',
    '� @>87>H;0 >H81:0 ?@8 =07=0G5=88 2AB@5G8. >?@>1C9B5 ?>765.': '❌ Произошла ошибка при назначении встречи. Попробуйте позже.',
    '📅 0H8 70?;0=8@>20==K5 2AB@5G8:': '📅 Ваши запланированные встречи:',
    'L B<5=8BL': '❌ Отменить',
    '� AB@5G0 =5 =0945=0.': '❌ Встреча не найдена.',
    'L AB@5G0 >B<5=5=0': '✅ Встреча отменена',
    ' 0H AB0BCA 87<5=5= =0:': '✅ Ваш статус изменен на:',
    '👤 **>9 ?@>D8;L**': '👤 **Мой профиль**',
    '📅 <O:': '👤 Имя:',
    '🏢 B45;:': '🏢 Отдел:',
    '📅 **!B0B8AB8:0:**': '📊 **Статистика:**',
    '✅" A53> 2AB@5G:': '• Всего встреч:',
    '✅" @>2545=>:': '• Проведено:',
    '✅" >A;54=OO 2AB@5G0:': '• Последняя встреча:',
    '> 1>;L=8G=K9': 'На больничный',
    ' 2 ': ' в ',
    '=': '📅',
    '<': '🔗',
}

for old, new in replacements.items():
    text = text.replace(old, new)

# Write fixed content
with open('src/handlers/manager.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("✅ Fixed src/handlers/manager.py")

# Test syntax
import subprocess
result = subprocess.run(['python3', '-m', 'py_compile', 'src/handlers/manager.py'], capture_output=True)
if result.returncode == 0:
    print("✅ Syntax check passed!")
else:
    print(f"❌ Syntax check failed: {result.stderr.decode()}")