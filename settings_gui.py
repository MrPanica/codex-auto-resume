# -*- coding: utf-8 -*-
"""
Codex Auto-Resume Settings & Localization Module
Менеджер настроек, локализация (RU/EN) и графическое окно настроек на PyQt6.
100% непрозрачный интерфейс (защита от багов прозрачности DWM в Windows 11).
"""

import os
import sys
import json
import time
import ctypes
import logging

from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QPushButton, QComboBox, QSlider, QSpinBox, QListWidget,
    QListWidgetItem, QLineEdit, QGroupBox, QMessageBox, QFrame, QStyleOption, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QPainter

logger = logging.getLogger("CodexTrayApp")

USER_PROFILE = os.environ.get("USERPROFILE", r"C:\Users\Artur")
CODEX_DIR = os.path.join(USER_PROFILE, ".codex")
SETTINGS_FILE = os.path.join(CODEX_DIR, "guardian_settings.json")
SESSION_INDEX_FILE = os.path.join(CODEX_DIR, "session_index.jsonl")

# -------------------------------------------------------------
# Дефолтная конфигурация
# -------------------------------------------------------------
DEFAULT_SETTINGS = {
    "language": "auto",  # "auto", "ru", "en"
    "autostart_windows": True,
    "enable_on_codex_start": True,
    "notify_on_toggle": True,
    "notify_on_resume": False,
    "sound_on_resume": False,
    "retry_pause_seconds": 10.0,
    "post_resume_cooldown": 6.0,
    "poll_interval_seconds": 1.0,
    "max_retries_consecutive": 10,
    "error_patterns": [
        {"pattern": "selected model is at capacity", "name": "Model Capacity / Server Overload", "enabled": True, "custom": False},
        {"pattern": "error running remote compact task", "name": "Remote Compact Task Error", "enabled": True, "custom": False},
        {"pattern": "stream disconnected", "name": "Stream Disconnected / Network Loss", "enabled": True, "custom": False},
        {"pattern": "connection lost", "name": "Connection Lost", "enabled": True, "custom": False},
        {"pattern": "rate limit", "name": "Rate Limit Exceeded", "enabled": True, "custom": False},
        {"pattern": "timeout", "name": "Request Timeout", "enabled": True, "custom": False},
        {"pattern": "an unexpected error occurred", "name": "Unexpected Server Error", "enabled": True, "custom": False},
        {"pattern": "serveroverloaded", "name": "Server Overloaded Code", "enabled": True, "custom": False}
    ],
    "excluded_projects": []
}

# -------------------------------------------------------------
# Словарь локализации (RU / EN)
# -------------------------------------------------------------
TRANSLATIONS = {
    "ru": {
        "menu_auto_resume_on": "🟢 Авто-возобновление: ВКЛЮЧЕНО",
        "menu_auto_resume_off": "⚪ Авто-возобновление: ВЫКЛЮЧЕНО",
        "menu_goals_submenu": "🎯 Задачи и цели Codex",
        "menu_no_goals": "(Нет недавних целей)",
        "menu_force_resume": "⚡ Возобновить цель сейчас",
        "menu_resumes_count": "📊 Возобновлено за сессию: {count}",
        "menu_settings": "⚙️ Настройки...",
        "menu_open_log": "📜 Открыть журнал (guardian.log)",
        "menu_open_folder": "📁 Открыть папку настроек (.codex)",
        "menu_autostart_windows": "🚀 Запускать при старте Windows",
        "menu_exit": "❌ Выход (закрыть сторож)",
        "tip_enabled": "Codex Auto-Resume: ВКЛЮЧЕНО",
        "tip_disabled": "Codex Auto-Resume: ВЫКЛЮЧЕНО (пауза)",
        "tip_goals": "Цели ({count}): {names}",
        "tip_resumes": "Возобновлений: {count}",
        "notif_app_title": "Codex Auto-Resume",
        "notif_started": "Сторож активен в системном трее.\nСостояние: {state}",
        "notif_state_on": "Авто-возобновление целей: ВКЛЮЧЕНО 🟢",
        "notif_state_off": "Авто-возобновление целей: ВЫКЛЮЧЕНО (пауза) ⚪",
        "notif_force_resume": "Запущено немедленное возобновление цели ⚡",
        "notif_autostart_on": "Автозагрузка при старте Windows включена.",
        "notif_autostart_off": "Автозагрузка при старте Windows отключена.",
        "dialog_title": "Настройки Codex Auto-Resume",
        "tab_general": "Общие и Запуск",
        "tab_errors": "Ошибки",
        "tab_projects": "Проекты",
        "tab_timers": "Тайминги и Лимиты",
        "grp_language": "Язык интерфейса",
        "lang_auto": "Автоматически (Язык системы)",
        "lang_ru": "Русский (Russian)",
        "lang_en": "English (Английский)",
        "grp_startup": "Параметры запуска",
        "chk_autostart_windows": "Запускать сторож при старте Windows",
        "chk_enable_on_codex_start": "Включать авто-возобновление при старте Кодекса",
        "grp_notifications": "Оповещения",
        "chk_notify_toggle": "Уведомление Windows при переключении (ярлык / трей)",
        "chk_notify_resume": "Уведомление Windows при возобновлении (может мешать играм)",
        "chk_sound_resume": "Звуковой сигнал при авто-возобновлении",
        "grp_error_patterns": "Отслеживаемые типы ошибок",
        "lbl_new_error": "Добавить новую ошибку (текст или ключевое слово):",
        "placeholder_new_error": "Например: rate limit reached или context length exceeded",
        "btn_add_error": "➕ Добавить",
        "btn_delete_error": "🗑️ Удалить выбранную",
        "btn_reset_errors": "🔄 Сбросить по умолчанию",
        "grp_projects": "Участвующие проекты",
        "lbl_projects_desc": "Сторож будет автоматически возобновлять цели только в отмеченных проектах:",
        "btn_select_all": "✅ Выбрать все",
        "btn_deselect_all": "❌ Снять все",
        "grp_timers": "Тайминги авто-возобновления",
        "lbl_retry_pause": "Пауза перед возобновлением после ошибки:",
        "lbl_cooldown": "Защитный кулдаун после успешного возобновления:",
        "lbl_poll_interval": "Интервал проверки состояния:",
        "lbl_max_retries": "Максимум попыток подряд:",
        "unit_seconds": "сек.",
        "unlimited": "Без ограничений",
        "btn_save": "💾 Сохранить",
        "btn_cancel": "Отмена",
        "btn_apply": "Применить",
        "msg_saved_title": "Успешно",
        "msg_saved": "Настройки успешно сохранены и применены!"
    },
    "en": {
        "menu_auto_resume_on": "🟢 Auto-Resume: ENABLED",
        "menu_auto_resume_off": "⚪ Auto-Resume: DISABLED",
        "menu_goals_submenu": "🎯 Codex Goals & Tasks",
        "menu_no_goals": "(No recent goals)",
        "menu_force_resume": "⚡ Resume Goal Now",
        "menu_resumes_count": "📊 Resumed this session: {count}",
        "menu_settings": "⚙️ Settings...",
        "menu_open_log": "📜 Open Log (guardian.log)",
        "menu_open_folder": "📁 Open Config Folder (.codex)",
        "menu_autostart_windows": "🚀 Launch on Windows Startup",
        "menu_exit": "❌ Exit (Close Watchdog)",
        "tip_enabled": "Codex Auto-Resume: ENABLED",
        "tip_disabled": "Codex Auto-Resume: DISABLED (Paused)",
        "tip_goals": "Goals ({count}): {names}",
        "tip_resumes": "Resumes: {count}",
        "notif_app_title": "Codex Auto-Resume",
        "notif_started": "Watchdog active in system tray.\nState: {state}",
        "notif_state_on": "Auto-Resume goals: ENABLED 🟢",
        "notif_state_off": "Auto-Resume goals: DISABLED (Paused) ⚪",
        "notif_force_resume": "Immediate goal resume triggered ⚡",
        "notif_autostart_on": "Windows startup launch enabled.",
        "notif_autostart_off": "Windows startup launch disabled.",
        "dialog_title": "Codex Auto-Resume Settings",
        "tab_general": "General & Startup",
        "tab_errors": "Errors",
        "tab_projects": "Projects",
        "tab_timers": "Timers & Limits",
        "grp_language": "Interface Language",
        "lang_auto": "Auto (System Default)",
        "lang_ru": "Russian (Русский)",
        "lang_en": "English",
        "grp_startup": "Startup Options",
        "chk_autostart_windows": "Launch watchdog on Windows startup",
        "chk_enable_on_codex_start": "Enable auto-resume when Codex starts",
        "grp_notifications": "Notifications",
        "chk_notify_toggle": "Windows notification on manual toggle (shortcut / tray)",
        "chk_notify_resume": "Windows notification on auto-resume (may disrupt games)",
        "chk_sound_resume": "Play sound chime on auto-resume",
        "grp_error_patterns": "Monitored Error Types",
        "lbl_new_error": "Add new error pattern (text or keyword):",
        "placeholder_new_error": "E.g.: rate limit reached or context length exceeded",
        "btn_add_error": "➕ Add",
        "btn_delete_error": "🗑️ Delete Selected",
        "btn_reset_errors": "🔄 Reset to Default",
        "grp_projects": "Active Projects",
        "lbl_projects_desc": "Watchdog will automatically resume goals only in checked projects:",
        "btn_select_all": "✅ Select All",
        "btn_deselect_all": "❌ Deselect All",
        "grp_timers": "Auto-Resume Timers",
        "lbl_retry_pause": "Pause before resume after error:",
        "lbl_cooldown": "Cooldown after successful resume:",
        "lbl_poll_interval": "Status polling interval:",
        "lbl_max_retries": "Max consecutive retries:",
        "unit_seconds": "sec.",
        "unlimited": "Unlimited",
        "btn_save": "💾 Save",
        "btn_cancel": "Cancel",
        "btn_apply": "Apply",
        "msg_saved_title": "Success",
        "msg_saved": "Settings successfully saved and applied!"
    }
}

def detect_system_language():
    """Определение языка системы Windows (0x419 = Русский, остальные = English)"""
    try:
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        if (lang_id & 0xFF) == 0x19: # Russian primary language
            return "ru"
    except Exception:
        pass
    return "en"

# -------------------------------------------------------------
# Класс управления настройками
# -------------------------------------------------------------
class SettingsManager:
    def __init__(self):
        self.settings = dict(DEFAULT_SETTINGS)
        self.load()

    def get_effective_language(self):
        cfg_lang = self.settings.get("language", "auto")
        if cfg_lang == "auto":
            return detect_system_language()
        return cfg_lang if cfg_lang in ("ru", "en") else "en"

    def tr(self, key, **kwargs):
        lang = self.get_effective_language()
        text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception:
                pass
        return text

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.settings[k] = v
            except Exception as e:
                logger.error(f"Ошибка загрузки настроек: {e}")

    def save(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            logger.info("Настройки успешно сохранены в guardian_settings.json")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")
            return False

    def is_error_allowed(self, err_text):
        """Проверка, разрешено ли возобновление для данной ошибки"""
        if not err_text:
            return True
        err_lower = str(err_text).lower()
        patterns = self.settings.get("error_patterns", [])
        active_patterns = [p for p in patterns if p.get("enabled", True)]
        if not active_patterns:
            return False
        for p in active_patterns:
            pat_str = p.get("pattern", "").strip().lower()
            if pat_str and pat_str in err_lower:
                return True
        return False

    def is_project_allowed(self, project_path_or_name):
        """Проверка, разрешен ли проект"""
        if not project_path_or_name:
            return True
        excluded = self.settings.get("excluded_projects", [])
        p_str = str(project_path_or_name).strip().lower()
        for ex in excluded:
            ex_clean = str(ex).strip().lower()
            if ex_clean and (ex_clean == p_str or ex_clean in p_str or p_str in ex_clean):
                return False
        return True

settings_mgr = SettingsManager()

def get_all_codex_projects():
    """Сбор всех уникальных проектов из session_index.jsonl"""
    projects = {}
    if os.path.exists(SESSION_INDEX_FILE):
        try:
            with open(SESSION_INDEX_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        cwd = obj.get("cwd")
                        if cwd:
                            norm = os.path.normpath(cwd).replace("\\\\?\\", "")
                            base = os.path.basename(norm) or norm
                            if norm not in projects:
                                projects[norm] = base
                    except Exception:
                        pass
        except Exception:
            pass
    return projects

# -------------------------------------------------------------
# 100% Непрозрачный контейнер для вкладок
# -------------------------------------------------------------
class TabContainer(QWidget):
    """Специальный виджет с гарантированной сплошной фоновой отрисовкой (без прозрачности)"""
    def __init__(self, bg_color="#1e1e2e"):
        super().__init__()
        self.bg_color = QColor(bg_color)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, self.bg_color)
        self.setPalette(pal)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), self.bg_color)
        p.end()
        super().paintEvent(event)

# -------------------------------------------------------------
# Графический интерфейс окна настроек (PyQt6)
# -------------------------------------------------------------
class SettingsDialog(QDialog):
    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mgr = settings_mgr

        # Гарантируем сплошной непрозрачный фон для всего окна на уровне Windows DWM
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("#181825"))
        pal.setColor(QPalette.ColorRole.WindowText, QColor("#cdd6f4"))
        pal.setColor(QPalette.ColorRole.Base, QColor("#1e1e2e"))
        self.setPalette(pal)

        # Иконка окна настроек
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.init_ui()
        self.load_values()
        self.apply_translations()

    def paintEvent(self, event):
        # Принудительная 100% заливка фоном каждого пикселя окна
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#181825"))
        p.end()
        super().paintEvent(event)

    def init_ui(self):
        self.setMinimumSize(640, 530)
        self.resize(700, 580)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        # Тёмный стиль Fluent Dark
        self.setStyleSheet("""
            QDialog {
                background-color: #181825;
                color: #cdd6f4;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QTabWidget::pane {
                border: 1px solid #313244;
                background: #1e1e2e;
                border-radius: 8px;
                padding: 10px;
            }
            QTabBar::tab {
                background: #181825;
                color: #a6adc8;
                padding: 8px 18px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: 1px solid #313244;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background: #1e1e2e;
                color: #89b4fa;
                border: 1px solid #45475a;
                border-bottom: 1px solid #1e1e2e;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                color: #cdd6f4;
                background: #252538;
            }
            QGroupBox {
                border: 1px solid #313244;
                background-color: #1e1e2e;
                border-radius: 6px;
                margin-top: 14px;
                padding-top: 12px;
                font-weight: bold;
                color: #89b4fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                background-color: #1e1e2e;
            }
            QCheckBox {
                color: #cdd6f4;
                spacing: 8px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #45475a;
                background: #181825;
            }
            QCheckBox::indicator:checked {
                background: #10b981;
                border: 1px solid #059669;
            }
            QComboBox, QSpinBox, QLineEdit {
                background: #181825;
                border: 1px solid #45475a;
                border-radius: 5px;
                padding: 5px 8px;
                color: #cdd6f4;
            }
            QComboBox:hover, QSpinBox:hover, QLineEdit:hover {
                border: 1px solid #89b4fa;
            }
            QListWidget {
                background: #181825;
                border: 1px solid #313244;
                border-radius: 6px;
                color: #cdd6f4;
            }
            QListWidget::item {
                padding: 6px 4px;
                border-bottom: 1px solid #252538;
            }
            QListWidget::item:hover {
                background: #252538;
            }
            QPushButton {
                background: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #45475a;
                border-color: #89b4fa;
            }
            QPushButton#btnSave {
                background: #10b981;
                color: #ffffff;
                border: 1px solid #059669;
                font-weight: bold;
            }
            QPushButton#btnSave:hover {
                background: #059669;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #313244;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #10b981;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #cdd6f4;
                border: 1px solid #10b981;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
        """)

        main_layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # 1. Вкладка Общие и Запуск
        self.tab_general = TabContainer("#1e1e2e")
        self.init_tab_general()
        self.tabs.addTab(self.tab_general, "")

        # 2. Вкладка Ошибки
        self.tab_errors = TabContainer("#1e1e2e")
        self.init_tab_errors()
        self.tabs.addTab(self.tab_errors, "")

        # 3. Вкладка Проекты
        self.tab_projects = TabContainer("#1e1e2e")
        self.init_tab_projects()
        self.tabs.addTab(self.tab_projects, "")

        # 4. Вкладка Тайминги
        self.tab_timers = TabContainer("#1e1e2e")
        self.init_tab_timers()
        self.tabs.addTab(self.tab_timers, "")

        # Нижняя панель с кнопками
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_cancel = QPushButton()
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        self.btn_apply = QPushButton()
        self.btn_apply.clicked.connect(self.save_values)
        btn_box.addWidget(self.btn_apply)

        self.btn_save = QPushButton()
        self.btn_save.setObjectName("btnSave")
        self.btn_save.clicked.connect(self.on_save_and_close)
        btn_box.addWidget(self.btn_save)

        main_layout.addLayout(btn_box)

    def init_tab_general(self):
        layout = QVBoxLayout(self.tab_general)

        # Язык
        self.grp_lang = QGroupBox()
        l_layout = QHBoxLayout(self.grp_lang)
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("", "auto")
        self.combo_lang.addItem("", "ru")
        self.combo_lang.addItem("", "en")
        self.combo_lang.currentIndexChanged.connect(self.on_language_changed)
        l_layout.addWidget(self.combo_lang)
        layout.addWidget(self.grp_lang)

        # Запуск
        self.grp_startup = QGroupBox()
        s_layout = QVBoxLayout(self.grp_startup)
        self.chk_autostart_win = QCheckBox()
        self.chk_codex_start = QCheckBox()
        s_layout.addWidget(self.chk_autostart_win)
        s_layout.addWidget(self.chk_codex_start)
        layout.addWidget(self.grp_startup)

        # Оповещения
        self.grp_notif = QGroupBox()
        n_layout = QVBoxLayout(self.grp_notif)
        self.chk_notify_toggle = QCheckBox()
        self.chk_notify_resume = QCheckBox()
        self.chk_sound_resume = QCheckBox()
        n_layout.addWidget(self.chk_notify_toggle)
        n_layout.addWidget(self.chk_notify_resume)
        n_layout.addWidget(self.chk_sound_resume)
        layout.addWidget(self.grp_notif)

        layout.addStretch()

    def init_tab_errors(self):
        layout = QVBoxLayout(self.tab_errors)

        self.grp_errors = QGroupBox()
        e_layout = QVBoxLayout(self.grp_errors)

        self.list_errors = QListWidget()
        e_layout.addWidget(self.list_errors)

        self.lbl_new_error = QLabel()
        e_layout.addWidget(self.lbl_new_error)

        input_row = QHBoxLayout()
        self.edit_new_error = QLineEdit()
        input_row.addWidget(self.edit_new_error)

        self.btn_add_error = QPushButton()
        self.btn_add_error.clicked.connect(self.on_add_error)
        input_row.addWidget(self.btn_add_error)
        e_layout.addLayout(input_row)

        ctrl_row = QHBoxLayout()
        self.btn_del_error = QPushButton()
        self.btn_del_error.clicked.connect(self.on_delete_error)
        ctrl_row.addWidget(self.btn_del_error)

        ctrl_row.addStretch()

        self.btn_reset_errors = QPushButton()
        self.btn_reset_errors.clicked.connect(self.on_reset_errors)
        ctrl_row.addWidget(self.btn_reset_errors)
        e_layout.addLayout(ctrl_row)

        layout.addWidget(self.grp_errors)

    def init_tab_projects(self):
        layout = QVBoxLayout(self.tab_projects)

        self.grp_projects = QGroupBox()
        p_layout = QVBoxLayout(self.grp_projects)

        self.lbl_projects_desc = QLabel()
        self.lbl_projects_desc.setWordWrap(True)
        p_layout.addWidget(self.lbl_projects_desc)

        self.list_projects = QListWidget()
        p_layout.addWidget(self.list_projects)

        btn_row = QHBoxLayout()
        self.btn_select_all_proj = QPushButton()
        self.btn_select_all_proj.clicked.connect(self.on_select_all_projects)
        btn_row.addWidget(self.btn_select_all_proj)

        self.btn_deselect_all_proj = QPushButton()
        self.btn_deselect_all_proj.clicked.connect(self.on_deselect_all_projects)
        btn_row.addWidget(self.btn_deselect_all_proj)

        btn_row.addStretch()
        p_layout.addLayout(btn_row)

        layout.addWidget(self.grp_projects)

    def init_tab_timers(self):
        layout = QVBoxLayout(self.tab_timers)

        self.grp_timers = QGroupBox()
        t_layout = QVBoxLayout(self.grp_timers)

        # 1. Пауза перед возобновлением
        self.lbl_retry_pause = QLabel()
        t_layout.addWidget(self.lbl_retry_pause)
        r_row = QHBoxLayout()
        self.slider_retry = QSlider(Qt.Orientation.Horizontal)
        self.slider_retry.setRange(2, 60)
        self.slider_retry.valueChanged.connect(lambda v: self.val_retry.setText(f"{v} {self.mgr.tr('unit_seconds')}"))
        r_row.addWidget(self.slider_retry)
        self.val_retry = QLabel("10 сек.")
        self.val_retry.setFixedWidth(60)
        r_row.addWidget(self.val_retry)
        t_layout.addLayout(r_row)

        # 2. Кулдаун
        self.lbl_cooldown = QLabel()
        t_layout.addWidget(self.lbl_cooldown)
        c_row = QHBoxLayout()
        self.slider_cooldown = QSlider(Qt.Orientation.Horizontal)
        self.slider_cooldown.setRange(2, 30)
        self.slider_cooldown.valueChanged.connect(lambda v: self.val_cooldown.setText(f"{v} {self.mgr.tr('unit_seconds')}"))
        c_row.addWidget(self.slider_cooldown)
        self.val_cooldown = QLabel("6 сек.")
        self.val_cooldown.setFixedWidth(60)
        c_row.addWidget(self.val_cooldown)
        t_layout.addLayout(c_row)

        # 3. Интервал опроса
        self.lbl_poll = QLabel()
        t_layout.addWidget(self.lbl_poll)
        self.combo_poll = QComboBox()
        self.combo_poll.addItem("0.5 сек. (Быстрый)", 0.5)
        self.combo_poll.addItem("1.0 сек. (Стандартный)", 1.0)
        self.combo_poll.addItem("2.0 сек. (Энергосберегающий)", 2.0)
        t_layout.addWidget(self.combo_poll)

        # 4. Лимит попыток
        self.lbl_max_retries = QLabel()
        t_layout.addWidget(self.lbl_max_retries)
        self.spin_retries = QSpinBox()
        self.spin_retries.setRange(0, 50)
        self.spin_retries.setSpecialValueText(self.mgr.tr("unlimited"))
        t_layout.addWidget(self.spin_retries)

        layout.addWidget(self.grp_timers)
        layout.addStretch()

    def load_values(self):
        s = self.mgr.settings

        l_idx = self.combo_lang.findData(s.get("language", "auto"))
        if l_idx >= 0:
            self.combo_lang.setCurrentIndex(l_idx)

        self.chk_autostart_win.setChecked(bool(s.get("autostart_windows", True)))
        self.chk_codex_start.setChecked(bool(s.get("enable_on_codex_start", True)))

        self.chk_notify_toggle.setChecked(bool(s.get("notify_on_toggle", True)))
        self.chk_notify_resume.setChecked(bool(s.get("notify_on_resume", False)))
        self.chk_sound_resume.setChecked(bool(s.get("sound_on_resume", False)))

        r_val = int(s.get("retry_pause_seconds", 10.0))
        self.slider_retry.setValue(r_val)
        self.val_retry.setText(f"{r_val} {self.mgr.tr('unit_seconds')}")

        c_val = int(s.get("post_resume_cooldown", 6.0))
        self.slider_cooldown.setValue(c_val)
        self.val_cooldown.setText(f"{c_val} {self.mgr.tr('unit_seconds')}")

        p_val = float(s.get("poll_interval_seconds", 1.0))
        p_idx = self.combo_poll.findData(p_val)
        if p_idx >= 0:
            self.combo_poll.setCurrentIndex(p_idx)

        self.spin_retries.setValue(int(s.get("max_retries_consecutive", 10)))

        self.refresh_error_list()
        self.refresh_project_list()

    def refresh_error_list(self):
        self.list_errors.clear()
        for item_data in self.mgr.settings.get("error_patterns", []):
            pat = item_data.get("pattern", "")
            name = item_data.get("name") or pat
            enabled = item_data.get("enabled", True)
            is_custom = item_data.get("custom", False)

            item = QListWidgetItem(f"[{'Пользовательская' if is_custom else 'Системная'}] {name} ({pat})")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, item_data)
            self.list_errors.addItem(item)

    def refresh_project_list(self):
        self.list_projects.clear()
        all_projs = get_all_codex_projects()
        excluded = [str(x).strip().lower() for x in self.mgr.settings.get("excluded_projects", [])]

        for p_path, p_base in sorted(all_projs.items(), key=lambda x: x[1].lower()):
            is_checked = (p_path.strip().lower() not in excluded and p_base.strip().lower() not in excluded)
            item = QListWidgetItem(f"📁 {p_base}  —  {p_path}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, p_path)
            self.list_projects.addItem(item)

    def on_language_changed(self):
        new_lang = self.combo_lang.currentData()
        self.mgr.settings["language"] = new_lang
        self.apply_translations()

    def apply_translations(self):
        tr = self.mgr.tr
        self.setWindowTitle(tr("dialog_title"))

        self.tabs.setTabText(0, tr("tab_general"))
        self.tabs.setTabText(1, tr("tab_errors"))
        self.tabs.setTabText(2, tr("tab_projects"))
        self.tabs.setTabText(3, tr("tab_timers"))

        self.grp_lang.setTitle(tr("grp_language"))
        self.combo_lang.setItemText(0, tr("lang_auto"))
        self.combo_lang.setItemText(1, tr("lang_ru"))
        self.combo_lang.setItemText(2, tr("lang_en"))

        self.grp_startup.setTitle(tr("grp_startup"))
        self.chk_autostart_win.setText(tr("chk_autostart_windows"))
        self.chk_codex_start.setText(tr("chk_enable_on_codex_start"))

        self.grp_notif.setTitle(tr("grp_notifications"))
        self.chk_notify_toggle.setText(tr("chk_notify_toggle"))
        self.chk_notify_resume.setText(tr("chk_notify_resume"))
        self.chk_sound_resume.setText(tr("chk_sound_resume"))

        self.grp_errors.setTitle(tr("grp_error_patterns"))
        self.lbl_new_error.setText(tr("lbl_new_error"))
        self.edit_new_error.setPlaceholderText(tr("placeholder_new_error"))
        self.btn_add_error.setText(tr("btn_add_error"))
        self.btn_del_error.setText(tr("btn_delete_error"))
        self.btn_reset_errors.setText(tr("btn_reset_errors"))

        self.grp_projects.setTitle(tr("grp_projects"))
        self.lbl_projects_desc.setText(tr("lbl_projects_desc"))
        self.btn_select_all_proj.setText(tr("btn_select_all"))
        self.btn_deselect_all_proj.setText(tr("btn_deselect_all"))

        self.grp_timers.setTitle(tr("grp_timers"))
        self.lbl_retry_pause.setText(tr("lbl_retry_pause"))
        self.lbl_cooldown.setText(tr("lbl_cooldown"))
        self.lbl_poll.setText(tr("lbl_poll_interval"))
        self.lbl_max_retries.setText(tr("lbl_max_retries"))
        self.spin_retries.setSpecialValueText(tr("unlimited"))

        self.btn_save.setText(tr("btn_save"))
        self.btn_cancel.setText(tr("btn_cancel"))
        self.btn_apply.setText(tr("btn_apply"))

        self.val_retry.setText(f"{self.slider_retry.value()} {tr('unit_seconds')}")
        self.val_cooldown.setText(f"{self.slider_cooldown.value()} {tr('unit_seconds')}")

    def on_add_error(self):
        text = self.edit_new_error.text().strip()
        if not text:
            return
        patterns = self.mgr.settings.setdefault("error_patterns", [])
        if any(p.get("pattern", "").lower() == text.lower() for p in patterns):
            return
        patterns.append({
            "pattern": text.lower(),
            "name": text,
            "enabled": True,
            "custom": True
        })
        self.edit_new_error.clear()
        self.refresh_error_list()

    def on_delete_error(self):
        cur_row = self.list_errors.currentRow()
        if cur_row < 0:
            return
        patterns = self.mgr.settings.get("error_patterns", [])
        if cur_row < len(patterns):
            del patterns[cur_row]
            self.refresh_error_list()

    def on_reset_errors(self):
        self.mgr.settings["error_patterns"] = json.loads(json.dumps(DEFAULT_SETTINGS["error_patterns"]))
        self.refresh_error_list()

    def on_select_all_projects(self):
        for i in range(self.list_projects.count()):
            self.list_projects.item(i).setCheckState(Qt.CheckState.Checked)

    def on_deselect_all_projects(self):
        for i in range(self.list_projects.count()):
            self.list_projects.item(i).setCheckState(Qt.CheckState.Unchecked)

    def save_values(self):
        s = self.mgr.settings
        s["language"] = self.combo_lang.currentData()
        s["autostart_windows"] = self.chk_autostart_win.isChecked()
        s["enable_on_codex_start"] = self.chk_codex_start.isChecked()
        s["notify_on_toggle"] = self.chk_notify_toggle.isChecked()
        s["notify_on_resume"] = self.chk_notify_resume.isChecked()
        s["sound_on_resume"] = self.chk_sound_resume.isChecked()

        s["retry_pause_seconds"] = float(self.slider_retry.value())
        s["post_resume_cooldown"] = float(self.slider_cooldown.value())
        s["poll_interval_seconds"] = float(self.combo_poll.currentData() or 1.0)
        s["max_retries_consecutive"] = int(self.spin_retries.value())

        patterns = s.get("error_patterns", [])
        for i in range(min(len(patterns), self.list_errors.count())):
            item = self.list_errors.item(i)
            patterns[i]["enabled"] = (item.checkState() == Qt.CheckState.Checked)

        excluded = []
        for i in range(self.list_projects.count()):
            item = self.list_projects.item(i)
            if item.checkState() == Qt.CheckState.Unchecked:
                p_path = item.data(Qt.ItemDataRole.UserRole)
                if p_path:
                    excluded.append(p_path)
        s["excluded_projects"] = excluded

        self.mgr.save()
        self.settings_saved.emit()

    def on_save_and_close(self):
        self.save_values()
        self.accept()
