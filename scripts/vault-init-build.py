#!/usr/bin/env python3
"""
Скрипт инициализации Vault при сборке Docker контейнера.
Запускается во время build контейнера для предварительной загрузки секретов.
"""
import os
import time
import requests
import sys
from typing import Dict, Optional

def load_env_file(env_path: str = '.env') -> Dict[str, str]:
    """Загружает переменные из .env файла"""
    env_vars = {}
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        return env_vars
    except FileNotFoundError:
        print(f"Ошибка: файл {env_path} не найден")
        return {}

def wait_for_vault(vault_addr: str, timeout: int = 60) -> bool:
    """Ожидает доступности Vault"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{vault_addr}/v1/sys/health", timeout=2)
            if response.status_code in (200, 473, 501, 503):
                print(f"[OK] Vault доступен на {vault_addr}")
                return True
        except (requests.ConnectionError, requests.Timeout):
            pass
        
        elapsed = int(time.time() - start_time)
        print(f"[WAIT] Ожидание Vault... ({elapsed}s/{timeout}s)")
        time.sleep(2)
    
    print(f"[ERROR] Vault не доступен после {timeout} секунд")
    return False

def init_vault_secrets(env_vars: Dict[str, str]) -> bool:
    """Инициализирует секреты в Vault"""
    vault_addr = env_vars.get('VAULT_ADDR', 'http://localhost:8200')
    vault_token = env_vars.get('VAULT_TOKEN', 'root')
    
    headers = {
        'X-Vault-Token': vault_token,
        'Content-Type': 'application/json'
    }
    
    # Проверяем доступность Vault
    if not wait_for_vault(vault_addr, timeout=30):
        print("[WARN] Vault недоступен, инициализация пропущена")
        return False
    
    # Подготавливаем учетные данные БД
    db_credentials = {
        'data': {
            'DB_HOST': env_vars.get('DB_HOST', 'postgres'),
            'DB_PORT': env_vars.get('DB_PORT', '5432'),
            'DB_USER': env_vars.get('DB_USER'),
            'DB_PASSWORD': env_vars.get('DB_PASSWORD'),
            'DB_NAME': env_vars.get('DB_NAME'),
        }
    }
    
    # Проверяем что все поля заполнены
    if not all(db_credentials['data'].values()):
        print("[ERROR] Не все параметры БД установлены")
        return False
    
    try:
        # Сохраняем учетные данные БД
        print("[*] Сохранение учетных данных БД в Vault...")
        response = requests.post(
            f"{vault_addr}/v1/secret/data/database/credentials",
            headers=headers,
            json=db_credentials,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"[ERROR] Ошибка сохранения БД учетных данных: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        print("[OK] Учетные данные БД сохранены")
        
        # Сохраняем конфигурацию приложения
        print("[*] Сохранение конфигурации приложения...")
        app_config = {
            'data': {
                'LOG_LEVEL': env_vars.get('LOG_LEVEL', 'INFO'),
                'API_VERSION': env_vars.get('API_VERSION', '1.0.0'),
                'MODEL_PATH': '/app/models/model.pkl'
            }
        }
        
        response = requests.post(
            f"{vault_addr}/v1/secret/data/app/config",
            headers=headers,
            json=app_config,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"[WARN] Ошибка сохранения конфигурации: {response.status_code}")
        else:
            print("[OK] Конфигурация приложения сохранена")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Исключение при инициализации: {e}")
        return False

def main():
    """Основная функция"""
    print("=" * 60)
    print("Инициализация Vault при сборке контейнера")
    print("=" * 60)
    
    # Загружаем переменные
    env_vars = load_env_file('.env')
    if not env_vars:
        print("[WARN] Переменные не загружены, используются defaults")
    
    print(f"[*] Vault Address: {env_vars.get('VAULT_ADDR', 'http://localhost:8200')}")
    print(f"[*] Database: {env_vars.get('DB_NAME', 'ml_predictions')}")
    print()
    
    # Инициализируем секреты
    success = init_vault_secrets(env_vars)
    
    print()
    print("=" * 60)
    if success:
        print("[OK] Инициализация завершена успешно")
        print("=" * 60)
        return 0
    else:
        print("[WARN] Инициализация завершена с ошибками")
        print("Приложение будет использовать переменные окружения")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
