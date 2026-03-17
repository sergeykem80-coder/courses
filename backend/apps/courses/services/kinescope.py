"""
Сервис для работы с Kinescope.io API
"""
import requests
from django.conf import settings
from typing import Optional, Dict, Any


class KinescopeService:
    """
    Сервис для взаимодействия с API Kinescope.io
    Документация: https://kinescope.io/api
    """
    
    BASE_URL = "https://api.kinescope.io/2.0"
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or getattr(settings, 'KINESCOPE_API_TOKEN', None)
        if not self.api_token:
            raise ValueError("KINESCOPE_API_TOKEN не настроен в settings")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """
        Получение метаданных видео
        
        :param video_id: ID видео в Kinescope
        :return: Информация о видео
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/videos/{video_id}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка получения информации о видео: {str(e)}")
    
    def generate_embed_url(
        self, 
        video_id: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Генерация URL для iframe с параметрами
        
        :param video_id: ID видео
        :param options: Дополнительные параметры (autoplay, controls и т.д.)
        :return: URL для embed
        """
        params = {
            "autoplay": "0",
            "controls": "1",
            "preload": "metadata",
        }
        
        if options:
            params.update({k: str(v).lower() if isinstance(v, bool) else str(v) 
                          for k, v in options.items()})
        
        query_string = "&".join(f"{key}={value}" for key, value in params.items())
        return f"https://kinescope.io/embed/{video_id}?{query_string}"
    
    def generate_secure_embed_html(
        self, 
        video_id: str, 
        request=None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Генерация безопасного HTML кода для iframe
        
        :param video_id: ID видео
        :param request: Django request объект для получения домена
        :param options: Параметры плеера
        :return: HTML код iframe
        """
        embed_options = options or {}
        
        # Добавляем restriction по домену
        if request:
            embed_options['domain'] = request.get_host()
        
        embed_url = self.generate_embed_url(video_id, embed_options)
        
        html = f'''
<iframe 
  src="{embed_url}"
  frameborder="0"
  allow="autoplay; fullscreen; picture-in-picture; encrypted-media"
  allowfullscreen
  loading="lazy"
  style="width:100%; aspect-ratio:16/9; border:0;"
  referrerpolicy="strict-origin-when-cross-origin"
  title="Video lesson"
></iframe>
'''.strip()
        
        return html
    
    def upload_video(
        self, 
        file_path: str, 
        title: str, 
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Загрузка видео через API (опционально)
        Обычно загрузка происходит через веб-интерфейс Kinescope
        
        :param file_path: Путь к файлу
        :param title: Название видео
        :param description: Описание
        :return: Информация о загруженном видео
        """
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {
                    'title': title,
                    'description': description
                }
                
                response = requests.post(
                    f"{self.BASE_URL}/videos/upload",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                    files=files,
                    data=data,
                    timeout=300  # Долгий таймаут для загрузки
                )
                response.raise_for_status()
                return response.json()
                
        except FileNotFoundError:
            raise Exception(f"Файл не найден: {file_path}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка загрузки видео: {str(e)}")
    
    def delete_video(self, video_id: str) -> bool:
        """
        Удаление видео
        
        :param video_id: ID видео
        :return: True если успешно
        """
        try:
            response = requests.delete(
                f"{self.BASE_URL}/videos/{video_id}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка удаления видео: {str(e)}")
    
    @staticmethod
    def extract_video_id_from_url(url: str) -> Optional[str]:
        """
        Извлечение ID видео из URL Kinescope
        
        :param url: URL видео (например, https://kinescope.io/abc123)
        :return: ID видео или None
        """
        if not url:
            return None
        
        # Паттерны URL Kinescope
        patterns = [
            r'kinescope\.io/([a-zA-Z0-9]+)',
            r'kinescope\.io/embed/([a-zA-Z0-9]+)',
            r'kinescope\.io/player\?v=([a-zA-Z0-9]+)',
        ]
        
        import re
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None


# Глобальный экземпляр сервиса
kinescope_service = None

def get_kinescope_service() -> KinescopeService:
    """Получение экземпляра сервиса (ленивая инициализация)"""
    global kinescope_service
    if kinescope_service is None:
        kinescope_service = KinescopeService()
    return kinescope_service
