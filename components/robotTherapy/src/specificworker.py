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
import copy
import csv
import shutil
from Queue import Queue, Empty
from datetime import datetime
from pprint import pprint

import cv2
import numpy as np
import vg
from PySide2.QtCore import QTimer, QUrl
from PySide2.QtMultimedia import QMediaPlayer
from PySide2.QtMultimediaWidgets import QVideoWidget
from PySide2.QtWidgets import QMessageBox

import plot_therapy as PTH
from genericworker import *


def get_AngleBetweenVectors(v1, v2):
    return vg.angle(v1, v2)


class SpecificWorker(GenericWorker):
    def __init__(self, proxy_map):
        super(SpecificWorker, self).__init__(proxy_map)

        self.recording = False
        self.Period = 2000
        self.timer.start(self.Period)

        self.player = QMediaPlayer()
        self.videoWidget = QVideoWidget()

        self.received_data_queue = Queue()
        self.data_to_record = None
        self.video_writer = None

        # self.aux_saving_dir = "/home/robolab/robocomp/components/robotherapy/components/robotTherapy/savedSessions"
        # if not os.path.isdir(self.aux_saving_dir):
        #     os.mkdir(self.aux_saving_dir)

        self.aux_therapy_name = None
        self.aux_patient_name = None
        self.aux_session_dir = None
        self.aux_therapy_dir = None
        self.aux_video_dir = None
        self.aux_joints_dir = None
        self.aux_metrics_dir = None
        self.aux_current_joints = None

        self.aux_firstTime_metric = None
        self.aux_firstMetric = True

        self.mix_data_to_send = MixedData()

        self.current_metrics = {}

        self.robotTherapyMachine.start()

    def __del__(self):
        print 'SpecificWorker destructor'

    def setParams(self, params):
        return True

    def video_state_changed(self, state):
        if state == QMediaPlayer.State.StoppedState:
            self.t_loopTherapy_to_finalizeTherapy.emit()

    def reset_metrics(self):
        self.current_metrics["Time"] = np.nan
        self.current_metrics["LeftArmFlexion"] = np.nan
        self.current_metrics["RightArmFlexion"] = np.nan
        self.current_metrics["LeftArmElevation"] = np.nan
        self.current_metrics["RightArmElevation"] = np.nan

        self.current_metrics["LeftLegFlexion"] = np.nan
        self.current_metrics["RightLegFlexion"] = np.nan
        self.current_metrics["LeftLegElevation"] = np.nan
        self.current_metrics["RightLegElevation"] = np.nan

        self.current_metrics["SpineDeviation"] = np.nan
        self.current_metrics["ShoulderDeviation"] = np.nan
        self.current_metrics["HipDeviation"] = np.nan
        self.current_metrics["KneeDeviation"] = np.nan

    def check_necessary_joints(self, list_joints):
        for jnt in list_joints:
            if jnt not in self.aux_current_joints:
                return False
        return True

    # Pierna o brazo sin flexionar --> 0º
    def get_armFlexion(self, side):
        necessary_joints = [side + "Elbow", side + "Shoulder", side + "Hand"]
        if not self.check_necessary_joints(necessary_joints):
            return

        elbow = np.array(self.aux_current_joints[side + "Elbow"])
        shoulder = np.array(self.aux_current_joints[side + "Shoulder"])
        hand = np.array(self.aux_current_joints[side + "Hand"])

        v1 = elbow - hand
        v2 = shoulder - elbow
        self.current_metrics[side + "ArmFlexion"] = round(get_AngleBetweenVectors(v1, v2), 4)

    def get_legFlexion(self, side):
        necessary_joints = [side + "Knee", side + "Hip", side + "Foot"]
        if not self.check_necessary_joints(necessary_joints):
            return

        knee = np.array(self.aux_current_joints[side + "Knee"])
        hip = np.array(self.aux_current_joints[side + "Hip"])
        foot = np.array(self.aux_current_joints[side + "Foot"])

        v1 = knee - foot
        v2 = hip - knee
        self.current_metrics[side + "LegFlexion"] = round(get_AngleBetweenVectors(v1, v2), 4)

    def get_armElevation(self, side):
        necessary_joints = [side + "Elbow", side + "Shoulder"]
        if not self.check_necessary_joints(necessary_joints):
            return

        elbow = np.array(self.aux_current_joints[side + "Elbow"])
        shoulder = np.array(self.aux_current_joints[side + "Shoulder"])
        # vertical = np.array([shoulder[0], 0, shoulder[2]])
        vertical = np.array([shoulder[0], elbow[1], shoulder[2]])

        v1 = shoulder - elbow
        v2 = shoulder - vertical

        self.current_metrics[side + "ArmElevation"] = round(get_AngleBetweenVectors(v1, v2), 4)

    def get_legElevation(self, side):

        necessary_joints = [side + "Knee", side + "Hip"]
        if not self.check_necessary_joints(necessary_joints):
            return

        knee = np.array(self.aux_current_joints[side + "Knee"])
        hip = np.array(self.aux_current_joints[side + "Hip"])
        # vertical = np.array([hip[0], 0, hip[2]])
        vertical = np.array([hip[0], knee[1], hip[2]])

        v1 = hip - knee
        v2 = hip - vertical

        self.current_metrics[side + "LegElevation"] = round(get_AngleBetweenVectors(v1, v2), 4)

    def get_deviationAngle(self, part):
        if part == "Spine":
            necessary_joints = ["BaseSpine", "ShoulderSpine"]
            if not self.check_necessary_joints(necessary_joints):
                return

            base = np.array(self.aux_current_joints["BaseSpine"])
            upper = np.array(self.aux_current_joints["ShoulderSpine"])
            vertical = np.array([upper[0], 0, upper[2]])

            v1 = upper - base
            if upper[1] < 0:
                v2 = vertical - upper
            else:
                v2 = upper - vertical

            self.current_metrics[part + "Deviation"] = round(get_AngleBetweenVectors(v1, v2), 4)

        else:
            necessary_joints = ["Left" + part, "Right" + part]
            if not self.check_necessary_joints(necessary_joints):
                return

            left = np.array(self.aux_current_joints["Left" + part])
            right = np.array(self.aux_current_joints["Right" + part])
            horizontal = np.array([right[0], left[1], right[2]])

            v1 = left - right
            v2 = left - horizontal

            self.current_metrics[part + "Deviation"] = round(get_AngleBetweenVectors(v1, v2), 4)

    # =============== Slots methods for State Machine ===================
    # ===================================================================
    #
    # sm_initialize
    #
    @QtCore.Slot()
    def sm_initialize(self):
        print("Entered state initialize")
        self.ui.video_layout.addWidget(self.videoWidget)
        self.player.setVideoOutput(self.videoWidget)

        self.ui.start_button.clicked.connect(self.t_initializingTherapy_to_loopTherapy)
        self.ui.start_button.clicked.connect(self.t_pauseTherapy_to_loopTherapy)
        self.ui.stop_button.clicked.connect(self.t_loopTherapy_to_finalizeTherapy)
        self.ui.stop_button.clicked.connect(self.t_pauseTherapy_to_finalizeTherapy)
        self.ui.reset_button.clicked.connect(self.t_loopTherapy_to_resetTherapy)
        self.ui.reset_button.clicked.connect(self.t_pauseTherapy_to_resetTherapy)
        self.ui.pause_button.clicked.connect(self.t_loopTherapy_to_pauseTherapy)

        self.player.stateChanged.connect(self.video_state_changed)

        self.t_initialize_to_waitSession.emit()

    #
    # sm_waitSession
    #
    @QtCore.Slot()
    def sm_waitSession(self):
        print("Entered state waitSession")
        self.send_status_change(StatusType.waitingSession)

    #
    # sm_initializingSession
    #
    @QtCore.Slot()
    def sm_initializingSession(self):
        print("Entered state initializingSession")
        self.send_status_change(StatusType.initializingSession)

        # TODO sustituir el guardar a fichero --> guardara el manager en la bbdd
        # patient_dir = os.path.join(self.aux_saving_dir, self.aux_patient_name)
        #
        # if not os.path.isdir(patient_dir):
        #     os.mkdir(patient_dir)
        #
        # currentDate = datetime.now()
        # date = datetime.strftime(currentDate, "%m%d%H%M")
        # self.aux_session_dir = os.path.join(patient_dir, "session_" + date)
        #
        # if not os.path.isdir(self.aux_session_dir):
        #     os.mkdir(self.aux_session_dir)

        self.send_status_change(StatusType.readySession)
        QTimer.singleShot(200, self.t_initializingSession_to_waitTherapy)

    #
    # sm_waitTherapy
    #
    @QtCore.Slot()
    def sm_waitTherapy(self):
        print("Entered state waitTherapy")

        self.send_status_change(StatusType.waitingTherapy)

    #
    # sm_initializingTherapy
    #
    @QtCore.Slot()
    def sm_initializingTherapy(self):
        print("Entered state initializingTherapy")

        # therapy = self.aux_therapy_name.replace(" ", "").strip()
        # self.aux_therapy_dir = os.path.join(self.aux_session_dir, therapy)
        #
        # if not os.path.isdir(self.aux_therapy_dir):
        #     print ("[CREATING] " + self.aux_therapy_dir)
        #     os.mkdir(self.aux_therapy_dir)
        #
        # video_name = therapy.lower() + ".avi"
        # joints_name = therapy.lower() + ".txt"
        # metrics_name = therapy.lower() + ".csv"
        #
        # self.aux_video_dir = os.path.join(self.aux_therapy_dir, video_name)
        # self.aux_joints_dir = os.path.join(self.aux_therapy_dir, joints_name)
        # self.aux_metrics_dir = os.path.join(self.aux_therapy_dir, metrics_name)

        self.player.setMedia(QUrl.fromLocalFile("/home/robolab/robocomp/components/robotherapy/components/robotTherapy"
                                                "/resources/examples/ejercicio_correcto2.avi"))

        self.send_status_change(StatusType.readyTherapy)

        self.t_initializingTherapy_to_loopTherapy.emit()

    #
    # sm_loopTherapy
    #
    @QtCore.Slot()
    def sm_loopTherapy(self):
        print("Entered state loopTherapy")
        # self.videoWidget.setFullScreen(True)
        self.videoWidget.show()
        self.player.setMuted(True)
        self.player.play()
        self.recording = True
        self.send_status_change(StatusType.playingTherapy)

    #
    # sm_captureFrame
    #
    @QtCore.Slot()
    def sm_captureFrame(self):
        # print("Entered state captureFrame")
        self.data_to_record = None
        self.aux_current_joints = None
        self.mix_data_to_send = MixedData()

        try:
            self.data_to_record = self.received_data_queue.get_nowait()
        except Empty:
            QTimer.singleShot(1000 / 33, self.t_captureFrame_to_captureFrame)

        else:
            self.ui.info_label.setText("Recording...")

            self.mix_data_to_send.timeStamp = self.data_to_record.timeStamp
            self.mix_data_to_send.rgbImage = self.data_to_record.rgbImage
            self.mix_data_to_send.persons = self.data_to_record.persons

            for id, person in self.data_to_record.persons.items():
                self.aux_current_joints = person.joints


            # Video
            # if self.data_to_record.rgbImage.height == 0 or self.data_to_record.rgbImage.width == 0:
            #     QTimer.singleShot(1000 / 33, self.t_captureFrame_to_captureFrame)
            #
            # frame = np.frombuffer(self.data_to_record.rgbImage.image, np.uint8).reshape(
            #     self.data_to_record.rgbImage.height, self.data_to_record.rgbImage.width,
            #     self.data_to_record.rgbImage.depth)
            # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            #
            # if self.video_writer is None:
            #     (height, width) = frame.shape[:2]
            #     self.video_writer = cv2.VideoWriter(self.aux_video_dir, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 30,
            #                                         (width, height))
            # self.video_writer.write(frame)
            #
            # # Joints
            # joint_file = open(self.aux_joints_dir, 'a+')
            # joint_file.write(str(self.data_to_record.timeStamp))
            # joint_file.write("#")
            #
            # if len(self.data_to_record.persons) > 0:
            #     for id, person in self.data_to_record.persons.items():
            #
            #         joint_file.write(str(id))
            #         joint_file.write("#")
            #
            #         self.aux_current_joints = person.joints
            #
            #         for id_joint, j in person.joints.items():
            #             joint_file.writelines([str(id_joint), " ", str(j[0]), " ", str(j[1]), " ", str(j[2]), "#"])
            #
            # else:
            #     self.ui.info_label.setText("No humans detected")
            #
            # joint_file.write("\n")
            # joint_file.close()

            self.t_captureFrame_to_computeMetrics.emit()

    #
    # sm_computeMetrics
    #
    @QtCore.Slot()
    def sm_computeMetrics(self):
        print("Entered state computeMetrics")
        self.reset_metrics()

        if self.aux_firstMetric:
            self.aux_firstTime_metric = self.data_to_record.timeStamp
            self.aux_firstMetric = False

        self.current_metrics["Time"] = round((self.data_to_record.timeStamp - self.aux_firstTime_metric) / 1000., 4)
        self.get_armFlexion("Left")
        self.get_armFlexion("Right")
        self.get_armElevation("Left")
        self.get_armElevation("Right")
        self.get_deviationAngle("Spine")
        self.get_deviationAngle("Shoulder")
        self.get_deviationAngle("Hip")
        self.get_deviationAngle("Knee")
        self.get_legFlexion("Left")
        self.get_legFlexion("Right")
        self.get_legElevation("Left")
        self.get_legElevation("Right")

        self.mix_data_to_send.metricsObtained = self.current_metrics

        self.therapymetrics_proxy.newDataObtained(self.mix_data_to_send)

        self.t_computeMetrics_to_updateMetrics.emit()

    #
    # sm_updateMetrics
    #
    @QtCore.Slot()
    def sm_updateMetrics(self):
        print("Entered state updateMetrics")

        # if not os.path.isfile(self.aux_metrics_dir):
        #     with open(self.aux_metrics_dir, 'w') as csvFile:
        #         writer = csv.writer(csvFile, delimiter=';')
        #         writer.writerow(
        #             ["Time", "LeftArmFlexion", "RightArmFlexion", "HipDeviation", "KneeDeviation",
        #              "ShoulderDeviation", "LeftArmElevation", "RightArmElevation", "SpineDeviation", "LeftLegFlexion",
        #              "RightLegFlexion", "LeftLegElevation", "RightLegElevation"])
        #     csvFile.close()
        #
        # with open(self.aux_metrics_dir, 'a') as csvFile:
        #     writer = csv.writer(csvFile, delimiter=';')
        #     writer.writerow(
        #         [self.current_metrics["Time"], self.current_metrics["LeftArmFlexion"],
        #          self.current_metrics["RightArmFlexion"], self.current_metrics["HipDeviation"],
        #          self.current_metrics["KneeDeviation"], self.current_metrics["ShoulderDeviation"],
        #          self.current_metrics["LeftArmElevation"], self.current_metrics["RightArmElevation"],
        #          self.current_metrics["SpineDeviation"], self.current_metrics["LeftLegFlexion"],
        #          self.current_metrics["RightLegFlexion"], self.current_metrics["LeftLegElevation"],
        #          self.current_metrics["RightLegElevation"]])
        #
        #     csvFile.close()

        self.t_updateMetrics_to_captureFrame.emit()

    #
    # sm_pauseTherapy
    #
    @QtCore.Slot()
    def sm_pauseTherapy(self):
        print("Entered state pauseTherapy")
        self.player.pause()
        self.recording = False
        self.send_status_change(StatusType.pausedTherapy)
        self.ui.info_label.setText("Paused...")

    #
    # sm_resetTherapy
    #
    @QtCore.Slot()
    def sm_resetTherapy(self):
        print("Entered state resetTherapy")
        self.player.stop()
        self.recording = False

        if self.video_writer is not None:
            self.video_writer.release()

        self.ui.info_label.setText("Reseted...")

        self.send_status_change(StatusType.resetedTherapy)
        self.t_resetTherapy_to_waitTherapy.emit()

    #
    # sm_finalizeTherapy
    #
    @QtCore.Slot()
    def sm_finalizeTherapy(self):
        print("Entered state finalizeTherapy")
        self.ui.info_label.setText("Finalizing therapy...")
        self.player.stop()
        self.recording = False

        if self.video_writer is not None:
            print("releasing video_writer")
            self.video_writer.release()

        self.t_finalizeTherapy_to_waitTherapy.emit()

        # PTH.save_graph(self.aux_metrics_dir, True)

        # reply = QMessageBox.question(self.focusWidget(), '',
        #                              ' ¿Desea guardar los datos de la terapia?', QMessageBox.Yes, QMessageBox.No)
        # if reply == QMessageBox.No:
        #     shutil.rmtree(self.aux_therapy_dir)

        self.send_status_change(StatusType.endTherapy)

    #
    # sm_finalizeSession
    #
    @QtCore.Slot()
    def sm_finalizeSession(self):

        print("Entered state finalizeSession")
        self.send_status_change(StatusType.endSession)

    # =================================================================
    # =================================================================
    #
    # newPersonListAndRGB
    #
    def newPersonListAndRGB(self, mixedData):
        if self.recording and len(mixedData.persons) > 0:
            self.received_data_queue.put(mixedData)

    # =============== Methods for Component Implements ==================
    # ===================================================================

    #
    # adminPauseTherapy
    #
    def adminPauseTherapy(self):

        print("adminPauseTherapy")
        self.t_loopTherapy_to_pauseTherapy.emit()

    #
    # adminStopApp
    #
    def adminStopApp(self):
        print("adminStopApp")
        qApp.quit()

    #
    # adminContinueTherapy
    #
    def adminContinueTherapy(self):
        print("adminContinueTherapy")
        self.t_pauseTherapy_to_loopTherapy.emit()

    #
    # adminEndSession
    #
    def adminEndSession(self):
        print("adminEndSession")
        self.t_waitTherapy_to_finalizeSession.emit()

    #
    # adminStartTherapy
    #
    def adminStartTherapy(self, therapy):
        print("adminStartTherapy ", therapy)
        self.aux_therapy_name = therapy
        self.t_waitTherapy_to_initializingTherapy.emit()

    #
    # adminStartSession
    #
    def adminStartSession(self, patient):
        print("adminStartSession ", patient)
        self.aux_patient_name = patient
        self.t_waitSession_to_initializingSession.emit()

    #
    # adminStopTherapy
    #
    def adminStopTherapy(self):
        print("adminStopTherapy")
        self.t_loopTherapy_to_finalizeTherapy.emit()
        self.t_pauseTherapy_to_finalizeTherapy.emit()

    #
    # adminResetTherapy
    #
    def adminResetTherapy(self):
        print("adminResetTherapy")
        self.t_loopTherapy_to_resetTherapy.emit()
        self.t_pauseTherapy_to_resetTherapy.emit()

    # ===================================================================
    # ===================================================================

    def send_status_change(self, status_type):
        initialicing_status = Status()
        initialicing_status.currentStatus = status_type
        initialicing_status.date = datetime.now().isoformat()
        print("Sending %s" % str(status_type))
        self.therapymetrics_proxy.statusChanged(initialicing_status)
