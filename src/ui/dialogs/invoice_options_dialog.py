from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QGroupBox,
    QComboBox,
    QDialogButtonBox,
)


class InvoiceOptionsDialog(QDialog):
    """Dialog to choose TVA inclusion and payment mode for invoice generation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Options de facture")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)

        # TVA choice
        tva_group = QGroupBox("TVA")
        tva_layout = QVBoxLayout()
        self.radio_with_tva = QRadioButton("Avec TVA (19%)")
        self.radio_without_tva = QRadioButton("Sans TVA")
        self.radio_with_tva.setChecked(True)
        tva_layout.addWidget(self.radio_with_tva)
        tva_layout.addWidget(self.radio_without_tva)
        tva_group.setLayout(tva_layout)
        layout.addWidget(tva_group)

        # Payment mode
        pay_layout = QHBoxLayout()
        pay_layout.addWidget(QLabel("Mode de paiement:"))
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Espèces", "Chèque", "Virement bancaire"])
        pay_layout.addWidget(self.payment_combo)
        layout.addLayout(pay_layout)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self) -> tuple[bool, str]:
        include_tva = self.radio_with_tva.isChecked()
        payment_mode = self.payment_combo.currentText()
        return include_tva, payment_mode


__all__ = ["InvoiceOptionsDialog"]
