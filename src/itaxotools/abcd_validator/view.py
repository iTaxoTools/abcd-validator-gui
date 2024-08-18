from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from pathlib import Path
from typing import Callable

from itaxotools.common.bindings import Binder, PropertyRef

from .model import LogModel, Model
from .types import LogEntry
from .widgets import BigPushButton, ElidedLineEdit, FailureDialog, LongLabel, SuccessDialog


class Main(QtWidgets.QWidget):
    def __init__(self, args: dict):
        super().__init__()
        self.title = "ABCD validator"
        self.resize(560, 0)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle(self.title)

        self.model = Model(args)
        self.logs = LogModel()
        self.binder = Binder()
        self.success_dialog = SuccessDialog(self)
        self.failure_dialog = FailureDialog(self, self.logs)

        label = LongLabel(
            "Test whether your tables with specimen-based taxonomic data "
            "and associated files are correctly structured and named to be "
            "uploaded to a repository. "
            "Table column headers will be checked against the standards of "
            "ABCD (Access to Biological Collections Data). "
            "<br><br>"
            "Read more about the ABCD schema here: "
            '<a href="https://abcd.tdwg.org">https://abcd.tdwg.org</a>'
        )
        fields = self.draw_input_fields()
        validate = BigPushButton("VALIDATE")

        self.binder.bind(self.model.properties.ready, validate.setEnabled)
        self.binder.bind(self.model.properties.busy, self.set_busy)
        self.binder.bind(self.model.logs, self.report_logs)
        self.binder.bind(validate.clicked, self.model.start)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addWidget(label)
        layout.addLayout(fields)
        layout.addWidget(validate)
        self.setLayout(layout)

        self.setFixedHeight(self.sizeHint().height())
        self.setMinimumWidth(self.sizeHint().width() + 100)

    def draw_input_fields(self):
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(8)

        properties = self.model.properties
        self.draw_input_field_row(layout, 0, "Specimen table", properties.specimen_file_path, self.show_file_dialog)
        self.draw_input_field_row(layout, 1, "Measurement table", properties.measurement_file_path, self.show_file_dialog)
        self.draw_input_field_row(layout, 2, "Multimedia file table", properties.multimedia_file_path, self.show_file_dialog)
        self.draw_input_field_row(layout, 3, "Folder with multimedia files", properties.multimedia_folder_path, self.show_folder_dialog)

        return layout

    def draw_input_field_row(self, layout: QtWidgets.QGridLayout, row: int, text: str, property: PropertyRef, method: Callable):
        label = QtWidgets.QLabel(text + ":")
        field = ElidedLineEdit()
        button = QtWidgets.QPushButton("Browse")
        self.binder.bind(button.clicked, lambda: method(property))
        self.binder.bind(field.textDeleted, lambda: property.set(Path()))
        self.binder.bind(property, field.setPath)
        layout.addWidget(label, row, 0)
        layout.addWidget(field, row, 1)
        layout.addWidget(button, row, 2)

    def show_file_dialog(self, property: PropertyRef):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self.window(),
            caption=f"{self.title} - Browse file",
        )
        if not filename:
            return
        property.set(Path(filename))

    def show_folder_dialog(self, property: PropertyRef):
        filename = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self.window(),
            caption=f"{self.title} - Browse file",
        )
        if not filename:
            return
        property.set(Path(filename))

    def set_busy(self, busy: bool):
        self.setEnabled(not busy)
        if busy:
            cursor = QtGui.QCursor(QtCore.Qt.BusyCursor)
            QtWidgets.QApplication.setOverrideCursor(cursor)
        else:
            QtWidgets.QApplication.restoreOverrideCursor()

    def report_logs(self, logs: list[LogEntry]):
        if not logs:
            self.success_dialog.exec()
        else:
            self.logs.set_logs(logs)
            self.failure_dialog.exec()