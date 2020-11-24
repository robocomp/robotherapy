# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainUI.ui'
##
## Created by: Qt User Interface Compiler version 5.15.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_guiDlg(object):
    def setupUi(self, guiDlg):
        if not guiDlg.objectName():
            guiDlg.setObjectName(u"guiDlg")
        guiDlg.resize(1054, 863)
        self.verticalLayout_2 = QVBoxLayout(guiDlg)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.video_layout = QVBoxLayout()
        self.video_layout.setObjectName(u"video_layout")

        self.verticalLayout_2.addLayout(self.video_layout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.start_button = QPushButton(guiDlg)
        self.start_button.setObjectName(u"start_button")

        self.horizontalLayout.addWidget(self.start_button)

        self.pause_button = QPushButton(guiDlg)
        self.pause_button.setObjectName(u"pause_button")

        self.horizontalLayout.addWidget(self.pause_button)

        self.reset_button = QPushButton(guiDlg)
        self.reset_button.setObjectName(u"reset_button")

        self.horizontalLayout.addWidget(self.reset_button)

        self.stop_button = QPushButton(guiDlg)
        self.stop_button.setObjectName(u"stop_button")

        self.horizontalLayout.addWidget(self.stop_button)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.info_label = QLabel(guiDlg)
        self.info_label.setObjectName(u"info_label")
        self.info_label.setMaximumSize(QSize(16777215, 20))
        font = QFont()
        font.setPointSize(9)
        font.setItalic(True)
        self.info_label.setFont(font)

        self.verticalLayout_2.addWidget(self.info_label)


        self.retranslateUi(guiDlg)

        QMetaObject.connectSlotsByName(guiDlg)
    # setupUi

    def retranslateUi(self, guiDlg):
        guiDlg.setWindowTitle(QCoreApplication.translate("guiDlg", u"robotTherapy", None))
        self.start_button.setText(QCoreApplication.translate("guiDlg", u"Start", None))
        self.pause_button.setText(QCoreApplication.translate("guiDlg", u"Pause", None))
        self.reset_button.setText(QCoreApplication.translate("guiDlg", u"Reset", None))
        self.stop_button.setText(QCoreApplication.translate("guiDlg", u"Stop", None))
        self.info_label.setText(QCoreApplication.translate("guiDlg", u"Info", None))
    # retranslateUi

