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

import sys, Ice, os
from PySide2 import QtWidgets, QtCore

ROBOCOMP = ''
try:
	ROBOCOMP = os.environ['ROBOCOMP']
except KeyError:
	print '$ROBOCOMP environment variable not set, using the default value /opt/robocomp'
	ROBOCOMP = '/opt/robocomp'

preStr = "-I/opt/robocomp/interfaces/ -I"+ROBOCOMP+"/interfaces/ --all /opt/robocomp/interfaces/"
Ice.loadSlice(preStr+"CommonBehavior.ice")
import RoboCompCommonBehavior

additionalPathStr = ''
icePaths = [ '/opt/robocomp/interfaces' ]
try:
	SLICE_PATH = os.environ['SLICE_PATH'].split(':')
	for p in SLICE_PATH:
		icePaths.append(p)
		additionalPathStr += ' -I' + p + ' '
	icePaths.append('/opt/robocomp/interfaces')
except:
	print 'SLICE_PATH environment variable was not exported. Using only the default paths'
	pass




try:
	from ui_mainUI import *
except:
	print "Can't import UI file. Did you run 'make'?"
	sys.exit(-1)


class GenericWorker(QtWidgets.QMainWindow):

	kill = QtCore.Signal()
#Signals for State Machine
	t_initialize_to_waitSession = QtCore.Signal()
	t_waitSession_to_waitTherapy = QtCore.Signal()
	t_waitTherapy_to_waitStartTherapy = QtCore.Signal()
	t_waitTherapy_to_finalizeSession = QtCore.Signal()
	t_waitStarTherapy_to_loopTherapy = QtCore.Signal()
	t_loopTherapy_to_resetTherapy = QtCore.Signal()
	t_loopTherapy_to_pauseTherapy = QtCore.Signal()
	t_loopTherapy_to_finalizeTherapy = QtCore.Signal()
	t_resetTherapy_to_loopTherapy = QtCore.Signal()
	t_resetTherapy_to_waitStartTherapy = QtCore.Signal()
	t_pauseTherapy_to_loopTherapy = QtCore.Signal()
	t_pauseTherapy_to_finalizeTherapy = QtCore.Signal()
	t_finalizeTherapy_to_waitTherapy = QtCore.Signal()

#-------------------------

	def __init__(self, mprx):
		super(GenericWorker, self).__init__()


		self.ui = Ui_guiDlg()
		self.ui.setupUi(self)
		self.show()

		
		self.mutex = QtCore.QMutex(QtCore.QMutex.Recursive)
		self.Period = 30
		self.timer = QtCore.QTimer(self)

#State Machine
		self.robotTherapyMachine= QtCore.QStateMachine()
		self.waitSession_state = QtCore.QState(self.robotTherapyMachine)
		self.waitTherapy_state = QtCore.QState(self.robotTherapyMachine)
		self.waitStartTherapy_state = QtCore.QState(self.robotTherapyMachine)
		self.loopTherapy_state = QtCore.QState(self.robotTherapyMachine)
		self.resetTherapy_state = QtCore.QState(self.robotTherapyMachine)
		self.pauseTherapy_state = QtCore.QState(self.robotTherapyMachine)
		self.finalizeTherapy_state = QtCore.QState(self.robotTherapyMachine)
		self.initialize_state = QtCore.QState(self.robotTherapyMachine)

		self.finalizeSession_state = QtCore.QFinalState(self.robotTherapyMachine)


#------------------
#Initialization State machine
		self.initialize_state.addTransition(self.t_initialize_to_waitSession, self.waitSession_state)
		self.waitSession_state.addTransition(self.t_waitSession_to_waitTherapy, self.waitTherapy_state)
		self.waitTherapy_state.addTransition(self.t_waitTherapy_to_waitStartTherapy, self.waitStartTherapy_state)
		self.waitTherapy_state.addTransition(self.t_waitTherapy_to_finalizeSession, self.finalizeSession_state)
		self.waitStarTherapy_state.addTransition(self.t_waitStarTherapy_to_loopTherapy, self.loopTherapy_state)
		self.loopTherapy_state.addTransition(self.t_loopTherapy_to_resetTherapy, self.resetTherapy_state)
		self.loopTherapy_state.addTransition(self.t_loopTherapy_to_pauseTherapy, self.pauseTherapy_state)
		self.loopTherapy_state.addTransition(self.t_loopTherapy_to_finalizeTherapy, self.finalizeTherapy_state)
		self.resetTherapy_state.addTransition(self.t_resetTherapy_to_loopTherapy, self.loopTherapy_state)
		self.resetTherapy_state.addTransition(self.t_resetTherapy_to_waitStartTherapy, self.waitStartTherapy_state)
		self.pauseTherapy_state.addTransition(self.t_pauseTherapy_to_loopTherapy, self.loopTherapy_state)
		self.pauseTherapy_state.addTransition(self.t_pauseTherapy_to_finalizeTherapy, self.finalizeTherapy_state)
		self.finalizeTherapy_state.addTransition(self.t_finalizeTherapy_to_waitTherapy, self.waitTherapy_state)


		self.waitSession_state.entered.connect(self.sm_waitSession)
		self.waitTherapy_state.entered.connect(self.sm_waitTherapy)
		self.waitStartTherapy_state.entered.connect(self.sm_waitStartTherapy)
		self.loopTherapy_state.entered.connect(self.sm_loopTherapy)
		self.resetTherapy_state.entered.connect(self.sm_resetTherapy)
		self.pauseTherapy_state.entered.connect(self.sm_pauseTherapy)
		self.finalizeTherapy_state.entered.connect(self.sm_finalizeTherapy)
		self.initialize_state.entered.connect(self.sm_initialize)
		self.finalizeSession_state.entered.connect(self.sm_finalizeSession)

		self.robotTherapyMachine.setInitialState(self.initialize_state)

#------------------

	@QtCore.Slot()
	def killYourSelf(self):
		rDebug("Killing myself")
		self.kill.emit()

	# \brief Change compute period
	# @param per Period in ms
	@QtCore.Slot(int)
	def setPeriod(self, p):
		print "Period changed", p
		Period = p
		timer.start(Period)
