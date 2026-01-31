# tests/test_database.py
import sys
from pathlib import Path

# Добавляем корень проекта в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from src.storage.database import Database

def test_database_operations():
    """Тестирует основные операции базы данных."""
    print("🧪 Тест базы данных")
    print("-" * 40)
    
    # 1. Инициализация
    print("1. Инициализация базы...")
    db = Database(settings)
    print("   ✓ База создана")
    
    # 2. Создание сессии
    print("2. Создание сессии...")
    session_id = db.create_session(region=157, search_engine='yandex')
    print(f"   ✓ Сессия #{session_id} создана")
    
    # 3. Сохранение результатов
    print("3. Сохранение тестовых данных...")
    test_data = [
        {
            'position': 1,
            'url': 'https://test1.com',
            'title': 'Тестовый сайт 1',
            'domain': 'test1.com',
            'description': 'Описание тестового сайта 1'
        },
        {
            'position': 2,
            'url': 'https://test2.com', 
            'title': 'Тестовый сайт 2',
            'domain': 'test2.com',
            'description': 'Описание тестового сайта 2'
        }
    ]
    
    db.save_results(session_id, 'тестовый запрос', test_data)
    print("   ✓ Данные сохранены")
    
    # 4. Чтение результатов
    print("4. Чтение данных...")
    saved_data = db.get_session_results(session_id)
    print(f"   ✓ Получено {len(saved_data)} записей")
    
    # 5. Проверка целостности
    print("5. Проверка целостности данных...")
    for item in saved_data:
        assert item['session_id'] == session_id
        assert item['query'] == 'тестовый запрос'
        assert item['position'] in [1, 2]
        assert item['url'].startswith('https://')
    print("   ✓ Данные корректны")
    
    # 6. Получение последних сессий
    print("6. Получение истории...")
    last_sessions = db.get_last_sessions(3)
    print(f"   ✓ Получено {len(last_sessions)} сессий")
    
    # 7. Проверка файла базы
    db_file = Path(settings.DATABASE_URL.replace('sqlite:///', ''))
    print(f"7. Проверка файла базы...")
    print(f"   Файл: {db_file}")
    print(f"   Размер: {db_file.stat().st_size if db_file.exists() else 0} байт")
    
    print("-" * 40)
    print("✅ Все тесты пройдены успешно!")
    return True

if __name__ == "__main__":
    try:
        test_database_operations()
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
