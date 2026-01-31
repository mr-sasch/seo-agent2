# src/storage/database.py
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import logging

class Database:
    """Простое хранилище для SEO данных."""
    
    def __init__(self, settings):
        self.settings = settings
        self.db_path = Path(settings.DATABASE_URL.replace('sqlite:///', ''))
        self.logger = logging.getLogger(__name__)
        self._init_db()
    
    def _init_db(self):
        """Создает таблицы если их нет."""
        self.db_path.parent.mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица сессий парсинга
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP NOT NULL,
                    region INTEGER NOT NULL,
                    search_engine TEXT DEFAULT 'yandex'
                )
            ''')
            
            # Таблица результатов поиска
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    query TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT,
                    domain TEXT,
                    description TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (id),
                    UNIQUE(session_id, query, position)
                )
            ''')
            
            # Индексы для быстрого поиска
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_date ON sessions(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_session ON results(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_query ON results(query)')
            
            conn.commit()
        self.logger.info(f"База данных инициализирована: {self.db_path}")
    
    def create_session(self, region: int, search_engine: str = 'yandex') -> int:
        """Создает новую сессию парсинга и возвращает её ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO sessions (created_at, region, search_engine) VALUES (?, ?, ?)',
                (datetime.now(), region, search_engine)
            )
            session_id = cursor.lastrowid
            conn.commit()
        
        self.logger.info(f"Создана сессия #{session_id} для региона {region}")
        return session_id
    
    def save_results(self, session_id: int, query: str, results: List[Dict]):
        """Сохраняет результаты для одного запроса в сессии."""
        if not results:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for result in results:
                cursor.execute('''
                    INSERT OR REPLACE INTO results 
                    (session_id, query, position, url, title, domain, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    query,
                    result['position'],
                    result['url'],
                    result.get('title', ''),
                    result.get('domain', ''),
                    result.get('description', '')
                ))
            
            conn.commit()
        
        self.logger.debug(f"Сохранено {len(results)} результатов для запроса '{query}'")
    
    def get_session_results(self, session_id: int) -> List[Dict]:
        """Возвращает все результаты сессии."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM results 
                WHERE session_id = ? 
                ORDER BY query, position
            ''', (session_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_last_sessions(self, limit: int = 10) -> List[Dict]:
        """Возвращает последние сессии."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM sessions 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_query_history(self, query: str, limit_sessions: int = 5) -> List[Dict]:
        """История позиций для запроса."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT r.*, s.created_at 
                FROM results r
                JOIN sessions s ON r.session_id = s.id
                WHERE r.query = ?
                ORDER BY s.created_at DESC, r.position
                LIMIT ?
            ''', (query, limit_sessions * 20))  # примерно 20 позиций на сессию
            
            return [dict(row) for row in cursor.fetchall()]