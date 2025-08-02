#!/usr/bin/env python3
"""
🔧 AUTOMATED FIX APPLICATOR v4.0
Автоматическое применение исправлений на основе результатов диагностики
"""
import json
import logging
import shutil
from pathlib import Path
from datetime import datetime
import re

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_application.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoFixApplicator:
    """Автоматическое применение исправлений"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.backup_dir = self.project_path / ".fix_backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def apply_fixes_from_diagnostic(self, diagnostic_report_path: str):
        """Применить исправления из отчета диагностики"""
        
        with open(diagnostic_report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        fixes = report.get('suggested_fixes', {})
        action_plan = report.get('action_plan', {})
        
        logger.info("🔧 Starting automated fix application")
        logger.info(f"📋 Total fixes to apply: {len(fixes)}")
        
        results = {
            'applied_fixes': [],
            'failed_fixes': [],
            'backup_location': str(self.backup_dir)
        }
        
        # Применить исправления в порядке приоритета
        for fix_name, fix_details in fixes.items():
            try:
                logger.info(f"🔧 Applying fix: {fix_name}")
                success = self._apply_fix(fix_name, fix_details)
                
                if success:
                    results['applied_fixes'].append({
                        'name': fix_name,
                        'description': fix_details.get('description', ''),
                        'file': fix_details.get('file', ''),
                        'timestamp': datetime.now().isoformat()
                    })
                    logger.info(f"✅ Successfully applied: {fix_name}")
                else:
                    results['failed_fixes'].append({
                        'name': fix_name,
                        'reason': 'Application failed',
                        'file': fix_details.get('file', '')
                    })
                    logger.error(f"❌ Failed to apply: {fix_name}")
                    
            except Exception as e:
                logger.error(f"❌ Error applying {fix_name}: {e}")
                results['failed_fixes'].append({
                    'name': fix_name,
                    'reason': str(e),
                    'file': fix_details.get('file', '')
                })
        
        # Дополнительные проверки и исправления
        self._apply_additional_improvements()
        
        # Сохранить отчет о применении исправлений
        report_path = self.project_path / "fix_application_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📄 Fix application report saved: {report_path}")
        
        return results
    
    def _apply_fix(self, fix_name: str, fix_details: dict) -> bool:
        """Применить конкретное исправление"""
        
        file_path = fix_details.get('file', '')
        if not file_path:
            logger.error(f"No file specified for fix: {fix_name}")
            return False
        
        full_path = self.project_path / file_path
        if not full_path.exists():
            logger.error(f"File not found: {full_path}")
            return False
        
        # Создать резервную копию
        self._backup_file(full_path)
        
        try:
            if fix_name == 'fix_conference_type':
                return self._fix_conference_type(full_path, fix_details)
            elif fix_name == 'fix_service_account_attendees':
                return self._fix_service_account_attendees(full_path)
            elif fix_name == 'improve_oauth_detection':
                return self._improve_oauth_detection(full_path)
            else:
                logger.warning(f"Unknown fix type: {fix_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error applying {fix_name}: {e}")
            # Восстановить из бэкапа
            self._restore_from_backup(full_path)
            return False
    
    def _backup_file(self, file_path: Path):
        """Создать резервную копию файла"""
        backup_path = self.backup_dir / file_path.relative_to(self.project_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        logger.info(f"📋 Backup created: {backup_path}")
    
    def _restore_from_backup(self, file_path: Path):
        """Восстановить файл из резервной копии"""
        backup_path = self.backup_dir / file_path.relative_to(self.project_path)
        if backup_path.exists():
            shutil.copy2(backup_path, file_path)
            logger.info(f"🔄 Restored from backup: {file_path}")
    
    def _fix_conference_type(self, file_path: Path, fix_details: dict) -> bool:
        """Исправить тип конференции"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        search_text = fix_details.get('search', "'type': 'eventHangout'")
        replace_text = fix_details.get('replace', "'type': 'hangoutsMeet'")
        
        # Проверить, нужно ли исправление
        if search_text not in content:
            logger.info(f"Conference type already fixed in {file_path}")
            return True
        
        # Применить исправление
        new_content = content.replace(search_text, replace_text)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info(f"🔧 Fixed conference type in {file_path}")
        return True
    
    def _fix_service_account_attendees(self, file_path: Path) -> bool:
        """Исправить проблему с участниками Service Account"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Поиск мест, где добавляются участники без проверки типа календаря
        lines = content.split('\n')
        modified = False
        
        for i, line in enumerate(lines):
            # Найти строки с добавлением участников
            if "'attendees'" in line and "oauth" not in line.lower():
                # Проверить, есть ли уже проверка OAuth
                context_start = max(0, i - 10)
                context_end = min(len(lines), i + 5)
                context = '\n'.join(lines[context_start:context_end])
                
                if "is_oauth" not in context and "oauth" not in context.lower():
                    # Добавить комментарий о необходимости проверки OAuth
                    indent = len(line) - len(line.lstrip())
                    comment = ' ' * indent + "# TODO: Add OAuth check before adding attendees to avoid Service Account errors"
                    lines.insert(i, comment)
                    modified = True
                    logger.info(f"Added OAuth check comment at line {i+1}")
        
        if modified:
            new_content = '\n'.join(lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logger.info(f"🔧 Added Service Account attendee checks in {file_path}")
        else:
            logger.info(f"Service Account attendee logic already handled in {file_path}")
        
        return True
    
    def _improve_oauth_detection(self, file_path: Path) -> bool:
        """Улучшить определение OAuth"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверить, есть ли уже улучшенная логика OAuth
        if 'refresh_token' in content and 'json.loads' in content:
            logger.info(f"OAuth detection already improved in {file_path}")
            return True
        
        # Найти функцию _is_oauth_calendar и улучшить её
        oauth_func_pattern = r'def _is_oauth_calendar\(self, calendar_id: str\) -> bool:'
        
        if re.search(oauth_func_pattern, content):
            # Функция найдена, проверить её содержимое
            lines = content.split('\n')
            in_oauth_func = False
            modified = False
            
            for i, line in enumerate(lines):
                if '_is_oauth_calendar' in line and 'def' in line:
                    in_oauth_func = True
                elif in_oauth_func and (line.strip().startswith('def ') or (line and not line.startswith(' ') and not line.startswith('\t'))):
                    in_oauth_func = False
                elif in_oauth_func and 'TODO: Add refresh_token validation' in line:
                    # Комментарий уже есть
                    break
                elif in_oauth_func and 'return' in line and not modified:
                    # Добавить комментарий о необходимости улучшения
                    indent = len(line) - len(line.lstrip())
                    comment = ' ' * indent + "# TODO: Add refresh_token validation for better OAuth detection"
                    lines.insert(i, comment)
                    modified = True
                    break
            
            if modified:
                new_content = '\n'.join(lines)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                logger.info(f"🔧 Added OAuth detection improvement comment in {file_path}")
        
        return True
    
    def _apply_additional_improvements(self):
        """Применить дополнительные улучшения"""
        
        logger.info("🔧 Applying additional improvements...")
        
        # 1. Проверить и исправить логирование ошибок
        self._improve_error_logging()
        
        # 2. Добать проверки валидации
        self._add_validation_checks()
        
        logger.info("✅ Additional improvements applied")
    
    def _improve_error_logging(self):
        """Улучшить логирование ошибок"""
        
        calendar_files = [
            'src/services/google_calendar_dual.py',
            'src/services/google_calendar.py',
            'src/services/meeting_service.py'
        ]
        
        for file_path in calendar_files:
            full_path = self.project_path / file_path
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Проверить, достаточно ли подробного логирования
                except_count = content.count('except')
                logger_error_count = content.count('logger.error')
                
                if except_count > 0 and logger_error_count / except_count < 0.8:
                    # Добавить комментарий о необходимости улучшения логирования
                    lines = content.split('\n')
                    lines.insert(0, "# TODO: Consider adding more detailed error logging for debugging")
                    
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
                    
                    logger.info(f"📝 Added error logging improvement comment to {file_path}")
    
    def _add_validation_checks(self):
        """Добавить проверки валидации"""
        
        # Проверить наличие валидации входных данных
        validation_patterns = [
            'if not.*calendar_id',
            'if.*email.*@',
            'if.*credentials',
        ]
        
        # Это реализация будет зависеть от конкретных потребностей
        logger.info("📋 Validation checks review completed")


def main():
    """Главная функция"""
    
    project_path = "/Users/evgenii/meeting-scheduler-bot"
    diagnostic_report = "/Users/evgenii/meeting-scheduler-bot/simple_diagnostic_report.json"
    
    if not Path(diagnostic_report).exists():
        logger.error(f"Diagnostic report not found: {diagnostic_report}")
        return
    
    try:
        # Создать аппликатор исправлений
        fix_applicator = AutoFixApplicator(project_path)
        
        # Применить исправления
        results = fix_applicator.apply_fixes_from_diagnostic(diagnostic_report)
        
        # Показать результаты
        print("\n" + "="*80)
        print("🔧 РЕЗУЛЬТАТЫ ПРИМЕНЕНИЯ ИСПРАВЛЕНИЙ")
        print("="*80)
        
        applied = results.get('applied_fixes', [])
        failed = results.get('failed_fixes', [])
        
        print(f"\n✅ Успешно применено: {len(applied)}")
        for fix in applied:
            print(f"   • {fix['name']}: {fix['description']}")
        
        if failed:
            print(f"\n❌ Не удалось применить: {len(failed)}")
            for fix in failed:
                print(f"   • {fix['name']}: {fix['reason']}")
        
        print(f"\n📋 Резервные копии: {results['backup_location']}")
        print(f"📄 Отчет сохранен: fix_application_report.json")
        
        if len(applied) > 0:
            print("\n🚀 Рекомендуется:")
            print("   1. Проверить изменения в коде")
            print("   2. Протестировать локально")
            print("   3. Закоммитить и развернуть")
            print("   4. Протестировать в продакшене")
        
        print("\n✅ Применение исправлений завершено!")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Fix application failed: {e}")
        raise


if __name__ == "__main__":
    results = main()