# FILE: src/fluent_filepicker/multi_file_widget.py
"""
Fluent Design Multi-File Drop Widget for PyQt6.

Allows drag & drop or browse-dialog to select multiple files.
"""

from __future__ import annotations

import os
from pathlib import Path

from PyQt6.QtCore import (
    QEvent,
    QPoint,
    QPointF,
    QRect,
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
    QResizeEvent,
)
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLayout,
    QLayoutItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QWidgetItem,
)

from .colors import FluentFileColors
from .styles import FluentFilePickerStyleSheet, Theme
from .utils import normalize_extensions

# ── Flow Layout ───────────────────────────────────────────────────────────────


class FlowLayout(QLayout):
    """
    A layout that arranges items left-to-right, wrapping to the next row
    when there is no more horizontal space.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        h_spacing: int = 6,
        v_spacing: int = 6,
    ) -> None:
        super().__init__(parent)
        self._items: list[QLayoutItem] = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing

    # ── QLayout interface (MUST BE camelCase for Qt Override) ─────────────────

    def addItem(self, item: QLayoutItem) -> None:
        self._items.append(item)

    def addWidget(self, widget: QWidget) -> None:  # type: ignore[override]
        """
        Reparent *widget* to the layout's parent widget, wrap it in a
        QWidgetItem and append it to the flow.
        """
        # Reparent so the widget is owned by the container.
        if self.parentWidget() and widget.parent() is not self.parentWidget():
            widget.setParent(self.parentWidget())
        item = QWidgetItem(widget)
        self.addItem(item)
        # Make sure the widget becomes visible (it may have been hidden).
        widget.show()

    def removeWidget(self, widget: QWidget) -> None:  # type: ignore[override]
        """
        Detach *widget* from the flow, hide it, and unparent it.
        The caller is responsible for calling ``widget.deleteLater()``.
        """
        for i, item in enumerate(self._items):
            if item.widget() is widget:
                self._items.pop(i)
                # Detach from layout geometry management.
                widget.hide()
                widget.setParent(None)  # type: ignore[arg-type]
                self.invalidate()
                pw = self.parentWidget()
                if pw is not None:
                    pw.updateGeometry()
                    pw.update()
                return

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem | None:
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            item = self._items.pop(index)
            self.invalidate()
            return item
        return None

    def expandingDirections(self) -> Qt.Orientation:
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.sizeHint())
        margins = self.contentsMargins()
        size += QSize(
            margins.left() + margins.right(),
            margins.top() + margins.bottom(),
        )
        return size

    # ── Internal ──────────────────────────────────────────────────────────────

    def _do_layout(self, rect: QRect, *, test_only: bool) -> int:
        margins = self.contentsMargins()
        effective = rect.adjusted(
            margins.left(), margins.top(), -margins.right(), -margins.bottom()
        )
        x = effective.x()
        y = effective.y()
        row_height = 0

        for item in self._items:
            widget = item.widget()
            if widget is None or not widget.isVisible():
                continue
            hint = item.sizeHint()
            next_x = x + hint.width()
            if next_x > effective.right() and row_height > 0:
                x = effective.x()
                y += row_height + self._v_spacing
                row_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x += hint.width() + self._h_spacing
            row_height = max(row_height, hint.height())

        return y + row_height - rect.y() + margins.bottom()


# ── File Chip (compact) ───────────────────────────────────────────────────────


class _FileChipItem(QWidget):
    """
    Compact horizontal chip: [EXT badge] [filename] [×]
    Fixed height ~36 px, width adapts to filename.
    """

    remove_requested = pyqtSignal(str)

    # Layout constants
    CHIP_H = 36
    BADGE_W = 34
    BADGE_H = 22
    BTN_SIZE = 18
    H_PAD = 8
    INNER_SPACING = 7
    MAX_NAME_WIDTH = 140

    def __init__(
        self,
        path: str,
        theme: Theme = Theme.DARK,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._path = path
        self._theme = theme

        p = Path(path)
        self._file_name = p.name
        self._file_ext = p.suffix.lstrip(".").upper() if p.suffix else "FILE"

        self._remove_hovered = False
        self._hovered = False
        self._btn_rect = QRectF()

        self.setMouseTracking(True)
        self.setFixedHeight(self.CHIP_H)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        font = QFont("Segoe UI", 9)
        self.setFont(font)

        # Pre-compute preferred width once.
        fm = QFontMetrics(font)
        self._display_name = fm.elidedText(
            self._file_name, Qt.TextElideMode.ElideMiddle, self.MAX_NAME_WIDTH
        )
        name_w = fm.horizontalAdvance(self._display_name)
        total_w = (
            self.H_PAD
            + self.BADGE_W
            + self.INNER_SPACING
            + name_w
            + self.INNER_SPACING
            + self.BTN_SIZE
            + self.H_PAD
        )
        self.setFixedWidth(max(total_w, 80))

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.update()

    def file_path(self) -> str:
        return self._path

    # ── Paint & Events (MUST BE camelCase) ────────────────────────────────────

    def paintEvent(self, event: QPaintEvent) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cols = FluentFileColors.resolve_chip_colors(self._theme, hovered=self._hovered)
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)

        # Chip background + border
        path = QPainterPath()
        path.addRoundedRect(rect, 6, 6)
        p.fillPath(path, cols["bg"])
        p.setPen(QPen(cols["border"], 1))
        p.drawPath(path)

        cy = rect.center().y()
        x: float = self.H_PAD

        # Extension badge
        badge_y = cy - self.BADGE_H / 2
        badge_rect = QRectF(x, badge_y, self.BADGE_W, self.BADGE_H)
        bp = QPainterPath()
        bp.addRoundedRect(badge_rect, 3, 3)
        p.fillPath(bp, FluentFileColors.for_extension(self._file_ext))

        badge_font = QFont(self.font())
        badge_font.setPointSize(max(5, self.font().pointSize() - 2))
        badge_font.setBold(True)
        p.setFont(badge_font)
        p.setPen(QColor(255, 255, 255))
        p.drawText(
            badge_rect.toRect(), Qt.AlignmentFlag.AlignCenter, self._file_ext[:4]
        )
        p.setFont(self.font())

        x += self.BADGE_W + self.INNER_SPACING

        # File name
        name_rect = QRectF(
            x,
            rect.top() + 2,
            self.width() - x - self.BTN_SIZE - self.H_PAD - self.INNER_SPACING,
            rect.height() - 4,
        )
        p.setPen(cols["text"])
        p.drawText(
            name_rect.toRect(), Qt.AlignmentFlag.AlignVCenter, self._display_name
        )

        # Remove button
        btn_x = rect.right() - self.BTN_SIZE - 6
        btn_y = cy - self.BTN_SIZE / 2
        self._btn_rect = QRectF(btn_x, btn_y, self.BTN_SIZE, self.BTN_SIZE)

        if self._remove_hovered:
            rp = QPainterPath()
            rp.addEllipse(self._btn_rect)
            p.fillPath(rp, cols["remove_hover_bg"])

        # × cross
        p.setPen(
            QPen(
                cols["remove_icon"],
                1.4,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        rc = self._btn_rect.center()
        s = 3.5
        p.drawLine(QPointF(rc.x() - s, rc.y() - s), QPointF(rc.x() + s, rc.y() + s))
        p.drawLine(QPointF(rc.x() - s, rc.y() + s), QPointF(rc.x() + s, rc.y() - s))

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
        in_btn = self._btn_rect.contains(event.position())
        if in_btn != self._remove_hovered:
            self._remove_hovered = in_btn
            self.setCursor(
                Qt.CursorShape.PointingHandCursor
                if in_btn
                else Qt.CursorShape.ArrowCursor
            )
            self.update()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._btn_rect.contains(event.position())
        ):
            self.remove_requested.emit(self._path)
            event.accept()
            return
        super().mousePressEvent(event)

    def sizeHint(self) -> QSize:
        return QSize(self.width(), self.CHIP_H)

    def minimumSizeHint(self) -> QSize:
        return QSize(self.width(), self.CHIP_H)


# ── Chip Container ────────────────────────────────────────────────────────────


class _FileListWidget(QWidget):
    """
    Wrapping flow of compact file chips.
    Grows vertically as chips are added.
    """

    file_removed = pyqtSignal(str)

    def __init__(
        self, theme: Theme = Theme.DARK, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._chips: list[_FileChipItem] = []

        self._flow = FlowLayout(self, h_spacing=6, v_spacing=6)
        self._flow.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._flow)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.hide()

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        for chip in self._chips:
            chip.set_theme(theme)

    def add_file(self, path: str) -> bool:
        if any(c.file_path() == path for c in self._chips):
            return False

        chip = _FileChipItem(path, self._theme, self)
        chip.remove_requested.connect(self._on_remove)
        self._flow.addWidget(chip)
        self._chips.append(chip)

        self._sync_visibility()
        self._relayout()
        return True

    def remove_file(self, path: str) -> None:
        for chip in list(self._chips):
            if chip.file_path() == path:
                chip.remove_requested.disconnect(self._on_remove)
                self._chips.remove(chip)
                self._flow.removeWidget(chip)
                chip.deleteLater()
                break

        self._sync_visibility()
        self._relayout()

    def clear(self) -> None:
        for chip in list(self._chips):
            chip.remove_requested.disconnect(self._on_remove)
            self._flow.removeWidget(chip)
            chip.deleteLater()
        self._chips.clear()

        self._sync_visibility()
        self._relayout()

    def file_paths(self) -> list[str]:
        return [c.file_path() for c in self._chips]

    def count(self) -> int:
        return len(self._chips)

    def is_empty(self) -> bool:
        return not self._chips

    def _on_remove(self, path: str) -> None:
        self.remove_file(path)
        self.file_removed.emit(path)

    def _sync_visibility(self) -> None:
        self.setVisible(bool(self._chips))

    def _relayout(self) -> None:
        self._flow.invalidate()
        self.updateGeometry()
        self.update()

        parent = self.parentWidget()
        while parent is not None:
            parent.updateGeometry()
            parent.update()
            parent = parent.parentWidget()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._flow.invalidate()


# ── Drop Zone ─────────────────────────────────────────────────────────────────


class _MultiDropZone(QWidget):
    """Internal drop zone for the multi-file widget."""

    files_dropped = pyqtSignal(list)
    browse_requested = pyqtSignal()

    BORDER_RADIUS = 8
    BORDER_DASH_LENGTH = 6
    BORDER_DASH_GAP = 4
    ICON_SIZE = 28
    ICON_STROKE = 2.0

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
        self._hint_text = "Drag & drop files here, or"
        self._browse_text = "browse"

        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(80)
        self.setMaximumHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFont(QFont("Segoe UI", 10))

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.update()

    def set_allowed_extensions(self, exts: list[str] | None) -> None:
        self._allowed_extensions = normalize_extensions(exts)

    def set_hint_text(self, text: str) -> None:
        self._hint_text = text
        self.update()

    def set_browse_text(self, text: str) -> None:
        self._browse_text = text
        self.update()

    def _is_valid_file(self, path: str) -> bool:
        if not self._allowed_extensions:
            return True
        return Path(path).suffix.lower().lstrip(".") in self._allowed_extensions

    # ── Paint & Events (MUST BE camelCase) ────────────────────────────────────

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

        path = QPainterPath()
        path.addRoundedRect(rect, self.BORDER_RADIUS, self.BORDER_RADIUS)
        painter.fillPath(path, colors["bg"])

        pen = QPen(colors["border"], 1.5, Qt.PenStyle.DashLine)
        pen.setDashPattern([self.BORDER_DASH_LENGTH, self.BORDER_DASH_GAP])
        painter.setPen(pen)
        painter.drawPath(path)

        cx = rect.center().x()
        cy = rect.center().y()
        self._draw_multi_icon(painter, cx, cy - 18, colors["icon"])

        fm = QFontMetrics(self.font())
        hint_w = fm.horizontalAdvance(self._hint_text)
        browse_w = fm.horizontalAdvance(f" {self._browse_text}")
        total_w = hint_w + browse_w
        text_y = cy + 10

        painter.setPen(colors["text_secondary"])
        painter.drawText(QPointF(cx - total_w / 2, text_y), self._hint_text)
        painter.setPen(colors["accent"])
        painter.drawText(
            QPointF(cx - total_w / 2 + hint_w, text_y), f" {self._browse_text}"
        )

        if self._allowed_extensions:
            ext_text = "Supported: " + ", ".join(
                f".{e}" for e in self._allowed_extensions
            )
            small_font = QFont(self.font())
            small_font.setPointSize(max(7, self.font().pointSize() - 1))
            painter.setFont(small_font)
            fm2 = QFontMetrics(small_font)
            painter.setPen(colors["text_hint"])
            painter.drawText(
                QPointF(cx - fm2.horizontalAdvance(ext_text) / 2, text_y + 17),
                ext_text,
            )

    def _draw_multi_icon(
        self, painter: QPainter, cx: float, cy: float, color: QColor
    ) -> None:
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
        self._draw_mini_page(
            painter,
            cx + s * 0.25,
            cy - s * 0.15,
            s * 0.75,
            QColor(color.red(), color.green(), color.blue(), 100),
        )
        self._draw_mini_page(painter, cx - s * 0.15, cy, s * 0.85, color)
        painter.restore()

    def _draw_mini_page(
        self, painter: QPainter, cx: float, cy: float, s: float, color: QColor
    ) -> None:
        pen = painter.pen()
        painter.setPen(
            QPen(
                color,
                pen.widthF(),
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        fold = s * 0.32
        page = QPainterPath()
        page.moveTo(cx - s * 0.5, cy - s)
        page.lineTo(cx + s * 0.18, cy - s)
        page.lineTo(cx + s * 0.5, cy - s + fold)
        page.lineTo(cx + s * 0.5, cy + s)
        page.lineTo(cx - s * 0.5, cy + s)
        page.closeSubpath()
        painter.drawPath(page)

        fold_path = QPainterPath()
        fold_path.moveTo(cx + s * 0.18, cy - s)
        fold_path.lineTo(cx + s * 0.18, cy - s + fold)
        fold_path.lineTo(cx + s * 0.5, cy - s + fold)
        painter.drawPath(fold_path)
        painter.setPen(pen)

    def enterEvent(self, event: QEnterEvent) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.browse_requested.emit()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in event.mimeData().urls()]
            valid_paths = [
                p for p in paths if os.path.isfile(p) and self._is_valid_file(p)
            ]
            self._drag_valid = len(valid_paths) > 0
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
        paths = [u.toLocalFile() for u in event.mimeData().urls()]
        valid = [p for p in paths if os.path.isfile(p) and self._is_valid_file(p)]
        if valid:
            self.files_dropped.emit(valid)
            event.acceptProposedAction()
        else:
            event.ignore()

    def sizeHint(self) -> QSize:
        return QSize(400, 90)


# ── Public Widget ─────────────────────────────────────────────────────────────


class DropMultiFilesWidget(QWidget):
    """
    Fluent Design widget for selecting multiple files via drag & drop or dialog.
    """

    files_changed = pyqtSignal(list)
    file_added = pyqtSignal(str)
    file_removed = pyqtSignal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        theme: Theme = Theme.DARK,
        allowed_extensions: list[str] | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._allowed_extensions: list[str] = normalize_extensions(allowed_extensions)
        self._dialog_title = "Select files"
        self._dialog_dir = ""
        self._max_file_count: int | None = None

        self._setup_ui()
        self._apply_theme()

    # ── UI setup ──────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # Drop zone (fixed height, always visible)
        self._drop_zone = _MultiDropZone(self, self._theme, self._allowed_extensions)
        self._drop_zone.files_dropped.connect(self._on_files_dropped)
        self._drop_zone.browse_requested.connect(self._open_dialog)
        root.addWidget(self._drop_zone)

        # Chip list — lives inside a scroll area so it never overflows
        self._file_list = _FileListWidget(self._theme)
        self._file_list.file_removed.connect(self._on_file_removed)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setSizeAdjustPolicy(QScrollArea.SizeAdjustPolicy.AdjustIgnored)
        self._scroll.setWidget(self._file_list)
        self._scroll.setFrameShape(self._scroll.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._scroll.setFixedHeight(120)
        self._scroll.hide()

        root.addWidget(self._scroll)

        # Bottom row: [stretch] [Add files] [✕]
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)

        self._browse_btn = QPushButton("Add files")
        self._browse_btn.setObjectName("browseButton")
        self._browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._browse_btn.clicked.connect(self._open_dialog)

        self._clear_btn = QPushButton("✕")
        self._clear_btn.setObjectName("clearButton")
        self._clear_btn.setToolTip("Clear all files")
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.clicked.connect(self._clear_all)
        self._clear_btn.hide()

        bottom_row.addStretch()
        bottom_row.addWidget(self._browse_btn)
        bottom_row.addWidget(self._clear_btn)
        root.addLayout(bottom_row)

    def _apply_theme(self) -> None:
        self.setStyleSheet(FluentFilePickerStyleSheet.get_widget_style(self._theme))
        self._drop_zone.set_theme(self._theme)
        self._file_list.set_theme(self._theme)

    def _update_ui_state(self) -> None:
        has = self._file_list.count() > 0
        self._clear_btn.setVisible(has)
        self._scroll.setVisible(has)

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

    def set_max_file_count(self, count: int | None) -> None:
        self._max_file_count = count if (count is None or count > 0) else None

    def max_file_count(self) -> int | None:
        return self._max_file_count

    def set_hint_text(self, text: str) -> None:
        self._drop_zone.set_hint_text(text)

    def set_browse_text(self, text: str) -> None:
        self._drop_zone.set_browse_text(text)

    def set_browse_button_text(self, text: str) -> None:
        self._browse_btn.setText(text)

    def set_browse_button_visible(self, visible: bool) -> None:
        self._browse_btn.setVisible(visible)

    def current_files(self) -> list[str]:
        return self._file_list.file_paths()

    def set_files(self, paths: list[str]) -> None:
        self._file_list.clear()
        for path in paths:
            self._add_file_internal(path, emit=False)
        self._update_ui_state()
        self.files_changed.emit(self._file_list.file_paths())

    def add_file(self, path: str) -> bool:
        return self._add_file_internal(path, emit=True)

    def remove_file(self, path: str) -> None:
        self._file_list.remove_file(path)
        self._update_ui_state()
        self.file_removed.emit(path)
        self.files_changed.emit(self._file_list.file_paths())

    def clear_files(self) -> None:
        self._file_list.clear()
        self._update_ui_state()
        self.files_changed.emit([])

    def file_count(self) -> int:
        return self._file_list.count()

    def has_files(self) -> bool:
        return not self._file_list.is_empty()

    # Qt Override method - Must be camelCase
    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        self._browse_btn.setEnabled(enabled)
        self._clear_btn.setEnabled(enabled)
        self._drop_zone.setEnabled(enabled)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _add_file_internal(self, path: str, *, emit: bool = True) -> bool:
        if not os.path.isfile(path):
            return False
        if (
            self._max_file_count is not None
            and self._file_list.count() >= self._max_file_count
        ):
            return False
        if self._allowed_extensions:
            ext = Path(path).suffix.lower().lstrip(".")
            if ext not in self._allowed_extensions:
                return False

        added = self._file_list.add_file(path)
        if added:
            self._update_ui_state()
            if emit:
                self.file_added.emit(path)
                self.files_changed.emit(self._file_list.file_paths())
        return added

    def _on_files_dropped(self, paths: list[str]) -> None:
        added_any = False
        for path in paths:
            if self._add_file_internal(path, emit=False):
                self.file_added.emit(path)
                added_any = True
        if added_any:
            self.files_changed.emit(self._file_list.file_paths())

    def _on_file_removed(self, path: str) -> None:
        self._update_ui_state()
        self.file_removed.emit(path)
        self.files_changed.emit(self._file_list.file_paths())

    def _clear_all(self) -> None:
        self._file_list.clear()
        self._update_ui_state()
        self.files_changed.emit([])

    def _open_dialog(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            self._dialog_title,
            self._dialog_dir,
            self._build_filter_string(),
        )
        if paths:
            self._on_files_dropped(paths)

    def _build_filter_string(self) -> str:
        if not self._allowed_extensions:
            return "All files (*.*)"
        patterns = " ".join(f"*.{e}" for e in self._allowed_extensions)
        return f"Supported files ({patterns});;All files (*.*)"
