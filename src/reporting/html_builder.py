# src/reporting/html_builder.py
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import logging
from src.storage.database import Database

class HTMLBuilder:
    """Генератор HTML отчетов в формате таблицы."""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
    
    def generate_report(self, days_back: int = 2) -> str:
        """
        Генератор HTML отчетов за последние N дней.
        
        Args:
            days_back: количество дней для отчета
            
        Returns:
            Путь к созданному HTML файлу
        """
        self.logger.info(f"Генерация отчета за последние {days_back} дней")
        
        # Получаем данные из базы
        db = Database(self.settings)
        
        # Получаем последние сессии
        sessions = self._get_last_sessions(db, days_back)
        if not sessions:
            self.logger.warning("Нет данных для отчета")
            return None
        
        # Получаем все запросы
        queries = self._get_all_queries(db)
        
        # Формируем данные для таблицы
        table_data = self._prepare_table_data(db, sessions, queries)
        
        # Генерация HTML
        html_content = self._build_html(sessions, queries, table_data)
        
        # Сохраняем файл
        report_path = self._save_html(html_content)
        
        return report_path
    
    def _get_last_sessions(self, db: 'Database', days_back: int) -> List[Dict]:
        """Получает последние сессии за указанное количество дней."""
        # Берем все сессии (или большой лимит)
        all_sessions = db.get_last_sessions(limit=100)
        
        # Сортируем от новых к старым
        sorted_sessions = sorted(
            all_sessions,
            key=lambda x: x['created_at'],
            reverse=True
        )
        
        # Если нужны сессии за последние N дней
        if days_back > 0:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            recent_sessions = []
            for session in sorted_sessions:
                session_date = datetime.strptime(session['created_at'], '%Y-%m-%d %H:%M:%S.%f')
                if session_date >= cutoff_date:
                    recent_sessions.append(session)
            return recent_sessions
        
        # Или все сессии
        return sorted_sessions
    
    def _get_all_queries(self, db: 'Database') -> List[str]:
        """Получает все уникальные запросы из базы."""
        # В простой реализации - читаем из файла queries.txt
        queries_file = Path(__file__).parent.parent.parent / 'config' / 'queries.txt'
        with open(queries_file, 'r', encoding='utf-8') as f:
            queries = [line.strip() for line in f if line.strip()]
        
        return queries
    
    def _prepare_table_data(self, db: 'Database', sessions: List[Dict], queries: List[str]) -> Dict:
        """Подготавливает данные для таблицы."""
        table_data = {}
        
        for query in queries:
            table_data[query] = {}
            
            for session in sessions:
                session_id = session['id']
                date_key = session['created_at']  # Полная дата-время (с миллисекундами)
                
                # Получаем результаты для этого запроса и сессии
                all_results = db.get_session_results(session_id)
                query_results = [r for r in all_results if r['query'] == query]
                
                # Ограничиваем 10 результатами
                table_data[query][date_key] = query_results[:10]
        
        return table_data
    
    def _build_html(self, sessions: List[Dict], queries: List[str], table_data: Dict) -> str:
        """Создает HTML контент на основе вашего шаблона."""
        
        # Подготавливаем даты для заголовков
        date_headers = []
        for session in sessions:
            # Парсим полную дату-время из базы
            session_dt = datetime.strptime(session['created_at'], '%Y-%m-%d %H:%M:%S.%f')
            # Форматируем как "2024-01-31<br>14:30"
            formatted_header = f"{session_dt.strftime('%Y-%m-%d')}<br>{session_dt.strftime('%H:%M')}"
            date_headers.append(formatted_header)
        
        # Подготавливаем статистику
        # Вычисляем количество уникальных дней
        unique_dates = set()
        for session in sessions:
            date_only = session['created_at'].split()[0]  # Берем только дату
            unique_dates.add(date_only)
        
        stats = {
            'keywords_count': len(queries),
            'sessions_count': len(sessions),  # Количество проверок
            'days_count': len(unique_dates),  # Количество дней
            'domains_in_top10': 0,
        }
        
        # Генерируем строки таблицы
        table_rows = ""
        for i, query in enumerate(queries):
            # Уникальные домены для этого запроса
            all_domains = set()
            for date_results in table_data[query].values():
                for result in date_results:
                    all_domains.add(result.get('domain', ''))
            
            row_class = "even" if i % 2 == 0 else "odd"
            
            # Начинаем строку
            table_rows += f"""
                    <tr class="{row_class}">
                        <td class="keyword-cell">
                            <div style="font-weight: 500;">{query}</div>
                            <div style="font-size: 11px; color: #6c757d; margin-top: 4px;">
                                Последняя проверка: {datetime.now().strftime('%Y-%m-%d')}<br>
                                Уникальных доменов: {len(all_domains)}
                            </div>
                        </td>"""
            
            # Добавляем ячейки с данными для каждой даты
            for session, date_header in zip(sessions, date_headers):
                # Берем оригинальную дату из сессии (без времени) для поиска в table_data
                date_key = session['created_at']
                results = table_data[query].get(date_key, [])
                
                table_rows += f"""
                        <td>
                            <div class="competitor-list">"""
                
                if results:
                    for result in results:
                        position = result['position']
                        domain = result.get('domain', '')
                        url = result.get('url', '')
                        title = result.get('title', '')[:100] + "..." if len(result.get('title', '')) > 100 else result.get('title', '')
                        short_url = (url[:60] + "...") if len(url) > 60 else url
                        
                        position_class = ""
                        if position == 1:
                            position_class = "position-1"
                        elif position == 2:
                            position_class = "position-2"
                        elif position == 3:
                            position_class = "position-3"
                        
                        # Определяем CSS класс для подсветки целевого домена
                        target_domain_class = ""
                        if domain and 'aquamoney.by' in domain.lower():
                            target_domain_class = "target-domain"
                        
                        table_rows += f"""
                                <div class="competitor-item {position_class}">
                                    <span class="position-badge">{position}</span>
                                    <span style="font-weight: 500;" class="{target_domain_class}">{domain}</span>
                                    <a href="{url}" target="_blank" class="competitor-url" title="{url}">
                                        {short_url}
                                    </a>"""
                        
                        if title:
                            table_rows += f"""
                                    <span class="competitor-title" title="{title}">{title}</span>"""
                        
                        table_rows += """
                                </div>"""
                else:
                    table_rows += """
                                <div class="empty-cell">Нет данных</div>"""
                
                table_rows += """
                            </div>
                        </td>"""
            
            table_rows += """
                    </tr>"""
        
        # Собираем полный HTML
        html_template = self._get_html_template()
        html_content = html_template.format(
            report_date=datetime.now().strftime('%d.%m.%Y %H:%M'),
            days_count=stats['days_count'],
            sessions_count=stats['sessions_count'],
            keywords_count=stats['keywords_count'],
            date_headers="\n                        ".join(
                [f'<th class="date-header">{date}</th>' for date in date_headers]
            ),
            table_rows=table_rows
        )
        
        return html_content
    
    def _get_html_template(self) -> str:
        """Возвращает шаблон HTML (ваш статический шаблон с заменяемыми полями)."""
        return """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Мониторинг конкурентов</title>
    <link rel="stylesheet" href="../src/reporting/style.css">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏆 SEO Мониторинг конкурентов</h1>
            <div class="subtitle">Мониторинг позиций в поисковой выдаче</div>
            <div class="meta">
                <div>📅 Дата отчета: {report_date}</div>
                <div>📊 Период: {days_count} дней</div>
                <div>🔑 Ключевых слов: {keywords_count}</div>
                <div>🔄 Проверок: {sessions_count}</div>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">{keywords_count}</div>
                <div class="stat-label">Ключевых слов</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{sessions_count}</div>
                <div class="stat-label">Проверок</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{days_count}</div>
                <div class="stat-label">Дней отслеживания</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">0</div>
                <div class="stat-label">Наш домен в топ-10</div>
            </div>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th class="keyword-cell">Ключевое слово</th>
                        {date_headers}
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <div>Отчет сгенерирован SEO-агентом • {report_date}</div>
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #28a745;"></div>
                    <span>1-я позиция</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #20c997;"></div>
                    <span>2-я позиция</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #17a2b8;"></div>
                    <span>3-я позиция</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #6c757d;"></div>
                    <span>4-10 позиции</span>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Скрипт для улучшения взаимодействия
        document.addEventListener('DOMContentLoaded', function() {{
            // Прокрутка внутри ячеек
            const competitorLists = document.querySelectorAll('.competitor-list');
            competitorLists.forEach(list => {{
                list.addEventListener('wheel', function(e) {{
                    if (e.deltaY !== 0) {{
                        this.scrollTop += e.deltaY;
                        e.preventDefault();
                    }}
                }});
            }});
            
            // Подсветка при наведении на конкурента
            document.querySelectorAll('.competitor-item').forEach(item => {{
                item.addEventListener('mouseenter', function() {{
                    const position = this.querySelector('.position-badge').textContent;
                    // Можно добавить дополнительную логику здесь
                }});
            }});
        }});
    </script>
</body>
</html>"""
    
    def _save_html(self, html_content: str) -> str:
        """Сохраняет HTML контент в файл."""
        report_filename = f"seo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        report_path = self.settings.REPORTS_DIR / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"HTML отчет сохранен: {report_path}")
        return str(report_path)