# config/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env файл
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / '.env')

class Settings:
    # API XMLStock
    XMLSTOCK_USER = os.getenv('XMLSTOCK_USER', '')
    XMLSTOCK_KEY = os.getenv('XMLSTOCK_KEY', '')
        
    # База данных
    DATABASE_URL = f"sqlite:///{BASE_DIR / 'data' / 'seo_data.db'}"
    
    # Пути
    REPORTS_DIR = BASE_DIR / 'reports'
    LOGS_DIR = BASE_DIR / 'logs'
    
    # Настройки парсинга
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    REQUEST_DELAY = 1.0  # секунд между запросами
    MAX_RESULTS_PER_QUERY = 10  # топ-10 позиций
    
    # Настройки отчетов
    REPORT_TEMPLATE = "daily_table.html"
    
    def __init__(self):
        # Создаем необходимые директории
        self.REPORTS_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)
        (BASE_DIR / 'data').mkdir(exist_ok=True)

# Глобальный экземпляр настроек
settings = Settings()