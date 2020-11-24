#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import signal
import sys
from passlib.hash import pbkdf2_sha256
from pprint import pprint

import passwordmeter
from PySide2.QtCore import QObject, Signal, QFile
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QMessageBox, QCompleter, QMainWindow, QAction

from admin_widgets import LoginWindow, RegisterWindow, UsersWindow,PlayersWindow
# from metrics import *

FILE_PATH = os.path.abspath(__file__)
print(FILE_PATH)
# DATABASE_PATH = "resources/users_db.sqlite"
USERS_FILE_PATH = "passwords.json"
SHADOWS_FILE_PATH = "shadows.json"
# print FILE_PATH
#print os.getcwd()

list_of_users = []
list_of_games = []


class DDBBStatus:
    connected = 1
    disconneted = 2


class Singleton(type(QObject), type):
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance


class QUserManager(QObject):
    __metaclass__ = Singleton

    status_changed = Signal(str)

    def __init__(self, parent=None,  **kwargs):
        super(QUserManager, self).__init__(parent, **kwargs)
        # self.users_db = QSqlDatabase.addDatabase("QSQLITE")
        # self.users_db.setDatabaseName(DATABASE_PATH)
        # self.status = DDBBStatus.disconneted
        self.users_data = {}

    def load_therapists(self):
        with open(USERS_FILE_PATH) as f:
            print ("[INFO] Loading users ...")
            self.users_data = json.load(f)
            for user,algo in self.users_data.items():
                list_of_users.append(user)
        pprint(self.users_data)

    def check_user_password(self, username, password_to_check):
        print ("[INFO] Checking password ...")
        if len(self.users_data) > 0:
            with open(SHADOWS_FILE_PATH) as f:
                stored_passwords = json.load(f)
                if username in stored_passwords:
                    if username in self.users_data:
                        if self.users_data[username][2] == '_':
                            hash = stored_passwords[username]
                            if pbkdf2_sha256.verify(password_to_check, hash):

                                return True
                            else:
                                print ("WARNING: check_user_password: password mismatch")
                                return False
                        else:
                            print ("ERROR: check_user_password: Password should be shadowed")
                    else:
                        print ("ERROR: check_user_password: username does't exist")
                else:
                    print ("ERROR: check_user_password: username does't exist")
        else:
            print ("ERROR: check_user_password: No user load.")
            return False

    def set_username_password(self, username, plain_password, role='admin'):
        with open(SHADOWS_FILE_PATH, "r") as f:
            stored_passwords = json.load(f)
        with open(SHADOWS_FILE_PATH, "w") as f:
            stored_passwords[username] = pbkdf2_sha256.hash(plain_password)
            json.dump(stored_passwords, f)
        self.users_data[username] = [username, role, '_']
        with open(USERS_FILE_PATH, "w") as f:
            json.dump(self.users_data, f)

    def check_user(self,username): #Return true when the user is found
        if len(self.users_data) > 0:
            if username in self.users_data:
                return True
            else:
                return False
        else:
            return False



class MainWindow(QMainWindow):
    login_executed = Signal(bool)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        #User Management
        self.user_ddbb_connector = QUserManager()
        self.user_ddbb_connector.status_changed.connect(self.ddbb_status_changed)
        self.user_ddbb_connector.load_users()

        #Load widget from ui
        # self.mylayout = QVBoxLayout()
        # self.setLayout(self.mylayout)
        loader = QUiLoader()
        loader.registerCustomWidget(LoginWindow)
        loader.registerCustomWidget(RegisterWindow)
        loader.registerCustomWidget(UsersWindow)
        loader.registerCustomWidget(PlayersWindow)
        file = QFile("/home/robocomp/robocomp/components/euroage-tv/components/tvGames/src/modules/mainUI.ui")
        file.open(QFile.ReadOnly)
        self.ui = loader.load(file, self.parent())
        file.close()
        # self.mylayout.addWidget(self.ui)
        # self.mylayout.setContentsMargins(0, 0, 0, 0)

        self.setCentralWidget(self.ui)
        self.ui.stackedWidget.setCurrentIndex(0) #Poner a 0

        ##Menu
        self.mainMenu = self.menuBar()
        fileMenu = self.mainMenu.addMenu('&Menú')
        self.mainMenu.setEnabled(False)

        exitAction = QAction( '&Salir', self)
        exitAction.triggered.connect(QApplication.quit)
        fileMenu.addAction(exitAction)

        closeAction = QAction ('&Cerrar sesión', self)
        closeAction.triggered.connect (self.close_session_clicked)
        fileMenu.addAction(closeAction)


        ## Login window
        self.ui.login_button_2.clicked.connect(self.check_login)
        self.ui.newuser_button_2.clicked.connect(self.newuser_clicked)
        self.login_executed.connect(self.update_login_status)

        completer = QCompleter(list_of_users)
        self.ui.username_lineedit.setCompleter(completer)

        ## Register window
        self.ui.password_lineedit_reg.textChanged.connect(self.password_strength_check)
        self.ui.password_2_lineedit_reg.textChanged.connect(self.password_strength_check)
        self.ui.createuser_button_reg.clicked.connect(self.create_new_user)
        self.ui.back_button_reg.clicked.connect(self.back_clicked)


        ##Users window

        self.admin = Admin_Elderly()
        list = self.admin.get_list_elderly()

        completer2 = QCompleter(list)
        self.ui.selplayer_combobox.addItems(list)
        self.ui.selplayer_combobox.setCompleter(completer2)
        self.ui.selplayer_combobox.lineEdit().setPlaceholderText("Selecciona jugador...")
        self.selected_player_incombo = ""
        self.ui.selgame_combobox.lineEdit().setPlaceholderText("Selecciona juego...")

        completer3 = QCompleter(list_of_games)
        self.ui.selgame_combobox.addItems(list_of_games)
        self.ui.selgame_combobox.setCompleter(completer3)

        self.selected_player_inlist = ""

        self.ui.listplayer_list.currentItemChanged.connect(self.selectediteminlist_changed)
        self.ui.selplayer_combobox.currentIndexChanged.connect(self.selectedplayer_changed)
        self.ui.addplayer_button.clicked.connect(self.addusertolist)
        self.ui.deleteplayer_buttton.clicked.connect(self.deleteuserfromlist)
        self.ui.startgame_button.clicked.connect(self.start_game)
        self.ui.seedata_button.clicked.connect(self.see_userdata)

        ##Player window
        self.ui.back_player_button.clicked.connect(self.back_clicked)
        self.ui.create_player_button.clicked.connect(self.create_player)

    def ddbb_status_changed(self, string):
        self.ui.login_status.setText(string)

    #Login window functions
    def check_login(self):
        print ("[INFO] Checking login ...")

        username = unicode(self.ui.username_lineedit.text())
        # username = username.strip().lower() ##The username is stored and checked in lower case
        password = unicode(self.ui.password_lineedit.text())

        if self.user_ddbb_connector.check_user_password(username, password):

            self.ui.stackedWidget.setCurrentIndex(2)
            self.mainMenu.setEnabled(True)
            self.login_executed.emit(True)
        else:
            QMessageBox().information(self.focusWidget(), 'Error',
                                      'El usuario o la contraseña son incorrectos',
                                      QMessageBox.Ok)
            self.login_executed.emit(False)

    def update_login_status(self, status):
        if not status:
            self.ui.login_status.setText("[!]Login failed")
        else:
            self.ui.login_status.setText("[+]Login OK")

    def newuser_clicked(self):
        index = self.ui.stackedWidget.indexOf(self.ui.register_page)
        self.ui.stackedWidget.setCurrentIndex(index)


    #Register window functions
    def password_strength_check(self):
        password = unicode(self.ui.password_lineedit_reg.text())
        repeated_password = unicode(self.ui.password_2_lineedit_reg.text())
        strength, improvements = passwordmeter.test(password)

        if strength < 0.5:
            message = ""
            for improve in improvements.values():
                if message != "":
                    message += "\n"
                message += u"· " + improve
            self.ui.password_status_reg.setText(message)
            return False
        if repeated_password != password:
            self.ui.password_status_reg.setText(u"Las contraseñas introducidas no coinciden")
            return False
        self.ui.password_status_reg.setText(u"")
        return True


    def create_new_user(self):
        print ("[INFO] Trying to create new user ...")

        if self.password_strength_check():
            username = unicode(self.ui.username_lineedit_reg.text())
            # username = username.strip().lower()
            password = unicode(self.ui.password_lineedit_reg.text())

            if self.user_ddbb_connector.check_user(username) == True: #The user already exist
                QMessageBox().information(self.focusWidget(), 'Error',
                                          'El nombre de usuario ya existe',
                                          QMessageBox.Ok)
                return False
            else:
                self.user_ddbb_connector.set_username_password(username, password)
                QMessageBox().information(self.focusWidget(), '',
                                          'Usuario creado correctamente',
                                          QMessageBox.Ok)

                self.user_ddbb_connector.load_users() ##Reload the users
                completer = QCompleter(list_of_users)
                self.ui.username_lineedit.setCompleter(completer)
                self.ui.stackedWidget.setCurrentIndex(0)
                return True
        else:
            print ("[ERROR] The user couldn't be created ")
            return False

    def close_session_clicked(self):
        self.mainMenu.setEnabled(False)
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.password_lineedit.clear()

    def back_clicked(self):
        index = self.ui.stackedWidget.currentIndex()
        if (index != 0):
            index = index - 1
            if (index == 0):
                self.mainMenu.setEnabled(False)
            self.ui.stackedWidget.setCurrentIndex(index)

    #Users window functions
    def deleteuserfromlist(self):
        item_to_delete = self.ui.listplayer_list.currentRow()
        self.ui.listplayer_list.takeItem(item_to_delete)

    def selectedplayer_changed(self):
        self.selected_player_incombo = self.ui.selplayer_combobox.currentText()
        if (self.ui.selplayer_combobox.currentIndex() == 1): #Nuevo jugador
            reply = QMessageBox.question(self.focusWidget(), '',
                                         ' Quiere añadir a un nuevo jugador?', QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.No:
                self.ui.selplayer_combobox.setCurrentIndex(0)
                return False

            else:
                self.new_player_window()
                return True

    def selectediteminlist_changed(self):
        self.selected_player_inlist =  self.ui.listplayer_list.currentItem().text()

    def addusertolist(self):
        if (self.selected_player_incombo != "" ):
            self.ui.listplayer_list.addItem(self.selected_player_incombo)
            return True
        else:
            QMessageBox().information(self.focusWidget(), 'Error',
                                      'No se han seleccionado jugadores',
                                      QMessageBox.Ok)
            return False

    def start_game(self):
        print('start_game')
        items = []
        for index in xrange(self.ui.listplayer_list.count()):
            items.append(self.ui.listplayer_list.item(index).text())

        if(self.ui.selgame_combobox.currentText() ==""):
            print("No se ha seleccionado ningún juego")
        else:
            print("Jugadores : ", items, "jugaran a: ", self.ui.selgame_combobox.currentText())


    def see_userdata(self): ##get the id of the user to get the metrics
        if (self.selected_player_inlist != ""):
            print ("Ver datos del usuario ",self.selected_player_inlist)
        else:
            print("No item selected")

    def new_player_window(self):
        self.ui.stackedWidget.setCurrentIndex(3)

    def create_player(self):

        name = unicode(self.ui.name_player_lineedit.text())
        s1 = unicode(self.ui.surname1_player_lineedit.text())
        s2 = unicode(self.ui.surname2_player_lineedit.text())
        age = float(self.ui.age_player_lineedit.text())

        id = self.admin.add_elderly(name,s1,s2,age)

        new_list = self.admin.get_list_elderly()
        completer = QCompleter(new_list)


        last_element =new_list[-1]
        self.ui.selplayer_combobox.addItem(last_element)


        self.ui.selplayer_combobox.setCompleter(completer)
        self.ui.selplayer_combobox.setCurrentIndex(0)
        self.ui.stackedWidget.setCurrentIndex(2)

        self.ui.name_player_lineedit.clear()
        self.ui.surname1_player_lineedit.clear()
        self.ui.surname2_player_lineedit.clear()
        self.ui.age_player_lineedit.clear()



if __name__ == '__main__':

    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    main = MainWindow()
    main.show()

    app.exec_()