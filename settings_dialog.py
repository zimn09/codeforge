"""Settings dialog with live window-transparency preview."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from . import icons, theme


class SettingsDialog(QDialog):
    """Appearance preferences, previewed live on the main window."""

    preview_changed = Signal(bool, int)

    def __init__(
        self,
        transparency_enabled: bool = False,
        transparency_opacity: int = 90,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("settingsDialog")
        self.setWindowTitle("Settings")
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setModal(True)
        self.setFixedWidth(520)
        self.setSizeGripEnabled(False)
        self._build_ui(transparency_enabled, transparency_opacity)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self, enabled: bool, opacity: int) -> None:
        icon_label = QLabel()
        icon_label.setObjectName("settingsBadge")
        icon_label.setFixedSize(38, 38)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setPixmap(
            icons.icon("settings", theme.ACCENT, 20).pixmap(20, 20)
        )

        title = QLabel("Settings")
        title.setObjectName("settingsTitle")
        subtitle = QLabel("Tune the workspace to your taste.")
        subtitle.setObjectName("settingsSubtitle")

        heading = QVBoxLayout()
        heading.setSpacing(1)
        heading.addWidget(title)
        heading.addWidget(subtitle)

        header = QHBoxLayout()
        header.setSpacing(12)
        header.addWidget(icon_label)
        header.addLayout(heading, 1)

        card = QFrame()
        card.setObjectName("settingsCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(10)

        section = QLabel("WINDOW")
        section.setObjectName("sectionLabel")

        self.enable_box = QCheckBox("Transparent window")
        self.enable_box.setObjectName("settingsCheck")
        self.enable_box.setChecked(enabled)
        self.enable_box.setToolTip(
            "Let the desktop show through the CodeForge window"
        )

        description = QLabel(
            "Let your desktop show through. Requires a compositing window manager."
        )
        description.setObjectName("settingsDescription")
        description.setWordWrap(True)

        opacity_label = QLabel("Opacity")
        opacity_label.setObjectName("settingsName")

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(50, 100)
        self.slider.setSingleStep(1)
        self.slider.setPageStep(5)
        self.slider.setValue(max(50, min(100, int(opacity))))
        self.slider.setEnabled(enabled)
        self.slider.setToolTip("Window opacity")

        self.value_label = QLabel(f"{self.slider.value()}%")
        self.value_label.setObjectName("settingsValue")
        self.value_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.value_label.setFixedWidth(38)
        self.value_label.setEnabled(enabled)

        opacity_row = QHBoxLayout()
        opacity_row.setSpacing(10)
        opacity_row.addWidget(opacity_label)
        opacity_row.addWidget(self.slider, 1)
        opacity_row.addWidget(self.value_label)

        hint = QLabel(
            "Changes preview live. Lower values let more of your desktop "
            "through."
        )
        hint.setObjectName("settingsHint")
        hint.setWordWrap(True)

        card_layout.addWidget(section)
        card_layout.addWidget(self.enable_box)
        card_layout.addWidget(description)
        card_layout.addSpacing(4)
        card_layout.addLayout(opacity_row)
        card_layout.addWidget(hint)

        cancel_button = QPushButton("Cancel")
        cancel_button.setMinimumWidth(88)
        cancel_button.clicked.connect(self.reject)

        apply_button = QPushButton("Apply")
        apply_button.setObjectName("primary")
        apply_button.setMinimumWidth(88)
        apply_button.setDefault(True)
        apply_button.clicked.connect(self.accept)

        footer = QHBoxLayout()
        footer.setSpacing(8)
        footer.addStretch(1)
        footer.addWidget(cancel_button)
        footer.addWidget(apply_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(16)
        layout.addLayout(header)
        layout.addWidget(card)
        layout.addStretch(1)
        layout.addLayout(footer)

        self.enable_box.toggled.connect(self._sync)
        self.slider.valueChanged.connect(self._sync)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------
    def _sync(self, _value=None) -> None:
        enabled = self.enable_box.isChecked()
        self.slider.setEnabled(enabled)
        self.value_label.setEnabled(enabled)
        self.value_label.setText(f"{self.slider.value()}%")
        self.preview_changed.emit(enabled, self.slider.value())

    def values(self) -> tuple[bool, int]:
        return self.enable_box.isChecked(), self.slider.value()
