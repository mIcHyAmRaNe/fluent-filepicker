# FILE: src/fluent_filepicker/single_file_widget.py
"""
Fluent Design Single File Drop Widget for PyQt6.

Allows drag & drop or browse-dialog to select a single file.
"""

from __future__ import annotations

import os
from pathlib import Path

from PyQt6.QtCore import (
    QEvent,
    QPointF,
    QRectF,
    QSize,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDropEvent,
    QEnterEvent,
    QFont,
    QFontMetrics,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
)
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .colors import FluentFileColors
from .styles import FluentFilePickerStyleSheet, Theme
from .utils import normalize_extensions


class _DropZone(QWidget):
    """
    Internal drop zone widget that handles drag & drop visuals and painting.
    Used by DropSingleFileWidget as the visual drop area.
    """

    # ── Signals — ALL declared here, at the top of the class ─────────────────
    file_dropped = pyqtSignal(str)  # Emitted with the selected file path
    file_cleared = pyqtSignal()  # Emitted when the user removes the current file
    browse_requested = pyqtSignal()  # Emitted when the user clicks to open a dialog

    # ── Layout constants ──────────────────────────────────────────────────────
    BORDER_RADIUS = 8
    BORDER_DASH_LENGTH = 6
    BORDER_DASH_GAP = 4
    ICON_SIZE = 32
    ICON_STROKE = 2.0

    # File-info chip constants
    CHIP_H = 52.0
    CHIP_MAX_W = 360.0
    CHIP_MARGIN_X = 40.0  # total horizontal margin inside the drop zone
    CHIP_PADDING_LEFT = 10.0  # gap between chip left edge and badge
    CHIP_BADGE_SIZE = 36.0
    CHIP_TEXT_GAP = 10.0  # gap between badge right and text
    CHIP_REMOVE_SIZE = 20.0  # remove-button bounding box
    CHIP_REMOVE_MARGIN = 8.0  # gap between remove button and chip right edge

    def __init__(
        self,
        parent: QWidget | None = None,
        theme: Theme = Theme.DARK,
        allowed_extensions: list[str] | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._allowed_extensions = normalize_extensions(allowed_extensions)
        self._hovered = False
        self._drag_over = False
        self._drag_valid = True
        self._has_file = False
        self._file_path: str | None = None
        self._hint_text = "Drag & drop a file here, or"
        self._browse_text = "browse"

        self._file_name = ""
        self._file_size_str = ""
        self._file_ext = ""

        self._remove_hovered = False
        self._remove_rect = QRectF()

        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFont(QFont("Segoe UI", 10))

    # ── Public API ────────────────────────────────────────────────────────────

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.update()

    def set_allowed_extensions(self, extensions: list[str] | None) -> None:
        self._allowed_extensions = normalize_extensions(extensions)

    def set_hint_text(self, text: str) -> None:
        self._hint_text = text
        self.update()

    def set_browse_text(self, text: str) -> None:
        self._browse_text = text
        self.update()

    def set_file(self, path: str | None) -> None:
        """Set or clear the current file."""
        if path is None:
            self._has_file = False
            self._file_path = None
            self._file_name = ""
            self._file_size_str = ""
            self._file_ext = ""
        else:
            self._has_file = True
            self._file_path = path
            p = Path(path)
            self._file_name = p.name
            self._file_ext = p.suffix.lstrip(".").upper() if p.suffix else "FILE"
            self._file_size_str = self._format_size(p)
        self.update()

    def file_path(self) -> str | None:
        return self._file_path

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _is_valid_file(self, path: str) -> bool:
        if not self._allowed_extensions:
            return True
        return Path(path).suffix.lower().lstrip(".") in self._allowed_extensions

    @staticmethod
    def _format_size(path: Path) -> str:
        try:
            size_f = float(path.stat().st_size)
            units = ("B", "KB", "MB", "GB", "TB")
            for unit in units:
                if size_f < 1024 or unit == units[-1]:
                    if unit == "B":
                        return f"{int(size_f)} B"
                    return f"{size_f:.1f} {unit}"
                size_f /= 1024
        except OSError:
            pass
        return ""

    # ── Paint & Events (MUST BE camelCase for Qt Overrides) ───────────────────

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font())

        colors = FluentFileColors.resolve_drop_zone_colors(
            self._theme,
            hovered=self._hovered,
            drag_over=self._drag_over,
            drag_valid=self._drag_valid,
        )
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)

        # Background
        path = QPainterPath()
        path.addRoundedRect(rect, self.BORDER_RADIUS, self.BORDER_RADIUS)
        painter.fillPath(path, colors["bg"])

        # Dashed border
        pen = QPen(colors["border"], 1.5, Qt.PenStyle.DashLine)
        pen.setDashPattern([self.BORDER_DASH_LENGTH, self.BORDER_DASH_GAP])
        painter.setPen(pen)
        painter.drawPath(path)

        if self._has_file:
            self._paint_file_info(painter, rect, colors)
        else:
            self._paint_empty_state(painter, rect, colors)

    def _paint_empty_state(self, painter: QPainter, rect: QRectF, colors: dict) -> None:
        cx = rect.center().x()
        cy = rect.center().y()

        self._draw_upload_icon(painter, cx, cy - 28, colors["icon"])

        fm = QFontMetrics(self.font())
        hint = self._hint_text
        browse = f" {self._browse_text}"
        hint_w = fm.horizontalAdvance(hint)
        browse_w = fm.horizontalAdvance(browse)
        total_w = hint_w + browse_w
        text_y = cy + 14

        painter.setPen(colors["text_secondary"])
        painter.drawText(QPointF(cx - total_w / 2, text_y), hint)
        painter.setPen(colors["accent"])
        painter.drawText(QPointF(cx - total_w / 2 + hint_w, text_y), browse)

        if self._allowed_extensions:
            ext_text = "Supported: " + ", ".join(f".{e}" for e in self._allowed_extensions)
            small_font = QFont(self.font())
            small_font.setPointSize(max(7, self.font().pointSize() - 1))
            painter.setFont(small_font)
            fm2 = QFontMetrics(small_font)
            painter.setPen(colors["text_hint"])
            painter.drawText(
                QPointF(cx - fm2.horizontalAdvance(ext_text) / 2, text_y + 18),
                ext_text,
            )
            painter.setFont(self.font())

    def _draw_upload_icon(self, painter: QPainter, cx: float, cy: float, color: QColor) -> None:
        painter.save()
        pen = QPen(
            color,
            self.ICON_STROKE,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        s = self.ICON_SIZE / 2

        page_path = QPainterPath()
        fold = s * 0.35
        page_path.moveTo(cx - s * 0.55, cy - s)
        page_path.lineTo(cx + s * 0.20, cy - s)
        page_path.lineTo(cx + s * 0.55, cy - s + fold)
        page_path.lineTo(cx + s * 0.55, cy + s)
        page_path.lineTo(cx - s * 0.55, cy + s)
        page_path.closeSubpath()
        painter.drawPath(page_path)

        fold_path = QPainterPath()
        fold_path.moveTo(cx + s * 0.20, cy - s)
        fold_path.lineTo(cx + s * 0.20, cy - s + fold)
        fold_path.lineTo(cx + s * 0.55, cy - s + fold)
        painter.drawPath(fold_path)

        line_x1 = cx - s * 0.35
        line_x2 = cx + s * 0.25
        for i, ly in enumerate([cy - s * 0.2, cy + s * 0.05, cy + s * 0.3]):
            x2 = line_x2 if i < 2 else cx
            painter.drawLine(QPointF(line_x1, ly), QPointF(x2, ly))

        painter.restore()

    def _paint_file_info(self, painter: QPainter, rect: QRectF, colors: dict) -> None:
        cx = rect.center().x()
        cy = rect.center().y()

        chip_w = min(rect.width() - self.CHIP_MARGIN_X, self.CHIP_MAX_W)
        chip_x = cx - chip_w / 2
        chip_y = cy - self.CHIP_H / 2
        chip_rect = QRectF(chip_x, chip_y, chip_w, self.CHIP_H)

        # Chip background
        chip_path = QPainterPath()
        chip_path.addRoundedRect(chip_rect, 6, 6)
        painter.fillPath(chip_path, colors["chip_bg"])
        painter.setPen(QPen(colors["chip_border"], 1))
        painter.drawPath(chip_path)

        # Extension badge
        badge_x = chip_x + self.CHIP_PADDING_LEFT
        badge_y = chip_y + (self.CHIP_H - self.CHIP_BADGE_SIZE) / 2
        badge_rect = QRectF(badge_x, badge_y, self.CHIP_BADGE_SIZE, self.CHIP_BADGE_SIZE)
        badge_path = QPainterPath()
        badge_path.addRoundedRect(badge_rect, 4, 4)
        painter.fillPath(badge_path, FluentFileColors.for_extension(self._file_ext))

        badge_font = QFont(self.font())
        badge_font.setPointSize(max(6, self.font().pointSize() - 2))
        badge_font.setBold(True)
        painter.setFont(badge_font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            badge_rect.toRect(),
            Qt.AlignmentFlag.AlignCenter,
            self._file_ext[:4],
        )
        painter.setFont(self.font())

        # Text area (name + size)
        text_x = badge_x + self.CHIP_BADGE_SIZE + self.CHIP_TEXT_GAP
        text_w = (
            chip_w
            - self.CHIP_PADDING_LEFT
            - self.CHIP_BADGE_SIZE
            - self.CHIP_TEXT_GAP
            - self.CHIP_REMOVE_SIZE
            - self.CHIP_REMOVE_MARGIN * 2
        )

        fm = QFontMetrics(self.font())
        elided_name = fm.elidedText(self._file_name, Qt.TextElideMode.ElideMiddle, int(text_w))
        painter.setPen(colors["chip_text"])
        painter.drawText(
            QRectF(text_x, chip_y + 8, text_w, 20).toRect(),
            Qt.AlignmentFlag.AlignVCenter,
            elided_name,
        )

        sub_font = QFont(self.font())
        sub_font.setPointSize(max(7, self.font().pointSize() - 1))
        painter.setFont(sub_font)
        painter.setPen(colors["chip_subtext"])
        painter.drawText(
            QRectF(text_x, chip_y + self.CHIP_H - 22, text_w, 16).toRect(),
            Qt.AlignmentFlag.AlignVCenter,
            self._file_size_str,
        )
        painter.setFont(self.font())

        # Remove button
        btn_x = chip_x + chip_w - self.CHIP_REMOVE_SIZE - self.CHIP_REMOVE_MARGIN
        btn_y = chip_y + (self.CHIP_H - self.CHIP_REMOVE_SIZE) / 2
        self._remove_rect = QRectF(btn_x, btn_y, self.CHIP_REMOVE_SIZE, self.CHIP_REMOVE_SIZE)

        if self._remove_hovered:
            remove_path = QPainterPath()
            remove_path.addEllipse(self._remove_rect)
            painter.fillPath(remove_path, colors["remove_hover_bg"])

        painter.setPen(
            QPen(
                colors["remove_icon"],
                1.5,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        rc = self._remove_rect.center()
        s = 4.0
        painter.drawLine(QPointF(rc.x() - s, rc.y() - s), QPointF(rc.x() + s, rc.y() + s))
        painter.drawLine(QPointF(rc.x() - s, rc.y() + s), QPointF(rc.x() + s, rc.y() - s))

    def enterEvent(self, event: QEnterEvent) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self._hovered = False
        self._remove_hovered = False
        self.update()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._has_file and self._remove_rect.contains(event.position()):
            if not self._remove_hovered:
                self._remove_hovered = True
                self.setCursor(Qt.CursorShape.PointingHandCursor)
                self.update()
        else:
            if self._remove_hovered:
                self._remove_hovered = False
                self.update()
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        if self._has_file and self._remove_rect.contains(event.position()):
            self.set_file(None)
            self.file_cleared.emit()
            event.accept()
            return

        if not self._has_file:
            self.browse_requested.emit()

        event.accept()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                self._drag_valid = self._is_valid_file(urls[0].toLocalFile())
                self._drag_over = True
                self.update()
                event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._drag_over = False
        self._drag_valid = True
        self.update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        self._drag_over = False
        self._drag_valid = True
        self.update()

        urls = event.mimeData().urls()
        if not urls:
            event.ignore()
            return

        path = urls[0].toLocalFile()
        if not os.path.isfile(path) or not self._is_valid_file(path):
            event.ignore()
            return

        self.set_file(path)
        self.file_dropped.emit(path)
        event.acceptProposedAction()

    def sizeHint(self) -> QSize:
        return QSize(400, 130)

    def minimumSizeHint(self) -> QSize:
        return QSize(200, 100)


class DropSingleFileWidget(QWidget):
    """
    Fluent Design widget for selecting a single file via drag & drop or dialog.
    """

    file_selected = pyqtSignal(str)
    file_cleared = pyqtSignal()

    def __init__(
        self,
        parent: QWidget | None = None,
        theme: Theme = Theme.DARK,
        allowed_extensions: list[str] | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._allowed_extensions: list[str] = normalize_extensions(allowed_extensions)
        self._dialog_title = "Select a file"
        self._dialog_dir = ""
        self._current_path: str | None = None

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._drop_zone = _DropZone(self, self._theme, self._allowed_extensions)
        self._drop_zone.file_dropped.connect(self._on_file_dropped)
        self._drop_zone.file_cleared.connect(self._on_file_cleared)
        self._drop_zone.browse_requested.connect(self._open_dialog)
        layout.addWidget(self._drop_zone)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addStretch()

        self._browse_btn = QPushButton("Browse files")
        self._browse_btn.setObjectName("browseButton")
        self._browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._browse_btn.clicked.connect(self._open_dialog)
        btn_layout.addWidget(self._browse_btn)

        layout.addLayout(btn_layout)

    def _apply_theme(self) -> None:
        self.setStyleSheet(FluentFilePickerStyleSheet.get_widget_style(self._theme))
        self._drop_zone.set_theme(self._theme)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._apply_theme()

    def theme(self) -> Theme:
        return self._theme

    def set_allowed_extensions(self, extensions: list[str] | None) -> None:
        self._allowed_extensions = normalize_extensions(extensions)
        self._drop_zone.set_allowed_extensions(extensions)

    def allowed_extensions(self) -> list[str]:
        return list(self._allowed_extensions)

    def set_dialog_title(self, title: str) -> None:
        self._dialog_title = title

    def dialog_title(self) -> str:
        return self._dialog_title

    def set_dialog_directory(self, directory: str) -> None:
        self._dialog_dir = directory

    def dialog_directory(self) -> str:
        return self._dialog_dir

    def set_hint_text(self, text: str) -> None:
        self._drop_zone.set_hint_text(text)

    def set_browse_text(self, text: str) -> None:
        self._drop_zone.set_browse_text(text)

    def set_browse_button_text(self, text: str) -> None:
        self._browse_btn.setText(text)

    def set_browse_button_visible(self, visible: bool) -> None:
        self._browse_btn.setVisible(visible)

    def current_file(self) -> str | None:
        return self._current_path

    def set_file(self, path: str | None) -> None:
        if path is None:
            self._current_path = None
            self._drop_zone.set_file(None)
        elif os.path.isfile(path):
            self._current_path = path
            self._drop_zone.set_file(path)

    def clear_file(self) -> None:
        self._current_path = None
        self._drop_zone.set_file(None)
        self.file_cleared.emit()

    def has_file(self) -> bool:
        return self._current_path is not None

    # Qt Override method - Must be camelCase
    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        self._browse_btn.setEnabled(enabled)
        self._drop_zone.setEnabled(enabled)

    # ── Internal slots ────────────────────────────────────────────────────────

    def _on_file_dropped(self, path: str) -> None:
        self._current_path = path
        self.file_selected.emit(path)

    def _on_file_cleared(self) -> None:
        self._current_path = None
        self.file_cleared.emit()

    def _open_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._dialog_title,
            self._dialog_dir,
            self._build_filter_string(),
        )
        if path:
            self._current_path = path
            self._drop_zone.set_file(path)
            self.file_selected.emit(path)

    def _build_filter_string(self) -> str:
        if not self._allowed_extensions:
            return "All files (*.*)"
        patterns = " ".join(f"*.{e}" for e in self._allowed_extensions)
        return f"Supported files ({patterns});;All files (*.*)"
