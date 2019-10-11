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
from datetime import datetime
from Queue import Queue, Empty

import cv2
from PySide2.QtCore import QTimer, QUrl
from PySide2.QtMultimedia import QMediaPlayer
from PySide2.QtMultimediaWidgets import QVideoWidget
import numpy as np
from matplotlib import transforms

from genericworker import *


# If RoboComp was compiled with Python bindings you can use InnerModel in Python
# sys.path.append('/opt/robocomp/lib')
# import librobocomp_qmat
# import librobocomp_osgviewer
# import librobocomp_innermodel

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
        self.aux_video_dir = None
        self.aux_joints_dir = None

        self.robotTherapyMachine.start()

    def __del__(self):
        print 'SpecificWorker destructor'

    def setParams(self, params):
        return True

    def video_state_changed(self, state):
        if state == QMediaPlayer.State.StoppedState:
            self.t_loopTherapy_to_finalizeTherapy.emit()

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
        else:
            print ("el paciente ya existe")

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
        therapy_dir = os.path.join(self.aux_session_dir, therapy)

        if not os.path.isdir(therapy_dir):
            print ("creating" + therapy_dir)
            os.mkdir(therapy_dir)

        video_name = therapy.lower() + ".avi"
        joints_name = therapy.lower() + ".txt"

        self.aux_video_dir = os.path.join(therapy_dir,video_name)
        self.aux_joints_dir = os.path.join(therapy_dir,joints_name)

        self.player.setMedia(QUrl.fromLocalFile("/home/robolab/robocomp/components/robotherapy/components/robotTherapy"
                                                "/resources/examples/ejercicio_correcto2.avi"))

        self.t_waitTherapy_to_waitStartTherapy.emit()

    #
    # sm_waitStartTherapy
    #
    @QtCore.Slot()
    def sm_waitStartTherapy(self):
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
        try:
            self.data_to_record = self.received_data_queue.get_nowait()
        except Empty:
            QTimer.singleShot(1000/33, self.t_saveFrame_to_saveFrame)

        else:
            self.ui.info_label.setText("Recording...")
            self.ui.info_label.setText("....Video...")

            if self.data_to_record.rgbImage.height == 0 or self.data_to_record.rgbImage.width == 0:
                QTimer.singleShot(1000/33, self.t_saveFrame_to_saveFrame)

            frame = np.frombuffer(self.data_to_record.rgbImage.image, np.uint8).reshape(
                self.data_to_record.rgbImage.height, self.data_to_record.rgbImage.width,
                self.data_to_record.rgbImage.depth)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            if self.video_writer is None:
                (height, width) = frame.shape[:2]
                self.video_writer = cv2.VideoWriter(self.aux_video_dir, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 30,
                                                    (width, height))
            self.video_writer.write(frame)


            self.ui.info_label.setText("...Joints...")


            self.t_saveFrame_to_computeMetrics.emit()

    #
    # sm_computeMetrics
    #
    @QtCore.Slot()
    def sm_computeMetrics(self):
        print("Entered state computeMetrics")
        self.t_computeMetrics_to_updateMetrics.emit()

    #
    # sm_updateMetrics
    #
    @QtCore.Slot()
    def sm_updateMetrics(self):
        print("Entered state updateMetrics")
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
        if self.recording: #and len(mixedData.persons) > 0:
            print("Frame received")
            self.received_data_queue.put(mixedData)