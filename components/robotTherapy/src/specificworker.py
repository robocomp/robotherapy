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
from Queue import Queue

from PySide2.QtCore import QTimer, QUrl
from PySide2.QtMultimedia import QMediaPlayer
from PySide2.QtMultimediaWidgets import QVideoWidget

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

		self.data_to_record = Queue()

		self.robotTherapyMachine.start()

	def __del__(self):
		print 'SpecificWorker destructor'

	def setParams(self, params):
		# try:
		#	self.innermodel = InnerModel(params["InnerModelPath"])
		# except:
		#	traceback.print_exc()
		#	print "Error reading config params"
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
		self.t_waitSession_to_waitTherapy.emit()

	#
	# sm_waitTherapy
	#
	@QtCore.Slot()
	def sm_waitTherapy(self):
		print("Entered state waitTherapy")
		self.t_waitTherapy_to_waitStartTherapy.emit()

	#
	# sm_waitStartTherapy
	#
	@QtCore.Slot()
	def sm_waitStartTherapy(self):
		print("Entered state waitStartTherapy")
		self.player.setMedia(QUrl.fromLocalFile("/home/robolab/robocomp/components/robotherapy/components/robotTherapy"
												"/resources/examples/ejercicio_correcto2.avi"))

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

	# QTimer.singleShot(1000,self.t_playingVideo_to_playingVideo)
	#
	# sm_captureFrame
	#
	@QtCore.Slot()
	def sm_saveFrame(self):
		print("Entered state saveFrame")
		QTimer.singleShot(300, self.t_saveFrame_to_computeMetrics)

	#
	# sm_computeMetrics
	#
	@QtCore.Slot()
	def sm_computeMetrics(self):
		print("Entered state computeMetrics")
		QTimer.singleShot(300, self.t_computeMetrics_to_updateMetrics)

	#
	# sm_updateMetrics
	#
	@QtCore.Slot()
	def sm_updateMetrics(self):
		print("Entered state updateMetrics")
		QTimer.singleShot(300, self.t_updateMetrics_to_saveFrame)

	#
	# sm_pauseTherapy
	#
	@QtCore.Slot()
	def sm_pauseTherapy(self):
		print("Entered state pauseTherapy")
		self.player.pause()

	#
	# sm_resetTherapy
	#
	@QtCore.Slot()
	def sm_resetTherapy(self):
		print("Entered state resetTherapy")
		self.player.stop()
		self.t_resetTherapy_to_waitStartTherapy.emit()

	#
	# sm_finalizeTherapy
	#
	@QtCore.Slot()
	def sm_finalizeTherapy(self):
		print("Entered state finalizeTherapy")
		self.player.stop()
		QTimer.singleShot(300, self.t_finalizeTherapy_to_waitTherapy)

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
		if self.recording:
			self.data_to_record.put(mixedData)
