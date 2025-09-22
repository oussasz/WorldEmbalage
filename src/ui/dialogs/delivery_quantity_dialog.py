from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QRadioButton, QSpinBox,
    QLabel, QPushButton, QDialogButtonBox
)
from PyQt6.QtCore import Qt


class DeliveryQuantityDialog(QDialog):
    """Dialog to choose delivery quantity: all or a specific amount."""

    def __init__(self, total_quantity: int, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Bon de livraison - Quantité")
        self._total = max(int(total_quantity or 0), 0)
        self._chosen = 0

        layout = QVBoxLayout(self)

        # Option: deliver all
        self.radio_all = QRadioButton(f"Livrer toute la quantité ({self._total})")
        self.radio_all.setChecked(True)
        layout.addWidget(self.radio_all)

        # Option: deliver specific
        row = QHBoxLayout()
        self.radio_specific = QRadioButton("Livrer une quantité spécifique:")
        self.spin_specific = QSpinBox()
        self.spin_specific.setRange(1, max(self._total, 1))
        self.spin_specific.setValue(min(1, self._total) if self._total > 0 else 1)
        self.spin_specific.setEnabled(False)

        row.addWidget(self.radio_specific)
        row.addWidget(self.spin_specific, 1)
        layout.addLayout(row)

        # Help text
        help_lbl = QLabel("Choisissez si vous souhaitez livrer toute la quantité disponible\n"
                          "ou bien une quantité partielle.")
        help_lbl.setWordWrap(True)
        help_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(help_lbl)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Wiring
        self.radio_specific.toggled.connect(self._on_toggle_specific)

    def _on_toggle_specific(self, checked: bool) -> None:
        self.spin_specific.setEnabled(checked)

    def _on_accept(self) -> None:
        if self.radio_all.isChecked():
            self._chosen = self._total
        else:
            self._chosen = int(self.spin_specific.value())
        # Guard against invalid values
        if self._chosen <= 0:
            self._chosen = 0
        self.accept()

    def chosen_quantity(self) -> int:
        return int(self._chosen)

    def delivered_all(self) -> bool:
        return self.radio_all.isChecked() or self._chosen >= self._total
