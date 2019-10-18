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
import shutil
from Queue import Queue, Empty
from datetime import datetime

import cv2
import numpy as np
import vg
from PySide2.QtCore import QTimer, QUrl
from PySide2.QtMultimedia import QMediaPlayer
from PySide2.QtMultimediaWidgets import QVideoWidget
from PySide2.QtWidgets import QMessageBox

import plot_therapy as PTH
from genericworker import *


# def get_AngleBetweenVectors(v1, v2):
#     v1 = v1 / np.linalg.norm(v1)
#     v2 = v2 / np.linalg.norm(v2)
#
#     dot_product = np.dot(v1, v2)
#     angle = np.arccos(dot_product / (np.linalg.norm(v1) * np.linalg.norm(v2)))
#
#     return np.degrees(angle)

def get_AngleBetweenVectors(v1, v2):
    v1 = vg.normalize(v1)
    v2 = vg.normalize(v2)
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

        self.aux_saving_dir = "/home/robolab/robocomp/components/robotherapy/components/robotTherapy/savedSessions"
        if not os.path.isdir(self.aux_saving_dir):
            os.mkdir(self.aux_saving_dir)

        self.aux_session_dir = None
        self.aux_therapy_dir = None
        self.aux_video_dir = None
        self.aux_joints_dir = None
        self.aux_metrics_dir = None
        self.aux_current_joints = None

        self.aux_firstTime_metric = None
        self.aux_firstMetric = True

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
        self.current_metrics["ElbowLeft"] = np.nan
        self.current_metrics["ElbowRight"] = np.nan
        self.current_metrics["ShoulderLeft"] = np.nan
        self.current_metrics["ShoulderRight"] = np.nan
        self.current_metrics["Spine"] = np.nan
        self.current_metrics["Shoulder"] = np.nan
        self.current_metrics["Hip"] = np.nan
        self.current_metrics["Knee"] = np.nan

    def get_elbowAngle(self, side):

        necessary_joints = [side + "Elbow", side + "Shoulder", side + "Hand"]

        if not self.check_necessary_joints(necessary_joints):
            return

        elbow = np.array(self.aux_current_joints[side + "Elbow"])
        shoulder = np.array(self.aux_current_joints[side + "Shoulder"])
        hand = np.array(self.aux_current_joints[side + "Hand"])

        v1 = elbow - hand
        v2 = elbow - shoulder
        self.current_metrics["Elbow" + side] = round(get_AngleBetweenVectors(v1, v2), 4)

    def get_shoulderAngle(self, side):

        necessary_joints = [side + "Elbow", side + "Shoulder"]

        if not self.check_necessary_joints(necessary_joints):
            return

        elbow = np.array(self.aux_current_joints[side + "Elbow"])
        shoulder = np.array(self.aux_current_joints[side + "Shoulder"])
        vertical = np.array([shoulder[0], 0, shoulder[2]])

        v1 = shoulder - elbow
        v2 = shoulder - vertical

        print get_AngleBetweenVectors(v1, v2)

        self.current_metrics["Shoulder" + side] = round(get_AngleBetweenVectors(v1, v2), 4)

    def get_deviationAngle(self, part):

        if part == "Spine":

            necessary_joints = ["BaseSpine", "ShoulderSpine"]

            if not self.check_necessary_joints(necessary_joints):
                return

            base = np.array(self.aux_current_joints["BaseSpine"])
            upper = np.array(self.aux_current_joints["ShoulderSpine"])
            vertical = np.array([upper[0], 0, upper[2]])

            v1 = upper - base
            v2 = upper - vertical

            self.current_metrics[part] = round(get_AngleBetweenVectors(v1, v2), 4)

        else:

            necessary_joints = ["Left" + part, "Right" + part]

            if not self.check_necessary_joints(necessary_joints):
                return

            left = np.array(self.aux_current_joints["Left" + part])
            right = np.array(self.aux_current_joints["Right" + part])
            horizontal = np.array([right[0], left[1], right[2]])

            v1 = left - right
            v2 = left - horizontal

            self.current_metrics[part] = round(get_AngleBetweenVectors(v1, v2), 4)

    def check_necessary_joints(self, list_joints):

        for jnt in list_joints:
            if jnt not in self.aux_current_joints:
                return False
        return True

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

        self.ui.start_button.clicked.connect(self.t_waitStartTherapy_to_loopTherapy)
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
        patient_name = "Sergio Barroso Ramirez"
        patient = patient_name.replace(" ", "").strip()
        patient_dir = os.path.join(self.aux_saving_dir, patient)

        if not os.path.isdir(patient_dir):
            os.mkdir(patient_dir)

        currentDate = datetime.now()
        date = datetime.strftime(currentDate, "%m%d%H%M")
        self.aux_session_dir = os.path.join(patient_dir, "session_" + date)

        if not os.path.isdir(self.aux_session_dir):
            os.mkdir(self.aux_session_dir)

        self.t_waitSession_to_waitTherapy.emit()

    #
    # sm_waitTherapy
    #
    @QtCore.Slot()
    def sm_waitTherapy(self):
        print("Entered state waitTherapy")

        therapy_name = "Levantar Brazos"
        therapy = therapy_name.replace(" ", "").strip()
        self.aux_therapy_dir = os.path.join(self.aux_session_dir, therapy)

        if not os.path.isdir(self.aux_therapy_dir):
            print ("creating" + self.aux_therapy_dir)
            os.mkdir(self.aux_therapy_dir)

        video_name = therapy.lower() + ".avi"
        joints_name = therapy.lower() + ".txt"
        metrics_name = therapy.lower() + ".csv"

        self.aux_video_dir = os.path.join(self.aux_therapy_dir, video_name)
        self.aux_joints_dir = os.path.join(self.aux_therapy_dir, joints_name)
        self.aux_metrics_dir = os.path.join(self.aux_therapy_dir, metrics_name)

        self.player.setMedia(QUrl.fromLocalFile("/home/robolab/robocomp/components/robotherapy/components/robotTherapy"
                                                "/resources/examples/ejercicio_correcto2.avi"))

        self.t_waitTherapy_to_waitStartTherapy.emit()

    #
    # sm_waitStartTherapy
    #
    @QtCore.Slot()
    def sm_waitStartTherapy(self):
        self.aux_firstMetric = True
        print("Entered state waitStartTherapy")

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

    #
    # sm_captureFrame
    #
    @QtCore.Slot()
    def sm_saveFrame(self):
        print("Entered state saveFrame")
        self.data_to_record = None
        self.aux_current_joints = None
        try:
            self.data_to_record = self.received_data_queue.get_nowait()
        except Empty:
            QTimer.singleShot(1000 / 33, self.t_saveFrame_to_saveFrame)

        else:
            self.ui.info_label.setText("Recording...")

            # Video
            if self.data_to_record.rgbImage.height == 0 or self.data_to_record.rgbImage.width == 0:
                QTimer.singleShot(1000 / 33, self.t_saveFrame_to_saveFrame)

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

            self.t_saveFrame_to_computeMetrics.emit()

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

        self.current_metrics["Time"] = round((self.data_to_record.timeStamp - self.aux_firstTime_metric)/1000., 4)
        self.get_elbowAngle("Left")
        self.get_elbowAngle("Right")
        self.get_shoulderAngle("Left")
        self.get_shoulderAngle("Right")
        self.get_deviationAngle("Spine")
        self.get_deviationAngle("Shoulder")
        self.get_deviationAngle("Hip")
        self.get_deviationAngle("Knee")

        self.t_computeMetrics_to_updateMetrics.emit()

    #
    # sm_updateMetrics
    #
    @QtCore.Slot()
    def sm_updateMetrics(self):
        print("Entered state updateMetrics")

        if not os.path.isfile(self.aux_metrics_dir):
            with open(self.aux_metrics_dir, 'w') as csvFile:
                writer = csv.writer(csvFile, delimiter=';')
                writer.writerow(
                    ["Time", "ElbowLeft", "ElbowRight", "Hip", "Knee",
                     "Shoulder", "ShoulderLeft", "ShoulderRight", "Spine"])
            csvFile.close()

        with open(self.aux_metrics_dir, 'a') as csvFile:
            writer = csv.writer(csvFile, delimiter=';')
            writer.writerow(
                [self.current_metrics["Time"], self.current_metrics["ElbowLeft"],
                 self.current_metrics["ElbowRight"], self.current_metrics["Hip"],
                 self.current_metrics["Knee"], self.current_metrics["Shoulder"],
                 self.current_metrics["ShoulderLeft"], self.current_metrics["ShoulderRight"],
                 self.current_metrics["Spine"]])

            csvFile.close()

        self.t_updateMetrics_to_saveFrame.emit()

    #
    # sm_pauseTherapy
    #
    @QtCore.Slot()
    def sm_pauseTherapy(self):
        print("Entered state pauseTherapy")
        self.player.pause()
        self.recording = False

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

        self.t_resetTherapy_to_waitStartTherapy.emit()

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

        PTH.save_graph(self.aux_metrics_dir, True)

        reply = QMessageBox.question(self.focusWidget(), '',
                                     ' ¿Desea guardar los datos de la terapia?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            shutil.rmtree(self.aux_therapy_dir)

    #
    # sm_finalizeSession
    #
    @QtCore.Slot()
    def sm_finalizeSession(self):

        print("Entered state finalizeSession")
        pass

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
		#
		# implementCODE
		#
		pass


	#
	# adminStopApp
	#
	def adminStopApp(self):
		#
		# implementCODE
		#
		pass


	#
	# adminContinueTherapy
	#
	def adminContinueTherapy(self):
		#
		# implementCODE
		#
		pass


	#
	# adminEndSession
	#
	def adminEndSession(self):
		#
		# implementCODE
		#
		pass


	#
	# adminStartTherapy
	#
	def adminStartTherapy(self, therapy):
		#
		# implementCODE
		#
		pass


	#
	# adminStartSession
	#
	def adminStartSession(self, player):
		#
		# implementCODE
		#
		pass


	#
	# adminStopTherapy
	#
	def adminStopTherapy(self):
		#
		# implementCODE
		#
		pass


	#
	# adminResetTherapy
	#
	def adminResetTherapy(self):
		#
		# implementCODE
		#
		pass

# ===================================================================
# ===================================================================

