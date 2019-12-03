# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'src/mainUI.ui',
# licensing of 'src/mainUI.ui' applies.
#
# Created: Wed Nov  6 13:08:55 2019
#      by: pyside2-uic  running on PySide2 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_guiDlg(object):
    def setupUi(self, guiDlg):
        guiDlg.setObjectName("guiDlg")
        guiDlg.resize(1054, 863)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(guiDlg)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.video_layout = QtWidgets.QVBoxLayout()
        self.video_layout.setObjectName("video_layout")
        self.verticalLayout_2.addLayout(self.video_layout)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.start_button = QtWidgets.QPushButton(guiDlg)
        self.start_button.setObjectName("start_button")
        self.horizontalLayout.addWidget(self.start_button)
        self.pause_button = QtWidgets.QPushButton(guiDlg)
        self.pause_button.setObjectName("pause_button")
        self.horizontalLayout.addWidget(self.pause_button)
        self.reset_button = QtWidgets.QPushButton(guiDlg)
        self.reset_button.setObjectName("reset_button")
        self.horizontalLayout.addWidget(self.reset_button)
        self.stop_button = QtWidgets.QPushButton(guiDlg)
        self.stop_button.setObjectName("stop_button")
        self.horizontalLayout.addWidget(self.stop_button)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.info_label = QtWidgets.QLabel(guiDlg)
        self.info_label.setMaximumSize(QtCore.QSize(16777215, 20))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setItalic(True)
        self.info_label.setFont(font)
        self.info_label.setObjectName("info_label")
        self.verticalLayout_2.addWidget(self.info_label)

        self.retranslateUi(guiDlg)
        QtCore.QMetaObject.connectSlotsByName(guiDlg)

    def retranslateUi(self, guiDlg):
        guiDlg.setWindowTitle(QtWidgets.QApplication.translate("guiDlg", "robotTherapy", None, -1))
        self.start_button.setText(QtWidgets.QApplication.translate("guiDlg", "Start", None, -1))
        self.pause_button.setText(QtWidgets.QApplication.translate("guiDlg", "Pause", None, -1))
        self.reset_button.setText(QtWidgets.QApplication.translate("guiDlg", "Reset", None, -1))
        self.stop_button.setText(QtWidgets.QApplication.translate("guiDlg", "Stop", None, -1))
        self.info_label.setText(QtWidgets.QApplication.translate("guiDlg", "Info", None, -1))

