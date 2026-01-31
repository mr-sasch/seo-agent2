# src/main.py - обновленная версия
import logging
from config.settings import settings

def setup_logging():
    """Настройка логирования для отладки парсера."""
    logging.basicConfig(
        level=logging.DEBUG,  # DEBUG для подробных логов
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.LOGS_DIR / 'seo_parser.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Тестируем только парсер."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🔍 Тестирование XMLStock парсера")
    print("=" * 50)
    
    # Импортируем парсер
    from src.parser.yandex_parser import YandexParser
    
    # Создаем экземпляр
    parser = YandexParser(settings)
    
    # Тестируем подключение
    print("\n1. Тестируем подключение к API...")
    if not parser.test_connection():
        print("❌ Не удалось подключиться к XMLStock API")
        print("   Проверьте:")
        print("   1. API ключ в .env файле")
        print("   2. Баланс на XMLStock")
        print("   3. Интернет-соединение")
        return
    
    print("✅ Подключение успешно")
    
    def load_queries():
        """Загружает запросы из файла."""
        from pathlib import Path
        queries_file = Path(__file__).parent.parent / 'config' / 'queries.txt'
        with open(queries_file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    
    # Загружаем запросы
    queries = load_queries()
    
    def load_region():
        """Читает регион из файла."""
        from pathlib import Path
        region_file = Path(__file__).parent.parent / 'config' / 'region.txt'
        with open(region_file, 'r', encoding='utf-8') as f:
            return int(f.read().strip())
    
    print(f"\n2. Парсим {len(queries)} запросов...")
    region = load_region()
    print(f"   (регион: {region}, результаты: топ-10)")
    
    try:
        results = parser.parse_queries(queries, region=region, max_results=10)
        
        # Сохраняем в базу данных
        from src.storage.database import Database
        db = Database(settings)
        session_id = db.create_session(region=region, search_engine='yandex')
        
        for query_result in results:
            db.save_results(session_id, query_result['query'], query_result['results'])
        
        print(f"💾 Данные сохранены в базу (сессия #{session_id})")
        
        print(f"\n3. Результаты парсинга:")
        print("=" * 50)
        
        for query_result in results:
            print(f"\n📋 Запрос: '{query_result['query']}'")
            print(f"   Время: {query_result['parsed_at']}")
            print(f"   Найдено результатов: {query_result['results_count']}")
            
            if query_result['results']:
                print("\n   Топ-5 результатов:")
                for i, result in enumerate(query_result['results'][:5], 1):
                    print(f"   {result['position']:2d}. {result.get('title', 'Без заголовка')[:60]}...")
                    print(f"      URL: {result['url']}")
                    print(f"      Домен: {result.get('domain', 'N/A')}")
                    
            print("-" * 50)
        
        # Сохраняем сырые данные для отладки
        import json
        debug_file = settings.LOGS_DIR / 'parser_debug.json'
        with open(debug_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Сырые данные сохранены в: {debug_file}")
        
    except Exception as e:
        logger.error(f"Критическая ошибка при парсинге: {e}", exc_info=True)
        print(f"\n❌ Ошибка: {e}")
        print("\nПроверьте логи в: seo_parser.log")

if __name__ == "__main__":
    main()