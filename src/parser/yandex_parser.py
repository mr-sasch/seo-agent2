# src/parser/yandex_parser.py
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
import time
import logging

class YandexParser:
    """
    Парсер для работы с XMLStock API и получения результатов из Яндекса.
    """
    
    def __init__(self, settings):
        self.settings = settings
        self.api_key = settings.XMLSTOCK_USER
        self.base_url = "https://xmlstock.com/yandex/xml/"
        self.logger = logging.getLogger(__name__)
        
        # Проверяем API ключ
        if not self.api_key or self.api_key.startswith('test_key'):
            self.logger.warning("Используется тестовый API ключ! Замените на реальный в .env файле")
    
    def parse_queries(self, queries: List[str], region: int = 213, 
                      max_results: int = 10) -> List[Dict]:
        """
        Парсит список поисковых запросов через XMLStock API.
        
        Args:
            queries: Список поисковых запросов
            region: Код региона Яндекса (213 - Москва)
            max_results: Максимальное количество результатов на запрос
            
        Returns:
            Список словарей с результатами для каждого запроса
        """
        self.logger.info(f"Начинаю парсинг {len(queries)} запросов для региона {region}")
        
        all_results = []
        
        for i, query in enumerate(queries, 1):
            self.logger.info(f"[{i}/{len(queries)}] Парсим запрос: '{query}'")
            
            try:
                # Парсим первую страницу выдачи
                results = self._parse_single_query(query, region, page=0, max_results=max_results)
                
                if results:
                    all_results.append({
                        'query': query,
                        'region': region,
                        'parsed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'results': results,
                        'results_count': len(results)
                    })
                    self.logger.info(f"  ✓ Получено результатов: {len(results)}")
                else:
                    self.logger.warning(f"  ✗ Нет результатов для запроса: '{query}'")
                
                # Соблюдаем задержку между запросами (если указана в настройках)
                if hasattr(self.settings, 'REQUEST_DELAY') and i < len(queries):
                    delay = self.settings.REQUEST_DELAY
                    time.sleep(delay)
                    
            except Exception as e:
                self.logger.error(f"Ошибка при парсинге запроса '{query}': {e}")
                # Продолжаем со следующим запросом
                continue
        
        self.logger.info(f"Парсинг завершен. Успешно обработано: {len(all_results)}/{len(queries)} запросов")
        return all_results
    
    def _parse_single_query(self, query: str, region: int, page: int = 0, 
                           max_results: int = 10) -> List[Dict]:
        """
        Парсит одну страницу результатов для одного запроса.
        """
        params = {
            'user': self.settings.XMLSTOCK_USER,
            'key': self.settings.XMLSTOCK_KEY,
            'query': query,
            'lr': region,  # Код региона
            'page': page,  # Номер страницы (0 - первая)
            'groupby': 'attr=d.mode%3Ddeep.groups-on-page%3D10.docs-in-group%3D1'
        }
        
        try:
            response = requests.get(
                self.base_url,
                params=params,
                headers={'User-Agent': self.settings.USER_AGENT},
                timeout=30  # 30 секунд таймаут
            )
            
            response.raise_for_status()  # Проверяем HTTP ошибки
            
            # Парсим XML
            results = self._parse_xml_response(response.content, max_results)
            return results
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Сетевая ошибка для запроса '{query}': {e}")
            return []
        except Exception as e:
            self.logger.error(f"Ошибка парсинга XML для '{query}': {e}")
            return []
    
    def _parse_xml_response(self, xml_content: bytes, max_results: int = 10) -> List[Dict]:
        """
        Парсит XML ответ от XMLStock API.
        
        Возвращает топ-N результатов с позициями и URL.
        """
        try:
            root = ET.fromstring(xml_content)
            results = []
            
            # Ищем все документы в ответе
            for i, doc in enumerate(root.findall('.//doc'), 1):
                if i > max_results:
                    break
                
                result = {
                    'position': i,
                    'url': self._get_element_text(doc, 'url'),
                    'title': self._get_element_text(doc, 'title'),
                    'domain': self._get_element_text(doc, 'domain'),
                    'headline': self._get_element_text(doc, 'headline')
                }
                
                # Очищаем URL от лишнего
                if result['url']:
                    result['url'] = result['url'].strip()
                
                results.append(result)
            
            return results
            
        except ET.ParseError as e:
            self.logger.error(f"Ошибка парсинга XML: {e}")
            return []
    
    def _get_element_text(self, element, tag_name: str, default: str = '') -> str:
        """Безопасное извлечение текста из XML элемента."""
        elem = element.find(tag_name)
        return elem.text if elem is not None and elem.text else default
    
    def test_connection(self) -> bool:
        """
        Тестирует подключение к XMLStock API.
        
        Returns:
            True если подключение успешно, False в противном случае
        """
        test_query = "тест"
        
        try:
            params = {
                'user': self.api_key,
                'query': test_query,
                'lr': 213,
                'page': 0
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("✓ Подключение к XMLStock API успешно")
                return True
            else:
                self.logger.error(f"✗ Ошибка API. Код: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"✗ Ошибка подключения: {e}")
            return False