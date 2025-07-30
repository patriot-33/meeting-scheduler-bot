#!/usr/bin/env python3
"""Fix encoding issues in all Python files."""

import os
import re
from pathlib import Path

def fix_corrupted_text(text):
    """Fix corrupted Cyrillic text."""
    # Common replacements for corrupted Cyrillic
    replacements = {
        '>7\rB\x0f # 20A =5B 70?;0=8@>20==KE 2AB@5G': '📅 У вас нет запланированных встреч',
        '06<8B5 /schedule 4;O =07=0G5=8O =>2>9 2AB@5G8': 'Нажмите /schedule для назначения новой встречи',
        '=� 0H8 70?;0=8@>20==K5 2AB@5G8': '📅 Ваши запланированные встречи',
        '=� @>A@>G5==K5 2AB@5G8': '⏰ Просроченные встречи',
        '!;54CNI85 @C:>2>48B5;8 =5 =07=0G8;8 2-=545;L=CN 2AB@5GC': 'Следующие руководители не назначили 2-недельную встречу',
        '>60;C9AB0, A2O68B5AL A =8<8 4;O =07=0G5=8O 2AB@5G8': 'Пожалуйста, свяжитесь с ними для назначения встречи',
        '=K @825B': 'Привет',
        '=� 4<8=8AB@0B>@': '👨‍💼 Администратор',
        '=� A=>2=K5 :><0=4K': '📋 Основные команды',
        '>A<>B@5BL 4>ABC?=K5 A;>BK': 'Посмотреть доступные слоты',
        '>8 2AB@5G8': 'Мои встречи',
        'B<5B8BL >B?CA:': 'Отметить отпуск',
        '>9 ?@>D8;L': 'Мой профиль',
        '><>IL': 'Помощь',
        '> ><>IL ?> 1>BC': '🤖 Помощь по боту',
        '=� **;0=8@>20=85 2AB@5G:**': '📅 **Планирование встреч:**',
        '>:070BL 4>ABC?=K5 A;>BK': 'Показать доступные слоты',
        '>8 70?;0=8@>20==K5 2AB@5G8': 'Мои запланированные встречи',
        '<4 **!B0BCA:**': '👤 **Статус:**',
        'B<5B8BL >B?CA:': 'Отметить отпуск',
        'B<5B8BL 1>;L=8G=K9': 'Отметить больничный',
        '4<8=-?0=5;L': 'Админ-панель',
        '6840NI85 ?>;L7>20B5;8': 'Ожидающие пользователи',
        '!?8A>: ?>;L7>20B5;59': 'Список пользователей',
        '!B0B8AB8:0': 'Статистика',
        '9 0H0 70O2:0 >68405B >4>1@5=8O 04<8=8AB@0B>@><': '⏳ Ваша заявка ожидает одобрения администратором',
        ";O =0G0;0 @01>BK =5>1E>48<> 70@538AB@8@>20BLAO": 'Для начала работы необходимо зарегистрироваться',
        "@>4068": 'Продажи',
        "0@:5B8=3": 'Маркетинг',
        " 07@01>B:0": 'Разработка',
        "$8=0=AK": 'Финансы',
        ">?5@0F88": 'Операции',
        ">38AB8:0": 'Логистика',
        ">445@6:0": 'Поддержка',
        " 0:B82=K9": 'Активный',
        "<4 >B?CA:": 'В отпуске',
        "> 1>;L=8G=K9": 'На больничном',
        " :><0=48@>2:0": 'В командировке',
    }
    
    for corrupted, fixed in replacements.items():
        text = text.replace(corrupted, fixed)
    
    return text

def fix_file(filepath):
    """Fix encoding issues in a single file."""
    try:
        # Read file content
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Check if file has issues
        original_content = content
        
        # Fix corrupted text
        content = fix_corrupted_text(content)
        
        # Remove special characters
        content = content.replace('\r', '')
        content = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', content)
        
        if content != original_content:
            # Write fixed content back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {filepath}")
            return True
        else:
            print(f"✓ No issues: {filepath}")
            return False
    except Exception as e:
        print(f"❌ Error fixing {filepath}: {e}")
        return False

def main():
    """Fix all Python files in the project."""
    print("🔍 Scanning for files with encoding issues...\n")
    
    fixed_count = 0
    total_count = 0
    
    # Find all Python files
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                total_count += 1
                if fix_file(filepath):
                    fixed_count += 1
    
    print(f"\n📊 Summary:")
    print(f"Total files checked: {total_count}")
    print(f"Files fixed: {fixed_count}")
    
    if fixed_count > 0:
        print("\n✅ All encoding issues have been fixed!")
    else:
        print("\n✅ No encoding issues found!")

if __name__ == "__main__":
    main()