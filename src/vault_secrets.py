"""
Модуль для управления секретами через HashiCorp Vault
"""
import os
import json
import requests
from typing import Optional, Dict, Any
from src.logger import Logger

logger = Logger(True).get_logger(__name__)


class VaultSecrets:
    """Клиент для работы с хранилищем секретов Vault"""
    
    def __init__(self):
        self.vault_addr = os.getenv('VAULT_ADDR', 'http://localhost:8200')
        self.vault_token = os.getenv('VAULT_TOKEN')
        self.use_vault = os.getenv('USE_VAULT', 'true').lower() in ('true', '1', 'yes')
        self.vault_required = self.use_vault

        if self.vault_required and not self.vault_token:
            raise RuntimeError("VAULT_TOKEN должен быть задан при USE_VAULT=true")
        self.headers = {
            'X-Vault-Token': self.vault_token,
            'Content-Type': 'application/json'
        }
        
        if self.use_vault:
            self._verify_connection()
    
    def _verify_connection(self) -> bool:
        """Проверка подключения к Vault"""
        try:
            response = requests.get(
                f"{self.vault_addr}/v1/sys/health",
                timeout=5
            )
            if response.status_code in (200, 473, 501, 503):
                logger.info("Успешное подключение к Vault")
                return True
        except Exception as e:
            logger.error(f"Не удалось подключиться к Vault: {e}")
            self.use_vault = False
            return False
        return False
    
    def store_secret(self, path: str, secret_data: Dict[str, Any]) -> bool:
        """Сохранить секрет в Vault"""
        if not self.use_vault:
            logger.debug("Vault отключен, сохранение пропущено")
            return False
        
        try:
            response = requests.post(
                f"{self.vault_addr}/v1/secret/data/{path}",
                headers=self.headers,
                json={"data": secret_data},
                timeout=5
            )
            if response.status_code == 200:
                logger.info(f"Секрет сохранён в Vault по пути: {path}")
                return True
            else:
                logger.error(f"Ошибка сохранения секрета: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Ошибка при сохранении секрета: {e}")
            return False
    
    def get_secret(self, path: str) -> Optional[Dict[str, Any]]:
        """Получить секрет из Vault"""
        if not self.use_vault:
            logger.debug("Vault отключен, возврат None")
            return None
        
        try:
            response = requests.get(
                f"{self.vault_addr}/v1/secret/data/{path}",
                headers=self.headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Секрет получен из Vault: {path}")
                return data.get('data', {}).get('data', {})
            elif response.status_code == 404:
                logger.warning(f"Секрет не найден в Vault: {path}")
                return None
            else:
                logger.error(f"Ошибка получения секрета: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении секрета: {e}")
            return None
    
    def get_db_credentials(self) -> Dict[str, str]:
        """Получить учетные данные БД из Vault или переменных окружения"""
        credentials = {
            'host': 'localhost',
            'port': '5432',
            'user': None,
            'password': None,
            'database': None,
        }
        
        # Сначала пытаемся получить из Vault
        if self.use_vault:
            vault_secret = self.get_secret("database/credentials")
            if vault_secret:
                logger.info("Учетные данные БД получены из Vault")
                return {
                    'host': vault_secret.get('DB_HOST', credentials['host']),
                    'port': vault_secret.get('DB_PORT', credentials['port']),
                    'user': vault_secret.get('DB_USER'),
                    'password': vault_secret.get('DB_PASSWORD'),
                    'database': vault_secret.get('DB_NAME'),
                }
        
        if self.vault_required:
            raise RuntimeError("Учетные данные БД не удалось получить из Vault")

        # Явный режим без Vault используется только для изолированных тестов
        logger.info("Учетные данные БД получены из переменных окружения")
        return {
            'host': os.getenv('DB_HOST', credentials['host']),
            'port': os.getenv('DB_PORT', credentials['port']),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME'),
        }
    
    def get_api_secret(self, secret_name: str) -> Optional[str]:
        """Получить секрет API (например, ключ доступа)"""
        if self.use_vault:
            vault_secret = self.get_secret(f"api/secrets/{secret_name}")
            if vault_secret:
                return vault_secret.get('value')
        
        # Fallback на переменные окружения
        return os.getenv(f"API_{secret_name.upper()}")
    
    def list_secrets(self, path: str) -> Optional[list]:
        """Получить список всех секретов в пути"""
        if not self.use_vault:
            return None
        
        try:
            response = requests.request(
                'LIST',
                f"{self.vault_addr}/v1/secret/metadata/{path}",
                headers=self.headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                keys = data.get('data', {}).get('keys', [])
                logger.info(f"Получен список секретов из {path}: {keys}")
                return keys
            else:
                logger.warning(f"Ошибка получения списка секретов: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении списка: {e}")
            return None
    
    def delete_secret(self, path: str) -> bool:
        """Удалить секрет из Vault"""
        if not self.use_vault:
            return False
        
        try:
            response = requests.delete(
                f"{self.vault_addr}/v1/secret/data/{path}",
                headers=self.headers,
                timeout=5
            )
            if response.status_code == 204:
                logger.info(f"Секрет удален из Vault: {path}")
                return True
            else:
                logger.error(f"Ошибка удаления секрета: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Ошибка при удалении секрета: {e}")
            return False


# Глобальный экземпляр для удобства
vault_client = VaultSecrets()
