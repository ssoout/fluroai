# 📦 Инструкция по установке FlurAI

## Системные требования

- **Python 3.8+** (рекомендуется 3.9 или новее)
- **Windows 10/11** или **macOS 10.15+** или **Linux Ubuntu 18.04+**
- **4 ГБ RAM** (минимум)
- **1 ГБ свободного места** на диске

## 🚀 Быстрая установка

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd FlurAI
```

### 2. Установка зависимостей
```bash
# Создание виртуального окружения (рекомендуется)
python -m venv venv

# Активация окружения
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Установка минимальных пакетов (рекомендуется для начала)
pip install -r requirements-minimal.txt

# Или полная установка всех зависимостей
pip install -r requirements.txt
```

### 3. Запуск приложения
```bash
# Основной запуск
python main.py

# Или через скрипт с проверкой зависимостей
python run.py

# Демонстрационный режим
python demo.py
```

## 🔧 Детальная установка

### Установка Python
1. Скачайте Python с [python.org](https://python.org)
2. При установке отметьте "Add Python to PATH"
3. Проверьте установку: `python --version`

### Установка зависимостей

#### Основные пакеты:
```bash
pip install customtkinter>=5.2.0
pip install Pillow>=10.0.0
```

#### Дополнительные пакеты для полной функциональности:
```bash
pip install opencv-python>=4.8.0
pip install numpy>=1.24.0
pip install matplotlib>=3.7.0
pip install pandas>=2.0.0
pip install plotly>=5.15.0
```

### Проверка установки
```bash
python -c "import customtkinter; print('CustomTkinter установлен')"
python -c "import PIL; print('Pillow установлен')"
```

## 🐛 Решение проблем

### Ошибка "ModuleNotFoundError: No module named 'customtkinter'"
```bash
pip install customtkinter
```

### Ошибка "No module named 'PIL'"
```bash
pip install Pillow
```

### Проблемы с tkinter на Linux
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# CentOS/RHEL
sudo yum install tkinter
```

### Проблемы с отображением на macOS
```bash
# Установка дополнительных библиотек
brew install python-tk
```

## 🎯 Первый запуск

1. **Запустите приложение:**
   ```bash
   python main.py
   ```

2. **Выберите роль:**
   - Врач-рентгенолог
   - Администратор

3. **Войдите в систему:**
   - Врач: `doctor` / `123`
   - Админ: `admin` / `123`
   - Или используйте "Демо-режим"

4. **Изучите интерфейс:**
   - Навигация по разделам
   - Загрузка тестовых снимков
   - Просмотр статистики

## 📁 Структура проекта

```
FlurAI/
├── main.py              # Точка входа
├── run.py               # Скрипт запуска с проверками
├── demo.py              # Демонстрационный режим
├── requirements.txt     # Зависимости
├── README.md           # Основная документация
├── INSTALL.md          # Инструкция по установке
├── auth/               # Аутентификация
├── doctor/             # Интерфейс врача
├── admin/              # Интерфейс администратора
└── components/         # UI компоненты
```

## 🔄 Обновление

```bash
# Обновление зависимостей
pip install --upgrade -r requirements.txt

# Обновление кода (если есть git)
git pull origin main
```

## 🧪 Тестирование

```bash
# Проверка всех модулей
python -c "import main, auth.login_window, doctor.doctor_app, admin.admin_app"

# Запуск тестов (если есть)
python -m pytest tests/
```

## 📞 Поддержка

При возникновении проблем:

1. **Проверьте версию Python:** `python --version`
2. **Проверьте установленные пакеты:** `pip list`
3. **Создайте Issue** в репозитории с описанием проблемы
4. **Приложите логи ошибок** и информацию о системе

---

**Удачной установки! 🚀**
