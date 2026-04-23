"""
Окно входа в систему с выбором роли
"""

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk

class LoginWindow:
    def __init__(self, parent, on_login_callback):
        self.parent = parent
        self.on_login_callback = on_login_callback
        
        # Создаем фрейм для окна входа
        self.frame = ctk.CTkFrame(parent)
        
        # Заголовок с иконкой
        header_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        header_frame.pack(pady=(50, 20))
        
        # Иконка
        icon_label = ctk.CTkLabel(
            header_frame,
            text="🏥",
            font=ctk.CTkFont(size=48)
        )
        icon_label.pack()
        
        self.title_label = ctk.CTkLabel(
            header_frame,
            text="FlurAI",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="#1a237e"
        )
        
        self.subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Система анализа флюорографии",
            font=ctk.CTkFont(size=18),
            text_color="#1a237e"
        )
        
        # Выбор роли
        self.role_label = ctk.CTkLabel(
            self.frame,
            text="Выберите роль:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1a237e"
        )
        
        self.role_var = tk.StringVar(value="doctor")
        
        self.doctor_radio = ctk.CTkRadioButton(
            self.frame,
            text="Врач-рентгенолог",
            variable=self.role_var,
            value="doctor",
            font=ctk.CTkFont(size=14)
        )
        
        self.admin_radio = ctk.CTkRadioButton(
            self.frame,
            text="Администратор",
            variable=self.role_var,
            value="admin",
            font=ctk.CTkFont(size=14)
        )
        
        # Поля входа
        self.username_label = ctk.CTkLabel(
            self.frame,
            text="Логин:",
            font=ctk.CTkFont(size=14)
        )
        
        self.username_entry = ctk.CTkEntry(
            self.frame,
            placeholder_text="Введите логин",
            width=250,
            height=35,
            font=ctk.CTkFont(size=14)
        )
        
        self.password_label = ctk.CTkLabel(
            self.frame,
            text="Пароль:",
            font=ctk.CTkFont(size=14)
        )
        
        self.password_entry = ctk.CTkEntry(
            self.frame,
            placeholder_text="Введите пароль",
            width=250,
            height=35,
            font=ctk.CTkFont(size=14),
            show="*"
        )
        
        # Кнопки
        self.login_button = ctk.CTkButton(
            self.frame,
            text="Войти",
            width=250,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.login,
            fg_color="#2196f3",
            hover_color="#1976d2"
        )
        
        self.demo_button = ctk.CTkButton(
            self.frame,
            text="Демо-режим",
            width=120,
            height=35,
            font=ctk.CTkFont(size=12),
            command=self.demo_login,
            fg_color="#2196f3",
            hover_color="#1976d2"
        )
        
        # Размещение элементов
        self.setup_layout()
        
        # Добавляем градиентный фон
        self.frame.configure(fg_color=("#f0f0f0", "#2b2b2b"))
        
        # Привязка Enter к полю пароля
        self.password_entry.bind("<Return>", lambda e: self.login())
    
    def setup_layout(self):
        """Размещение элементов интерфейса"""
        self.frame.pack(expand=True, fill="both")
        
        # Центрирование контента
        main_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        main_frame.pack(expand=True, fill="both")
        
        # Заголовок
        self.title_label.pack(pady=(50, 10))
        self.subtitle_label.pack(pady=(0, 40))
        
        # Выбор роли
        self.role_label.pack(pady=(0, 15))
        self.doctor_radio.pack(pady=5)
        self.admin_radio.pack(pady=5)
        
        # Поля входа
        self.username_label.pack(pady=(30, 5))
        self.username_entry.pack(pady=(0, 15))
        
        self.password_label.pack(pady=(0, 5))
        self.password_entry.pack(pady=(0, 30))
        
        # Кнопки
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack()
        
        self.login_button.pack(side="left", padx=(0, 10))
        self.demo_button.pack(side="left")
    
    def login(self):
        """Обработка входа"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_var.get()
        
        if not username or not password:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return
        
        # Заглушка аутентификации
        if self.authenticate(username, password, role):
            user_data = {
                "username": username,
                "role": role,
                "name": self.get_user_name(role)
            }
            self.on_login_callback(role, user_data)
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")
    
    def demo_login(self):
        """Демо-вход для тестирования"""
        role = self.role_var.get()
        user_data = {
            "username": f"demo_{role}",
            "role": role,
            "name": self.get_user_name(role)
        }
        self.on_login_callback(role, user_data)
    
    def authenticate(self, username, password, role):
        """Заглушка аутентификации"""
        # В реальном приложении здесь будет проверка в базе данных
        demo_users = {
            "doctor": {"username": "doctor", "password": "123"},
            "admin": {"username": "admin", "password": "123"}
        }
        
        if role in demo_users:
            return (username == demo_users[role]["username"] and 
                   password == demo_users[role]["password"])
        return False
    
    def get_user_name(self, role):
        """Получение имени пользователя по роли"""
        names = {
            "doctor": "Доктор Иванов А.В.",
            "admin": "Администратор Петров С.И."
        }
        return names.get(role, "Пользователь")
    
    def show(self):
        """Показать окно входа"""
        self.frame.pack(expand=True, fill="both")
        self.username_entry.focus()
    
    def hide(self):
        """Скрыть окно входа"""
        self.frame.pack_forget()
