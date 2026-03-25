#!/usr/bin/env python3
"""
Демонстрационный скрипт FlurAI
Показывает основные возможности системы
"""

import sys
import os

def show_demo_info():
    """Показ информации о демо-режиме"""
    print("🎯 FlurAI - Демонстрационный режим")
    print("=" * 50)
    print()
    print("📋 Доступные роли:")
    print("   👨‍⚕️ Врач-рентгенолог")
    print("      - Работа со снимками")
    print("      - Управление пациентами")
    print("      - Персональная статистика")
    print()
    print("   👨‍💼 Администратор")
    print("      - Управление врачами")
    print("      - Аналитика и отчеты")
    print("      - Настройки системы")
    print()
    print("🔑 Данные для входа:")
    print("   Врач:     логин 'doctor', пароль '123'")
    print("   Админ:    логин 'admin', пароль '123'")
    print("   Демо:     кнопка 'Демо-режим'")
    print()
    print("🚀 Запуск приложения...")
    print()

def main():
    """Главная функция демо"""
    show_demo_info()
    
    try:
        from main import FlurAIApp
        app = FlurAIApp()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Демонстрация завершена")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("💡 Убедитесь, что все зависимости установлены:")
        print("   pip install -r requirements.txt")

if __name__ == "__main__":
    main()


