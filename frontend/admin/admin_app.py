"""
Интерфейс администратора
"""

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
from datetime import datetime, timedelta
import random

class AdminApp:
    def __init__(self, parent, user_data, logout_callback):
        self.parent = parent
        self.user_data = user_data
        self.logout_callback = logout_callback
        
        # Создаем главный фрейм
        self.main_frame = ctk.CTkFrame(parent, fg_color="transparent")
        
        # Настройка сетки
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Создаем боковую панель
        self.create_sidebar()
        
        # Создаем основной контент
        self.create_content_area()
        
        # Показываем главную страницу
        self.show_dashboard()
    
    def create_sidebar(self):
        """Создание боковой панели навигации"""
        self.sidebar = ctk.CTkFrame(
            self.main_frame,
            width=250,
            corner_radius=0,
            fg_color="#1a237e"
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.sidebar.grid_propagate(False)
        
        # Заголовок с иконкой
        header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header_frame.pack(pady=(20, 15))
        
        # Иконка
        icon_label = ctk.CTkLabel(
            header_frame,
            text="🏥",
            font=ctk.CTkFont(size=32)
        )
        icon_label.pack()
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="FlurAI",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#1a237e"
        )
        title_label.pack(pady=(5, 0))
        
        # Информация о пользователе
        user_label = ctk.CTkLabel(
            self.sidebar,
            text=self.user_data["name"],
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff"
        )
        user_label.pack(pady=(0, 5))
        
        role_label = ctk.CTkLabel(
            self.sidebar,
            text="Администратор",
            font=ctk.CTkFont(size=12),
            text_color="#7e57c2"
        )
        role_label.pack(pady=(0, 20))
        
        # Навигационные кнопки
        nav_buttons = [
            ("Панель", "dashboard", self.show_dashboard),
            ("Врачи", "doctors", self.show_doctors),
            ("Аналитика", "analytics", self.show_analytics),
            ("Настройки", "settings", self.show_settings),
            ("Отчеты", "reports", self.show_reports)
        ]
        
        self.nav_buttons = {}
        for text, key, command in nav_buttons:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                width=200,
                height=40,
                font=ctk.CTkFont(size=14),
                command=command,
                fg_color="transparent",
                hover_color="#4caf50",
                text_color="#1a237e",
                anchor="w"
            )
            btn.pack(pady=5, padx=20)
            self.nav_buttons[key] = btn
        
        # Кнопка выхода
        logout_btn = ctk.CTkButton(
            self.sidebar,
            text="Выход",
            width=200,
            height=40,
            font=ctk.CTkFont(size=14),
            command=self.logout,
            fg_color="#d32f2f",
            hover_color="#b71c1c"
        )
        logout_btn.pack(side="bottom", pady=20, padx=20)
    
    def create_content_area(self):
        """Создание области основного контента"""
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        
        # Заголовок страницы
        self.page_title = ctk.CTkLabel(
            self.content_frame,
            text="",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#ffffff"
        )
        self.page_title.pack(pady=(20, 10))
        
        # Контейнер для контента
        self.content_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    def show_dashboard(self):
        """Показать админ-панель"""
        self.update_nav_buttons("dashboard")
        self.page_title.configure(text="Админ-панель")
        
        # Очищаем контейнер
        for widget in self.content_container.winfo_children():
            widget.destroy()
        
        # Общая статистика
        stats_frame = ctk.CTkFrame(self.content_container)
        stats_frame.pack(fill="x", pady=(0, 20))
        
        stats_title = ctk.CTkLabel(
            stats_frame,
            text="Общая статистика клиники",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        )
        stats_title.pack(pady=15)
        
        # Карточки статистики
        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(fill="x", padx=20, pady=(0, 20))
        
        stats_data = [
            ("Всего исследований", "156", "#4caf50"),
            ("Активных врачей", "8", "#2d5a27"),
            ("Пациентов сегодня", "24", "#ff9800"),
            ("Средняя точность", "94.2%", "#2196f3")
        ]
        
        for i, (title, value, color) in enumerate(stats_data):
            card = ctk.CTkFrame(stats_grid, fg_color=color)
            card.grid(row=0, column=i, padx=10, sticky="ew")
            stats_grid.grid_columnconfigure(i, weight=1)
            
            value_label = ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color="#ffffff"
            )
            value_label.pack(pady=(15, 5))
            
            title_label = ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=12),
                text_color="#ffffff"
            )
            title_label.pack(pady=(0, 15))
        
        # Активность врачей
        activity_frame = ctk.CTkFrame(self.content_container)
        activity_frame.pack(fill="x", pady=(0, 20))
        
        activity_title = ctk.CTkLabel(
            activity_frame,
            text="Активность врачей",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        )
        activity_title.pack(pady=15)
        
        self.create_doctors_activity_table(activity_frame)
        
        # Ключевые метрики
        metrics_frame = ctk.CTkFrame(self.content_container)
        metrics_frame.pack(fill="both", expand=True)
        
        metrics_title = ctk.CTkLabel(
            metrics_frame,
            text="Ключевые метрики",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        )
        metrics_title.pack(pady=15)
        
        self.create_metrics_grid(metrics_frame)
    
    def create_doctors_activity_table(self, parent):
        """Создание таблицы активности врачей"""
        table_frame = ctk.CTkFrame(parent)
        table_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Заголовки таблицы
        headers = ["Врач", "Исследования сегодня", "Точность", "Статус", "Последняя активность"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                table_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#ffffff"
            )
            label.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            table_frame.grid_columnconfigure(i, weight=1)
        
        # Данные врачей (заглушки)
        doctors_data = [
            ("Иванов А.В.", "12", "96%", "🟢 Онлайн", "2 мин назад"),
            ("Петрова С.И.", "8", "94%", "🟢 Онлайн", "5 мин назад"),
            ("Сидоров П.В.", "15", "92%", "🟡 Занят", "1 час назад"),
            ("Козлова М.А.", "6", "98%", "🔴 Офлайн", "3 часа назад"),
            ("Морозов Д.С.", "10", "95%", "🟢 Онлайн", "10 мин назад")
        ]
        
        for row, (doctor, studies, accuracy, status, last_activity) in enumerate(doctors_data, 1):
            # Врач
            doctor_label = ctk.CTkLabel(table_frame, text=doctor, font=ctk.CTkFont(size=11))
            doctor_label.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
            
            # Исследования
            studies_label = ctk.CTkLabel(table_frame, text=studies, font=ctk.CTkFont(size=11))
            studies_label.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
            
            # Точность
            accuracy_label = ctk.CTkLabel(table_frame, text=accuracy, font=ctk.CTkFont(size=11))
            accuracy_label.grid(row=row, column=2, padx=10, pady=5, sticky="ew")
            
            # Статус
            status_color = "#43a047" if "🟢" in status else "#ff9800" if "🟡" in status else "#d32f2f"
            status_label = ctk.CTkLabel(
                table_frame,
                text=status,
                font=ctk.CTkFont(size=11),
                text_color=status_color
            )
            status_label.grid(row=row, column=3, padx=10, pady=5, sticky="ew")
            
            # Последняя активность
            activity_label = ctk.CTkLabel(table_frame, text=last_activity, font=ctk.CTkFont(size=11))
            activity_label.grid(row=row, column=4, padx=10, pady=5, sticky="ew")
    
    def create_metrics_grid(self, parent):
        """Создание сетки метрик"""
        metrics_grid = ctk.CTkFrame(parent, fg_color="transparent")
        metrics_grid.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Метрики
        metrics_data = [
            ("Эффективность работы", "87%", "#43a047"),
            ("Загрузка оборудования", "65%", "#ff9800"),
            ("Время отклика системы", "1.2с", "#00acc1"),
            ("Удовлетворенность", "4.8/5", "#7e57c2")
        ]
        
        for i, (title, value, color) in enumerate(metrics_data):
            metric_frame = ctk.CTkFrame(metrics_grid, fg_color=color)
            metric_frame.grid(row=0, column=i, padx=10, sticky="ew")
            metrics_grid.grid_columnconfigure(i, weight=1)
            
            value_label = ctk.CTkLabel(
                metric_frame,
                text=value,
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color="#ffffff"
            )
            value_label.pack(pady=(15, 5))
            
            title_label = ctk.CTkLabel(
                metric_frame,
                text=title,
                font=ctk.CTkFont(size=12),
                text_color="#ffffff"
            )
            title_label.pack(pady=(0, 15))
    
    def show_doctors(self):
        """Показать страницу управления врачами"""
        self.update_nav_buttons("doctors")
        self.page_title.configure(text="Управление врачами")
        
        # Очищаем контейнер
        for widget in self.content_container.winfo_children():
            widget.destroy()
        
        # Заголовок с кнопкой добавления
        header_frame = ctk.CTkFrame(self.content_container)
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Управление врачами",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        )
        title_label.pack(side="left", padx=20, pady=15)
        
        add_btn = ctk.CTkButton(
            header_frame,
            text="➕ Добавить врача",
            width=150,
            height=35,
            command=self.add_doctor,
            fg_color="#2196f3",
            hover_color="#1976d2"
        )
        add_btn.pack(side="right", padx=20, pady=15)
        
        # Список врачей
        self.create_doctors_list()
    
    def create_doctors_list(self):
        """Создание списка врачей"""
        doctors_frame = ctk.CTkFrame(self.content_container)
        doctors_frame.pack(fill="both", expand=True)
        
        # Заголовки
        headers_frame = ctk.CTkFrame(doctors_frame)
        headers_frame.pack(fill="x", padx=10, pady=10)
        
        headers = ["ID", "ФИО", "Специализация", "Исследования/день", "Точность", "Статус", "Действия"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                headers_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#ffffff"
            )
            label.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            headers_frame.grid_columnconfigure(i, weight=1)
        
        # Данные врачей (заглушки)
        doctors_data = [
            ("DOC001", "Иванов А.В.", "Рентгенолог", "12", "96%", "Активен"),
            ("DOC002", "Петрова С.И.", "Рентгенолог", "8", "94%", "Активен"),
            ("DOC003", "Сидоров П.В.", "Рентгенолог", "15", "92%", "Активен"),
            ("DOC004", "Козлова М.А.", "Рентгенолог", "6", "98%", "Неактивен"),
            ("DOC005", "Морозов Д.С.", "Рентгенолог", "10", "95%", "Активен")
        ]
        
        for row, (doc_id, name, specialization, studies, accuracy, status) in enumerate(doctors_data, 1):
            row_frame = ctk.CTkFrame(doctors_frame)
            row_frame.pack(fill="x", padx=10, pady=2)
            
            # ID
            id_label = ctk.CTkLabel(row_frame, text=doc_id, font=ctk.CTkFont(size=11))
            id_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
            
            # ФИО
            name_label = ctk.CTkLabel(row_frame, text=name, font=ctk.CTkFont(size=11))
            name_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            
            # Специализация
            spec_label = ctk.CTkLabel(row_frame, text=specialization, font=ctk.CTkFont(size=11))
            spec_label.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
            
            # Исследования
            studies_label = ctk.CTkLabel(row_frame, text=studies, font=ctk.CTkFont(size=11))
            studies_label.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
            
            # Точность
            accuracy_label = ctk.CTkLabel(row_frame, text=accuracy, font=ctk.CTkFont(size=11))
            accuracy_label.grid(row=0, column=4, padx=5, pady=5, sticky="ew")
            
            # Статус
            status_color = "#43a047" if status == "Активен" else "#d32f2f"
            status_label = ctk.CTkLabel(
                row_frame,
                text=status,
                font=ctk.CTkFont(size=11),
                text_color=status_color
            )
            status_label.grid(row=0, column=5, padx=5, pady=5, sticky="ew")
            
            # Действия
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions_frame.grid(row=0, column=6, padx=5, pady=5, sticky="ew")
            
            edit_btn = ctk.CTkButton(
                actions_frame,
                text="✏️",
                width=30,
                height=25,
                command=lambda d=doc_id: self.edit_doctor(d),
                fg_color="#00acc1",
                hover_color="#0097a7"
            )
            edit_btn.pack(side="left", padx=2)
            
            delete_btn = ctk.CTkButton(
                actions_frame,
                text="🗑️",
                width=30,
                height=25,
                command=lambda d=doc_id: self.delete_doctor(d),
                fg_color="#d32f2f",
                hover_color="#b71c1c"
            )
            delete_btn.pack(side="left", padx=2)
            
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=2)
            row_frame.grid_columnconfigure(2, weight=1)
            row_frame.grid_columnconfigure(3, weight=1)
            row_frame.grid_columnconfigure(4, weight=1)
            row_frame.grid_columnconfigure(5, weight=1)
            row_frame.grid_columnconfigure(6, weight=1)
    
    def show_analytics(self):
        """Показать страницу аналитики"""
        self.update_nav_buttons("analytics")
        self.page_title.configure(text="Аналитика")
        
        # Очищаем контейнер
        for widget in self.content_container.winfo_children():
            widget.destroy()
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self.content_container,
            text="Аналитика и отчеты",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        )
        title_label.pack(pady=20)
        
        # Графики (заглушки)
        charts_frame = ctk.CTkFrame(self.content_container)
        charts_frame.pack(fill="both", expand=True)
        
        charts_title = ctk.CTkLabel(
            charts_frame,
            text="Графики и диаграммы",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#ffffff"
        )
        charts_title.pack(pady=15)
        
        # Сетка для графиков
        charts_grid = ctk.CTkFrame(charts_frame, fg_color="transparent")
        charts_grid.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Заглушки графиков
        chart_placeholders = [
            "График исследований по дням",
            "Динамика точности диагнозов",
            "Распределение по врачам",
            "Статистика по отделениям"
        ]
        
        for i, placeholder in enumerate(chart_placeholders):
            chart_frame = ctk.CTkFrame(charts_grid, fg_color="#f5f5f5")
            chart_frame.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="ew")
            charts_grid.grid_columnconfigure(i%2, weight=1)
            
            chart_label = ctk.CTkLabel(
                chart_frame,
                text=placeholder,
                font=ctk.CTkFont(size=14),
                text_color="#666666"
            )
            chart_label.pack(expand=True, pady=50)
    
    def show_settings(self):
        """Показать страницу настроек"""
        self.update_nav_buttons("settings")
        self.page_title.configure(text="Настройки системы")
        
        # Очищаем контейнер
        for widget in self.content_container.winfo_children():
            widget.destroy()
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self.content_container,
            text="Настройки системы",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        )
        title_label.pack(pady=20)
        
        # Настройки
        settings_data = [
            ("Конфигурация интеграций", "Настройка подключений к внешним системам"),
            ("Шаблоны заключений", "Управление шаблонами медицинских заключений"),
            ("Резервное копирование", "Настройка автоматического резервного копирования"),
            ("Права доступа", "Управление правами пользователей"),
            ("Уведомления", "Настройка системы уведомлений")
        ]
        
        for title, description in settings_data:
            setting_frame = ctk.CTkFrame(self.content_container)
            setting_frame.pack(fill="x", pady=5)
            
            title_label = ctk.CTkLabel(
                setting_frame,
                text=title,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#ffffff"
            )
            title_label.pack(anchor="w", padx=20, pady=(15, 5))
            
            desc_label = ctk.CTkLabel(
                setting_frame,
                text=description,
                font=ctk.CTkFont(size=12),
                text_color="#666666"
            )
            desc_label.pack(anchor="w", padx=20, pady=(0, 15))
    
    def show_reports(self):
        """Показать страницу отчетов"""
        self.update_nav_buttons("reports")
        self.page_title.configure(text="Отчеты")
        
        # Очищаем контейнер
        for widget in self.content_container.winfo_children():
            widget.destroy()
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self.content_container,
            text="Отчеты и статистика",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        )
        title_label.pack(pady=20)
        
        # Кнопки экспорта
        export_frame = ctk.CTkFrame(self.content_container)
        export_frame.pack(fill="x", pady=(0, 20))
        
        export_title = ctk.CTkLabel(
            export_frame,
            text="Экспорт отчетов",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#ffffff"
        )
        export_title.pack(pady=15)
        
        export_buttons = ctk.CTkFrame(export_frame, fg_color="transparent")
        export_buttons.pack(fill="x", padx=20, pady=(0, 15))
        
        # Кнопки экспорта
        export_btn1 = ctk.CTkButton(
            export_buttons,
            text="📄 PDF отчет",
            width=120,
            height=35,
            command=self.export_pdf,
            fg_color="#d32f2f",
            hover_color="#b71c1c"
        )
        export_btn1.pack(side="left", padx=(0, 10))
        
        export_btn2 = ctk.CTkButton(
            export_buttons,
            text="📊 Excel отчет",
            width=120,
            height=35,
            command=self.export_excel,
            fg_color="#2196f3",
            hover_color="#1976d2"
        )
        export_btn2.pack(side="left", padx=(0, 10))
        
        export_btn3 = ctk.CTkButton(
            export_buttons,
            text="📈 Графики",
            width=120,
            height=35,
            command=self.export_charts,
            fg_color="#00acc1",
            hover_color="#0097a7"
        )
        export_btn3.pack(side="left")
        
        # Создаем отчеты с рандомными данными
        self.create_reports_content()
    
    def create_reports_content(self):
        """Создание контента отчетов"""
        # Основные метрики
        metrics_frame = ctk.CTkFrame(self.content_container)
        metrics_frame.pack(fill="x", pady=(0, 20))
        
        metrics_title = ctk.CTkLabel(
            metrics_frame,
            text="Ключевые показатели",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#ffffff"
        )
        metrics_title.pack(pady=15)
        
        # Генерируем рандомные данные
        import random
        from datetime import datetime, timedelta
        
        metrics_data = [
            ("Всего исследований", f"{random.randint(120, 200)}"),
            ("Исследований за месяц", f"{random.randint(80, 150)}"),
            ("Средняя точность", f"{random.uniform(92, 98):.1f}%"),
            ("Активных врачей", f"{random.randint(6, 12)}"),
            ("Пациентов в очереди", f"{random.randint(5, 25)}"),
            ("Время отклика системы", f"{random.uniform(0.8, 2.5):.1f}с")
        ]
        
        metrics_grid = ctk.CTkFrame(metrics_frame, fg_color="transparent")
        metrics_grid.pack(fill="x", padx=20, pady=(0, 15))
        
        for i, (label, value) in enumerate(metrics_data):
            metric_frame = ctk.CTkFrame(metrics_grid, fg_color="#f5f5f5")
            metric_frame.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            metrics_grid.grid_columnconfigure(i, weight=1)
            
            value_label = ctk.CTkLabel(
                metric_frame,
                text=value,
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="#000000"
            )
            value_label.pack(pady=(10, 5))
            
            label_label = ctk.CTkLabel(
                metric_frame,
                text=label,
                font=ctk.CTkFont(size=12),
                text_color="#666666"
            )
            label_label.pack(pady=(0, 10))
        
        # Статистика по врачам
        doctors_stats_frame = ctk.CTkFrame(self.content_container)
        doctors_stats_frame.pack(fill="both", expand=True)
        
        doctors_title = ctk.CTkLabel(
            doctors_stats_frame,
            text="Статистика по врачам",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#ffffff"
        )
        doctors_title.pack(pady=15)
        
        # Таблица статистики врачей
        self.create_doctors_stats_table(doctors_stats_frame)
    
    def create_doctors_stats_table(self, parent):
        """Создание таблицы статистики врачей"""
        table_frame = ctk.CTkFrame(parent)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Заголовки
        headers_frame = ctk.CTkFrame(table_frame)
        headers_frame.pack(fill="x", padx=10, pady=10)
        
        headers = ["Врач", "Исследований", "Точность", "Среднее время", "Рейтинг"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                headers_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#ffffff"
            )
            label.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            headers_frame.grid_columnconfigure(i, weight=1)
        
        # Данные врачей (рандомные)
        import random
        
        doctors_data = [
            ("Иванов А.В.", random.randint(15, 25), f"{random.uniform(94, 99):.1f}%", f"{random.uniform(2.5, 4.0):.1f}мин", f"{random.uniform(4.5, 5.0):.1f}★"),
            ("Петрова С.И.", random.randint(12, 20), f"{random.uniform(92, 98):.1f}%", f"{random.uniform(2.0, 3.5):.1f}мин", f"{random.uniform(4.0, 4.8):.1f}★"),
            ("Сидоров П.В.", random.randint(18, 28), f"{random.uniform(93, 97):.1f}%", f"{random.uniform(2.8, 4.2):.1f}мин", f"{random.uniform(4.2, 4.9):.1f}★"),
            ("Козлова М.А.", random.randint(10, 18), f"{random.uniform(95, 99):.1f}%", f"{random.uniform(1.8, 3.0):.1f}мин", f"{random.uniform(4.6, 5.0):.1f}★"),
            ("Морозов Д.С.", random.randint(14, 22), f"{random.uniform(91, 97):.1f}%", f"{random.uniform(2.2, 3.8):.1f}мин", f"{random.uniform(4.1, 4.7):.1f}★")
        ]
        
        for row, (doctor, studies, accuracy, avg_time, rating) in enumerate(doctors_data, 1):
            row_frame = ctk.CTkFrame(table_frame)
            row_frame.pack(fill="x", padx=10, pady=2)
            
            # Врач
            doctor_label = ctk.CTkLabel(row_frame, text=doctor, font=ctk.CTkFont(size=11))
            doctor_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
            
            # Исследования
            studies_label = ctk.CTkLabel(row_frame, text=str(studies), font=ctk.CTkFont(size=11))
            studies_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            
            # Точность
            accuracy_label = ctk.CTkLabel(row_frame, text=accuracy, font=ctk.CTkFont(size=11))
            accuracy_label.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
            
            # Среднее время
            time_label = ctk.CTkLabel(row_frame, text=avg_time, font=ctk.CTkFont(size=11))
            time_label.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
            
            # Рейтинг
            rating_color = "#43a047" if float(rating.split("★")[0]) >= 4.5 else "#ff9800" if float(rating.split("★")[0]) >= 4.0 else "#d32f2f"
            rating_label = ctk.CTkLabel(
                row_frame,
                text=rating,
                font=ctk.CTkFont(size=11),
                text_color=rating_color
            )
            rating_label.grid(row=0, column=4, padx=5, pady=5, sticky="ew")
            
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=1)
            row_frame.grid_columnconfigure(2, weight=1)
            row_frame.grid_columnconfigure(3, weight=1)
            row_frame.grid_columnconfigure(4, weight=1)
    
    def export_pdf(self):
        """Экспорт PDF отчета"""
        messagebox.showinfo("Экспорт", "PDF отчет сгенерирован и сохранен (демо-режим)")
    
    def export_excel(self):
        """Экспорт Excel отчета"""
        messagebox.showinfo("Экспорт", "Excel отчет сгенерирован и сохранен (демо-режим)")
    
    def export_charts(self):
        """Экспорт графиков"""
        messagebox.showinfo("Экспорт", "Графики экспортированы (демо-режим)")
    
    def add_doctor(self):
        """Добавление нового врача"""
        # Создаем модальное окно для добавления врача
        add_window = ctk.CTkToplevel(self.parent)
        add_window.title("Добавить врача")
        add_window.geometry("400x500")
        add_window.transient(self.parent)
        add_window.grab_set()
        
        # Центрирование окна
        add_window.update_idletasks()
        x = (add_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (add_window.winfo_screenheight() // 2) - (500 // 2)
        add_window.geometry(f"400x500+{x}+{y}")
        
        # Заголовок
        title_label = ctk.CTkLabel(
            add_window,
            text="Добавить нового врача",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#1a237e"
        )
        title_label.pack(pady=20)
        
        # Поля формы
        fields_frame = ctk.CTkFrame(add_window)
        fields_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # ФИО
        ctk.CTkLabel(fields_frame, text="ФИО:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(20, 5))
        name_entry = ctk.CTkEntry(fields_frame, placeholder_text="Введите ФИО врача", width=300, height=35)
        name_entry.pack(padx=20, pady=(0, 15))
        
        # Специализация
        ctk.CTkLabel(fields_frame, text="Специализация:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(0, 5))
        spec_entry = ctk.CTkEntry(fields_frame, placeholder_text="Рентгенолог", width=300, height=35)
        spec_entry.pack(padx=20, pady=(0, 15))
        
        # ID врача
        ctk.CTkLabel(fields_frame, text="ID врача:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(0, 5))
        id_entry = ctk.CTkEntry(fields_frame, placeholder_text="DOC001", width=300, height=35)
        id_entry.pack(padx=20, pady=(0, 15))
        
        # Отделение
        ctk.CTkLabel(fields_frame, text="Отделение:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(0, 5))
        dept_entry = ctk.CTkEntry(fields_frame, placeholder_text="Рентгенология", width=300, height=35)
        dept_entry.pack(padx=20, pady=(0, 15))
        
        # Кнопки
        buttons_frame = ctk.CTkFrame(add_window, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        def save_doctor():
            name = name_entry.get().strip()
            spec = spec_entry.get().strip()
            doc_id = id_entry.get().strip()
            dept = dept_entry.get().strip()
            
            if not all([name, spec, doc_id, dept]):
                messagebox.showerror("Ошибка", "Заполните все поля")
                return
            
            # Добавляем врача в список (в реальном приложении - в БД)
            messagebox.showinfo("Успех", f"Врач {name} добавлен в систему")
            add_window.destroy()
            # Обновляем список врачей
            self.show_doctors()
        
        save_btn = ctk.CTkButton(
            buttons_frame,
            text="Сохранить",
            width=120,
            height=40,
            command=save_doctor,
            fg_color="#2196f3",
            hover_color="#1976d2"
        )
        save_btn.pack(side="left", padx=(0, 10))
        
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Отмена",
            width=120,
            height=40,
            command=add_window.destroy,
            fg_color="#666666",
            hover_color="#555555"
        )
        cancel_btn.pack(side="left")
    
    def edit_doctor(self, doctor_id):
        """Редактирование врача"""
        messagebox.showinfo("Редактирование", f"Редактирование врача {doctor_id} будет реализовано в полной версии")
    
    def delete_doctor(self, doctor_id):
        """Удаление врача"""
        result = messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить врача {doctor_id}?")
        if result:
            messagebox.showinfo("Удаление", f"Врач {doctor_id} удален из системы")
            # В реальном приложении здесь будет удаление из БД
            # Обновляем список врачей
            self.show_doctors()
    
    def update_nav_buttons(self, active_button):
        """Обновление состояния навигационных кнопок"""
        for key, button in self.nav_buttons.items():
            if key == active_button:
                button.configure(fg_color="#7e57c2", text_color="white")
            else:
                button.configure(fg_color="transparent", text_color="white")
    
    def show(self):
        """Показать приложение"""
        self.main_frame.pack(fill="both", expand=True)
    
    def destroy(self):
        """Уничтожить приложение"""
        self.main_frame.destroy()
    
    def logout(self):
        """Выход из системы"""
        self.logout_callback()
