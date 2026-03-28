"""
Интерфейс врача-рентгенолога
"""

try:
    import customtkinter as ctk
except ImportError:
    print("CustomTkinter не установлен. Установите: pip install customtkinter")
    exit(1)

from tkinter import messagebox, filedialog
import tkinter as tk
from datetime import date, datetime
import random
from pathlib import Path
import threading

from PIL import Image

from services.api_client import ApiClient, ApiError

class DoctorApp:
    def __init__(self, parent, user_data, logout_callback):
        self.parent = parent
        self.user_data = user_data
        self.logout_callback = logout_callback
        self.api_client = ApiClient()
        self.project_root = Path(__file__).resolve().parents[2]
        self.current_page = "dashboard"
        
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
            fg_color="#212121"
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
            text_color="white"
        )
        title_label.pack(pady=(5, 0))
        
        # Информация о пользователе
        user_label = ctk.CTkLabel(
            self.sidebar,
            text=self.user_data["name"],
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white"
        )
        user_label.pack(pady=(0, 20))
        
        # Навигационные кнопки
        nav_buttons = [
            ("🏠 Главная", "dashboard", self.show_dashboard),
            ("📸 Снимки", "images", self.show_images),
            ("👥 Пациенты", "patients", self.show_patients),
            ("📊 История", "history", self.show_history),
            ("⚙️ Профиль", "profile", self.show_profile)
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
                hover_color="#424242",
                text_color="white",
                anchor="w"
            )
            btn.pack(pady=5, padx=20)
            self.nav_buttons[key] = btn
        
        # Кнопка выхода
        logout_btn = ctk.CTkButton(
            self.sidebar,
            text="🚪 Выход",
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
            text_color="white"
        )
        self.page_title.pack(pady=(20, 10))
        
        # Контейнер для контента
        self.content_container = ctk.CTkFrame(self.content_frame, fg_color="#212121")
        self.content_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    def show_dashboard(self):
        """Показать главную страницу"""
        self.update_nav_buttons("dashboard")
        self.page_title.configure(text="Главная страница")
        
        self.clear_content_container()
        
        # Статистика
        stats_frame = ctk.CTkFrame(self.content_container, fg_color="#212121")
        stats_frame.pack(fill="x", pady=(0, 20))
        
        stats_title = ctk.CTkLabel(
            stats_frame,
            text="📊 Моя статистика",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        stats_title.pack(pady=15)
        
        # Карточки статистики
        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(fill="x", padx=20, pady=(0, 20))
        
        stats = self.safe_api_call(
            self.api_client.get_dashboard_stats,
            default={"processed": 0, "pathology_count": 0, "manual_review": 0},
            error_message="Не удалось загрузить статистику дашборда",
        )
        stats_data = [
            ("Обработано исследований", str(stats.get("processed", 0)), "#2196f3"),
            ("Обнаружено патологий", str(stats.get("pathology_count", 0)), "#d32f2f"),
            ("Требует внимания", str(stats.get("manual_review", 0)), "#ff9800"),
            ("Подтверждено врачами", f"{self.calculate_success_rate(stats)}%", "#43a047"),
        ]
        
        for i, (title, value, color) in enumerate(stats_data):
            card = ctk.CTkFrame(stats_grid, fg_color=color)
            card.grid(row=0, column=i, padx=10, sticky="ew")
            stats_grid.grid_columnconfigure(i, weight=1)
            
            value_label = ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color="white"
            )
            value_label.pack(pady=(15, 5))
            
            title_label = ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=12),
                text_color="white"
            )
            title_label.pack(pady=(0, 15))
        
        # Быстрые действия
        actions_frame = ctk.CTkFrame(self.content_container, fg_color="#212121")
        actions_frame.pack(fill="x", pady=(0, 20))
        
        actions_title = ctk.CTkLabel(
            actions_frame,
            text="⚡ Быстрые действия",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        actions_title.pack(pady=15)
        
        actions_grid = ctk.CTkFrame(actions_frame, fg_color="transparent")
        actions_grid.pack(fill="x", padx=20, pady=(0, 20))
        
        action_buttons = [
            ("📸 Новое исследование", self.show_images, "#2196f3"),
            ("👥 Добавить пациента", self.show_patients, "#1a237e"),
            ("📊 Просмотр статистики", self.show_history, "#ff9800"),
            ("⚙️ Настройки", self.show_profile, "#2196f3")
        ]
        
        for i, (text, command, color) in enumerate(action_buttons):
            btn = ctk.CTkButton(
                actions_grid,
                text=text,
                width=200,
                height=60,
                font=ctk.CTkFont(size=14),
                command=command,
                fg_color=color,
                hover_color=self.darken_color(color)
            )
            btn.grid(row=0, column=i, padx=10, sticky="ew")
            actions_grid.grid_columnconfigure(i, weight=1)

        # Исследования, ожидающие проверки
        pending_frame = ctk.CTkFrame(self.content_container, fg_color="#212121")
        pending_frame.pack(fill="x", pady=(0, 20))

        pending_title = ctk.CTkLabel(
            pending_frame,
            text="⏳ Исследования, ожидающие проверки",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white",
        )
        pending_title.pack(pady=15)

        pending_results = self.safe_api_call(
            lambda: self.api_client.get_pending_analysis().get("items", []),
            default=[],
            error_message="Не удалось загрузить исследования, ожидающие проверки",
        )
        self.create_pending_results_list(pending_frame, pending_results)
        
        # Последние исследования
        recent_frame = ctk.CTkFrame(self.content_container, fg_color="#212121")
        recent_frame.pack(fill="both", expand=True)
        
        recent_title = ctk.CTkLabel(
            recent_frame,
            text="🕒 Последние исследования",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        recent_title.pack(pady=15)
        
        # Таблица последних исследований
        recent_items_raw = self.safe_api_call(
            lambda: self.api_client.get_dashboard_recent().get("items", []),
            default=[],
            error_message="Не удалось загрузить последние исследования",
        )
        prepared_recent = [self.transform_result_item(item) for item in recent_items_raw]
        self.create_recent_studies_table(recent_frame, prepared_recent)
    
    def create_recent_studies_table(self, parent, studies):
        """Создание таблицы последних исследований"""
        table_frame = ctk.CTkFrame(parent, fg_color="#212121")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Заголовки таблицы
        headers = ["Время", "Пациент", "Тип", "Результат", "Статус"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                table_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="white"
            )
            label.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            table_frame.grid_columnconfigure(i, weight=1)
        if not studies:
            empty_label = ctk.CTkLabel(
                table_frame,
                text="Нет данных для отображения",
                font=ctk.CTkFont(size=12),
                text_color="#9e9e9e",
            )
            empty_label.grid(row=1, column=0, columnspan=len(headers), pady=20)
            return
        
        for row, study in enumerate(studies, 1):
            # Время
            time_label = ctk.CTkLabel(
                table_frame,
                text=study.get("time_short", "—"),
                font=ctk.CTkFont(size=11),
            )
            time_label.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
            
            # Пациент
            patient_label = ctk.CTkLabel(
                table_frame,
                text=study.get("patient", "—"),
                font=ctk.CTkFont(size=11),
            )
            patient_label.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
            
            # Тип
            type_label = ctk.CTkLabel(
                table_frame,
                text=study.get("type", "Флюорография"),
                font=ctk.CTkFont(size=11),
            )
            type_label.grid(row=row, column=2, padx=10, pady=5, sticky="ew")
            
            # Результат
            result_label = ctk.CTkLabel(
                table_frame,
                text=study.get("result", "—"),
                font=ctk.CTkFont(size=11),
                text_color=self.get_result_color(study.get("result")),
            )
            result_label.grid(row=row, column=3, padx=10, pady=5, sticky="ew")
            
            # Статус
            status_label = ctk.CTkLabel(
                table_frame, 
                text=study.get("status_display", "—"), 
                font=ctk.CTkFont(size=11),
                text_color=self.get_status_color(study.get("status_display", "")),
            )
            status_label.grid(row=row, column=4, padx=10, pady=5, sticky="ew")

    def create_pending_results_list(self, parent, items):
        """Список исследований, ожидающих подтверждения врача"""
        list_frame = ctk.CTkFrame(parent, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        if not items:
            empty_label = ctk.CTkLabel(
                list_frame,
                text="Все исследования подтверждены. Новых задач нет.",
                font=ctk.CTkFont(size=12),
                text_color="#9e9e9e",
            )
            empty_label.pack(pady=10)
            return

        for item in items:
            card = ctk.CTkFrame(list_frame, fg_color="#2b2b2b")
            card.pack(fill="x", pady=5)

            header = ctk.CTkLabel(
                card,
                text=f"{item.get('patient_name', 'Пациент')} • {self.format_datetime(item.get('taken_at'))}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="white",
            )
            header.pack(anchor="w", padx=20, pady=(15, 5))

            status_label = ctk.CTkLabel(
                card,
                text=f"Статус AI: {self.map_status_label(item.get('ai_status'))}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=self.get_result_color(self.map_status_label(item.get("ai_status"))),
            )
            status_label.pack(anchor="w", padx=20)

            confidence_label = ctk.CTkLabel(
                card,
                text=f"Уверенность модели: {self.format_confidence(item.get('ai_confidence'))}",
                font=ctk.CTkFont(size=12),
                text_color="white",
            )
            confidence_label.pack(anchor="w", padx=20, pady=(5, 0))

            findings_label = ctk.CTkLabel(
                card,
                text=f"Описание: {item.get('ai_findings') or 'Нет данных'}",
                font=ctk.CTkFont(size=12),
                text_color="#dddddd",
                wraplength=800,
                justify="left",
            )
            findings_label.pack(anchor="w", padx=20, pady=(5, 10))

            actions_frame = ctk.CTkFrame(card, fg_color="transparent")
            actions_frame.pack(fill="x", padx=20, pady=(0, 15))

            approve_btn = ctk.CTkButton(
                actions_frame,
                text="✅ Подтвердить",
                width=140,
                height=32,
                fg_color="#43a047",
                hover_color="#2e7d32",
                command=lambda rid=item.get("result_id"): self.handle_pending_action(rid, "approve"),
            )
            approve_btn.pack(side="left", padx=(0, 10))

            reject_btn = ctk.CTkButton(
                actions_frame,
                text="❌ Отклонить",
                width=140,
                height=32,
                fg_color="#d32f2f",
                hover_color="#b71c1c",
                command=lambda rid=item.get("result_id"): self.handle_pending_action(rid, "reject"),
            )
            reject_btn.pack(side="left", padx=(0, 10))

            details_btn = ctk.CTkButton(
                actions_frame,
                text="Подробнее",
                width=120,
                height=32,
                fg_color="#2196f3",
                hover_color="#1976d2",
                command=lambda rid=item.get("result_id"): self.open_result_details(rid),
            )
            details_btn.pack(side="left")
    
    def show_images(self):
        """Показать страницу работы со снимками"""
        self.update_nav_buttons("images")
        self.page_title.configure(text="Работа со снимками")
        
        self.clear_content_container()
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self.content_container,
            text="Проведение исследования",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        title_label.pack(pady=20)
        
        # Создаем основной интерфейс исследования
        self.create_study_interface()
    
    def show_patients(self):
        """Показать страницу пациентов"""
        self.update_nav_buttons("patients")
        self.page_title.configure(text="Мои пациенты")
        
        self.clear_content_container()
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self.content_container,
            text="👥 Управление пациентами",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        title_label.pack(pady=20)
        
        # Поиск
        search_frame = ctk.CTkFrame(self.content_container, fg_color="#212121")
        search_frame.pack(fill="x", pady=(0, 20))
        
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Поиск по имени или ID пациента",
            width=400,
            height=35
        )
        search_entry.pack(side="left", padx=20, pady=15)
        
        search_btn = ctk.CTkButton(
            search_frame,
            text="🔍 Поиск",
            width=100,
            height=35,
            command=self.search_patients
        )
        search_btn.pack(side="left", padx=(0, 20), pady=15)
        
        patients = self.safe_api_call(
            self.api_client.list_patients,
            default=[],
            error_message="Не удалось загрузить список пациентов",
        )
        self.create_patients_list(patients)
    
    def create_patients_list(self, patients):
        """Создание списка пациентов"""
        patients_frame = ctk.CTkFrame(self.content_container, fg_color="#212121")
        patients_frame.pack(fill="both", expand=True)
        
        # Заголовки
        headers_frame = ctk.CTkFrame(patients_frame, fg_color="transparent")
        headers_frame.pack(fill="x", padx=10, pady=10)
        
        headers = ["ID", "ФИО", "Возраст", "Последнее исследование", "Статус"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                headers_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="white"
            )
            label.grid(row=0, column=i, padx=10, pady=5, sticky="ew")
            headers_frame.grid_columnconfigure(i, weight=1)
        
        if not patients:
            empty_label = ctk.CTkLabel(
                patients_frame,
                text="Пациенты не найдены",
                font=ctk.CTkFont(size=12),
                text_color="#9e9e9e",
            )
            empty_label.pack(pady=20)
            return
        
        for patient in patients:
            patient_id = patient.get("id")
            if patient_id is None:
                continue  # Пропускаем пациентов без ID
                
            patient_id_str = str(patient_id)
            name = patient.get("full_name", "—")
            age = self.calculate_age(patient.get("birth_date"))
            last_study = self.format_datetime(patient.get("created_at"))
            status = "Активен"
            
            # Делаем строку кликабельной
            row_frame = ctk.CTkFrame(patients_frame, fg_color="#2b2b2b", corner_radius=5)
            row_frame.pack(fill="x", padx=10, pady=3)
            
            # Делаем всю строку кликабельной
            def make_clickable(pat_id, pat_name):
                def on_click(event=None):
                    if pat_id is None:
                        messagebox.showerror("Ошибка", "Не удалось определить ID пациента")
                        return
                    try:
                        self.show_patient_studies(int(pat_id), pat_name)
                    except (ValueError, TypeError) as e:
                        messagebox.showerror("Ошибка", f"Некорректный ID пациента: {e}")
                return on_click
            
            click_handler = make_clickable(patient_id, name)
            row_frame.bind("<Button-1>", click_handler)
            row_frame.configure(cursor="hand2")
            
            # ID
            id_label = ctk.CTkLabel(row_frame, text=patient_id_str, font=ctk.CTkFont(size=11))
            id_label.grid(row=0, column=0, padx=10, pady=8, sticky="ew")
            id_label.bind("<Button-1>", click_handler)
            id_label.configure(cursor="hand2")
            
            # ФИО (кликабельное)
            name_label = ctk.CTkLabel(
                row_frame, 
                text=name, 
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#2196f3"
            )
            name_label.grid(row=0, column=1, padx=10, pady=8, sticky="ew")
            name_label.bind("<Button-1>", click_handler)
            name_label.configure(cursor="hand2")
            
            # Возраст
            age_label = ctk.CTkLabel(row_frame, text=age, font=ctk.CTkFont(size=11))
            age_label.grid(row=0, column=2, padx=10, pady=8, sticky="ew")
            age_label.bind("<Button-1>", click_handler)
            age_label.configure(cursor="hand2")
            
            # Последнее исследование
            study_label = ctk.CTkLabel(row_frame, text=last_study, font=ctk.CTkFont(size=11))
            study_label.grid(row=0, column=3, padx=10, pady=8, sticky="ew")
            study_label.bind("<Button-1>", click_handler)
            study_label.configure(cursor="hand2")
            
            # Статус
            status_color = "#43a047" if status == "Активен" else "#ff9800"
            status_label = ctk.CTkLabel(
                row_frame,
                text=status,
                font=ctk.CTkFont(size=11),
                text_color=status_color
            )
            status_label.grid(row=0, column=4, padx=10, pady=8, sticky="ew")
            status_label.bind("<Button-1>", click_handler)
            status_label.configure(cursor="hand2")
            
            # Кнопка просмотра
            view_btn = ctk.CTkButton(
                row_frame,
                text="👁 Просмотр",
                width=100,
                height=28,
                font=ctk.CTkFont(size=10),
                command=click_handler,
                fg_color="#2196f3",
                hover_color="#1976d2"
            )
            view_btn.grid(row=0, column=5, padx=10, pady=8, sticky="e")
            
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=2)
            row_frame.grid_columnconfigure(2, weight=1)
            row_frame.grid_columnconfigure(3, weight=1)
            row_frame.grid_columnconfigure(4, weight=1)
            row_frame.grid_columnconfigure(5, weight=0)
    
    def show_patient_studies(self, patient_id: int, patient_name: str):
        """Показать все исследования конкретного пациента"""
        self.update_nav_buttons("patients")
        self.page_title.configure(text=f"Исследования: {patient_name}")
        
        self.clear_content_container()
        
        # Кнопка назад
        back_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        back_frame.pack(fill="x", pady=(0, 15))
        
        back_btn = ctk.CTkButton(
            back_frame,
            text="← Назад к списку пациентов",
            command=self.show_patients,
            fg_color="#424242",
            hover_color="#616161",
            width=200
        )
        back_btn.pack(side="left")
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self.content_container,
            text=f"📋 Исследования пациента: {patient_name}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        title_label.pack(pady=(0, 20))
        
        # Получаем исследования пациента
        try:
            # Убеждаемся, что patient_id - это число
            patient_id = int(patient_id)
            print(f"[FRONTEND] Запрос исследований для пациента ID={patient_id}, Имя={patient_name}")
            
            # Сначала проверяем доступность backend
            try:
                health = self.api_client.health()
                print(f"[FRONTEND] Backend доступен: {health}")
            except Exception as e:
                print(f"[FRONTEND] ⚠ Backend недоступен: {e}")
                messagebox.showerror("Ошибка", "Backend недоступен. Убедитесь, что backend запущен.")
                studies = []
            else:
                # Если backend доступен, делаем запрос исследований
                studies = self.safe_api_call(
                    lambda: self.api_client.get_patient_studies(patient_id),
                    default=[],
                    error_message=f"Не удалось загрузить исследования для пациента ID {patient_id}",
                )
                
                print(f"[FRONTEND] Получено исследований: {len(studies) if studies else 0}")
                if studies:
                    for s in studies:
                        print(f"[FRONTEND]   - Исследование ID={s.get('id')}, Patient ID={s.get('patient_id')}, Дата={s.get('taken_at')}")
        except (ValueError, TypeError) as e:
            print(f"[FRONTEND] ОШИБКА: Некорректный ID пациента: {e}")
            messagebox.showerror("Ошибка", f"Некорректный ID пациента: {e}")
            studies = []
        except Exception as e:
            print(f"[FRONTEND] ОШИБКА при получении исследований: {e}")
            import traceback
            traceback.print_exc()
            studies = []
        
        if not studies:
            empty_label = ctk.CTkLabel(
                self.content_container,
                text="У этого пациента пока нет исследований",
                font=ctk.CTkFont(size=14),
                text_color="#9e9e9e",
            )
            empty_label.pack(pady=40)
            return
        
        # Список исследований
        studies_frame = ctk.CTkScrollableFrame(self.content_container, fg_color="#212121")
        studies_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        for study in studies:
            study_frame = ctk.CTkFrame(studies_frame, fg_color="#2b2b2b", corner_radius=8)
            study_frame.pack(fill="x", pady=5, padx=5)
            
            # Заголовок исследования
            header_frame = ctk.CTkFrame(study_frame, fg_color="transparent")
            header_frame.pack(fill="x", padx=15, pady=10)
            
            date_label = ctk.CTkLabel(
                header_frame,
                text=f"📅 {self.format_datetime(study.get('taken_at'))}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="white"
            )
            date_label.pack(side="left")
            
            priority = study.get("priority", "routine")
            priority_text = {"urgent": "Срочно", "routine": "Обычно", "high": "Высокий"}.get(priority, priority)
            priority_color = {"urgent": "#d32f2f", "routine": "#43a047", "high": "#ff9800"}.get(priority, "#9e9e9e")
            
            priority_label = ctk.CTkLabel(
                header_frame,
                text=f"Приоритет: {priority_text}",
                font=ctk.CTkFont(size=12),
                text_color=priority_color
            )
            priority_label.pack(side="right")
            
            # Информация об исследовании
            info_text = f"Заметки: {study.get('notes') or 'Нет заметок'}"
            info_label = ctk.CTkLabel(
                study_frame,
                text=info_text,
                font=ctk.CTkFont(size=11),
                text_color="#bbbbbb"
            )
            info_label.pack(anchor="w", padx=15, pady=(0, 10))
            
            # Кнопки действий
            actions_frame = ctk.CTkFrame(study_frame, fg_color="transparent")
            actions_frame.pack(fill="x", padx=15, pady=(0, 10))
            
            view_btn = ctk.CTkButton(
                actions_frame,
                text="👁 Просмотр",
                width=120,
                height=32,
                command=lambda s=study: self.handle_history_view(s),
                fg_color="#2196f3",
                hover_color="#1976d2"
            )
            view_btn.pack(side="left", padx=(0, 10))
            
            # Получаем результат анализа если есть
            study_id = study.get("id")
            if study_id:
                try:
                    analysis = self.api_client.get_study_analysis(study_id)
                    if analysis:
                        email_btn = ctk.CTkButton(
                            actions_frame,
                            text="📧 Отправить на email",
                            width=150,
                            height=32,
                            command=lambda a=analysis: self.send_result_email(a),
                            fg_color="#4caf50",
                            hover_color="#388e3c"
                        )
                        email_btn.pack(side="left")
                except:
                    pass
    
    def send_result_email(self, analysis_result: dict):
        """Отправить результаты анализа на email пациента"""
        result_id = analysis_result.get("id")
        if not result_id:
            messagebox.showerror("Ошибка", "Не удалось определить ID результата")
            return
        
        try:
            response = self.api_client.send_result_email(result_id)
            messagebox.showinfo(
                "Успех", 
                response.get("message", "Email успешно отправлен!")
            )
        except ApiError as e:
            messagebox.showerror("Ошибка", f"Не удалось отправить email: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    
    def show_history(self):
        """Показать страницу истории"""
        self.update_nav_buttons("history")
        self.page_title.configure(text="История исследований")
        
        # Очищаем контейнер безопасно
        try:
            widgets = list(self.content_container.winfo_children())
            for widget in widgets:
                try:
                    widget.destroy()
                except:
                    pass
        except:
            pass
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self.content_container,
            text="📊 История моих исследований",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        title_label.pack(pady=20)
        
        # Фильтры
        filters_frame = ctk.CTkFrame(self.content_container, fg_color="#212121")
        filters_frame.pack(fill="x", pady=(0, 20))
        
        filters_title = ctk.CTkLabel(
            filters_frame,
            text="🔍 Фильтры",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        filters_title.pack(pady=15)
        
        # Поля фильтров
        filters_content = ctk.CTkFrame(filters_frame, fg_color="transparent")
        filters_content.pack(fill="x", padx=20, pady=(0, 15))
        
        # Период
        period_frame = ctk.CTkFrame(filters_content, fg_color="transparent")
        period_frame.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(period_frame, text="Период:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        period_combo = ctk.CTkComboBox(
            period_frame,
            values=["За сегодня", "За неделю", "За месяц", "За год", "Все время"],
            width=150,
            height=30
        )
        period_combo.pack(anchor="w", pady=(5, 0))
        period_combo.set("За неделю")
        
        # Статус
        status_frame = ctk.CTkFrame(filters_content, fg_color="transparent")
        status_frame.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(status_frame, text="Статус:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        status_combo = ctk.CTkComboBox(
            status_frame,
            values=["Все", "Норма", "Подозрение", "Патология"],
            width=150,
            height=30
        )
        status_combo.pack(anchor="w", pady=(5, 0))
        status_combo.set("Все")
        
        # Кнопка применения фильтров
        apply_btn = ctk.CTkButton(
            filters_content,
            text="Применить",
            width=100,
            height=30,
            command=self.apply_history_filters
        )
        apply_btn.pack(side="left", padx=(20, 0))
        
        recent_items_raw = self.safe_api_call(
            lambda: self.api_client.get_dashboard_recent().get("items", []),
            default=[],
            error_message="Не удалось загрузить историю исследований",
        )
        prepared_history = [self.transform_result_item(item) for item in recent_items_raw]
        self.create_history_table(prepared_history)
    
    def create_history_table(self, studies):
        """Создание таблицы истории исследований"""
        history_frame = ctk.CTkFrame(self.content_container, fg_color="#212121")
        history_frame.pack(fill="both", expand=True)
        
        # Заголовки таблицы
        headers_frame = ctk.CTkFrame(history_frame, fg_color="transparent")
        headers_frame.pack(fill="x", padx=10, pady=10)
        
        headers = ["Дата", "Пациент", "Тип", "Результат", "Уверенность", "Статус", "Действия"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                headers_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="white"
            )
            label.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            headers_frame.grid_columnconfigure(i, weight=1)
        
        if not studies:
            empty_label = ctk.CTkLabel(
                history_frame,
                text="История исследований пуста",
                font=ctk.CTkFont(size=12),
                text_color="#9e9e9e",
            )
            empty_label.pack(pady=20)
            return
        
        for row, study in enumerate(studies, 1):
            row_frame = ctk.CTkFrame(history_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=2)
            
            # Дата
            date_label = ctk.CTkLabel(
                row_frame,
                text=study.get("date", "—"),
                font=ctk.CTkFont(size=11),
            )
            date_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
            
            # Пациент
            patient_label = ctk.CTkLabel(
                row_frame,
                text=study.get("patient", "—"),
                font=ctk.CTkFont(size=11),
            )
            patient_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            
            # Тип
            type_label = ctk.CTkLabel(
                row_frame,
                text=study.get("type", "Флюорография"),
                font=ctk.CTkFont(size=11),
            )
            type_label.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
            
            # Результат
            result_label = ctk.CTkLabel(
                row_frame,
                text=study.get("result", "—"),
                font=ctk.CTkFont(size=11),
                text_color=self.get_result_color(study.get("result")),
            )
            result_label.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
            
            # Уверенность
            confidence_label = ctk.CTkLabel(
                row_frame,
                text=study.get("confidence_display", "—"),
                font=ctk.CTkFont(size=11),
            )
            confidence_label.grid(row=0, column=4, padx=5, pady=5, sticky="ew")
            
            # Статус
            status_label = ctk.CTkLabel(
                row_frame,
                text=study.get("status_display", "—"),
                font=ctk.CTkFont(size=11),
                text_color=self.get_status_color(study.get("status_display", "")),
            )
            status_label.grid(row=0, column=5, padx=5, pady=5, sticky="ew")
            
            # Действия
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions_frame.grid(row=0, column=6, padx=5, pady=5, sticky="ew")
            
            view_btn = ctk.CTkButton(
                actions_frame,
                text="👁",
                width=30,
                height=25,
                command=lambda s=study: self.handle_history_view(s),
                fg_color="#00acc1",
                hover_color="#0097a7"
            )
            view_btn.pack(side="left", padx=2)
            
            edit_btn = ctk.CTkButton(
                actions_frame,
                text="✏️",
                width=30,
                height=25,
                command=lambda s=study: self.edit_study(s),
                fg_color="#ff9800",
                hover_color="#f57c00"
            )
            edit_btn.pack(side="left", padx=2)
            
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=1)
            row_frame.grid_columnconfigure(2, weight=1)
            row_frame.grid_columnconfigure(3, weight=1)
            row_frame.grid_columnconfigure(4, weight=1)
            row_frame.grid_columnconfigure(5, weight=1)
            row_frame.grid_columnconfigure(6, weight=1)
    
    def apply_history_filters(self):
        """Применение фильтров к истории"""
        messagebox.showinfo("Фильтры", "Фильтры применены (демо-режим)")
    
    def view_study_details(self, study):
        """Просмотр деталей исследования с медицинской формой"""
        print(f"[FRONTEND] view_study_details вызван, study keys: {study.keys() if isinstance(study, dict) else 'not a dict'}")
        print(f"[FRONTEND] study data: {study}")
        print(f"[FRONTEND] image_path в study: {study.get('image_path') if isinstance(study, dict) else 'N/A'}")
        
        details_window = ctk.CTkToplevel(self.parent)
        details_window.title("Результаты флюорографического исследования")
        
        # Делаем окно изменяемым по размеру
        details_window.resizable(True, True)
        
        # Устанавливаем минимальный размер
        details_window.minsize(800, 600)
        
        # Устанавливаем начальный размер (80% от экрана)
        screen_width = details_window.winfo_screenwidth()
        screen_height = details_window.winfo_screenheight()
        initial_width = int(screen_width * 0.8)
        initial_height = int(screen_height * 0.8)
        
        details_window.transient(self.parent)
        details_window.grab_set()
        
        # Центрирование окна
        details_window.update_idletasks()
        x = (screen_width // 2) - (initial_width // 2)
        y = (screen_height // 2) - (initial_height // 2)
        details_window.geometry(f"{initial_width}x{initial_height}+{x}+{y}")
        
        # Создаем главный контейнер с прокруткой
        main_container = ctk.CTkFrame(details_window, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Панель инструментов (кнопки управления)
        toolbar_frame = ctk.CTkFrame(main_container, fg_color="#2b2b2b", height=50)
        toolbar_frame.pack(fill="x", pady=(0, 10))
        toolbar_frame.pack_propagate(False)
        
        # Кнопка полноэкранного режима
        fullscreen_btn = ctk.CTkButton(
            toolbar_frame,
            text="⛶ Полный экран",
            width=120,
            height=35,
            command=lambda: self.toggle_fullscreen(details_window),
            fg_color="#4caf50",
            hover_color="#388e3c"
        )
        fullscreen_btn.pack(side="left", padx=10, pady=7)
        
        # Кнопка печати
        print_btn = ctk.CTkButton(
            toolbar_frame,
            text="🖨 Печать",
            width=120,
            height=35,
            command=lambda: self.print_results(details_window),
            fg_color="#2196f3",
            hover_color="#1976d2"
        )
        print_btn.pack(side="left", padx=5, pady=7)
        
        # Кнопка закрытия
        close_btn = ctk.CTkButton(
            toolbar_frame,
            text="✕ Закрыть",
            width=120,
            height=35,
            command=details_window.destroy,
            fg_color="#666666",
            hover_color="#555555"
        )
        close_btn.pack(side="right", padx=10, pady=7)
        
        # Создаем прокручиваемую область (используем CTkScrollableFrame)
        scrollable_frame = ctk.CTkScrollableFrame(main_container, fg_color="#1a1a1a")
        
        # Заголовок
        title_label = ctk.CTkLabel(
            scrollable_frame,
            text="Результаты флюорографического исследования",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        )
        title_label.pack(pady=20)
        
        # Создаем медицинскую форму
        self.create_medical_form(scrollable_frame, study)
        
        # Кнопки внизу формы
        buttons_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=20)
        
        # Упаковка прокручиваемой области
        scrollable_frame.pack(fill="both", expand=True)
        
        # Сохраняем ссылку на окно для полноэкранного режима
        details_window._is_fullscreen = False
        details_window._prev_geometry = None
    
    def create_medical_form(self, parent, study):
        """Создание медицинской формы результатов"""
        import random
        from datetime import datetime
        
        # Основная форма
        form_frame = ctk.CTkFrame(parent, fg_color="#212121")
        form_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Заголовок организации
        org_label = ctk.CTkLabel(
            form_frame,
            text="ГБУЗ \"Городская поликлиника №1\"\nг. Москва, ул. Медицинская, д. 1",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white"
        )
        org_label.pack(pady=15)
        
        # Разделитель
        separator = ctk.CTkFrame(form_frame, height=2, fg_color="#1a237e")
        separator.pack(fill="x", padx=20, pady=10)
        
        # Секция 0: Изображение исследования (если есть)
        image_path = study.get("image_path")
        if image_path:
            image_section = ctk.CTkFrame(form_frame, fg_color="#2b2b2b")
            image_section.pack(fill="x", padx=20, pady=10)
            
            image_title = ctk.CTkLabel(
                image_section,
                text="Рентгеновский снимок",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="white"
            )
            image_title.pack(pady=(15, 10))
            
            # Отображаем изображение
            self.render_image_preview(image_section, image_path)
        
        # Секция 1: Данные пациента и исследования
        self.create_patient_section(form_frame, study)
        
        # Секция 2: Подробное описание результатов
        self.create_description_section(form_frame, study)
        
        # Секция 3: Заключение
        self.create_conclusion_section(form_frame, study)
        
        # Секция 4: Рекомендации
        self.create_recommendations_section(form_frame, study)
    
    def create_patient_section(self, parent, study):
        """Создание секции данных пациента"""
        patient_frame = ctk.CTkFrame(parent, fg_color="transparent")
        patient_frame.pack(fill="x", padx=20, pady=10)
        
        # Заголовок секции
        section_title = ctk.CTkLabel(
            patient_frame,
            text="Данные пациента и исследования",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        section_title.pack(pady=10)
        
        # Получаем данные пациента, если нужно
        patient_name = "Неизвестно"
        patient_id = study.get("patient_id")
        if patient_id:
            try:
                patient_data = self.api_client.get_patient(patient_id)
                patient_name = patient_data.get("full_name", "Неизвестно")
            except:
                pass
        
        # Форматируем дату исследования
        taken_at = study.get("taken_at") or study.get("date", "")
        if taken_at:
            try:
                if isinstance(taken_at, str):
                    # Парсим ISO формат
                    dt = datetime.fromisoformat(taken_at.replace("Z", "+00:00"))
                    formatted_date = dt.strftime("%d.%m.%Y %H:%M")
                else:
                    formatted_date = str(taken_at)
            except:
                formatted_date = str(taken_at)
        else:
            formatted_date = "Не указано"
        
        # Разбиваем имя пациента на части
        name_parts = patient_name.split() if patient_name else []
        surname = name_parts[0] if len(name_parts) > 0 else "Иванов"
        first_name = name_parts[1] if len(name_parts) > 1 else "Иван"
        middle_name = name_parts[2] if len(name_parts) > 2 else "Иванович"
        
        # Поля формы
        fields = [
            ("Дата и время проведения исследования:", formatted_date),
            ("Фамилия:", surname),
            ("Имя:", first_name),
            ("Отчество:", middle_name),
            ("Пол (М/Ж):", "М"),
            ("Дата рождения:", "15.03.1979"),
            ("Номер медицинской карты:", str(patient_id) if patient_id else "Не указано"),
            ("Цель исследования:", "Профилактическое обследование"),
            ("Первичное/вторичное исследование:", "Первичное"),
            ("Краткий анамнез:", study.get("notes", "Жалоб не предъявляет")),
            ("Вид рентгенологического исследования:", "Флюорография органов грудной клетки"),
            ("Анатомическая область:", "Органы грудной клетки"),
            ("Наименование медицинского оборудования:", "Цифровой флюорограф ФЦ-01"),
            ("Эффективная доза:", "0.05 мЗв"),
            ("Ограничения визуализации:", "Нет")
        ]
        
        for label, value in fields:
            field_frame = ctk.CTkFrame(patient_frame, fg_color="transparent")
            field_frame.pack(fill="x", padx=10, pady=2)
            
            label_widget = ctk.CTkLabel(
                field_frame,
                text=label,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="white",
                width=300,
                anchor="w"
            )
            label_widget.pack(side="left")
            
            value_widget = ctk.CTkLabel(
                field_frame,
                text=value,
                font=ctk.CTkFont(size=12),
                text_color="white",
                anchor="w"
            )
            value_widget.pack(side="left", padx=(10, 0))
    
    def create_description_section(self, parent, study):
        """Создание секции подробного описания"""
        desc_frame = ctk.CTkFrame(parent, fg_color="#212121")
        desc_frame.pack(fill="x", padx=20, pady=10)
        
        # Заголовок секции
        section_title = ctk.CTkLabel(
            desc_frame,
            text="Подробное описание результатов проведенного рентгенологического исследования",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        section_title.pack(pady=10)
        
        # Описание результатов
        descriptions = {
            "Норма": "Легочные поля прозрачны, легочный рисунок четкий, структурный. Корни легких не расширены, структурны. Сердечная тень обычной формы и размеров. Диафрагма четкая, синусы свободны.",
            "Подозрение": "Легочные поля прозрачны. Легочный рисунок несколько усилен в прикорневых зонах. Корни легких незначительно расширены, структурны. Сердечная тень обычной формы. Диафрагма четкая.",
            "Патология": "В легочных полях определяются очаговые затемнения в S1-S2 сегментах правого легкого. Легочный рисунок усилен. Корни легких расширены, малоструктурны. Сердечная тень увеличена в поперечнике."
        }
        
        # Получаем результат из анализа, если есть
        result = study.get("result") or "Норма"
        description_text = descriptions.get(result, descriptions["Норма"])
        
        desc_text = ctk.CTkTextbox(
            desc_frame,
            height=100,
            font=ctk.CTkFont(size=12),
            text_color="white"
        )
        desc_text.pack(fill="x", padx=10, pady=(0, 10))
        desc_text.insert("1.0", description_text)
        desc_text.configure(state="disabled")
    
    def create_conclusion_section(self, parent, study):
        """Создание секции заключения"""
        conclusion_frame = ctk.CTkFrame(parent, fg_color="#212121")
        conclusion_frame.pack(fill="x", padx=20, pady=10)
        
        # Заголовок секции
        section_title = ctk.CTkLabel(
            conclusion_frame,
            text="Заключение по результатам рентгенологического исследования",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        section_title.pack(pady=10)
        
        # Заключения
        conclusions = {
            "Норма": "Рентгенологических признаков патологических изменений в органах грудной клетки не выявлено. Рекомендуется повторное обследование через 12 месяцев.",
            "Подозрение": "Рентгенологические признаки неспецифических изменений в прикорневых зонах легких. Рекомендуется контрольное обследование через 6 месяцев и консультация пульмонолога.",
            "Патология": "Рентгенологические признаки очаговых изменений в верхних долях легких. Требуется дообследование: компьютерная томография органов грудной клетки, консультация фтизиатра."
        }
        
        # Получаем результат из анализа, если есть
        result = study.get("result") or "Норма"
        conclusion_text = conclusions.get(result, conclusions["Норма"])
        
        conclusion_textbox = ctk.CTkTextbox(
            conclusion_frame,
            height=120,
            font=ctk.CTkFont(size=12),
            text_color="white"
        )
        conclusion_textbox.pack(fill="x", padx=10, pady=(0, 10))
        conclusion_textbox.insert("1.0", conclusion_text)
        conclusion_textbox.configure(state="disabled")
    
    def create_recommendations_section(self, parent, study):
        """Создание секции рекомендаций"""
        rec_frame = ctk.CTkFrame(parent, fg_color="#212121")
        rec_frame.pack(fill="x", padx=20, pady=10)
        
        # Заголовок секции
        section_title = ctk.CTkLabel(
            rec_frame,
            text="Рекомендации по дополнительному или контрольному обследованию",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        section_title.pack(pady=10)
        
        # Рекомендации
        recommendations = {
            "Норма": "Повторное флюорографическое обследование через 12 месяцев в рамках профилактического осмотра.",
            "Подозрение": "1. Контрольное флюорографическое обследование через 6 месяцев.\n2. Консультация пульмонолога.\n3. Общий анализ крови.",
            "Патология": "1. Компьютерная томография органов грудной клетки.\n2. Консультация фтизиатра.\n3. Общий анализ крови, анализ мокроты на БК.\n4. Повторное обследование через 3 месяца."
        }
        
        # Получаем результат из анализа, если есть
        result = study.get("result") or "Норма"
        rec_text = recommendations.get(result, recommendations["Норма"])
        
        rec_textbox = ctk.CTkTextbox(
            rec_frame,
            height=100,
            font=ctk.CTkFont(size=12),
            text_color="white"
        )
        rec_textbox.pack(fill="x", padx=10, pady=(0, 10))
        rec_textbox.insert("1.0", rec_text)
        rec_textbox.configure(state="disabled")
        
        # Подпись врача
        signature_frame = ctk.CTkFrame(rec_frame, fg_color="transparent")
        signature_frame.pack(fill="x", padx=10, pady=10)
        
        # Форматируем дату для подписи
        taken_at = study.get("taken_at") or study.get("date", "")
        if taken_at:
            try:
                if isinstance(taken_at, str):
                    dt = datetime.fromisoformat(taken_at.replace("Z", "+00:00"))
                    formatted_date = dt.strftime("%d.%m.%Y")
                else:
                    formatted_date = str(taken_at)
            except:
                formatted_date = str(taken_at)
        else:
            formatted_date = datetime.now().strftime("%d.%m.%Y")
        
        signature_label = ctk.CTkLabel(
            signature_frame,
            text=f"Врач-рентгенолог: {self.user_data.get('name', 'Неизвестно')}\nДата: {formatted_date}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="white"
        )
        signature_label.pack(anchor="e")
    
    def toggle_fullscreen(self, window):
        """Переключение полноэкранного режима"""
        if not hasattr(window, '_is_fullscreen'):
            window._is_fullscreen = False
            window._prev_geometry = None
        
        if window._is_fullscreen:
            # Выход из полноэкранного режима
            window.attributes('-fullscreen', False)
            window._is_fullscreen = False
            if window._prev_geometry:
                window.geometry(window._prev_geometry)
        else:
            # Вход в полноэкранный режим
            window._prev_geometry = window.geometry()
            window.attributes('-fullscreen', True)
            window._is_fullscreen = True
    
    def print_results(self, window):
        """Печать результатов"""
        messagebox.showinfo("Печать", "Результаты отправлены на печать (демо-режим)")
    
    def edit_study(self, study):
        """Редактирование исследования"""
        # Получаем ID исследования из данных
        study_id = study.get("id") or study.get("study_id")
        if not study_id:
            messagebox.showerror("Ошибка", "ID исследования не найден")
            return
        
        # Получаем полные данные исследования через API
        try:
            full_study = self.api_client.get_study(study_id)
        except ApiError as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные исследования: {e}")
            return
        
        # Создаем модальное окно для редактирования
        edit_window = ctk.CTkToplevel(self.parent)
        edit_window.title("Редактирование исследования")
        edit_window.geometry("500x400")
        edit_window.transient(self.parent)
        edit_window.grab_set()
        
        # Заголовок
        title_label = ctk.CTkLabel(
            edit_window,
            text="Редактирование исследования",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Форма редактирования
        form_frame = ctk.CTkFrame(edit_window)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Поля для редактирования
        ctk.CTkLabel(form_frame, text="Приоритет:").pack(anchor="w", padx=10, pady=(10, 5))
        priority_combo = ctk.CTkComboBox(
            form_frame,
            values=["routine", "urgent", "stat"],
            width=200
        )
        priority_combo.pack(anchor="w", padx=10, pady=(0, 10))
        priority_combo.set(full_study.get("priority", "routine"))
        
        ctk.CTkLabel(form_frame, text="Заметки:").pack(anchor="w", padx=10, pady=(10, 5))
        notes_text = ctk.CTkTextbox(form_frame, width=400, height=150)
        notes_text.pack(anchor="w", padx=10, pady=(0, 10))
        notes_text.insert("1.0", full_study.get("notes", ""))
        
        # Кнопки
        buttons_frame = ctk.CTkFrame(edit_window)
        buttons_frame.pack(pady=20)
        
        def save_changes():
            try:
                update_data = {
                    "priority": priority_combo.get(),
                    "notes": notes_text.get("1.0", "end-1c").strip()
                }
                
                self.api_client.update_study(study_id, update_data)
                messagebox.showinfo("Успех", "Исследование обновлено")
                edit_window.destroy()
                
                # Обновляем список исследований если открыта страница истории
                if hasattr(self, 'current_page') and self.current_page == "history":
                    self.show_history()
            except ApiError as e:
                messagebox.showerror("Ошибка", f"Ошибка при обновлении: {e}")
        
        save_btn = ctk.CTkButton(
            buttons_frame,
            text="Сохранить",
            command=save_changes,
            width=120
        )
        save_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Отмена",
            command=edit_window.destroy,
            width=120,
            fg_color="gray"
        )
        cancel_btn.pack(side="left", padx=10)
    
    def show_profile(self):
        """Показать страницу профиля"""
        self.update_nav_buttons("profile")
        self.page_title.configure(text="Мой профиль")
        
        # Очищаем контейнер безопасно
        try:
            widgets = list(self.content_container.winfo_children())
            for widget in widgets:
                try:
                    widget.destroy()
                except:
                    pass
        except:
            pass
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self.content_container,
            text="⚙️ Настройки профиля",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        title_label.pack(pady=20)
        
        # Информация о пользователе
        info_frame = ctk.CTkFrame(self.content_container, fg_color="#212121")
        info_frame.pack(fill="x", pady=20)
        
        info_title = ctk.CTkLabel(
            info_frame,
            text="Информация о враче",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        info_title.pack(pady=15)
        
        # Поля информации
        fields = [
            ("ФИО:", self.user_data["name"]),
            ("Роль:", "Врач-рентгенолог"),
            ("ID:", "DOC001"),
            ("Отделение:", "Рентгенология"),
            ("Стаж:", "5 лет")
        ]
        
        for label_text, value in fields:
            field_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            field_frame.pack(fill="x", padx=20, pady=5)
            
            label = ctk.CTkLabel(
                field_frame,
                text=label_text,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="white"
            )
            label.pack(side="left")
            
            value_label = ctk.CTkLabel(
                field_frame,
                text=value,
                font=ctk.CTkFont(size=14),
                text_color="white"
            )
            value_label.pack(side="left", padx=(10, 0))
    
    def update_nav_buttons(self, active_button):
        """Обновление состояния навигационных кнопок"""
        for key, button in self.nav_buttons.items():
            if key == active_button:
                button.configure(fg_color="#2196f3", text_color="white")
            else:
                button.configure(fg_color="transparent", text_color="white")
    
    def create_study_interface(self):
        """Создание интерфейса исследования в одном окне"""
        # Верхняя панель с информацией о пациенте
        patient_frame = ctk.CTkFrame(self.content_container, fg_color="#212121")
        patient_frame.pack(fill="x", pady=(0, 20))
        
        patient_title = ctk.CTkLabel(
            patient_frame,
            text="Информация о пациенте",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        patient_title.pack(pady=15)
        
        # Поля пациента
        patient_fields = ctk.CTkFrame(patient_frame, fg_color="transparent")
        patient_fields.pack(fill="x", padx=20, pady=(0, 15))
        
        # Сетка полей
        fields_grid = ctk.CTkFrame(patient_fields, fg_color="transparent")
        fields_grid.pack(fill="x")
        
        # ID пациента
        ctk.CTkLabel(fields_grid, text="ID пациента:", font=ctk.CTkFont(size=12)).grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")
        self.patient_id_entry = ctk.CTkEntry(fields_grid, placeholder_text="PAT001", width=150, height=30)
        self.patient_id_entry.grid(row=0, column=1, padx=(0, 20), pady=5, sticky="w")
        
        # ФИО пациента
        ctk.CTkLabel(fields_grid, text="ФИО:", font=ctk.CTkFont(size=12)).grid(row=0, column=2, padx=(0, 10), pady=5, sticky="w")
        self.patient_name_entry = ctk.CTkEntry(fields_grid, placeholder_text="Иванов И.И.", width=200, height=30)
        self.patient_name_entry.grid(row=0, column=3, padx=(0, 20), pady=5, sticky="w")
        
        # Возраст
        ctk.CTkLabel(fields_grid, text="Возраст:", font=ctk.CTkFont(size=12)).grid(row=1, column=0, padx=(0, 10), pady=5, sticky="w")
        self.patient_age_entry = ctk.CTkEntry(fields_grid, placeholder_text="45", width=80, height=30)
        self.patient_age_entry.grid(row=1, column=1, padx=(0, 20), pady=5, sticky="w")
        
        # Пол
        ctk.CTkLabel(fields_grid, text="Пол:", font=ctk.CTkFont(size=12)).grid(row=1, column=2, padx=(0, 10), pady=5, sticky="w")
        self.patient_gender_combo = ctk.CTkComboBox(fields_grid, values=["М", "Ж"], width=80, height=30)
        self.patient_gender_combo.grid(row=1, column=3, padx=(0, 20), pady=5, sticky="w")
        self.patient_gender_combo.set("М")
        
        # Кнопка загрузки снимка
        upload_btn = ctk.CTkButton(
            patient_fields,
            text="Загрузить снимок",
            width=150,
            height=35,
            command=self.upload_image,
            fg_color="#2196f3",
            hover_color="#1976d2"
        )
        upload_btn.pack(pady=15)
        
        # Основная область с снимком и результатами
        main_area = ctk.CTkFrame(self.content_container, fg_color="#212121")
        main_area.pack(fill="both", expand=True)
        
        # Левая часть - снимок
        image_frame = ctk.CTkFrame(main_area, fg_color="#212121")
        image_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        image_title = ctk.CTkLabel(
            image_frame,
            text="Рентгеновский снимок",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#ffffff"
        )
        image_title.pack(pady=15)
        
        # Область для отображения снимка
        self.image_display_frame = ctk.CTkFrame(image_frame, fg_color="#212121")
        self.image_display_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Заглушка для снимка
        self.image_placeholder = ctk.CTkLabel(
            self.image_display_frame,
            text="Загрузите снимок для анализа",
            font=ctk.CTkFont(size=14),
            text_color="#ffffff"
        )
        self.image_placeholder.pack(expand=True, pady=50)
        
        # Разделитель
        divider = ctk.CTkFrame(main_area, width=8, fg_color="#e0e0e0")
        divider.pack(side="left", fill="y", padx=20, pady=15)
        
        # Правая часть - результаты
        results_frame = ctk.CTkFrame(main_area, fg_color="#212121")
        results_frame.pack(side="right", fill="both", expand=True)
        
        results_title = ctk.CTkLabel(
            results_frame,
            text="Результаты анализа",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        )
        results_title.pack(pady=15)
        
        # Область для результатов
        self.results_display_frame = ctk.CTkFrame(results_frame, fg_color="#212121")
        self.results_display_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Заглушка для результатов
        self.results_placeholder = ctk.CTkLabel(
            self.results_display_frame,
            text="Результаты анализа появятся здесь",
            font=ctk.CTkFont(size=14),
            text_color="#ffffff"
        )
        self.results_placeholder.pack(expand=True, pady=50)
    
    def upload_image(self):
        """Обработка загрузки изображения"""
        # Проверяем заполненность полей
        if not self.patient_id_entry.get().strip() or not self.patient_name_entry.get().strip():
            messagebox.showwarning("Предупреждение", "Заполните ID и ФИО пациента")
            return
        
        # Выбираем файл изображения
        file_path = filedialog.askopenfilename(
            title="Выберите изображение флюорографии",
            filetypes=[
                ("Изображения", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                ("Все файлы", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        # Запускаем загрузку и анализ в отдельном потоке
        thread = threading.Thread(
            target=self.process_image_analysis,
            args=(file_path,),
            daemon=True
        )
        thread.start()
    
    def process_image_analysis(self, image_path: str):
        """Обработка изображения и анализ через API"""
        try:
            # Показываем индикатор загрузки
            self.show_loading()
            
            # Получаем данные пациента
            patient_name = self.patient_name_entry.get().strip()
            patient_id_str = self.patient_id_entry.get().strip()
            
            # Создаем или находим пациента
            try:
                patients = self.api_client.list_patients()
                patient = None
                for p in patients:
                    if str(p.get("id")) == patient_id_str or p.get("full_name") == patient_name:
                        patient = p
                        break
                
                if not patient:
                    # Создаем нового пациента
                    # Преобразуем возраст в дату рождения
                    birth_date = None
                    age_str = self.patient_age_entry.get().strip()
                    if age_str:
                        try:
                            age = int(age_str)
                            # Вычисляем примерную дату рождения (год назад от текущей даты)
                            today = date.today()
                            birth_date = date(today.year - age, today.month, today.day)
                        except (ValueError, TypeError):
                            pass  # Если возраст некорректный, оставляем None
                    
                    patient_data = {
                        "full_name": patient_name,
                        "email": f"patient_{patient_id_str}@example.com",
                        "medical_record_number": patient_id_str
                    }
                    if birth_date:
                        patient_data["birth_date"] = birth_date.isoformat()
                    
                    patient = self.api_client.create_patient(patient_data)
                
                patient_id = patient["id"]
            except ApiError as e:
                messagebox.showerror("Ошибка", f"Ошибка при работе с пациентом: {e}")
                self.hide_loading()
                return
            
            # Создаем исследование
            try:
                study = self.api_client.create_study({
                    "patient_id": patient_id,
                    "taken_at": datetime.now().isoformat(),
                    "priority": "routine",
                    "notes": f"Возраст: {self.patient_age_entry.get()}, Пол: {self.patient_gender_combo.get()}"
                })
                study_id = study["id"]
            except ApiError as e:
                messagebox.showerror("Ошибка", f"Ошибка при создании исследования: {e}")
                self.hide_loading()
                return
            
            # Загружаем изображение
            try:
                study = self.api_client.upload_study_image(study_id, image_path)
                # Изображение автоматически анализируется при загрузке
            except ApiError as e:
                messagebox.showerror("Ошибка", f"Ошибка при загрузке изображения: {e}")
                self.hide_loading()
                return
            
            # Получаем результаты анализа
            # Сначала пытаемся получить из базы (если анализ уже выполнен при загрузке)
            analysis_result = None
            try:
                # Пытаемся получить результаты из базы (если анализ уже выполнен)
                analysis_result = self.api_client.get_study_analysis(study_id)
            except ApiError:
                # Если результата еще нет, запускаем анализ
                try:
                    analysis_result = self.api_client.analyze_study(study_id)
                except ApiError as e:
                    # Если и это не удалось, используем fallback
                    analysis_result = None
            
            # Обновляем UI с результатами
            self.parent.after(0, lambda: self.update_image_display(image_path))
            
            # Формируем результаты для отображения
            if analysis_result:
                status_map = {
                    "clear": "Норма",
                    "pathology_detected": "Патология",
                    "needs_review": "Подозрение"
                }
                results = {
                    "status": status_map.get(analysis_result.get("ai_status", "needs_review"), "Подозрение"),
                    "confidence": round(analysis_result.get("ai_confidence", 0.5) * 100, 1),
                    "diagnosis": analysis_result.get("ai_diagnosis", ""),  # Диагноз
                    "findings": analysis_result.get("ai_findings", "Анализ выполнен"),
                    "recommendations": self._get_recommendations(analysis_result.get("ai_status", "needs_review")),
                    "analysis_time": 2.5
                }
            else:
                # Fallback на симуляцию, если анализ не вернул результаты
                results = {
                    "status": "Подозрение",
                    "confidence": 75.0,
                    "diagnosis": "Требуется дополнительный анализ",
                    "findings": "Анализ выполнен, требуется проверка",
                    "recommendations": "Повторное исследование через 6 месяцев",
                    "analysis_time": 2.5
                }
            
            self.parent.after(0, lambda: self.update_results_display(results))
            self.parent.after(0, self.hide_loading)
            
        except Exception as e:
            self.parent.after(0, lambda: messagebox.showerror("Ошибка", f"Неожиданная ошибка: {e}"))
            self.parent.after(0, self.hide_loading)
    
    def _get_recommendations(self, status: str) -> str:
        """Получить рекомендации на основе статуса"""
        recommendations_map = {
            "clear": "Повторное исследование через 12 месяцев",
            "pathology_detected": "Консультация пульмонолога, дополнительное обследование",
            "needs_review": "Повторное исследование через 6 месяцев, наблюдение в динамике"
        }
        return recommendations_map.get(status, "Повторное исследование через 6 месяцев")
    
    def show_loading(self):
        """Показать индикатор загрузки"""
        for widget in self.results_display_frame.winfo_children():
            widget.destroy()
        
        loading_label = ctk.CTkLabel(
            self.results_display_frame,
            text="⏳ Анализ изображения...\n\nПожалуйста, подождите",
            font=ctk.CTkFont(size=14),
            text_color="white"
        )
        loading_label.pack(expand=True, pady=50)
    
    def hide_loading(self):
        """Скрыть индикатор загрузки"""
        pass  # Будет заменено при обновлении результатов
    
    def update_image_display(self, image_path: str = None):
        """Обновление отображения снимка"""
        # Очищаем область снимка безопасно
        try:
            for widget in self.image_display_frame.winfo_children():
                try:
                    widget.destroy()
                except:
                    pass  # Игнорируем ошибки при уничтожении уже удаленных виджетов
        except:
            pass
        
        if image_path and Path(image_path).exists():
            try:
                # Загружаем и отображаем изображение
                img = Image.open(image_path)
                # Масштабируем для отображения
                max_size = 600
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Используем CTkImage вместо PhotoImage
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(max_size, max_size))
                
                image_label = ctk.CTkLabel(
                    self.image_display_frame,
                    image=ctk_image,
                    text=""
                )
                image_label.image = ctk_image  # Сохраняем ссылку
                image_label.pack(expand=True, pady=20)
            except Exception as e:
                # Если не удалось загрузить изображение, показываем заглушку
                image_label = ctk.CTkLabel(
                    self.image_display_frame,
                    text=f"📸 Рентгеновский снимок\n\nОшибка загрузки: {e}",
                    font=ctk.CTkFont(size=16),
                    text_color="white"
                )
                image_label.pack(expand=True, pady=50)
        else:
            # Заглушка если изображения нет
            image_label = ctk.CTkLabel(
                self.image_display_frame,
                text="📸 Рентгеновский снимок\n\nЗагрузите изображение",
                font=ctk.CTkFont(size=16),
                text_color="white"
            )
            image_label.pack(expand=True, pady=50)
        
        # Информация о пациенте на снимке
        patient_info = ctk.CTkLabel(
            self.image_display_frame,
            text=f"Пациент: {self.patient_name_entry.get()}\nID: {self.patient_id_entry.get()}",
            font=ctk.CTkFont(size=12),
            text_color="white"
        )
        patient_info.pack(pady=(0, 20))
    
    def update_results_display(self, results):
        """Обновление отображения результатов"""
        # Очищаем область результатов безопасно
        try:
            # Обновляем GUI перед уничтожением виджетов
            self.parent.update_idletasks()
            widgets = list(self.results_display_frame.winfo_children())
            for widget in widgets:
                try:
                    # Проверяем, что виджет еще существует
                    if widget.winfo_exists():
                        widget.destroy()
                except:
                    pass
            self.parent.update_idletasks()
        except:
            pass
        
        # ДИАГНОЗ СВЕРХУ (если есть)
        if results.get("diagnosis"):
            diagnosis_frame = ctk.CTkFrame(
                self.results_display_frame, 
                fg_color="#1a237e",
                corner_radius=10
            )
            diagnosis_frame.pack(fill="x", pady=(0, 15))
            
            diagnosis_title = ctk.CTkLabel(
                diagnosis_frame,
                text="Диагноз:",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#ffffff"
            )
            diagnosis_title.pack(anchor="w", padx=15, pady=(15, 5))
            
            diagnosis_text = ctk.CTkLabel(
                diagnosis_frame,
                text=results["diagnosis"],
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#ffffff",
                wraplength=400,
                justify="left"
            )
            diagnosis_text.pack(anchor="w", padx=15, pady=(0, 15))
        
        # Статус
        status_color = "#43a047" if results["status"] == "Норма" else "#ff9800" if results["status"] == "Подозрение" else "#d32f2f"
        status_frame = ctk.CTkFrame(self.results_display_frame, fg_color=status_color)
        status_frame.pack(fill="x", pady=(0, 15))
        
        status_label = ctk.CTkLabel(
            status_frame,
            text=f"Статус: {results['status']}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        status_label.pack(pady=15)
        
        # Детальное описание находок (из ML модели)
        findings_text = results.get("findings", "")
        if findings_text:
            desc_frame = ctk.CTkFrame(self.results_display_frame, fg_color="transparent")
            desc_frame.pack(fill="x", pady=(0, 10))
            
            desc_label = ctk.CTkLabel(
                desc_frame,
                text="Описание снимка:",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="white"
            )
            desc_label.pack(anchor="w", padx=10, pady=(10, 5))
            
            # Используем Textbox для многострочного текста
            desc_textbox = ctk.CTkTextbox(
                desc_frame,
                height=120,
                font=ctk.CTkFont(size=11),
                text_color="white",
                wrap="word"
            )
            desc_textbox.pack(fill="x", padx=10, pady=(0, 10))
            desc_textbox.insert("1.0", findings_text)
            desc_textbox.configure(state="disabled")  # Только для чтения
        
        # Метрики
        metrics_frame = ctk.CTkFrame(self.results_display_frame, fg_color="transparent")
        metrics_frame.pack(fill="both", expand=True)
        
        metrics = [
            ("Уверенность", f"{results['confidence']}%", "#2196f3"),
            ("Время анализа", f"{results['analysis_time']} сек", "#1a237e"),
            ("Доза облучения", "0.05 мЗв", "#ff9800")
        ]
        
        for label, value, color in metrics:
            metric_frame = ctk.CTkFrame(metrics_frame, fg_color=color)
            metric_frame.pack(fill="x", pady=3)
            
            value_label = ctk.CTkLabel(
                metric_frame,
                text=value,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="white"
            )
            value_label.pack(pady=(8, 3))
            
            label_widget = ctk.CTkLabel(
                metric_frame,
                text=label,
                font=ctk.CTkFont(size=10),
                text_color="white"
            )
            label_widget.pack(pady=(0, 8))
        
        # Рекомендации
        recommendations = {
            "Норма": "Повторное обследование через 12 месяцев",
            "Подозрение": "Контроль через 6 месяцев, консультация пульмонолога",
            "Патология": "КТ органов грудной клетки, консультация фтизиатра"
        }
        
        rec_text = recommendations.get(results["status"], recommendations["Норма"])
        
        rec_frame = ctk.CTkFrame(self.results_display_frame, fg_color="transparent")
        rec_frame.pack(fill="x", pady=(10, 0))
        
        rec_label = ctk.CTkLabel(
            rec_frame,
            text="Рекомендации:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="white"
        )
        rec_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        rec_text_widget = ctk.CTkLabel(
            rec_frame,
            text=rec_text,
            font=ctk.CTkFont(size=11),
            text_color="white",
            wraplength=300
        )
        rec_text_widget.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Кнопки действий
        actions_frame = ctk.CTkFrame(self.results_display_frame, fg_color="transparent")
        actions_frame.pack(fill="x", pady=(15, 0))
        
        save_btn = ctk.CTkButton(
            actions_frame,
            text="Сохранить",
            width=100,
            height=30,
            command=lambda: self.save_analysis_result(results),
            fg_color="#2196f3",
            hover_color="#1976d2"
        )
        save_btn.pack(side="left", padx=(0, 5))
        
        details_btn = ctk.CTkButton(
            actions_frame,
            text="Подробно",
            width=100,
            height=30,
            command=lambda: self.show_detailed_results(results),
            fg_color="#2196f3",
            hover_color="#1976d2"
        )
        details_btn.pack(side="left", padx=(0, 5))
        
        new_btn = ctk.CTkButton(
            actions_frame,
            text="Новое",
            width=80,
            height=30,
            command=self.start_new_study,
            fg_color="#ff9800",
            hover_color="#f57c00"
        )
        new_btn.pack(side="left")
    
    def show_detailed_results(self, results):
        '''Показать подробные результаты без редактирования (только просмотр).'''
        # Формируем объект исследования для подробной формы
        study_data = {
            'date': '15.01.2024 14:30',
            'patient': self.patient_name_entry.get() or 'Иванов И.И.',
            'type': 'Флюорография',
            'result': results.get('status', ''),
            'confidence': f"{results.get('confidence', 0)}%",
            'status': 'Завершено'
        }
        self.view_study_details(study_data)
    
    def save_analysis_result(self, results):
        """Сохранение результата анализа"""
        messagebox.showinfo("Сохранение", "Результат анализа сохранен в системе")
    
    def start_new_study(self):
        """Начать новое исследование"""
        # Очищаем поля
        self.patient_id_entry.delete(0, 'end')
        self.patient_name_entry.delete(0, 'end')
        self.patient_age_entry.delete(0, 'end')
        self.patient_gender_combo.set("М")
        
        # Сбрасываем отображение
        self.reset_display()
    
    def reset_display(self):
        """Сброс отображения к начальному состоянию"""
        # Очищаем область снимка безопасно
        try:
            widgets = list(self.image_display_frame.winfo_children())
            for widget in widgets:
                try:
                    widget.destroy()
                except:
                    pass
        except:
            pass
        
        self.image_placeholder = ctk.CTkLabel(
            self.image_display_frame,
            text="Загрузите снимок для анализа",
            font=ctk.CTkFont(size=14),
            text_color="white"
        )
        self.image_placeholder.pack(expand=True, pady=50)
        
        # Очищаем область результатов
        for widget in self.results_display_frame.winfo_children():
            widget.destroy()
        
        self.results_placeholder = ctk.CTkLabel(
            self.results_display_frame,
            text="Результаты анализа появятся здесь",
            font=ctk.CTkFont(size=14),
            text_color="white"
        )
        self.results_placeholder.pack(expand=True, pady=50)
    
    def search_patients(self):
        """Обработка поиска пациентов"""
        messagebox.showinfo("Поиск", "Функция поиска будет реализована в полной версии")
    
    # ------------------------------------------------------------------
    # Backend helpers и форматирование данных
    # ------------------------------------------------------------------
    def clear_content_container(self):
        """Безопасная очистка контейнера контента"""
        try:
            # Обновляем GUI перед уничтожением виджетов
            self.parent.update_idletasks()
            widgets = list(self.content_container.winfo_children())
            for widget in widgets:
                try:
                    # Проверяем, что виджет еще существует
                    if widget.winfo_exists():
                        widget.destroy()
                except:
                    pass
            self.parent.update_idletasks()
        except:
            pass

    def safe_api_call(self, func, default=None, *, error_message=None):
        try:
            return func()
        except ApiError as exc:
            if error_message:
                messagebox.showerror("Ошибка", f"{error_message}\n{exc}")
            return default

    def handle_pending_action(self, result_id, action):
        if not result_id:
            messagebox.showerror("Ошибка", "Не удалось определить исследование")
            return
        payload = {"action": action, "notes": None}
        response = self.safe_api_call(
            lambda: self.api_client.confirm_analysis(result_id, payload),
            default=None,
            error_message="Не удалось обновить статус исследования",
        )
        if response is None:
            return
        confirmation_text = (
            "Результат подтвержден и пациент уведомлен."
            if action == "approve"
            else "Результат отправлен на доработку."
        )
        messagebox.showinfo("Готово", confirmation_text)
        self.show_dashboard()

    def open_result_details(self, result_id):
        if not result_id:
            messagebox.showerror("Ошибка", "Не удалось загрузить подробности исследования")
            return
        detail = self.safe_api_call(
            lambda: self.api_client.get_analysis_detail(result_id),
            default=None,
            error_message="Не удалось загрузить подробности исследования",
        )
        if not detail:
            return
        self.show_result_detail_window(detail)

    def show_result_detail_window(self, detail):
        patient = detail.get("patient", {})
        study = detail.get("study", {})
        result = detail.get("result", {})

        window = ctk.CTkToplevel(self.parent)
        window.title(f"Исследование — {patient.get('full_name', 'Пациент')}")
        window.geometry("1024x720")
        window.transient(self.parent)
        window.grab_set()

        container = ctk.CTkFrame(window, fg_color="#1e1e1e")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        header = ctk.CTkLabel(
            container,
            text=f"Пациент: {patient.get('full_name', '—')}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white",
        )
        header.pack(anchor="w", pady=(0, 15))

        info_frame = ctk.CTkFrame(container, fg_color="#2b2b2b")
        info_frame.pack(fill="x", pady=(0, 15))
        info_frame.grid_columnconfigure(1, weight=1)

        info_items = [
            ("Дата рождения", patient.get("birth_date", "—")),
            ("E-mail", patient.get("email", "—")),
            ("Мед. карта", patient.get("medical_record_number", "—")),
            ("Дата исследования", self.format_datetime(study.get("taken_at"))),
            ("Приоритет", study.get("priority", "routine")),
            ("Заметки", study.get("notes") or "—"),
        ]

        for row, (label_text, value) in enumerate(info_items):
            label_widget = ctk.CTkLabel(
                info_frame,
                text=f"{label_text}:",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#bbbbbb",
            )
            label_widget.grid(row=row, column=0, padx=15, pady=6, sticky="w")

            value_widget = ctk.CTkLabel(
                info_frame,
                text=value,
                font=ctk.CTkFont(size=13),
                text_color="white",
            )
            value_widget.grid(row=row, column=1, padx=15, pady=6, sticky="w")

        status_frame = ctk.CTkFrame(container, fg_color="#2b2b2b")
        status_frame.pack(fill="x", pady=(0, 15))

        ai_status_label = ctk.CTkLabel(
            status_frame,
            text=f"Статус AI: {self.map_status_label(result.get('ai_status'))}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.get_result_color(self.map_status_label(result.get("ai_status"))),
        )
        ai_status_label.pack(anchor="w", padx=15, pady=(15, 5))

        confidence_label = ctk.CTkLabel(
            status_frame,
            text=f"Уверенность модели: {self.format_confidence(result.get('ai_confidence'))}",
            font=ctk.CTkFont(size=13),
            text_color="white",
        )
        confidence_label.pack(anchor="w", padx=15, pady=(0, 10))

        findings_label = ctk.CTkLabel(
            status_frame,
            text="Очаг заболевания / описание исследования:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#bbbbbb",
        )
        findings_label.pack(anchor="w", padx=15)

        findings_text = ctk.CTkTextbox(
            status_frame,
            height=120,
            font=ctk.CTkFont(size=12),
            text_color="white",
        )
        findings_text.pack(fill="x", padx=15, pady=(5, 15))
        findings_text.insert("1.0", result.get("ai_findings") or "Нет данных")
        findings_text.configure(state="disabled")
        
        # Кнопка отправки на email
        email_btn_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        email_btn_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        email_btn = ctk.CTkButton(
            email_btn_frame,
            text="📧 Отправить результаты на email",
            width=250,
            height=35,
            command=lambda: self.send_result_email(result),
            fg_color="#4caf50",
            hover_color="#388e3c",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        email_btn.pack(side="left")

        image_frame = ctk.CTkFrame(container, fg_color="#2b2b2b")
        image_frame.pack(fill="both", expand=True)

        image_title = ctk.CTkLabel(
            image_frame,
            text="Снимок исследования",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white",
        )
        image_title.pack(anchor="w", padx=15, pady=(15, 5))

        self.render_image_preview(image_frame, study.get("image_path"))

    def render_image_preview(self, parent, image_path):
        print(f"[FRONTEND] render_image_preview: image_path = {image_path}")
        
        # Очищаем предыдущие изображения безопасно
        try:
            for widget in list(parent.winfo_children()):
                try:
                    widget.destroy()
                except:
                    pass
        except:
            pass
        
        if not image_path:
            print(f"[FRONTEND] ✗ Путь к снимку не указан")
            ctk.CTkLabel(
                parent,
                text="Путь к снимку не указан",
                font=ctk.CTkFont(size=13),
                text_color="#bbbbbb",
            ).pack(padx=15, pady=15)
            return

        resolved_path = self.resolve_media_path(image_path)
        print(f"[FRONTEND] resolve_media_path вернул: {resolved_path}")
        
        if not resolved_path or not resolved_path.exists():
            print(f"[FRONTEND] ✗ Файл не найден: resolved_path={resolved_path}, exists={resolved_path.exists() if resolved_path else False}")
            ctk.CTkLabel(
                parent,
                text=f"Файл не найден: {image_path}",
                font=ctk.CTkFont(size=13),
                text_color="#bbbbbb",
            ).pack(padx=15, pady=15)
            return

        try:
            print(f"[FRONTEND] Открываем изображение: {resolved_path}")
            image = Image.open(resolved_path)
            print(f"[FRONTEND] Изображение открыто, размер: {image.size}")
            
            # Получаем размер родительского контейнера для адаптивного масштабирования
            try:
                parent.update_idletasks()
                max_width = parent.winfo_width() - 30  # Отступы
                max_height = 600  # Максимальная высота для изображения
                
                # Если родитель еще не отрисован, используем значения по умолчанию
                if max_width < 100:
                    max_width = 900
            except:
                max_width = 900
                max_height = 500
            
            # Сохраняем оригинальное соотношение сторон
            original_width, original_height = image.size
            ratio = min(max_width / original_width, max_height / original_height)
            
            # Не увеличиваем изображение, только уменьшаем если нужно
            if ratio < 1:
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
            else:
                new_width = original_width
                new_height = original_height
            
            # Ограничиваем максимальный размер
            new_width = min(new_width, max_width)
            new_height = min(new_height, max_height)
            
            image.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"[FRONTEND] Изображение уменьшено до: {image.size}")
            
            # Используем CTkImage вместо PhotoImage
            ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(new_width, new_height))
            print(f"[FRONTEND] CTkImage создан, размер: {new_width}x{new_height}")
            
            label = ctk.CTkLabel(parent, image=ctk_image, text="")
            label.image = ctk_image
            label.pack(padx=15, pady=15)
            print(f"[FRONTEND] ✓ Изображение отображено")
        except Exception as e:
            print(f"[FRONTEND] ✗ Ошибка при загрузке изображения: {e}")
            import traceback
            traceback.print_exc()
            ctk.CTkLabel(
                parent,
                text=f"Не удалось загрузить изображение: {e}",
                font=ctk.CTkFont(size=13),
                text_color="#bbbbbb",
            ).pack(padx=15, pady=15)

    def resolve_media_path(self, relative_path):
        if not relative_path:
            return None
        
        print(f"[FRONTEND] resolve_media_path: входной путь = {relative_path}")
        
        rel_path = Path(relative_path)
        candidates = []
        
        # Если путь абсолютный, проверяем его напрямую
        if rel_path.is_absolute():
            print(f"[FRONTEND] Путь абсолютный, проверяем напрямую: {rel_path}")
            if rel_path.exists():
                print(f"[FRONTEND] ✓ Файл найден: {rel_path}")
                return rel_path
            else:
                print(f"[FRONTEND] ✗ Абсолютный путь не существует: {rel_path}")
                candidates.append(rel_path)
        else:
            # Если путь относительный, пробуем разные варианты
            print(f"[FRONTEND] Путь относительный, пробуем варианты...")
            candidates.extend(
                [
                    self.project_root / relative_path,
                    self.project_root / "backend" / relative_path,
                    self.project_root / "frontend" / relative_path,
                ]
            )

        # Проверяем все кандидаты
        for candidate in candidates:
            try:
                absolute = candidate if candidate.is_absolute() else candidate.resolve()
                print(f"[FRONTEND] Проверяем кандидат: {absolute}")
                if absolute.exists():
                    print(f"[FRONTEND] ✓ Файл найден: {absolute}")
                    return absolute
                else:
                    print(f"[FRONTEND] ✗ Файл не существует: {absolute}")
            except Exception as e:
                print(f"[FRONTEND] Ошибка при проверке {candidate}: {e}")
                continue
        
        # Последняя попытка - проверить исходный путь
        if rel_path.exists():
            print(f"[FRONTEND] ✓ Исходный путь существует: {rel_path}")
            return rel_path
        
        print(f"[FRONTEND] ✗ Файл не найден ни по одному пути")
        return None

    def handle_history_view(self, study):
        result_id = (study.get("raw") or {}).get("result_id")
        if result_id:
            self.open_result_details(result_id)
        else:
            self.view_study_details(study)

    def calculate_success_rate(self, stats):
        processed = stats.get("processed") or 0
        manual = stats.get("manual_review") or 0
        if not processed:
            return "0"
        approved = max(processed - manual, 0)
        return str(round((approved / processed) * 100))

    def transform_result_item(self, item):
        taken_at = item.get("taken_at")
        return {
            "id": item.get("result_id") or item.get("id"),
            "study_id": item.get("study_id"),
            "date": self.format_datetime(taken_at),
            "time_short": self.format_time(taken_at),
            "patient": item.get("patient_name", "—"),
            "type": "Флюорография",
            "result": self.map_status_label(item.get("status")),
            "confidence_display": self.format_confidence(item.get("confidence")),
            "status_display": self.map_confirmation_status(item.get("confirmation_status")),
            "raw": item,
        }

    def parse_datetime(self, value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str) and value:
            normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
            try:
                return datetime.fromisoformat(normalized)
            except ValueError:
                return None
        return None

    def format_datetime(self, value):
        dt = self.parse_datetime(value)
        if not dt:
            return "—"
        return dt.strftime("%d.%m.%Y %H:%M")

    def format_time(self, value):
        dt = self.parse_datetime(value)
        if not dt:
            return "—"
        return dt.strftime("%H:%M")

    def format_confidence(self, value):
        if value is None:
            return "—"
        try:
            value = float(value)
        except (TypeError, ValueError):
            return "—"
        if value <= 1:
            value *= 100
        return f"{value:.0f}%"

    def map_status_label(self, status):
        mapping = {
            "clear": "Норма",
            "pathology_detected": "Патология",
            "needs_review": "Подозрение",
        }
        return mapping.get(status, status or "Неизвестно")

    def map_confirmation_status(self, status):
        mapping = {
            "approved": "✅ Подтверждено",
            "rejected": "❌ Отклонено",
            "pending": "⏳ Ожидает врача",
        }
        return mapping.get(status, "⏳ Ожидает врача")

    def get_result_color(self, label):
        if not label:
            return "#ffffff"
        if "Норма" in label:
            return "#43a047"
        if "Подозрение" in label:
            return "#ff9800"
        if "Патология" in label:
            return "#d32f2f"
        return "#ffffff"

    def get_status_color(self, label):
        if "✅" in label:
            return "#43a047"
        if "⚠️" in label or "⏳" in label:
            return "#ff9800"
        if "❌" in label:
            return "#d32f2f"
        return "#00acc1"

    def calculate_age(self, birth_date_str):
        dt = self.parse_datetime(birth_date_str)
        if not dt:
            return "—"
        birth = dt.date()
        today = date.today()
        years = today.year - birth.year - (
            (today.month, today.day) < (birth.month, birth.day)
        )
        return str(years)

    def darken_color(self, color):
        """Затемнение цвета для hover-эффекта"""
        color_map = {
            "#00acc1": "#0097a7",
            "#43a047": "#388e3c",
            "#ff9800": "#f57c00",
            "#7e57c2": "#6a4c93"
        }
        return color_map.get(color, color)
    
    def show(self):
        """Показать приложение"""
        self.main_frame.pack(fill="both", expand=True)
    
    def destroy(self):
        """Уничтожить приложение"""
        self.main_frame.destroy()
    
    def logout(self):
        """Выход из системы"""
        self.logout_callback()
