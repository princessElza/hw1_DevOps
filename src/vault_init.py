"""
Инициализация секретов в Vault при запуске приложения
"""
import os
import time
from src.vault_secrets import vault_client
from src.logger import Logger

logger = Logger(True).get_logger(__name__)


def init_vault_secrets():
    """
    Инициализирует секреты в Vault при первом запуске приложения.
    Если Vault недоступен, использует переменные окружения.
    """
    if not vault_client.use_vault:
        logger.info("Vault отключен, инициализация пропущена")
        return False
    
    logger.info("Начало инициализации Vault секретов...")
    
    # Получаем учетные данные из переменных окружения
    db_credentials = {
        'DB_HOST': os.getenv('DB_HOST', 'postgres'),
        'DB_PORT': os.getenv('DB_PORT', '5432'),
        'DB_USER': os.getenv('DB_USER'),
        'DB_PASSWORD': os.getenv('DB_PASSWORD'),
        'DB_NAME': os.getenv('DB_NAME'),
    }
    
    # Проверяем что все значения установлены
    if not all([db_credentials['DB_USER'], db_credentials['DB_PASSWORD'], db_credentials['DB_NAME']]):
        logger.warning("Некоторые учетные данные БД не установлены в переменных окружения")
        return False
    
    # Пытаемся сохранить в Vault
    max_retries = 5
    for attempt in range(max_retries):
        try:
            success = vault_client.store_secret('database/credentials', db_credentials)
            if success:
                logger.info("Секреты БД успешно сохранены в Vault")
                
                # Сохраняем конфигурацию приложения
                app_config = {
                    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
                    'API_VERSION': '1.0.0',
                    'MODEL_PATH': '/app/models/model.pkl'
                }
                vault_client.store_secret('app/config', app_config)
                logger.info("Конфигурация приложения сохранена в Vault")
                
                return True
        except Exception as e:
            logger.warning(f"Попытка сохранения {attempt + 1}/{max_retries} не удалась: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    logger.error("Не удалось сохранить секреты в Vault после нескольких попыток")
    return False


def verify_vault_secrets():
    """
    Проверяет наличие необходимых секретов в Vault.
    Используется для диагностики при проблемах подключения.
    """
    if not vault_client.use_vault:
        logger.debug("Vault отключен, проверка пропущена")
        return True
    
    logger.debug("Проверка секретов в Vault...")
    
    # Проверяем наличие учетных данных БД
    db_creds = vault_client.get_secret("database/credentials")
    if db_creds:
        logger.debug("Учетные данные БД найдены в Vault")
        return True
    else:
        logger.warning("Учетные данные БД не найдены в Vault")
        return False


if __name__ == "__main__":
    init_vault_secrets()
    verify_vault_secrets()
