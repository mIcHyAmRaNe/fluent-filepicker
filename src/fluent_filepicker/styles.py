# FILE: src/fluent_filepicker/styles.py
"""Fluent Design style sheet definitions for file picker widgets."""

from enum import Enum


class Theme(Enum):
    """Theme enumeration."""

    LIGHT = "light"
    DARK = "dark"


class FluentFilePickerStyleSheet:
    """Fluent Design style sheet generator for file pickers."""

    @staticmethod
    def get_widget_style(theme: Theme) -> str:
        if theme == Theme.DARK:
            return FluentFilePickerStyleSheet._dark_widget_style()
        return FluentFilePickerStyleSheet._light_widget_style()

    @staticmethod
    def _dark_widget_style() -> str:
        return """
            DropSingleFileWidget,
            DropMultiFilesWidget {
                background-color: transparent;
                border: none;
            }

            QPushButton#browseButton {
                background-color: rgba(255, 255, 255, 0.0605);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 5px;
                color: white;
                padding: 5px 16px;
                min-height: 30px;
                outline: none;
                font-size: 13px;
            }

            QPushButton#browseButton:hover {
                background-color: rgba(255, 255, 255, 0.0837);
            }

            QPushButton#browseButton:pressed {
                background-color: rgba(255, 255, 255, 0.0326);
                color: rgba(255, 255, 255, 0.63);
            }

            QPushButton#browseButton:disabled {
                color: rgba(255, 255, 255, 0.3628);
                background: rgba(255, 255, 255, 0.0419);
            }

            QPushButton#clearButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                color: rgba(255, 255, 255, 0.7);
                padding: 2px;
                min-width: 20px;
                min-height: 20px;
                max-width: 20px;
                max-height: 20px;
            }

            QPushButton#clearButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
            }

            QPushButton#clearButton:pressed {
                background-color: rgba(255, 255, 255, 0.06);
            }

            /* Fluent ScrollBar */

            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                margin: 4px 2px 4px 0px;
            }

            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.18);
                border-radius: 5px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.28);
            }

            QScrollBar::handle:vertical:pressed {
                background: rgba(255, 255, 255, 0.38);
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
                border: none;
            }
        """

    @staticmethod
    def _light_widget_style() -> str:
        return """
            DropSingleFileWidget,
            DropMultiFilesWidget {
                background-color: transparent;
                border: none;
            }

            QPushButton#browseButton {
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(0, 0, 0, 0.073);
                border-bottom: 1px solid rgba(0, 0, 0, 0.183);
                border-radius: 5px;
                color: black;
                padding: 5px 16px;
                min-height: 30px;
                outline: none;
                font-size: 13px;
            }

            QPushButton#browseButton:hover {
                background-color: rgba(249, 249, 249, 0.5);
            }

            QPushButton#browseButton:pressed {
                background-color: rgba(249, 249, 249, 0.3);
                color: rgba(0, 0, 0, 0.63);
            }

            QPushButton#browseButton:disabled {
                color: rgba(0, 0, 0, 0.3614);
                background: rgba(249, 249, 249, 0.3);
            }

            QPushButton#clearButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                color: rgba(0, 0, 0, 0.5);
                padding: 2px;
                min-width: 20px;
                min-height: 20px;
                max-width: 20px;
                max-height: 20px;
            }

            QPushButton#clearButton:hover {
                background-color: rgba(0, 0, 0, 0.07);
                color: black;
            }

            QPushButton#clearButton:pressed {
                background-color: rgba(0, 0, 0, 0.04);
            }

            /* Fluent ScrollBar */

            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                margin: 4px 2px 4px 0px;
            }

            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.18);
                border-radius: 5px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background: rgba(0, 0, 0, 0.28);
            }

            QScrollBar::handle:vertical:pressed {
                background: rgba(0, 0, 0, 0.38);
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
                border: none;
            }
        """
