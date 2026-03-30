"""
FlurAI - Система анализа флюорографии
Desktop-приложение с ролевой системой (Врач/Администратор)
"""

import customtkinter as ctk
from tkinter import messagebox
import sys
import os

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth.login_window import LoginWindow
from doctor.doctor_app import DoctorApp
from admin.admin_app import AdminApp

class FlurAIApp:
    def __init__(self):
        # Настройка темы CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("FlurAI - Система анализа флюорографии")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Центрирование окна
        self.center_window()
        
        # Текущее приложение (врач/админ)
        self.current_app = None
        
        # Запуск экрана входа
        self.show_login()
    
    def center_window(self):
        """Центрирование окна на экране"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def show_login(self):
        """Показать экран входа"""
        if self.current_app:
            self.current_app.destroy()
            self.current_app = None
        
        self.login_window = LoginWindow(self.root, self.on_login_success)
        self.login_window.show()
    
    def on_login_success(self, role, user_data):
        """Обработка успешного входа"""
        self.login_window.hide()
        
        if role == "doctor":
            self.current_app = DoctorApp(self.root, user_data, self.logout)
        elif role == "admin":
            self.current_app = AdminApp(self.root, user_data, self.logout)
        
        self.current_app.show()
    
    def logout(self):
        """Выход из системы"""
        if self.current_app:
            self.current_app.destroy()
            self.current_app = None
        
        self.show_login()
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()

if __name__ == "__main__":
    app = FlurAIApp()
    app.run()

