# example.py
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from fluent_filepicker import DropMultiFilesWidget, DropSingleFileWidget, Theme


def make_label(text: str, dark: bool) -> QLabel:
    label = QLabel(text)
    color = "white" if dark else "black"
    label.setStyleSheet(
        f"color: {color}; font-size: 13px; font-weight: 600; margin-top: 8px;"
    )
    return label


def make_section_sep(dark: bool) -> QWidget:
    sep = QWidget()
    sep.setFixedHeight(1)
    color = "rgba(255,255,255,0.08)" if dark else "rgba(0,0,0,0.08)"
    sep.setStyleSheet(f"background: {color};")
    return sep


class DemoWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._dark = True
        self.setWindowTitle("Fluent File Picker — Demo")
        self.resize(560, 700)
        self._build_ui()
        self._apply_theme()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(10)

        # ── Header ──────────────────────────────────────────────────────────
        header_row = QHBoxLayout()

        title = QLabel("File Picker Demo")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
        self._title_label = title
        header_row.addWidget(title)
        header_row.addStretch()

        self._theme_btn = QPushButton("Switch to Light")
        self._theme_btn.setObjectName("themeToggle")
        self._theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._theme_btn.clicked.connect(self._toggle_theme)
        header_row.addWidget(self._theme_btn)

        root.addLayout(header_row)
        root.addWidget(make_section_sep(self._dark))

        # ── Single file ──────────────────────────────────────────────────────
        self._single_label = make_label("Single File Picker", self._dark)
        root.addWidget(self._single_label)

        self._single = DropSingleFileWidget(theme=Theme.DARK)
        self._single.set_allowed_extensions(["pdf", "docx", "txt", "png", "jpg", "jpeg"])
        self._single.set_dialog_title("Select a document")
        self._single.set_browse_button_text("Browse files")
        self._single.file_selected.connect(self._on_single_selected)
        self._single.file_cleared.connect(self._on_single_cleared)
        root.addWidget(self._single)

        self._single_status = QLabel("No file selected.")
        self._single_status.setWordWrap(True)
        self._single_status_label = self._single_status
        root.addWidget(self._single_status)

        root.addWidget(make_section_sep(self._dark))

        # ── Multi file ───────────────────────────────────────────────────────
        self._multi_label = make_label("Multi-File Picker  (max 6 files)", self._dark)
        root.addWidget(self._multi_label)

        self._multi = DropMultiFilesWidget(theme=Theme.DARK)
        self._multi.set_allowed_extensions(["py", "txt", "json", "csv", "md"])
        self._multi.set_dialog_title("Select source files")
        self._multi.set_max_file_count(6)
        self._multi.set_browse_button_text("Add files")
        self._multi.files_changed.connect(self._on_files_changed)
        self._multi.file_added.connect(lambda p: print(f"  [+] Added  : {p}"))
        self._multi.file_removed.connect(lambda p: print(f"  [-] Removed: {p}"))
        root.addWidget(self._multi)

        self._multi_status = QLabel("No files selected.")
        self._multi_status.setWordWrap(True)
        self._multi_status_label = self._multi_status
        root.addWidget(self._multi_status)

        root.addStretch()

        # Collect theme-sensitive plain widgets
        self._sep_widgets: list[QWidget] = []

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_single_selected(self, path: str) -> None:
        import os

        name = os.path.basename(path)
        self._single_status.setText(f"✔  {name}")
        print(f"[Single] Selected: {path}")

    def _on_single_cleared(self) -> None:
        self._single_status.setText("No file selected.")
        print("[Single] Cleared")

    def _on_files_changed(self, paths: list) -> None:
        n = len(paths)
        if n == 0:
            self._multi_status.setText("No files selected.")
        else:
            self._multi_status.setText(f"✔  {n} file(s) selected.")
        print(f"[Multi ] {n} file(s): {paths}")

    def _toggle_theme(self) -> None:
        self._dark = not self._dark
        self._apply_theme()

    # ── Theme ────────────────────────────────────────────────────────────────

    def _apply_theme(self) -> None:
        theme = Theme.DARK if self._dark else Theme.LIGHT

        # Window background
        bg = "rgb(32, 32, 32)" if self._dark else "rgb(243, 243, 243)"
        text_color = "white" if self._dark else "black"
        status_color = "rgba(255,255,255,0.55)" if self._dark else "rgba(0,0,0,0.5)"
        btn_bg = "rgba(255,255,255,0.08)" if self._dark else "rgba(0,0,0,0.06)"
        btn_hover = "rgba(255,255,255,0.13)" if self._dark else "rgba(0,0,0,0.10)"
        btn_border = "rgba(255,255,255,0.12)" if self._dark else "rgba(0,0,0,0.12)"

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg};
                font-family: "Segoe UI";
            }}
            QPushButton#themeToggle {{
                background-color: {btn_bg};
                border: 1px solid {btn_border};
                border-radius: 5px;
                color: {text_color};
                padding: 5px 14px;
                font-size: 12px;
            }}
            QPushButton#themeToggle:hover {{
                background-color: {btn_hover};
            }}
        """)

        self._title_label.setStyleSheet(f"color: {text_color};")
        self._single_label.setStyleSheet(
            f"color: {text_color}; font-size: 13px; font-weight: 600; margin-top: 8px;"
        )
        self._multi_label.setStyleSheet(
            f"color: {text_color}; font-size: 13px; font-weight: 600; margin-top: 8px;"
        )
        self._single_status.setStyleSheet(f"color: {status_color}; font-size: 12px;")
        self._multi_status.setStyleSheet(f"color: {status_color}; font-size: 12px;")

        self._theme_btn.setText("Switch to Light" if self._dark else "Switch to Dark")

        # Propagate theme to widgets
        self._single.set_theme(theme)
        self._multi.set_theme(theme)


def main() -> None:
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    window = DemoWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
