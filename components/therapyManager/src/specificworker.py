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
from Queue import Queue, Empty

import cv2
import numpy as np

from PySide2.QtGui import QKeySequence
from passlib.hash import pbkdf2_sha256
from pprint import pprint

import passwordmeter
from PySide2.QtCore import Signal, QObject, Qt, QTimer
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
        self.aux_firstTherapyInSession = True
        self.aux_reseted = False
        self.aux_firstMetricReceived = True
        self.aux_savedGames = False



        self.selected_patient_incombo = ""
        self.selected_game_inlist = ""
        self.list_therapies_todo = []

        self.__readySessionReceived = False
        self.__waitingTherapyReceived = False
        self.updateUISig.connect(self.updateUI)

        ##For saving sessions
        self.aux_current_joints = None
        self.data_to_record = None
        self.received_data_queue = Queue()
        self.video_writer = None

        self.aux_therapy_name = None
        self.aux_patient_name = None
        self.aux_session_dir = None
        self.aux_therapy_dir = None
        self.aux_video_dir = None
        self.aux_joints_dir = None
        self.aux_metrics_dir = None

        self.aux_saving_dir = "/home/robolab/robocomp/components/robotherapy/components/therapyManager/savedSessions"
        if not os.path.isdir(self.aux_saving_dir):
            os.mkdir(self.aux_saving_dir)

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
        self.skiploginShortcut = QShortcut(QKeySequence(Qt.Key_Tab), self)
        self.loginShortcut.activated.connect(self.check_login)
        self.skiploginShortcut.activated.connect(self.t_userLogin_to_adminSessions)

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
        selected_game_incombo = self.ui.selTh_combobox.currentText()
        if selected_game_incombo != "":
            self.ui.therapies_list.addItem(selected_game_incombo)
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

        if current_index == 0:
            return
        new_index = current_index - 1
        previous_text = self.ui.therapies_list.item(new_index).text()

        print self.ui.therapies_list.item(new_index).text()

        self.ui.therapies_list.item(current_index).setText(previous_text)
        self.ui.therapies_list.item(new_index).setText(current_text)
        self.ui.therapies_list.setCurrentRow(new_index)

    def movelist_down(self):
        current_text = self.ui.therapies_list.currentItem().text()
        current_index = self.ui.therapies_list.currentRow()

        if current_index == self.ui.therapies_list.count() - 1:
            return
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
        self.admintherapy_proxy.adminStartTherapy(self.list_therapies_todo[0])

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
        self.aux_patient_name = self.selected_patient_incombo
        self.list_therapies_todo = []

        for index in xrange(self.ui.therapies_list.count()):
            self.list_therapies_todo.append(self.ui.therapies_list.item(index).text())

        if self.aux_patient_name == "":
            QMessageBox().information(self.focusWidget(), 'Error',
                                      'No se han seleccionado ningún paciente',
                                      QMessageBox.Ok)
        elif len(self.list_therapies_todo) == 0:
            QMessageBox().information(self.focusWidget(), 'Error',
                                      'No se ha seleccionado ninguna terapia',
                                      QMessageBox.Ok)
        else:

            patient_dir = os.path.join(self.aux_saving_dir, self.aux_patient_name)

            if not os.path.isdir(patient_dir):
                os.mkdir(patient_dir)

            currentDate = datetime.now()
            date = datetime.strftime(currentDate, "%m%d%H%M")
            self.aux_session_dir = os.path.join(patient_dir, "session_" + date)

            if not os.path.isdir(self.aux_session_dir):
                os.mkdir(self.aux_session_dir)

            self.admintherapy_proxy.adminStartSession(self.aux_patient_name)

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

        reply = QMessageBox.question(self.focusWidget(), 'Terapia terminado',
                                     ' ¿Desea guardar los datos de la terapia?', QMessageBox.Yes, QMessageBox.No)
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
    # sm_performingTherapy
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

        # if self.currentGame.date is None:
        #     self.currentGame.date = self.aux_currentDate

        if self.aux_datePaused is not None:
            self.ui.continue_game_button.setEnabled(False)
            self.ui.pause_game_button.setEnabled(True)
            time = self.aux_currentDate - self.aux_datePaused
            self.currentGame.timePaused += time.total_seconds() * 1000
            self.aux_datePaused = None
            print "Time paused =  ", self.currentGame.timePaused, "milliseconds"


    #
    # sm_waitingFrame
    #
    @QtCore.Slot()
    def sm_waitingFrame(self):
        print("Entered state waitingFrame")
        self.data_to_record = None
        self.aux_current_joints = None

        try:
            self.data_to_record = self.received_data_queue.get_nowait()
        except Empty:
            QTimer.singleShot(1000 / 33, self.t_waitingFrame_to_waitingFrame)

        else:
            self.t_waitingFrame_to_savingFrame.emit()

    #
    # sm_savingFrame
    #
    @QtCore.Slot()
    def sm_savingFrame(self):
        print("Entered state savingFrame")

        # Video
        if self.data_to_record.rgbImage.height == 0 or self.data_to_record.rgbImage.width == 0:
            QTimer.singleShot(1000 / 33, self.t_captureFrame_to_captureFrame)

        frame = np.frombuffer(self.data_to_record.rgbImage.image, np.uint8).reshape(
            self.data_to_record.rgbImage.height, self.data_to_record.rgbImage.width,
            self.data_to_record.rgbImage.depth)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if self.video_writer is None:
            (height, width) = frame.shape[:2]
            self.video_writer = cv2.VideoWriter(self.aux_video_dir, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 30,
                                                (width, height))
        self.video_writer.write(frame)

        # Joints
        joint_file = open(self.aux_joints_dir, 'a+')
        joint_file.write(str(self.data_to_record.timeStamp))
        joint_file.write("#")

        if len(self.data_to_record.persons) > 0:
            for id, person in self.data_to_record.persons.items():

                joint_file.write(str(id))
                joint_file.write("#")

                self.aux_current_joints = person.joints

                for id_joint, j in person.joints.items():
                    joint_file.writelines([str(id_joint), " ", str(j[0]), " ", str(j[1]), " ", str(j[2]), "#"])

        else:
            self.ui.info_label.setText("No humans detected")

        joint_file.write("\n")
        joint_file.close()

        # Metrics
        if not os.path.isfile(self.aux_metrics_dir):
            with open(self.aux_metrics_dir, 'w') as csvFile:
                writer = csv.writer(csvFile, delimiter=';')
                writer.writerow(
                    ["Time", "LeftArmFlexion", "RightArmFlexion", "HipDeviation", "KneeDeviation",
                     "ShoulderDeviation", "LeftArmElevation", "RightArmElevation", "SpineDeviation", "LeftLegFlexion",
                     "RightLegFlexion", "LeftLegElevation", "RightLegElevation"])
            csvFile.close()

        with open(self.aux_metrics_dir, 'a') as csvFile:
            writer = csv.writer(csvFile, delimiter=';')
            writer.writerow(
                [self.data_to_record.metricsObtained["Time"], self.data_to_record.metricsObtained["LeftArmFlexion"],
                 self.data_to_record.metricsObtained["RightArmFlexion"], self.data_to_record.metricsObtained["HipDeviation"],
                 self.data_to_record.metricsObtained["KneeDeviation"], self.data_to_record.metricsObtained["ShoulderDeviation"],
                 self.data_to_record.metricsObtained["LeftArmElevation"], self.data_to_record.metricsObtained["RightArmElevation"],
                 self.data_to_record.metricsObtained["SpineDeviation"], self.data_to_record.metricsObtained["LeftLegFlexion"],
                 self.data_to_record.metricsObtained["RightLegFlexion"], self.data_to_record.metricsObtained["LeftLegElevation"],
                 self.data_to_record.metricsObtained["RightLegElevation"]])

            csvFile.close()


        self.t_savingFrame_to_waitingFrame.emit()

    #
    # sm_showingResults
    #
    @QtCore.Slot()
    def sm_showingResults(self):
        print("Entered state showingResults")
        pass

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

        if not self.aux_sessionInit:
            self.bbdd = BBDD()
            self.bbdd.open_database("/home/robocomp/robocomp/components/euroage-tv/components/bbdd/prueba1.db")

            patients = self.bbdd.get_all_patients()
            patients_list = []
            for p in patients:
                patients_list.append(p.username)

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

        if self.aux_firstTherapyInSession or self.aux_reseted:
            therapy = self.list_therapies_todo[0]
            self.aux_therapy_name = therapy
            self.ui.info_game_label.setText(therapy)

            self.aux_firstTherapyInSession = False
            self.aux_reseted = False

        else:
            self.list_therapies_todo.pop(0)

            if len(self.list_therapies_todo) == 0:
                print("No quedan terapias")
                self.admintherapy_proxy.adminEndSession()

            else:
                therapy = self.list_therapies_todo[0]
                self.aux_therapy_name = therapy
                self.ui.info_game_label.setText(therapy)

        self.ui.pause_game_button.setEnabled(False)
        self.ui.continue_game_button.setEnabled(False)
        self.ui.finish_game_button.setEnabled(False)
        self.ui.reset_game_button.setEnabled(False)

        # TODO: FIX
        if self.__waitingTherapyReceived:
            print ("waitingTherapy already received")
            self.t_adminTherapies_to_waitingStart.emit()
            self.__waitingTherapyReceived = False

    #
    # sm_wait_play
    #
    @QtCore.Slot()
    def sm_waitingStart(self):
        print("Entered state waitingStart")
        self.ui.start_game_button.setEnabled(True)
        self.ui.end_session_button.setEnabled(True)
        self.ui.status_label.setText(self.aux_currentStatus)
        self.ui.date_label.setText("-")

        therapy = self.aux_therapy_name.replace(" ", "").strip()
        self.aux_therapy_dir = os.path.join(self.aux_session_dir, therapy)

        if not os.path.isdir(self.aux_therapy_dir):
            print ("[CREATING] " + self.aux_therapy_dir)
            os.mkdir(self.aux_therapy_dir)

        video_name = therapy.lower() + ".avi"
        joints_name = therapy.lower() + ".txt"
        metrics_name = therapy.lower() + ".csv"

        self.aux_video_dir = os.path.join(self.aux_therapy_dir, video_name)
        self.aux_joints_dir = os.path.join(self.aux_therapy_dir, joints_name)
        self.aux_metrics_dir = os.path.join(self.aux_therapy_dir, metrics_name)

    #
    # sm_wait_ready
    #
    @QtCore.Slot()
    def sm_waitSessionReady(self):
        print("Entered state waitSessionReady")
        self.ui.stackedWidget.setCurrentIndex(4)

        self.ui.start_game_button.setEnabled(False)
        self.ui.pause_game_button.setEnabled(False)
        self.ui.continue_game_button.setEnabled(False)
        self.ui.finish_game_button.setEnabled(False)
        self.ui.reset_game_button.setEnabled(False)
        self.ui.end_session_button.setEnabled(False)

        self.aux_firstTherapyInSession = True

        QMessageBox().information(self.focusWidget(), 'Info',
                                  'Asegurese que el paciente está dentro del rango de visión de la cámara',
                                  QMessageBox.Ok)

        # TODO: FIX
        if self.__readySessionReceived:
            print ("readySession already received")
            self.t_waitSessionReady_to_adminTherapies.emit()
            self.__readySessionReceived = False
        # self.currentSession.date = self.aux_currentDate

    #
    # sm_session_end
    #
    @QtCore.Slot()
    def sm_endSession(self):
        print("Entered state endSession")

        if self.aux_savedGames:
            reply = QMessageBox.question(self.focusWidget(), 'Terapias finalizados',
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

    #
    # newDataObtained
    #
    def newDataObtained(self, data):
        print("New Data received")

        if data.rgbImage.height == 0 or data.rgbImage.width == 0:
            return
        else:
            self.received_data_queue.put(data)

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
    #
    # statusChanged
    def statusChanged(self, s):
        self.aux_currentStatus = str(s.currentStatus.name)
        print "ESTADO ", self.aux_currentStatus
        self.aux_currentDate = datetime.strptime(s.date, "%Y-%m-%dT%H:%M:%S.%f")

        self.updateUISig.emit()

        if s.currentStatus == StatusType.initializingSession:
            self.t_adminSessions_to_waitSessionReady.emit()

        if s.currentStatus == StatusType.readySession:
            self.__readySessionReceived = True
            self.t_waitSessionReady_to_adminTherapies.emit()

        if s.currentStatus == StatusType.waitingTherapy:
            self.__waitingTherapyReceived = True
            self.t_adminTherapies_to_waitingStart.emit()

        if s.currentStatus == StatusType.playingTherapy:
            self.t_waitingStart_to_performingTherapy.emit()
            self.t_pausedTherapy_to_performingTherapy.emit()

        if s.currentStatus == StatusType.pausedTherapy:
            self.t_performingTherapy_to_pausedTherapy.emit()

        if s.currentStatus == StatusType.endTherapy:
            self.t_performingTherapy_to_endTherapy.emit()
            self.t_pausedTherapy_to_endTherapy.emit()

        if s.currentStatus == StatusType.resetedTherapy:
            self.aux_reseted = True
            self.t_pausedTherapy_to_adminTherapies.emit()

        if s.currentStatus == StatusType.endSession:
            self.t_adminTherapies_to_endSession.emit()
            self.t_waitingStart_to_endSession.emit()

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
    def updateUI(self):
        self.ui.date_label.setText(self.aux_currentDate.strftime("%c"))
        self.ui.status_label.setText(self.aux_currentStatus)

        # if self.currentGame.date is not None:
    #         self.ui.num_screentouched_label.setText(str(self.currentGame.metrics[-1].touched))
    #         self.ui.num_closedhand_label.setText(str(self.currentGame.metrics[-1].handClosed))
    #         self.ui.num_helps_label.setText(str(self.currentGame.metrics[-1].helps))
    #         self.ui.num_checks_label.setText(str(self.currentGame.metrics[-1].checks))
    #         self.ui.timeplayed_label.setText(str("{:.3f}".format(self.currentGame.timePlayed / 1000)) + " s")
    #         self.ui.distance_label.setText(str("{:.3f}".format(self.currentGame.metrics[-1].distance)) + " mm")
    #         self.ui.num_hits_label.setText(str(self.currentGame.metrics[-1].hits))
    #         self.ui.num_fails_label.setText(str(self.currentGame.metrics[-1].fails))
