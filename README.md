# fluent-filepicker

**Fluent Design file picker widgets for PyQt6.**

Drop-in widgets that let users select files via drag & drop or a native
file dialog — styled after Microsoft's Fluent Design System, with full
dark and light theme support.

---

## Features

- **Single-file** and **multi-file** picker widgets
- Drag & drop with live valid / invalid visual feedback
- Native file-dialog integration (single and multi-select)
- Extension filtering with "Supported: .pdf, .png …" hint
- Compact flow-wrapped file chips with remove buttons
- Extension colour-coded badges (PDF → red, XLSX → green, …)
- Dark **and** light Fluent themes
- No external dependencies beyond PyQt6

---

## Requirements

| Dependency | Version |
|---|---|
| Python | ≥ 3.9 |
| PyQt6 | ≥ 6.4.0 |

---

## Installation

```bash
pip install fluent-filepicker
```

---

## Quick start

### Single-file picker

```python
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from fluent_filepicker import DropSingleFileWidget, Theme

app = QApplication(sys.argv)

window = QMainWindow()
container = QWidget()
layout = QVBoxLayout(container)

picker = DropSingleFileWidget(theme=Theme.DARK)
picker.set_allowed_extensions(["pdf", "docx", "png"])
picker.set_dialog_title("Choose a document")

picker.file_selected.connect(lambda path: print(f"Selected: {path}"))
picker.file_cleared.connect(lambda: print("Selection cleared"))

layout.addWidget(picker)
window.setCentralWidget(container)
window.resize(500, 300)
window.show()

sys.exit(app.exec())
```

### Multi-file picker

```python
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from fluent_filepicker import DropMultiFilesWidget, Theme

app = QApplication(sys.argv)

window = QMainWindow()
container = QWidget()
layout = QVBoxLayout(container)

picker = DropMultiFilesWidget(theme=Theme.LIGHT)
picker.set_allowed_extensions(["jpg", "png", "webp"])
picker.set_max_file_count(10)
picker.set_dialog_title("Choose images")

picker.files_changed.connect(lambda paths: print(f"{len(paths)} file(s) selected"))
picker.file_added.connect(lambda path: print(f"Added: {path}"))
picker.file_removed.connect(lambda path: print(f"Removed: {path}"))

layout.addWidget(picker)
window.setCentralWidget(container)
window.resize(600, 400)
window.show()

sys.exit(app.exec())
```

---

## API reference

### `Theme`

```python
from fluent_filepicker import Theme

Theme.DARK   # dark Fluent theme (default)
Theme.LIGHT  # light Fluent theme
```

---

### `DropSingleFileWidget`

```python
DropSingleFileWidget(
    parent=None,
    theme=Theme.DARK,
    allowed_extensions=None,   # e.g. ["pdf", "png"]
)
```

#### Signals

| Signal | Payload | Description |
|---|---|---|
| `file_selected` | `str` | Emitted when a file is selected |
| `file_cleared` | — | Emitted when the selection is cleared |

#### Methods

| Method | Description |
|---|---|
| `set_theme(theme)` | Switch dark / light theme |
| `set_allowed_extensions(exts)` | Set accepted extensions (`None` = all) |
| `set_dialog_title(title)` | File-dialog window title |
| `set_dialog_directory(path)` | Default directory for the dialog |
| `set_hint_text(text)` | Text shown in the empty drop zone |
| `set_browse_text(text)` | Clickable "browse" text in the drop zone |
| `set_browse_button_text(text)` | Label of the button below the drop zone |
| `set_browse_button_visible(visible)` | Show / hide the browse button |
| `current_file()` | Return current path or `None` |
| `set_file(path)` | Programmatically set / clear the file |
| `clear_file()` | Clear selection and emit `file_cleared` |
| `has_file()` | `True` if a file is selected |

---

### `DropMultiFilesWidget`

```python
DropMultiFilesWidget(
    parent=None,
    theme=Theme.DARK,
    allowed_extensions=None,
)
```

#### Signals

| Signal | Payload | Description |
|---|---|---|
| `files_changed` | `list[str]` | Emitted on any change to the file list |
| `file_added` | `str` | Emitted when a file is added |
| `file_removed` | `str` | Emitted when a file is removed |

#### Methods

| Method | Description |
|---|---|
| `set_theme(theme)` | Switch dark / light theme |
| `set_allowed_extensions(exts)` | Set accepted extensions (`None` = all) |
| `set_max_file_count(n)` | Maximum number of files (`None` = unlimited) |
| `set_dialog_title(title)` | File-dialog window title |
| `set_dialog_directory(path)` | Default directory for the dialog |
| `set_hint_text(text)` | Text shown in the drop zone |
| `set_browse_text(text)` | Clickable "browse" text in the drop zone |
| `set_browse_button_text(text)` | Label of the "Add files" button |
| `set_browse_button_visible(visible)` | Show / hide the button |
| `current_files()` | Return `list[str]` of current paths |
| `set_files(paths)` | Replace the file list programmatically |
| `add_file(path)` | Add a single file; returns `True` if added |
| `remove_file(path)` | Remove a specific file |
| `clear_files()` | Remove all files |
| `file_count()` | Number of files currently selected |
| `has_files()` | `True` if at least one file is selected |

---

## Theming

Both widgets adapt automatically when you call `set_theme()`:

```python
from fluent_filepicker import Theme

picker.set_theme(Theme.LIGHT)
picker.set_theme(Theme.DARK)
```

For system-level auto-switching you can connect to your own theme-change
signal and propagate it:

```python
system_theme_changed.connect(
    lambda dark: picker.set_theme(Theme.DARK if dark else Theme.LIGHT)
)
```

---

## Supported extension colours

Badges on file chips are colour-coded automatically:

| Category | Extensions | Colour |
|---|---|---|
| PDF | pdf | Red |
| Word | doc, docx | Blue |
| Excel | xls, xlsx | Green |
| PowerPoint | ppt, pptx | Orange |
| Images | png, jpg, jpeg, gif, webp | Teal |
| SVG | svg | Amber |
| Python | py | Steel blue |
| JavaScript | js | Yellow |
| TypeScript | ts | Blue |
| HTML | html | Orange-red |
| CSS | css | Blue |
| JSON | json | Dark amber |
| Plain text | txt | Grey |
| Archives | zip, rar, 7z | Purple |
| Video | mp4 | Blue |
| Audio | mp3, wav | Mint |

Unknown extensions receive a neutral grey badge.

---

## License

MIT — see [LICENSE](LICENSE) for details.