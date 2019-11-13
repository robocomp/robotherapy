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
from Queue import Queue, Empty
from datetime import datetime
from shutil import rmtree

import matplotlib
matplotlib.use('Qt5Agg')

import cv2
import numpy as np

from PySide2.QtGui import QKeySequence, QImage, QPixmap

import passwordmeter
from PySide2.QtCore import Signal, Qt, QTimer
from PySide2.QtWidgets import QMessageBox, QCompleter, QAction, qApp, QShortcut

from admin_widgets import *
from genericworker import *

from userManager import QUserManager
from canvas import DynamicCanvas

import plot_therapy as PTH

try:
    from bbdd import BBDD
except:
    print ("Database module not found")
    sys.path.append("/home/robolab/robocomp/components/robotherapy/components/bbdd")
    from bbdd import BBDD

FILE_PATH = os.path.abspath(__file__)
CURRENT_PATH = os.path.dirname(__file__)


list_of_therapies = ["Levantar los brazos"]


class SpecificWorker(GenericWorker):
    login_executed = Signal(bool)
    updateUISig = Signal()

    def __init__(self, proxy_map):
        super(SpecificWorker, self).__init__(proxy_map)

        self.Period = 2000
        self.timer.start(self.Period)

        self.bbdd = BBDD()
        self.bbdd.open_database("/home/robolab/robocomp/components/robotherapy/components/bbdd/prueba_therapy.db")
        self.user_login_manager = QUserManager(ddbb=self.bbdd)

        self.list_of_users = self.user_login_manager.load_therapists()

        self.init_ui()
        self.setCentralWidget(self.ui)

        self.__current_therapist = None
        self.current_session = None


        self.aux_sessionInit = False
        self.aux_datePaused = None
        self.aux_currentDate = None
        self.aux_currentStatus = None
        self.aux_firstTherapyInSession = True
        self.aux_reseted = False
        self.aux_savedGames = False

        self.list_therapies_todo = []

        self.__readySessionReceived = False
        self.__waitingTherapyReceived = False
        self.updateUISig.connect(self.updateUI)

        ##For saving sessions
        self.aux_current_joints = None
        self.data_to_record = None
        self.received_data_queue = Queue()
        self.video_writer = None

        self.aux_session_dir = None
        self.aux_video_dir = None
        self.aux_joints_dir = None
        self.aux_metrics_dir = None

        self.aux_current_frame = None

        self.aux_saving_dir = "/home/robolab/robocomp/components/robotherapy/components/therapyManager/savedSessions"
        if not os.path.isdir(self.aux_saving_dir):
            os.mkdir(self.aux_saving_dir)

        self.aux_timePlayed = None
        self.current_metrics = None

        self.visualize_therapy = False
        self.canvas = None
        self.skip_frames = 10
        self.total_frames = 0
        self.to_represent = []

        self.manager_machine.start()

    def __del__(self):
        print 'SpecificWorker destructor'

    def setParams(self, params):
        return True

    @property
    def current_therapist(self):
        """
        Getter for the current therapis of the current session
        Current Therapist can exists without a current session while this is being created.
        :return: therapist of the current session
        """
        if self.current_session is not None:
            return self.current_session.therapist
        else:
            return self.__current_therapist

    @current_therapist.setter
    def current_therapist(self, therapist):
        """
        Setter for the current therapist of the current session
        :return: game of the current session
        """
        if self.current_session is not None:
            self.current_session.therapist = therapist
        else:
            self.__current_therapist = therapist

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
        self.ui.selpatient_combobox.currentIndexChanged.connect(self.selectedplayer_changed)
        self.ui.addTh_button.clicked.connect(self.addgametolist)
        self.ui.deleteTh_button.clicked.connect(self.deleteTherapyFromList)
        self.ui.up_button.clicked.connect(self.movelist_up)
        self.ui.down_button.clicked.connect(self.movelist_down)

        self.ui.startsession_button.clicked.connect(self.start_session)

        ##new Player window
        self.ui.back_patient_button.clicked.connect(self.t_createPatient_to_adminSessions.emit)
        self.ui.create_patient_button.clicked.connect(self.create_patient)

        # therapy window
        self.ui.start_game_button.clicked.connect(self.start_clicked)
        self.ui.pause_game_button.clicked.connect(self.pause_clicked)
        self.ui.continue_game_button.clicked.connect(self.continue_clicked)
        self.ui.finish_game_button.clicked.connect(self.finish_clicked)
        self.ui.reset_game_button.clicked.connect(self.reset_clicked)
        self.ui.end_session_button.clicked.connect(self.end_session_clicked)
        self.ui.visualize_check.stateChanged.connect(self.change_visualize_state)

        self.ui.deviations_check.stateChanged.connect(self.change_values_to_plot)
        self.ui.lower_trunk_check.stateChanged.connect(self.change_values_to_plot)
        self.ui.upper_trunk_check.stateChanged.connect(self.change_values_to_plot)

        self.ui.visualize_gbox.hide()

    # Login window functions
    def check_login(self):
        print ("[INFO] Checking login ...")

        username = unicode(self.ui.username_lineedit.text())
        password = unicode(self.ui.password_lineedit.text())

        if self.user_login_manager.check_user_password(username, password):
            self.current_therapist = username
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

        if strength < 0.6:
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
            password = unicode(self.ui.password_lineedit_reg.text())
            nombre = unicode(self.ui.name_lineedit_reg.text())
            telefono = unicode(self.ui.telefono_lineedit.text())
            centro = unicode(self.ui.centro_lineedit_reg.text())
            profesion = unicode(self.ui.profesion_lineedit.text())
            observaciones = unicode(self.ui.observaciones_plaintext.toPlainText())

            if not self.user_login_manager.set_username_password(username, password, nombre, telefono, centro,
                                                                 profesion, observaciones):
                QMessageBox().information(self.focusWidget(), 'Error',
                                          'El nombre de usuario ya existe',
                                          QMessageBox.Ok)
                return False
            else:

                QMessageBox().information(self.focusWidget(), '',
                                          'Usuario creado correctamente',
                                          QMessageBox.Ok)

                self.list_of_users = self.user_login_manager.load_therapists()  ##Reload the users

                completer = QCompleter(self.list_of_users)
                self.ui.username_lineedit.setCompleter(completer)

                self.t_createUser_to_userLogin.emit()
                return True
        else:
            print ("[ERROR] No se pudo crear el usuario ")
            return False

    # Session window
    def deleteTherapyFromList(self):
        item_to_delete = self.ui.therapies_list.currentRow()
        self.ui.therapies_list.takeItem(item_to_delete)

    def selectedplayer_changed(self):
        if self.ui.selpatient_combobox.currentIndex() == 1:  # New player selected
            reply = QMessageBox.question(self.focusWidget(), '',
                                         ' Quiere añadir a un nuevo paciente?', QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.No:
                self.ui.selpatient_combobox.setCurrentIndex(0)
                return False

            else:
                self.t_adminSessions_to_createPatient.emit()
                return True

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

        username = unicode(self.ui.username_patient_lineedit.text())
        nombre = unicode(self.ui.name_patient_lineedit.text())
        sexo = str(self.ui.sexo_combobox.currentText())
        edad = float(self.ui.age_player_lineedit.text())
        centro = unicode(self.ui.centro_lineedit.text())
        nfisico = float(self.ui.nfisico_combobox.currentText())
        ncognitivo = float(self.ui.ncognitivo_lineedit.currentText())
        observaciones = unicode(self.ui.observaciones_patient_plaintext.toPlainText())

        result, patient = self.bbdd.new_patient(username, nombre, sexo=sexo, edad=edad, datosRegistro="", nivelCognitivo=ncognitivo, nivelFisico=nfisico,
                             nivelJuego=5, centro=centro,  profesional=self.current_therapist, observaciones=observaciones, fechaAlta=datetime.strftime(datetime.now(), "%Y-%m-%d"))

        if result:
            patients = self.bbdd.get_all_patients_by_therapist(self.current_therapist)
            completer = QCompleter([patient.username for patient in patients])

            self.ui.selpatient_combobox.addItem(patient.username)
            self.ui.selpatient_combobox.setCompleter(completer)
            self.t_createPatient_to_adminSessions.emit()
        else:
            QMessageBox().information(self.focusWidget(), 'Error',
                                      'No se ha podido crear un nuevo paciente. El nombre de usuario ya existe.',
                                      QMessageBox.Ok)

    # Game window functions
    def change_visualize_state(self, state):
        print "change_visualize_state"
        if state == QtCore.Qt.Checked:
            self.visualize_therapy = True
            self.ui.visualize_gbox.show()
            self.ui.video_lb.show()
            if self.canvas is not None:
                self.canvas.show()

        else:
            self.visualize_therapy = False
            self.ui.visualize_gbox.hide()
            self.ui.video_lb.hide()
            if self.canvas is not None:
                self.canvas.hide()

    def change_values_to_plot(self):
        self.to_represent = []

        if self.ui.upper_trunk_check.isChecked():
            self.to_represent.append("upper_trunk")
        if self.ui.lower_trunk_check.isChecked():
            self.to_represent.append("lower_trunk")
        if self.ui.deviations_check.isChecked():
            self.to_represent.append("deviations")

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
        patient = self.ui.selpatient_combobox.currentText()
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

            patient_dir = os.path.join(self.aux_saving_dir, patient)

            if not os.path.isdir(patient_dir):
                os.mkdir(patient_dir)

            currentDate = datetime.now()
            date = datetime.strftime(currentDate, "%m%d%H%M")
            self.aux_session_dir = os.path.join(patient_dir, "session_" + date)

            if not os.path.isdir(self.aux_session_dir):
                os.mkdir(self.aux_session_dir)

            self.admintherapy_proxy.adminStartSession(patient)

    def end_session_clicked(self):

        reply = QMessageBox.question(self.focusWidget(), '',
                                     ' ¿Desea finalizar la sesión?', QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.admintherapy_proxy.adminEndSession()

    def updateUI(self):
        self.ui.date_label.setText(self.aux_currentDate.strftime("%c"))
        self.ui.status_label.setText(self.aux_currentStatus)
        if self.aux_timePlayed is not None:
            self.ui.timeplayed_label.setText(str("{:.3f}".format(self.aux_timePlayed)) + " s")

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
        completer = QCompleter(self.list_of_users)
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
        self.ui.username_patient_lineedit.clear()
        self.ui.name_patient_lineedit.clear()
        self.ui.sexo_combobox.setCurrentIndex(0)
        self.ui.nfisico_combobox.setCurrentIndex(0)
        self.ui.ncognitivo_lineedit.setCurrentIndex(0)
        self.ui.age_player_lineedit.clear()
        self.ui.centro_lineedit.clear()
        self.ui.observaciones_patient_plaintext.clear()

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

        reply = QMessageBox.question(self.focusWidget(), 'Terapia terminada',
                                     ' ¿Desea guardar los datos de la terapia?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # self.aux_savedGames = True
            # timeplayed = self.aux_currentDate - self.currentGame.date
            # self.currentGame.timePlayed = timeplayed.total_seconds() * 1000
            # print "Time played =  ", self.currentGame.timePlayed, "milliseconds"
            # self.currentSession.games.append(self.currentGame)

            reply2 = QMessageBox.question(self.focusWidget(), 'Terapia terminada',
                                          ' ¿Desea visualizar los datos de la terapia?', QMessageBox.Yes,
                                          QMessageBox.No)

            if reply2 == QMessageBox.Yes:
                visualization = True
            else:
                visualization = False

            PTH.save_graph(self.aux_metrics_dir, visualization)

        if self.video_writer is not None:
            self.video_writer.release()

        self.aux_datePaused = None

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
        self.aux_current_frame = frame

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
            print("No humans detected")

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
                [self.data_to_record.metricsObtained["Time"],
                 self.data_to_record.metricsObtained["LeftArmFlexion"],
                 self.data_to_record.metricsObtained["RightArmFlexion"],
                 self.data_to_record.metricsObtained["HipDeviation"],
                 self.data_to_record.metricsObtained["KneeDeviation"],
                 self.data_to_record.metricsObtained["ShoulderDeviation"],
                 self.data_to_record.metricsObtained["LeftArmElevation"],
                 self.data_to_record.metricsObtained["RightArmElevation"],
                 self.data_to_record.metricsObtained["SpineDeviation"],
                 self.data_to_record.metricsObtained["LeftLegFlexion"],
                 self.data_to_record.metricsObtained["RightLegFlexion"],
                 self.data_to_record.metricsObtained["LeftLegElevation"],
                 self.data_to_record.metricsObtained["RightLegElevation"]])

            csvFile.close()
        self.current_metrics = self.data_to_record.metricsObtained

        self.total_frames += 1

        if self.visualize_therapy:
            self.t_savingFrame_to_showingResults.emit()

        else:
            self.t_savingFrame_to_waitingFrame.emit()

    #
    # sm_showingResults
    #
    @QtCore.Slot()
    def sm_showingResults(self):
        print("Entered state showingResults")

        (height, width) = self.aux_current_frame.shape[:2]
        frame = cv2.cvtColor(self.aux_current_frame, cv2.COLOR_BGR2RGB)
        img = QImage(frame, width, height, QImage.Format_RGB888)

        self.ui.video_lb.setPixmap(QPixmap.fromImage(img).scaled(320, 240, Qt.KeepAspectRatio))

        self.aux_timePlayed = self.current_metrics["Time"]
        self.updateUISig.emit()

        if self.canvas is None:
            print ("creating canvas")
            self.canvas = DynamicCanvas(self.ui, dpi=80)
            self.canvas.setStyleSheet("background-color:transparent;")
            self.ui.result_layout.addWidget(self.canvas)

        if self.total_frames % self.skip_frames == 0:
            # data = [random.random() for i in range(10)]

            self.canvas.axes.cla()
            # self.canvas.axes.plot(data, '*-')
            PTH.plot_graph(self.aux_metrics_dir, self.to_represent, self.canvas)
            self.canvas.update_figure()

        self.t_showingResults_to_waitingFrame.emit()

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

            patients = self.bbdd.get_all_patients_by_therapist(self.current_therapist)
            patients_list = []
            for p in patients:
                patients_list.append(p.username)

            # patients_list = ["AlbertoSerrano","SergioBarroso"]
            completer2 = QCompleter(patients_list)

            self.ui.selpatient_combobox.addItems(patients_list)
            self.ui.selpatient_combobox.lineEdit().setCompleter(completer2)
            self.ui.selpatient_combobox.lineEdit().setPlaceholderText("Selecciona paciente...")

            games = self.bbdd.get_all_games()
            completer3 = QCompleter([game.name for game in games])
            self.ui.selTh_combobox.addItems([game.name for game in games])

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
                self.ui.info_game_label.setText(therapy)

        therapy = therapy.replace(" ", "").strip()
        therapy_dir = os.path.join(self.aux_session_dir, therapy)

        if os.path.isdir(therapy_dir):
            rmtree(therapy_dir)

        print ("[CREATING] " + therapy_dir)
        os.mkdir(therapy_dir)

        video_name = therapy.lower() + ".avi"
        joints_name = therapy.lower() + ".txt"
        metrics_name = therapy.lower() + ".csv"

        self.aux_video_dir = os.path.join(therapy_dir, video_name)
        self.aux_joints_dir = os.path.join(therapy_dir, joints_name)
        self.aux_metrics_dir = os.path.join(therapy_dir, metrics_name)

        self.video_writer = None

        # Reset results
        if self.canvas is not None:
            self.ui.result_layout.removeWidget(self.canvas)
            self.canvas = None

        img = QImage()
        self.ui.video_lb.setPixmap(QPixmap.fromImage(img).scaled(320, 240, Qt.KeepAspectRatio))

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
        self.ui.visualize_check.setCheckState(QtCore.Qt.Unchecked)
        self.ui.upper_trunk_check.setCheckState(QtCore.Qt.Unchecked)
        self.ui.lower_trunk_check.setCheckState(QtCore.Qt.Unchecked)
        self.ui.deviations_check.setCheckState(QtCore.Qt.Unchecked)

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
        self.ui.date_label.setText("-")
        self.ui.timeplayed_label.setText("-")

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
        if data.rgbImage.height == 0 or data.rgbImage.width == 0:
            return
        else:
            self.received_data_queue.put(data)

        self.aux_timePlayed = data.metricsObtained["Time"]
        self.updateUISig.emit()

    #
    # statusChanged
    #
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
