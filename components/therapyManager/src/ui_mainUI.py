# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'src/mainUI.ui',
# licensing of 'src/mainUI.ui' applies.
#
# Created: Fri Oct 18 12:53:16 2019
#      by: pyside2-uic  running on PySide2 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_guiDlg(object):
    def setupUi(self, guiDlg):
        guiDlg.setObjectName("guiDlg")
        guiDlg.resize(400, 300)

        self.retranslateUi(guiDlg)
        QtCore.QMetaObject.connectSlotsByName(guiDlg)

    def retranslateUi(self, guiDlg):
        guiDlg.setWindowTitle(QtWidgets.QApplication.translate("guiDlg", "gameManager", None, -1))

