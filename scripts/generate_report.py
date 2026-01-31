# scripts/generate_report.py
import sys
from pathlib import Path

# КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent  # Поднимаемся на уровень выше scripts/
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.reporting.html_builder import HTMLBuilder

def main():
    """Генерация отчета из существующих данных в базе."""
    print("📊 Генерация SEO отчета из базы данных")
    print("=" * 50)
    
    # Создаем генератор отчетов
    reporter = HTMLBuilder(settings)
    
    # Генерируем отчет за 2 последних дня
    report_path = reporter.generate_report(days_back=0)
    
    if report_path:
        print(f"✅ Отчет успешно создан:")
        print(f"   Файл: {report_path}")
        
        # Опционально: открываем в браузере
        import webbrowser
        import os
        if os.path.exists(report_path):
            webbrowser.open(f"file://{os.path.abspath(report_path)}")
            print("   Отчет открыт в браузере")
    else:
        print("❌ Не удалось создать отчет")
        print("   Возможные причины:")
        print("   1. Нет данных в базе")
        print("   2. База данных недоступна")
        print("   3. Ошибка в конфигурации")

if __name__ == "__main__":
    main()
