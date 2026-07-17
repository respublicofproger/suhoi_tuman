import requests
import pandas as pd
from datetime import datetime, timedelta
import io
import urllib3
import os
import json
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class VendotekDownloader:
    def __init__(self, cookie_file='vendotek_cookie.json'):
        self.base_url = "https://tms.vendotek.ru"
        self.session = requests.Session()
        self.cookie_file = cookie_file
        
        # Загружаем куку из файла или используем стандартную
        self._load_cookie()
        
        # Полные заголовки как в браузере
        self.session.headers.update({
            'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Host': 'tms.vendotek.ru',
            'Origin': 'https://tms.vendotek.ru',
            'Referer': 'https://tms.vendotek.ru/project/29/reports/TDO',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        })
    
    def _load_cookie(self):
        """Загружает куку из файла"""
        if os.path.exists(self.cookie_file):
            try:
                with open(self.cookie_file, 'r') as f:
                    config = json.load(f)
                    cookie = config.get('cookie')
                    if cookie:
                        self.session.cookies.set('tms_v3_auth_cookie', cookie)
                        self.session.cookies.set('_ym_uid', '1783533097845316583')
                        self.session.cookies.set('_ym_d', '1783533097')
                        self.session.cookies.set('_ym_isad', '2')
                        print("✅ Кука загружена из файла")
                        return
            except Exception as e:
                print(f"⚠️ Ошибка загрузки куки: {e}")
        
        # Если файла нет - используем стандартную куку
        self._set_default_cookie()
    
    def _set_default_cookie(self):
        """Устанавливает стандартную куку"""
        self.session.cookies.set('_ym_uid', '1783533097845316583')
        self.session.cookies.set('_ym_d', '1783533097')
        self.session.cookies.set('_ym_isad', '2')
        self.session.cookies.set('tms_v3_auth_cookie', 'gm1ojKUgkkwN8G92Q8kWrjHhJ5oySrcXIEAE245ujcY3KJ0sSi9PN0oJ/jXl90eOTboV/uEZ+ZVSzOrX/drE9JKvR0tHUYjYuTxoQxBC7EA=')
        print("✅ Установлена стандартная кука")
    
    def save_cookie(self, cookie_value):
        """Сохраняет новую куку в файл"""
        config = {
            'cookie': cookie_value,
            'last_updated': datetime.now().isoformat()
        }
        with open(self.cookie_file, 'w') as f:
            json.dump(config, f, indent=2)
        print("✅ Кука сохранена в файл")
    
    def download_transactions(self, org_id, from_date, to_date, max_retries=3):
        """Скачивает транзакции с повторными попытками"""
        
        filename = f"TDO_{org_id}_{from_date}_{to_date}.xlsx"
        url = f"{self.base_url}/api/v1/org/{org_id}/transactions-stream-xlsx/{filename}"
        params = {'from': from_date, 'to': to_date}
        
        for attempt in range(max_retries):
            print(f"Попытка {attempt + 1}/{max_retries}...")
            
            try:
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    print(f"✅ Успешно! Размер: {len(response.content)} байт")
                    return response.content
                elif response.status_code == 401:
                    print(f"❌ Ошибка 401 - кука не работает (попытка {attempt + 1})")
                    if attempt < max_retries - 1:
                        print("🔄 Попробуйте обновить куку в файле vendotek_cookie.json")
                else:
                    print(f"❌ Ошибка {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Исключение: {e}")
            
            import time
            time.sleep(2)
        
        return None
    
    def download_to_dataframe(self, org_id, from_date, to_date):
        """Скачивает и возвращает DataFrame"""
        data = self.download_transactions(org_id, from_date, to_date)
        if data:
            try:
                df = pd.read_excel(io.BytesIO(data))
                print(f"📊 Загружено {len(df)} транзакций")
                return df
            except Exception as e:
                print(f"❌ Ошибка чтения: {e}")
        return None