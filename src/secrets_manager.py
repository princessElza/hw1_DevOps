"""
Утилита для управления секретами в Vault
Позволяет сохранять, получать и удалять секреты
"""
import os
import json
from src.vault_secrets import vault_client
from src.logger import Logger

logger = Logger(True).get_logger(__name__)


def initialize_db_credentials():
    """Инициализировать учетные данные БД в Vault"""
    db_credentials = {
        'DB_HOST': os.getenv('DB_HOST', 'postgres'),
        'DB_PORT': os.getenv('DB_PORT', '5432'),
        'DB_USER': os.getenv('DB_USER'),
        'DB_PASSWORD': os.getenv('DB_PASSWORD'),
        'DB_NAME': os.getenv('DB_NAME'),
    }
    
    # Проверяем, что все значения заполнены
    if all(db_credentials.values()):
        success = vault_client.store_secret('database/credentials', db_credentials)
        if success:
            logger.info("Учетные данные БД сохранены в Vault")
            return True
    else:
        logger.warning("Некоторые учетные данные БД не установлены")
    return False


def store_api_secret(secret_name: str, secret_value: str) -> bool:
    """Сохранить секрет API (например, ключ доступа)"""
    secret_data = {'value': secret_value}
    success = vault_client.store_secret(f'api/secrets/{secret_name}', secret_data)
    if success:
        logger.info(f"API секрет '{secret_name}' сохранен в Vault")
    return success


def get_api_secret(secret_name: str) -> str:
    """Получить секрет API"""
    secret = vault_client.get_api_secret(secret_name)
    if secret:
        logger.info(f"API секрет '{secret_name}' получен из Vault")
    else:
        logger.warning(f"API секрет '{secret_name}' не найден")
    return secret


def list_api_secrets() -> list:
    """Получить список всех API секретов"""
    secrets = vault_client.list_secrets('api/secrets')
    if secrets:
        logger.info(f"Получен список API секретов: {secrets}")
    return secrets or []


def verify_vault_connection() -> bool:
    """Проверить подключение к Vault"""
    if vault_client.use_vault:
        logger.info("Vault включен и доступен")
        return True
    else:
        logger.warning("Vault отключен или недоступен, используются переменные окружения")
        return False


def print_secrets_info():
    """Вывести информацию о текущих секретах (без значений)"""
    print("\n=== Информация о хранилище секретов ===")
    print(f"Статус Vault: {'Включен' if vault_client.use_vault else 'Отключен'}")
    print(f"Адрес Vault: {vault_client.vault_addr}")
    
    if vault_client.use_vault:
        api_secrets = list_api_secrets()
        if api_secrets:
            print(f"\nВозможные API секреты: {', '.join(api_secrets)}")
        else:
            print("\nAPI секреты не найдены")
    else:
        print("\nИспользуются переменные окружения для конфигурации")


if __name__ == "__main__":
    print("Инициализация хранилища секретов...")
    
    # Проверяем подключение
    if verify_vault_connection():
        # Инициализируем учетные данные БД
        initialize_db_credentials()
    
    # Выводим информацию
    print_secrets_info()
