"""Fluent Design color definitions and resolution helpers for file picker widgets."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtGui import QColor

    from .styles import Theme


# Raw RGBA tuples — safe to define at module level (no QApplication needed).
# Format: (R, G, B, A) — A is optional (defaults to 255 if omitted).
_PALETTE: dict[str, tuple[int, ...]] = {
    # ── Drop zone — Dark ──────────────────────────────────────────────────────
    "DARK_DROP_BG":                  (255, 255, 255, 10),
    "DARK_DROP_BG_HOVER":            (255, 255, 255, 18),
    "DARK_DROP_BG_DRAG":             (138, 180, 248, 25),
    "DARK_DROP_BG_DRAG_INVALID":     (255, 100, 100, 20),
    "DARK_DROP_BORDER":              (255, 255, 255, 35),
    "DARK_DROP_BORDER_HOVER":        (255, 255, 255, 55),
    "DARK_DROP_BORDER_DRAG":         (138, 180, 248, 180),
    "DARK_DROP_BORDER_DRAG_INVALID": (255, 100, 100, 150),
    "DARK_TEXT_PRIMARY":             (255, 255, 255),
    "DARK_TEXT_SECONDARY":           (255, 255, 255, 140),
    "DARK_TEXT_HINT":                (255, 255, 255, 100),
    "DARK_ACCENT":                   (138, 180, 248),
    "DARK_ICON":                     (255, 255, 255, 160),
    "DARK_ICON_DRAG":                (138, 180, 248),
    # ── File chip — Dark ──────────────────────────────────────────────────────
    "DARK_CHIP_BG":                  (255, 255, 255, 22),
    "DARK_CHIP_BG_HOVER":            (255, 255, 255, 32),
    "DARK_CHIP_BORDER":              (255, 255, 255, 40),
    "DARK_CHIP_TEXT":                (255, 255, 255),
    "DARK_CHIP_SUBTEXT":             (255, 255, 255, 140),
    "DARK_CHIP_REMOVE_ICON":         (255, 255, 255, 160),
    "DARK_CHIP_REMOVE_HOVER_BG":     (255, 255, 255, 45),
    # ── Drop zone — Light ─────────────────────────────────────────────────────
    "LIGHT_DROP_BG":                 (0, 0, 0, 6),
    "LIGHT_DROP_BG_HOVER":           (0, 0, 0, 10),
    "LIGHT_DROP_BG_DRAG":            (0, 103, 192, 15),
    "LIGHT_DROP_BG_DRAG_INVALID":    (255, 50, 50, 12),
    "LIGHT_DROP_BORDER":             (0, 0, 0, 40),
    "LIGHT_DROP_BORDER_HOVER":       (0, 0, 0, 65),
    "LIGHT_DROP_BORDER_DRAG":        (0, 103, 192, 180),
    "LIGHT_DROP_BORDER_DRAG_INVALID":(220, 50, 50, 150),
    "LIGHT_TEXT_PRIMARY":            (0, 0, 0),
    "LIGHT_TEXT_SECONDARY":          (0, 0, 0, 140),
    "LIGHT_TEXT_HINT":               (0, 0, 0, 100),
    "LIGHT_ACCENT":                  (0, 103, 192),
    "LIGHT_ICON":                    (0, 0, 0, 140),
    "LIGHT_ICON_DRAG":               (0, 103, 192),
    # ── File chip — Light ─────────────────────────────────────────────────────
    "LIGHT_CHIP_BG":                 (0, 0, 0, 12),
    "LIGHT_CHIP_BG_HOVER":           (0, 0, 0, 18),
    "LIGHT_CHIP_BORDER":             (0, 0, 0, 25),
    "LIGHT_CHIP_TEXT":               (0, 0, 0),
    "LIGHT_CHIP_SUBTEXT":            (0, 0, 0, 140),
    "LIGHT_CHIP_REMOVE_ICON":        (0, 0, 0, 140),
    "LIGHT_CHIP_REMOVE_HOVER_BG":    (0, 0, 0, 35),
}

# Extension → RGBA tuple mapping (single source of truth).
_EXT_COLOR_MAP: dict[str, tuple[int, int, int]] = {
    # Documents
    "pdf":  (220, 50,  50),
    "doc":  (0,   86,  179),
    "docx": (0,   86,  179),
    "xls":  (16,  124, 65),
    "xlsx": (16,  124, 65),
    "ppt":  (198, 75,  28),
    "pptx": (198, 75,  28),
    "txt":  (100, 100, 100),
    # Images
    "png":  (0,   150, 136),
    "jpg":  (0,   150, 136),
    "jpeg": (0,   150, 136),
    "gif":  (0,   150, 136),
    "svg":  (255, 152, 0),
    "webp": (0,   150, 136),
    # Code
    "py":   (53,  114, 165),
    "js":   (241, 196, 15),
    "ts":   (0,   122, 204),
    "html": (227, 79,  38),
    "css":  (21,  114, 182),
    "json": (150, 100, 0),
    # Archives
    "zip":  (120, 80,  160),
    "rar":  (120, 80,  160),
    "7z":   (120, 80,  160),
    # Media
    "mp4":  (0,   120, 215),
    "mp3":  (0,   180, 120),
    "wav":  (0,   180, 120),
}

_DEFAULT_EXT_COLOR: tuple[int, int, int] = (100, 100, 110)


def _make_color(rgba: tuple[int, ...]) -> QColor:
    """Construct a QColor from a 3- or 4-element RGBA tuple."""
    from PyQt6.QtGui import QColor  # deferred — requires QApplication to exist
    if len(rgba) == 4:
        return QColor(rgba[0], rgba[1], rgba[2], rgba[3])
    return QColor(rgba[0], rgba[1], rgba[2])


class FluentFileColors:
    """
    Color palette and resolution helpers for file picker widgets.

    All ``QColor`` objects are constructed **on first use** (lazy), so this
    class is safe to import before a ``QApplication`` is created.

    Use the class-methods (``for_extension``, ``resolve_drop_zone_colors``,
    ``resolve_chip_colors``) instead of reading raw colour values directly.
    """

    # Internal QColor cache — populated lazily.
    _cache: dict[str, QColor] = {}

    # ── Private helpers ───────────────────────────────────────────────────────

    @classmethod
    def _c(cls, key: str) -> QColor:
        """Return (and cache) the QColor for *key* from ``_PALETTE``."""
        if key not in cls._cache:
            cls._cache[key] = _make_color(_PALETTE[key])
        return cls._cache[key]

    # ── Public helpers ────────────────────────────────────────────────────────

    @classmethod
    def for_extension(cls, ext: str) -> QColor:
        """
        Return the badge colour for *ext* (case-insensitive, with or without dot).

        Examples::

            FluentFileColors.for_extension("pdf")   # → red
            FluentFileColors.for_extension(".PNG")   # → teal
            FluentFileColors.for_extension("unknown")  # → default grey
        """
        key = ext.lower().lstrip(".")
        cache_key = f"__ext_{key}"
        if cache_key not in cls._cache:
            rgba = _EXT_COLOR_MAP.get(key, _DEFAULT_EXT_COLOR)
            cls._cache[cache_key] = _make_color(rgba)
        return cls._cache[cache_key]

    @classmethod
    def resolve_drop_zone_colors(
        cls,
        theme: Theme,
        *,
        hovered: bool = False,
        drag_over: bool = False,
        drag_valid: bool = True,
    ) -> dict:
        """
        Return a fully-resolved colour dict for a drop zone widget.

        Keys
        ----
        ``bg``, ``border``, ``icon``,
        ``text_primary``, ``text_secondary``, ``text_hint``, ``accent``,
        ``chip_bg``, ``chip_bg_hover``, ``chip_border``,
        ``chip_text``, ``chip_subtext``,
        ``remove_icon``, ``remove_hover_bg``
        """
        from .styles import Theme  # local — avoids circular import at module level

        prefix = "DARK" if theme == Theme.DARK else "LIGHT"

        if drag_over:
            state = "DRAG" if drag_valid else "DRAG_INVALID"
            bg     = cls._c(f"{prefix}_DROP_BG_{state}")
            border = cls._c(f"{prefix}_DROP_BORDER_{state}")
            icon   = cls._c(f"{prefix}_ICON_DRAG")
        elif hovered:
            bg     = cls._c(f"{prefix}_DROP_BG_HOVER")
            border = cls._c(f"{prefix}_DROP_BORDER_HOVER")
            icon   = cls._c(f"{prefix}_ICON")
        else:
            bg     = cls._c(f"{prefix}_DROP_BG")
            border = cls._c(f"{prefix}_DROP_BORDER")
            icon   = cls._c(f"{prefix}_ICON")

        return {
            "bg":              bg,
            "border":          border,
            "icon":            icon,
            "text_primary":    cls._c(f"{prefix}_TEXT_PRIMARY"),
            "text_secondary":  cls._c(f"{prefix}_TEXT_SECONDARY"),
            "text_hint":       cls._c(f"{prefix}_TEXT_HINT"),
            "accent":          cls._c(f"{prefix}_ACCENT"),
            "chip_bg":         cls._c(f"{prefix}_CHIP_BG"),
            "chip_bg_hover":   cls._c(f"{prefix}_CHIP_BG_HOVER"),
            "chip_border":     cls._c(f"{prefix}_CHIP_BORDER"),
            "chip_text":       cls._c(f"{prefix}_CHIP_TEXT"),
            "chip_subtext":    cls._c(f"{prefix}_CHIP_SUBTEXT"),
            "remove_icon":     cls._c(f"{prefix}_CHIP_REMOVE_ICON"),
            "remove_hover_bg": cls._c(f"{prefix}_CHIP_REMOVE_HOVER_BG"),
        }

    @classmethod
    def resolve_chip_colors(cls, theme: Theme, *, hovered: bool = False) -> dict:
        """
        Return a fully-resolved colour dict for a compact file chip.

        Keys: ``bg``, ``border``, ``text``, ``remove_icon``, ``remove_hover_bg``
        """
        from .styles import Theme  # local — avoids circular import at module level

        prefix = "DARK" if theme == Theme.DARK else "LIGHT"
        bg_key = f"{prefix}_CHIP_BG_HOVER" if hovered else f"{prefix}_CHIP_BG"

        return {
            "bg":              cls._c(bg_key),
            "border":          cls._c(f"{prefix}_CHIP_BORDER"),
            "text":            cls._c(f"{prefix}_CHIP_TEXT"),
            "remove_icon":     cls._c(f"{prefix}_CHIP_REMOVE_ICON"),
            "remove_hover_bg": cls._c(f"{prefix}_CHIP_REMOVE_HOVER_BG"),
        }
