#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 by YOUR NAME HERE
#
#    This file is part of RoboComp
#
#    RoboComp is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RoboComp is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with RoboComp.  If not, see <http://www.gnu.org/licenses/>.
#

import csv
import json
import math
from datetime import datetime

from PySide2.QtGui import QKeySequence
from passlib.hash import pbkdf2_sha256
from pprint import pprint

import passwordmeter
from PySide2.QtCore import Signal, QObject, Qt
from PySide2.QtWidgets import QMessageBox, QCompleter, QAction, qApp, QApplication, QShortcut

from admin_widgets import *
from genericworker import *

try:
    from bbdd import BBDD
except:
    print ("Database module not found")

FILE_PATH = os.path.abspath(__file__)
CURRENT_PATH = os.path.dirname(__file__)

print(FILE_PATH)
# DATABASE_PATH = "resources/users_db.sqlite"
USERS_FILE_PATH = "src/passwords.json"
SHADOWS_FILE_PATH = "src/shadows.json"
# print FILE_PATH
# print os.getcwd()

list_of_users = []
list_of_therapies = ["Levantar los brazos"]


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


#
# class Session():
#     def __init__(self):
#         self.date = None
#         self.patient = None
#         self.totaltime = 0
#         self.games = []
#         self.numGames = 0
#         self.totalHelps = 0
#         self.totalChecks = 0
#         self.wonGames = 0
#         self.lostGames = 0
#
#     def save_session(self):
#         saving_dir = os.path.join(CURRENT_PATH, "../savedSessions")
#         print ("Saving session in ", saving_dir)
#
#         if not os.path.isdir(saving_dir):
#             os.mkdir(saving_dir)
#
#         patient = self.patient.replace(" ", "").strip()
#         patient_dir = os.path.join(saving_dir, patient)
#
#         if not os.path.isdir(patient_dir):
#             os.mkdir(patient_dir)
#
#         date = datetime.strftime(self.date, "%y%m%d_%H%M%S")
#         date_dir = os.path.join(patient_dir, date)
#
#         if os.path.isdir(date_dir):
#             print ("Error, la sesion ya ha sido guardada")
#             return
#         else:
#             os.mkdir(date_dir)
#
#             for game in self.games:
#                 game.save_game(date_dir)
#
#             rows = [
#                 ['tiempo total', 'num juegos', 'num ayudas', 'num comprobaciones', 'juegos ganados', 'juegos perdidos'],
#                 [self.totaltime, len(self.games), self.totalHelps, self.totalChecks, self.wonGames, self.lostGames]]
#
#             filename = os.path.join(date_dir, "resumeSession" + ".csv")
#
#             with open(filename, 'w') as csvFile:
#                 writer = csv.writer(csvFile)
#                 writer.writerows(rows)
#             csvFile.close()


# class Metrics():
#     def __init__(self):
#         self.time = None
#         self.distance = 0
#         self.touched = 0
#         self.handClosed = 0
#         self.helps = 0
#         self.checks = 0
#         self.hits = 0
#         self.fails = 0
#
#
# class Game():
#     def __init__(self):
#         self.nameGame = None
#         self.date = None
#         self.timePlayed = 0
#         self.timePaused = 0
#         self.metrics = []
#         self.gameWon = False
#
#     def save_game(self, dir):
#         name = self.nameGame
#         filename = os.path.join(dir, name.replace(" ", "").strip().lower() + ".csv")
#         date = datetime.strftime(self.date, "%H:%M:%S")
#
#         rows = [['hora comienzo', 'tiempo total', 'tiempo pausado', 'distancia recorrida', 'num pantalla pulsada',
#                  'num mano cerrada', 'num ayudas', 'num comprobaciones', 'aciertos', 'fallos', 'juego ganado']]
#
#         for m in self.metrics:
#             rows.append([date, self.timePlayed, self.timePaused, m.distance, m.touched, m.handClosed, m.helps,
#                          m.checks, m.hits, m.fails, self.gameWon])
#
#         with open(filename, 'w') as csvFile:
#             writer = csv.writer(csvFile)
#             writer.writerows(rows)
#         csvFile.close()


class QUserManager(QObject):
    __metaclass__ = Singleton

    status_changed = Signal(str)

    def __init__(self, parent=None, **kwargs):
        super(QUserManager, self).__init__(parent, **kwargs)
        # self.users_db = QSqlDatabase.addDatabase("QSQLITE")
        # self.users_db.setDatabaseName(DATABASE_PATH)
        # self.status = DDBBStatus.disconneted
        self.users_data = {}

    def load_users(self):
        with open(USERS_FILE_PATH) as f:
            print ("[INFO] Loading users ...")
            self.users_data = json.load(f)
            for user, algo in self.users_data.items():
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

    def check_user(self, username):  # Return true when the user is found
        if len(self.users_data) > 0:
            if username in self.users_data:
                return True
            else:
                return False
        else:
            return False


class SpecificWorker(GenericWorker):
    login_executed = Signal(bool)
    updateUISig = Signal()

    def __init__(self, proxy_map):
        super(SpecificWorker, self).__init__(proxy_map)
        self.Period = 2000
        self.timer.start(self.Period)

        self.user_ddbb_connector = QUserManager()
        self.user_ddbb_connector.status_changed.connect(self.ddbb_status_changed)
        self.user_ddbb_connector.load_users()

        self.init_ui()
        self.setCentralWidget(self.ui)

        # self.sessions = []
        # self.currentSession = Session()

        # self.currentGame = Game()
        # self.game_metrics = []

        self.aux_sessionInit = False
        self.aux_datePaused = None
        self.aux_currentDate = None
        self.aux_currentStatus = None
        self.aux_wonGame = False
        self.aux_firtsGameInSession = True
        self.aux_reseted = False
        self.aux_firstMetricReceived = True
        self.aux_savedGames = False

        self.selected_patient_incombo = ""
        self.selected_game_inlist = ""
        self.selected_game_incombo = ""
        self.list_therapies_todo = []

        # self.updateUISig.connect(self.updateUI)

        self.manager_machine.start()

    def init_ui(self):
        loader = QUiLoader()
        loader.registerCustomWidget(LoginWindow)
        loader.registerCustomWidget(RegisterWindow)
        loader.registerCustomWidget(UsersWindow)
        loader.registerCustomWidget(PlayersWindow)
        loader.registerCustomWidget(GameWindow)
        file = QFile("/home/robolab/robocomp/components/robotherapy/components/therapyManager/src/stackedUI.ui")
        file.open(QFile.ReadOnly)
        self.ui = loader.load(file, self.parent())
        file.close()

        ##Menu
        self.mainMenu = self.menuBar()
        fileMenu = self.mainMenu.addMenu('&Menú')
        if self.ui.stackedWidget.currentIndex == 0 or self.ui.stackedWidget.currentIndex == 1:
            self.mainMenu.setEnabled(False)

        exitAction = QAction('&Salir', self)
        exitAction.triggered.connect(self.t_admin_to_appEnd)
        QApplication.instance().aboutToQuit.connect(self.t_admin_to_appEnd)
        fileMenu.addAction(exitAction)

        ## Login window
        self.loginShortcut = QShortcut(QKeySequence(Qt.Key_Return), self)
        self.loginShortcut.activated.connect(self.check_login)
        self.ui.login_button_2.clicked.connect(self.check_login)
        self.ui.newuser_button_2.clicked.connect(self.t_userLogin_to_createUser.emit)

        ## Register window
        self.ui.password_lineedit_reg.textChanged.connect(self.password_strength_check)
        self.ui.password_2_lineedit_reg.textChanged.connect(self.password_strength_check)
        self.ui.createuser_button_reg.clicked.connect(self.create_new_user)
        self.ui.back_button_reg.clicked.connect(self.t_createUser_to_userLogin.emit)

        ## User window
        self.ui.therapies_list.currentItemChanged.connect(self.selectediteminlist_changed)
        self.ui.selpatient_combobox.currentIndexChanged.connect(self.selectedplayer_changed)
        self.ui.addTh_button.clicked.connect(self.addgametolist)
        self.ui.deleteTh_button.clicked.connect(self.deleteTherapyFromList)
        self.ui.up_button.clicked.connect(self.movelist_up)
        self.ui.down_button.clicked.connect(self.movelist_down)

        self.ui.startsession_button.clicked.connect(self.start_session)

        ##new Player window
        self.ui.back_patient_button.clicked.connect(self.t_createPatient_to_adminSessions.emit)
        self.ui.create_patient_button.clicked.connect(self.create_patient)

        # Game window
        self.ui.start_game_button.clicked.connect(self.start_clicked)
        self.ui.pause_game_button.clicked.connect(self.pause_clicked)
        self.ui.continue_game_button.clicked.connect(self.continue_clicked)
        self.ui.finish_game_button.clicked.connect(self.finish_clicked)
        self.ui.reset_game_button.clicked.connect(self.reset_clicked)
        self.ui.end_session_button.clicked.connect(self.end_session_clicked)

    def ddbb_status_changed(self, string):
        self.ui.login_status.setText(string)

    # Login window functions

    def check_login(self):
        print ("[INFO] Checking login ...")

        username = unicode(self.ui.username_lineedit.text())
        # username = username.strip().lower() ##The username is stored and checked in lower case
        password = unicode(self.ui.password_lineedit.text())

        if self.user_ddbb_connector.check_user_password(username, password):
            self.loginShortcut.activated.disconnect(self.check_login)
            self.login_executed.emit(True)
            self.t_userLogin_to_adminSessions.emit()

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

    # Register window functions
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

            if self.user_ddbb_connector.check_user(username):  # The user already exist
                QMessageBox().information(self.focusWidget(), 'Error',
                                          'El nombre de usuario ya existe',
                                          QMessageBox.Ok)
                return False
            else:
                self.user_ddbb_connector.set_username_password(username, password)
                QMessageBox().information(self.focusWidget(), '',
                                          'Usuario creado correctamente',
                                          QMessageBox.Ok)

                self.user_ddbb_connector.load_users()  ##Reload the users

                completer = QCompleter(list_of_users)
                self.ui.username_lineedit.setCompleter(completer)

                self.t_createUser_to_userLogin.emit()
                return True
        else:
            print ("[ERROR] No se pudo crear el usuario ")
            return False

    def deleteTherapyFromList(self):
        item_to_delete = self.ui.therapies_list.currentRow()
        self.ui.therapies_list.takeItem(item_to_delete)

    def selectedplayer_changed(self):
        self.selected_patient_incombo = self.ui.selpatient_combobox.currentText()
        if self.ui.selpatient_combobox.currentIndex() == 1:  # New player selected
            reply = QMessageBox.question(self.focusWidget(), '',
                                         ' Quiere añadir a un nuevo paciente?', QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.No:
                self.ui.selpatient_combobox.setCurrentIndex(0)
                return False

            else:
                self.t_adminSessions_to_createPatient.emit()
                return True

    def selectediteminlist_changed(self):
        self.selected_game_inlist = self.ui.therapies_list.currentItem().text()
        print (self.ui.therapies_list.currentRow())

    def addgametolist(self):
        self.selected_game_incombo = self.ui.selTh_combobox.currentText()
        if self.selected_game_incombo != "":
            self.ui.therapies_list.addItem(self.selected_game_incombo)
            self.ui.selTh_combobox.setCurrentIndex(0)
            return True
        else:
            QMessageBox().information(self.focusWidget(), 'Error',
                                      'No se han seleccionado ninguna terapia',
                                      QMessageBox.Ok)
            return False

    def movelist_up(self):
        current_text = self.ui.therapies_list.currentItem().text()
        current_index = self.ui.therapies_list.currentRow()

        if current_index == 0: return
        new_index = current_index - 1
        previous_text = self.ui.therapies_list.item(new_index).text()

        print self.ui.therapies_list.item(new_index).text()

        self.ui.therapies_list.item(current_index).setText(previous_text)
        self.ui.therapies_list.item(new_index).setText(current_text)
        self.ui.therapies_list.setCurrentRow(new_index)

    def movelist_down(self):
        current_text = self.ui.therapies_list.currentItem().text()
        current_index = self.ui.therapies_list.currentRow()

        if current_index == self.ui.therapies_list.count() - 1: return
        new_index = current_index + 1
        previous_text = self.ui.therapies_list.item(new_index).text()

        print self.ui.therapies_list.item(new_index).text()

        self.ui.therapies_list.item(current_index).setText(previous_text)
        self.ui.therapies_list.item(new_index).setText(current_text)
        self.ui.therapies_list.setCurrentRow(new_index)

    # New player
    def create_patient(self):

        name = unicode(self.ui.name_player_lineedit.text())
        s1 = unicode(self.ui.surname1_player_lineedit.text())
        s2 = unicode(self.ui.surname2_player_lineedit.text())
        age = float(self.ui.age_player_lineedit.text())

        self.bbdd.new_patient(name, s1 + " " + s2)
        patients = self.bbdd.get_all_patients()
        patients_list = []
        for p in patients:
            patients_list.append(p.name + " " + p.surname)

        completer = QCompleter(patients_list)
        self.ui.selpatient_combobox.addItem(patients_list[-1])
        self.ui.selpatient_combobox.setCompleter(completer)
        self.t_createPatient_to_adminSessions.emit()

    # Game window functions
    def start_clicked(self):
        self.admintherapy_proxy.adminStartTherapy(self.currentGame.nameGame)

    def pause_clicked(self):
        self.admintherapy_proxy.adminPauseTherapy()

    def continue_clicked(self):
        self.admintherapy_proxy.adminContinueTherapy()

    def finish_clicked(self):
        reply = QMessageBox.question(self.focusWidget(), '',
                                     '¿Desea finalizar la terapia?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.admintherapy_proxy.adminStopTherapy()

    def reset_clicked(self):
        reply = QMessageBox.question(self.focusWidget(), '',
                                     '¿Desea volver a empezar? Los datos de la terapia no se guardarán',
                                     QMessageBox.Yes,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.admintherapy_proxy.adminResetTherapy()

    def start_session(self):
        patient = self.selected_patient_incombo
        self.list_therapies_todo = []

        for index in xrange(self.ui.therapies_list.count()):
            self.list_therapies_todo.append(self.ui.therapies_list.item(index).text())

        if patient == "":
            QMessageBox().information(self.focusWidget(), 'Error',
                                      'No se han seleccionado ningún paciente',
                                      QMessageBox.Ok)
        elif len(self.list_therapies_todo) == 0:
            QMessageBox().information(self.focusWidget(), 'Error',
                                      'No se ha seleccionado ninguna terapia',
                                      QMessageBox.Ok)
        else:
            self.admintherapy_proxy.adminStartSession(patient)

    def end_session_clicked(self):

        reply = QMessageBox.question(self.focusWidget(), '',
                                     ' ¿Desea finalizar la sesión?', QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.admintherapy_proxy.adminEndSession()

    def __del__(self):
        print 'SpecificWorker destructor'

    def setParams(self, params):
        return True

    # =============== Slots methods for State Machine ===================
    # ===================================================================
    #
    # sm_admin
    #
    @QtCore.Slot()
    def sm_admin(self):
        print("Entered state admin")
        pass

    #
    # sm_app_end
    #
    @QtCore.Slot()
    def sm_appEnd(self):
        print("Entered state appEnd")
        self.admintherapy_proxy.adminStopApp()
        qApp.quit()
        pass

    #
    # sm_user_login
    #
    @QtCore.Slot()
    def sm_userLogin(self):
        print("Entered state userLogin")

        self.ui.stackedWidget.setCurrentIndex(0)
        completer = QCompleter(list_of_users)
        self.ui.username_lineedit.setCompleter(completer)
        self.login_executed.connect(self.update_login_status)

    #
    # sm_create_user
    #
    @QtCore.Slot()
    def sm_createUser(self):
        print("Entered state createUser")
        self.ui.stackedWidget.setCurrentIndex(1)

    #
    # sm_create_patient
    #
    @QtCore.Slot()
    def sm_createPatient(self):
        print("Entered state createPatient")
        self.ui.stackedWidget.setCurrentIndex(3)
        self.ui.name_player_lineedit.clear()
        self.ui.surname1_player_lineedit.clear()
        self.ui.surname2_player_lineedit.clear()
        self.ui.age_player_lineedit.clear()

        #
        # sm_consultPatient
        #
        @QtCore.Slot()
        def sm_consultPatient(self):
            print("Entered state consultPatient")
            pass

    # sm_game_end
    #
    @QtCore.Slot()
    def sm_endTherapy(self):
        print("Entered state endTherapy")

        reply = QMessageBox.question(self.focusWidget(), 'Juego terminado',
                                     ' ¿Desea guardar los datos del juego?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.aux_savedGames = True
            timeplayed = self.aux_currentDate - self.currentGame.date
            self.currentGame.timePlayed = timeplayed.total_seconds() * 1000
            print "Time played =  ", self.currentGame.timePlayed, "milliseconds"

            # self.currentSession.games.append(self.currentGame)

        self.aux_datePaused = None
        self.aux_wonGame = False
        self.aux_firstMetricReceived = True

        # self.currentGame = Game()
        # self.game_metrics = []

        self.t_endTherapy_to_adminTherapies.emit()

    #
    # sm_paused
    #
    @QtCore.Slot()
    def sm_pausedTherapy(self):
        print("Entered state pausedTherapy")
        self.ui.continue_game_button.setEnabled(True)
        self.ui.reset_game_button.setEnabled(True)
        self.ui.pause_game_button.setEnabled(False)

        self.aux_datePaused = self.aux_currentDate

    #
    # sm_playing
    #
    @QtCore.Slot()
    def sm_performingTherapy(self):
        print("Entered state performingTherapy")
        self.ui.start_game_button.setEnabled(False)
        self.ui.pause_game_button.setEnabled(True)
        self.ui.finish_game_button.setEnabled(True)
        self.ui.reset_game_button.setEnabled(False)
        self.ui.reset_game_button.setToolTip("Debe pausar la terapia para poder reiniciarla")
        self.ui.end_session_button.setEnabled(False)  # No se puede finalizar la sesion si hay un juego en marcha
        self.ui.end_session_button.setToolTip("Debe finalizar la terapia para poder terminar la sesión")

        if self.currentGame.date is None:
            self.currentGame.date = self.aux_currentDate

        if self.aux_datePaused is not None:
            self.ui.continue_game_button.setEnabled(False)
            self.ui.pause_game_button.setEnabled(True)
            time = self.aux_currentDate - self.aux_datePaused
            self.currentGame.timePaused += time.total_seconds() * 1000
            self.aux_datePaused = None
            print "Time paused =  ", self.currentGame.timePaused, "milliseconds"

    #
    # sm_session_init
    #
    @QtCore.Slot()
    def sm_adminSessions(self):
        print("Entered state adminSessions")
        # self.currentSession = Session()
        self.ui.stackedWidget.setCurrentIndex(2)

        self.ui.selpatient_combobox.setCurrentIndex(0)
        self.ui.selTh_combobox.setCurrentIndex(0)

        if self.aux_sessionInit == False:
            self.bbdd = BBDD()
            self.bbdd.open_database("/home/robocomp/robocomp/components/euroage-tv/components/bbdd/prueba.db")

            patients = self.bbdd.get_all_patients()
            patients_list = []
            for p in patients:
                patients_list.append(p.name + " " + p.surname)

            completer2 = QCompleter(patients_list)

            self.ui.selpatient_combobox.addItems(patients_list)
            self.ui.selpatient_combobox.lineEdit().setCompleter(completer2)
            self.ui.selpatient_combobox.lineEdit().setPlaceholderText("Selecciona paciente...")

            completer3 = QCompleter(list_of_therapies)

            self.ui.selTh_combobox.addItems(list_of_therapies)
            self.ui.selTh_combobox.lineEdit().setCompleter(completer3)
            self.ui.selTh_combobox.lineEdit().setPlaceholderText("Selecciona terapia...")

            self.aux_sessionInit = True
        self.ui.therapies_list.clear()

        self.mainMenu.setEnabled(True)
        self.aux_savedGames = False

    #
    # sm_admin_games
    #
    @QtCore.Slot()
    def sm_adminTherapies(self):
        print("Entered state adminTherapies")

        if self.aux_firtsGameInSession or self.aux_reseted:

            game = self.list_therapies_todo[0]

            self.ui.info_game_label.setText(game)

            self.aux_firtsGameInSession = False
            self.aux_reseted = False

        else:
            self.list_therapies_todo.pop(0)

            if len(self.list_therapies_todo) == 0:
                print("No quedan juegos")
                self.admintherapy_proxy.adminEndSession()

            else:
                game = self.list_therapies_todo[0]
                self.ui.info_game_label.setText(game)

        self.ui.pause_game_button.setEnabled(False)
        self.ui.continue_game_button.setEnabled(False)
        self.ui.finish_game_button.setEnabled(False)
        self.ui.reset_game_button.setEnabled(False)

    #
    # sm_wait_play
    #
    @QtCore.Slot()
    def sm_waitingStart(self):
        print("Entered state waitingStart")
        self.ui.start_game_button.setEnabled(True)
        self.ui.end_session_button.setEnabled(True)

        self.ui.status_label.setText(self.aux_currentStatus)
        self.ui.num_screentouched_label.setText("-")
        self.ui.num_closedhand_label.setText("-")
        self.ui.timeplayed_label.setText("-")
        self.ui.num_helps_label.setText("-")
        self.ui.num_checks_label.setText("-")
        self.ui.distance_label.setText("-")
        self.ui.num_hits_label.setText("-")
        self.ui.num_fails_label.setText("-")
        self.ui.date_label.setText("-")

    #
    # sm_wait_ready
    #
    @QtCore.Slot()
    def sm_waitTherapyReady(self):
        print("Entered state waitTherapyReady")
        self.ui.stackedWidget.setCurrentIndex(4)

        self.ui.start_game_button.setEnabled(False)
        self.ui.pause_game_button.setEnabled(False)
        self.ui.continue_game_button.setEnabled(False)
        self.ui.finish_game_button.setEnabled(False)
        self.ui.reset_game_button.setEnabled(False)
        self.ui.end_session_button.setEnabled(False)

        self.aux_firtsGameInSession = True

        QMessageBox().information(self.focusWidget(), 'Info',
                                  'Asegurese que el paciente está dentro del rango de visión de la cámara',
                                  QMessageBox.Ok)

        # self.currentSession.date = self.aux_currentDate

    #
    # sm_session_end
    #
    @QtCore.Slot()
    def sm_endSession(self):
        print("Entered state endSession")

        if (self.aux_savedGames):
            reply = QMessageBox.question(self.focusWidget(), 'Juegos finalizados',
                                         ' Desea guardar los datos de la sesion actual?', QMessageBox.Yes,
                                         QMessageBox.No)
            if reply == QMessageBox.Yes:
                pass
                # time = self.aux_currentDate - self.currentSession.date
                # self.currentSession.totaltime = time.total_seconds() * 1000
                # print "Session time =  ", self.currentSession.totaltime, "milliseconds"

                # self.compute_session_metrics()
                # self.currentSession.save_session()
                # self.sessions.append(self.currentSession)

        QMessageBox().information(self.focusWidget(), 'Adios',
                                  'Se ha finalizado la sesion',
                                  QMessageBox.Ok)

        self.t_endSession_to_adminSessions.emit()

    # =================================================================
    # =================================================================

    # #
    # # metricsObtained
    # #
    # def metricsObtained(self, m):
    #     self.aux_currentDate = datetime.strptime(m.currentDate, "%Y-%m-%dT%H:%M:%S.%f")
    #     current_metrics = Metrics()
    #     current_metrics.time = self.aux_currentDate
    #
    #     if self.currentGame.date is not None:
    #         self.currentGame.timePlayed = (self.aux_currentDate - self.currentGame.date).total_seconds() * 1000
    #         current_metrics.touched = m.numScreenTouched
    #         current_metrics.handClosed = m.numHandClosed
    #         current_metrics.helps = m.numHelps
    #         current_metrics.checks = m.numChecked
    #         current_metrics.hits = m.numHits
    #         current_metrics.fails = m.numFails
    #
    #         if self.aux_firstMetricReceived:
    #             current_metrics.distance = 0
    #             self.aux_firstMetricReceived = False
    #         else:
    #             current_metrics.distance += self.compute_distance_travelled(m.pos.x, m.pos.y)
    #
    #         self.currentGame.metrics.append(current_metrics)
    #         self.aux_prevPos = m.pos
    #         self.updateUISig.emit()
    #     else:
    #         print ("NO se ha iniciado el juego")
    #
    # #
    # # statusChanged
    # #
    # def statusChanged(self, s):
    #     state_name = str(s.currentStatus.name)
    #     self.aux_currentStatus = state_name
    #     self.aux_currentDate = datetime.strptime(s.date, "%Y-%m-%dT%H:%M:%S.%f")
    #
    #     self.updateUISig.emit()
    #
    #     if state_name == "initializingSession":
    #         self.t_session_init_to_wait_ready.emit()
    #
    #     if state_name == "readySession":
    #         self.t_wait_ready_to_admin_games.emit()
    #
    #     if state_name == "waitingGame":
    #         self.t_admin_games_to_wait_play.emit()
    #
    #     if state_name == "playingGame":
    #         self.t_wait_play_to_playing.emit()
    #         self.t_paused_to_playing.emit()
    #
    #     if state_name == "pausedGame":
    #         self.t_playing_to_paused.emit()
    #
    #     if state_name == "wonGame":
    #         self.aux_wonGame = True
    #         self.t_playing_to_game_end.emit()
    #         self.t_paused_to_game_end.emit()
    #
    #     if state_name == "lostGame":
    #         self.aux_wonGame = False
    #         self.t_playing_to_game_end.emit()
    #         self.t_paused_to_game_end.emit()
    #
    #     if state_name == "resetedGame":
    #         self.aux_reseted = True
    #         self.t_paused_to_admin_games.emit()
    #
    #     if state_name == "endSession":
    #         self.t_admin_games_to_session_end.emit()
    #         self.t_wait_play_to_session_end.emit()
    #
    # def compute_distance_travelled(self, x, y):
    #     prev_x = self.aux_prevPos.x
    #     prev_y = self.aux_prevPos.y
    #     return math.sqrt(((x - prev_x) ** 2) + ((y - prev_y) ** 2))
    #
    # def compute_session_metrics(self):
    #     for game in self.currentSession.games:
    #
    #         if game.gameWon:
    #             self.currentSession.wonGames += 1
    #         else:
    #             self.currentSession.lostGames += 1
    #
    #         self.currentSession.totalHelps += game.metrics[-1].helps
    #         self.currentSession.totalChecks += game.metrics[-1].checks
    #
    # def updateUI(self):
    #     if self.currentGame.date is not None:
    #         self.ui.date_label.setText(self.currentGame.date.strftime("%c"))
    #
    #         self.ui.status_label.setText(self.aux_currentStatus)
    #         self.ui.num_screentouched_label.setText(str(self.currentGame.metrics[-1].touched))
    #         self.ui.num_closedhand_label.setText(str(self.currentGame.metrics[-1].handClosed))
    #         self.ui.num_helps_label.setText(str(self.currentGame.metrics[-1].helps))
    #         self.ui.num_checks_label.setText(str(self.currentGame.metrics[-1].checks))
    #         self.ui.timeplayed_label.setText(str("{:.3f}".format(self.currentGame.timePlayed / 1000)) + " s")
    #         self.ui.distance_label.setText(str("{:.3f}".format(self.currentGame.metrics[-1].distance)) + " mm")
    #         self.ui.num_hits_label.setText(str(self.currentGame.metrics[-1].hits))
    #         self.ui.num_fails_label.setText(str(self.currentGame.metrics[-1].fails))
