#!/usr/bin/env python3
"""Final fixes for remaining syntax errors."""

# Fix src/handlers/common.py
with open('src/handlers/common.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix line 65 - wrong quotes
content = content.replace('"" AB@5G8 ?@>2>4OBAO @07 2 2 =545;8', '"• Встречи проводятся раз в 2 недели')
content = content.replace('"" >ABC?=K5 G0AK:', '"• Доступные часы:')
content = content.replace('"" @>4>;68B5;L=>ABL:', '"• Продолжительность:')
content = content.replace('"" 0?><8=0=8O ?@8E>4OB 02B><0B8G5A:8', '"• Напоминания приходят автоматически')

# Fix other corrupted text
content = content.replace('B<5B8BL :><0=48@>2:C', 'Отметить командировку')
content = content.replace('5@=CBLAO 2Активный AB0BCA', 'Вернуться в активный статус')
content = content.replace('=d **@>D8;L:**', '👤 **Профиль:**')
content = content.replace('>A<>B@5BL <Мой профиль', 'Посмотреть мой профиль')
content = content.replace('9 **A>15==>AB8:**', '📝 **Особенности:**')
content = content.replace('> Помощь ?> 1>BC', '🤖 Помощь по боту')
content = content.replace('=K @825B, ', 'Привет, ')
content = content.replace('=K @825B! / 1>B 4;O ?;0=8@>20=8O 2AB@5G.', 'Привет! Я бот для планирования встреч.')
content = content.replace('=� ', '📋 ')
content = content.replace('L ?5@0F8O >B<5=5=0.', 'Операция отменена.')
content = content.replace('A?>;L7C9B5 /help 4;O ?@>A<>B@0 4>ABC?=KE :><0=4.', 'Используйте /help для просмотра доступных команд.')
content = content.replace('� >72@0I05<AO =0704...', '⬅️ Возвращаемся назад...')

with open('src/handlers/common.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed src/handlers/common.py")

# Fix src/handlers/manager.py
with open('src/handlers/manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix line 224-225 issue
content = content.replace('>7\nB # 20A =5B 70?;0=8@>20==KE 2AB@5G.', '📅 У вас нет запланированных встреч.')

# Fix other corrupted text in manager.py
corrupted_replacements = {
    '� K =0E>48B5AL =0 ': '❌ Вы находитесь в статусе ',
    ';O =07=0G5=8O 2AB@5G A=0G0;0 25@=8B5AL 2Активный AB0BCA:': 'Для назначения встреч сначала вернитесь в активный статус:',
    '=  A>60;5=8N, =0 1;8609H85 4 =545;8 =5B A2>1>4=KE A;>B>2.': '😔 К сожалению, на ближайшие 4 недели нет свободных слотов.',
    '>?@>1C9B5 ?>765 8;8 A2O68B5AL A 04<8=8AB@0B>@><.': 'Попробуйте позже или свяжитесь с администратором.',
    '=� >ABC?=K5 A;>BK 4;O 2AB@5G': '📅 Доступные слоты для встреч',
    '= 0 4>ABC?=K5 4=8 =5B A2>1>4=KE A;>B>2.': '❌ На доступные дни нет свободных слотов.',
    '� @>87>H;0 >H81:0 ?@8 ?>;CG5=88 4>ABC?=KE A;>B>2. >?@>1C9B5 ?>765.': '❌ Произошла ошибка при получении доступных слотов. Попробуйте позже.',
    '� 5;L7O =07=0G8BL 2AB@5GC 2 =50:B82=>< AB0BCA5.': '❌ Нельзя назначить встречу в неактивном статусе.',
    '� # 20A C65 5ABL 70?;0=8@>20==0O 2AB@5G0.': '❌ У вас уже есть запланированная встреча.',
    '!;54CNICN 2AB@5GC <>6=> =07=0G8BL =5 @0=55 ': 'Следующую встречу можно назначить не ранее ',
    '�  A>60;5=8N, MB>B A;>B C65 70=OB. >?@>1C9B5 2K1@0BL 4@C3>5 2@5<O.': '❌ К сожалению, этот слот уже занят. Попробуйте выбрать другое время.',
    '=� >20O 2AB@5G0': '📅 Новая встреча',
    '=� 0H8 70?;0=8@>20==K5 2AB@5G8:': '📅 Ваши запланированные встречи:',
    ' AB@5G0 CA?5H=> =07=0G5=0!': '✅ Встреча успешно назначена!',
    '=� 0B0:': '📅 Дата:',
    '� @5<O:': '🕐 Время:',
    '= K ?>;CG8B5 =0?><8=0=85 70 1 G0A 4> 2AB@5G8.': '💡 Вы получите напоминание за 1 час до встречи.',
    '� @>87>H;0 >H81:0 ?@8 =07=0G5=88 2AB@5G8. >?@>1C9B5 ?>765.': '❌ Произошла ошибка при назначении встречи. Попробуйте позже.',
    'L B<5=8BL ': '❌ Отменить ',
    '� AB@5G0 =5 =0945=0.': '❌ Встреча не найдена.',
    'L AB@5G0 >B<5=5=0': '✅ Встреча отменена',
    '>65B5 =07=0G8BL =>2CN 2AB@5GC G5@57 /schedule': 'Можете назначить новую встречу через /schedule',
    ' 0H AB0BCA 87<5=5= =0:': '✅ Ваш статус изменен на:',
    '=� <O:': '👤 Имя:',
    '<� B45;:': '🏢 Отдел:',
    '!B0BCA:': 'Статус:',
    '=� **Статистика:**': '📊 **Статистика:**',
    '• A53> 2AB@5G:': '• Всего встреч:',
    '• @>2545=>:': '• Проведено:',
    '• >A;54=OO 2AB@5G0:': '• Последняя встреча:',
    '=d **Мой профиль**': '👤 **Мой профиль**',
    '">BC': '🤖 Помощь по боту',
    'В отпуске5': 'В отпуске',
    "> 1>;L=8G=><": 'На больничном',
    " :><0=48@>2:5": 'В командировке',
    "=50:B82=>< AB0BCA5": 'неактивном статусе',
    "> 1>;L=8G=K9": 'На больничный',
    "<4": '🏖️',
    ">": '🏥',
    "": '✈️',
    "": '✅',
    "S": '❓',
}

for corrupted, fixed in corrupted_replacements.items():
    content = content.replace(corrupted, fixed)

with open('src/handlers/manager.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed src/handlers/manager.py")

# Now test again
import subprocess
result = subprocess.run(['python3', 'test_imports.py'], capture_output=True, text=True)
print("\n" + result.stdout)
if result.returncode != 0:
    print(result.stderr)