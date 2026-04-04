#!/usr/bin/env python3
"""
Скрипт запуска FlurAI
Проверяет зависимости и запускает приложение
"""

import sys
import subprocess
import os

def check_dependencies():
    """Проверка установленных зависимостей"""
    required_packages = [
        'customtkinter',
        'Pillow',
        'tkinter'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Отсутствуют необходимые пакеты:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Установите их командой:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ Все зависимости установлены")
    return True

def main():
    """Главная функция запуска"""
    print("🚀 Запуск FlurAI - Система анализа флюорографии")
    print("=" * 50)
    
    # Проверяем зависимости
    if not check_dependencies():
        sys.exit(1)
    
    # Запускаем приложение
    try:
        from main import FlurAIApp
        app = FlurAIApp()
        print("✅ Приложение запущено успешно")
        app.run()
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


