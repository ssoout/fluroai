#!/usr/bin/env python3
"""
Скрипт проверки установки FlurAI
Проверяет все необходимые зависимости
"""

import sys
import importlib

def check_python_version():
    """Проверка версии Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"ОШИБКА: Требуется Python 3.8+, установлена версия {version.major}.{version.minor}")
        return False
    print(f"OK Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_required_packages():
    """Проверка необходимых пакетов"""
    required_packages = {
        'tkinter': 'Стандартная библиотека Python',
        'customtkinter': 'pip install customtkinter',
        'PIL': 'pip install Pillow'
    }
    
    missing_packages = []
    
    for package, install_cmd in required_packages.items():
        try:
            if package == 'PIL':
                importlib.import_module('PIL')
            else:
                importlib.import_module(package)
            print(f"OK {package}")
        except ImportError:
            print(f"ОШИБКА {package} - {install_cmd}")
            missing_packages.append((package, install_cmd))
    
    return missing_packages

def check_optional_packages():
    """Проверка опциональных пакетов"""
    optional_packages = {
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'matplotlib': 'matplotlib',
        'pandas': 'pandas',
        'plotly': 'plotly'
    }
    
    print("\nОпциональные пакеты:")
    for package, pip_name in optional_packages.items():
        try:
            importlib.import_module(package)
            print(f"OK {package}")
        except ImportError:
            print(f"НЕТ {package} - pip install {pip_name}")

def main():
    """Главная функция проверки"""
    print("Проверка установки FlurAI")
    print("=" * 40)
    
    # Проверка Python
    if not check_python_version():
        sys.exit(1)
    
    # Проверка необходимых пакетов
    print("\nНеобходимые пакеты:")
    missing = check_required_packages()
    
    if missing:
        print(f"\nОтсутствуют {len(missing)} необходимых пакетов")
        print("Установите их командой:")
        for package, cmd in missing:
            print(f"   {cmd}")
        print("\nИли используйте: pip install -r requirements-minimal.txt")
        sys.exit(1)
    
    # Проверка опциональных пакетов
    check_optional_packages()
    
    print("\nВсе необходимые зависимости установлены!")
    print("Можете запускать: python main.py")

if __name__ == "__main__":
    main()
