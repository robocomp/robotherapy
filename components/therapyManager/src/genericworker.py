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

ice_TherapyMetrics = False
for p in icePaths:
	if os.path.isfile(p+'/TherapyMetrics.ice'):
		preStr = "-I/opt/robocomp/interfaces/ -I"+ROBOCOMP+"/interfaces/ " + additionalPathStr + " --all "+p+'/'
		wholeStr = preStr+"TherapyMetrics.ice"
		Ice.loadSlice(wholeStr)
		ice_TherapyMetrics = True
		break
if not ice_TherapyMetrics:
	print 'Couln\'t load TherapyMetrics'
	sys.exit(-1)
from RoboCompTherapyMetrics import *
ice_TherapyMetrics = False
for p in icePaths:
	if os.path.isfile(p+'/TherapyMetrics.ice'):
		preStr = "-I/opt/robocomp/interfaces/ -I"+ROBOCOMP+"/interfaces/ " + additionalPathStr + " --all "+p+'/'
		wholeStr = preStr+"TherapyMetrics.ice"
		Ice.loadSlice(wholeStr)
		ice_TherapyMetrics = True
		break
if not ice_TherapyMetrics:
	print 'Couln\'t load TherapyMetrics'
	sys.exit(-1)
from RoboCompTherapyMetrics import *
ice_TherapyMetrics = False
for p in icePaths:
	if os.path.isfile(p+'/TherapyMetrics.ice'):
		preStr = "-I/opt/robocomp/interfaces/ -I"+ROBOCOMP+"/interfaces/ " + additionalPathStr + " --all "+p+'/'
		wholeStr = preStr+"TherapyMetrics.ice"
		Ice.loadSlice(wholeStr)
		ice_TherapyMetrics = True
		break
if not ice_TherapyMetrics:
	print 'Couln\'t load TherapyMetrics'
	sys.exit(-1)
from RoboCompTherapyMetrics import *


from therapymetricsI import *

try:
	from ui_mainUI import *
except:
	print "Can't import UI file. Did you run 'make'?"
	sys.exit(-1)


class GenericWorker(QtWidgets.QMainWindow):

	kill = QtCore.Signal()
#Signals for State Machine
	t_admin_to_appEnd = QtCore.Signal()
	t_userLogin_to_createUser = QtCore.Signal()
	t_userLogin_to_adminSessions = QtCore.Signal()
	t_createUser_to_userLogin = QtCore.Signal()
	t_adminSessions_to_createPatient = QtCore.Signal()
	t_adminSessions_to_waitSessionReady = QtCore.Signal()
	t_adminSessions_to_consultPatient = QtCore.Signal()
	t_consultPatient_to_adminSessions = QtCore.Signal()
	t_createPatient_to_adminSessions = QtCore.Signal()
	t_waitSessionReady_to_adminTherapies = QtCore.Signal()
	t_adminTherapies_to_waitingStart = QtCore.Signal()
	t_adminTherapies_to_endSession = QtCore.Signal()
	t_waitingStart_to_performingTherapy = QtCore.Signal()
	t_waitingStart_to_endSession = QtCore.Signal()
	t_performingTherapy_to_pausedTherapy = QtCore.Signal()
	t_performingTherapy_to_endTherapy = QtCore.Signal()
	t_pausedTherapy_to_adminTherapies = QtCore.Signal()
	t_pausedTherapy_to_performingTherapy = QtCore.Signal()
	t_pausedTherapy_to_endTherapy = QtCore.Signal()
	t_endTherapy_to_adminTherapies = QtCore.Signal()
	t_endSession_to_adminSessions = QtCore.Signal()
	t_waitingFrame_to_waitingFrame = QtCore.Signal()
	t_waitingFrame_to_savingFrame = QtCore.Signal()
	t_savingFrame_to_waitingFrame = QtCore.Signal()
	t_savingFrame_to_showingResults = QtCore.Signal()
	t_showingResults_to_waitingFrame = QtCore.Signal()

#-------------------------

	def __init__(self, mprx):
		super(GenericWorker, self).__init__()


		self.admintherapy_proxy = mprx["AdminTherapyProxy"]
		self.ui = Ui_guiDlg()
		self.ui.setupUi(self)
		self.show()

		
		self.mutex = QtCore.QMutex(QtCore.QMutex.Recursive)
		self.Period = 30
		self.timer = QtCore.QTimer(self)

#State Machine
		self.manager_machine= QtCore.QStateMachine()
		self.admin_state = QtCore.QState(self.manager_machine)

		self.appEnd_state = QtCore.QFinalState(self.manager_machine)



		self.createUser_state = QtCore.QState(self.admin_state)
		self.adminSessions_state = QtCore.QState(self.admin_state)
		self.consultPatient_state = QtCore.QState(self.admin_state)
		self.createPatient_state = QtCore.QState(self.admin_state)
		self.waitSessionReady_state = QtCore.QState(self.admin_state)
		self.adminTherapies_state = QtCore.QState(self.admin_state)
		self.waitingStart_state = QtCore.QState(self.admin_state)
		self.performingTherapy_state = QtCore.QState(self.admin_state)
		self.pausedTherapy_state = QtCore.QState(self.admin_state)
		self.endTherapy_state = QtCore.QState(self.admin_state)
		self.endSession_state = QtCore.QState(self.admin_state)
		self.userLogin_state = QtCore.QState(self.admin_state)




		self.savingFrame_state = QtCore.QState(self.performingTherapy_state)
		self.showingResults_state = QtCore.QState(self.performingTherapy_state)
		self.waitingFrame_state = QtCore.QState(self.performingTherapy_state)



#------------------
#Initialization State machine
		self.admin_state.addTransition(self.t_admin_to_appEnd, self.appEnd_state)
		self.userLogin_state.addTransition(self.t_userLogin_to_createUser, self.createUser_state)
		self.userLogin_state.addTransition(self.t_userLogin_to_adminSessions, self.adminSessions_state)
		self.createUser_state.addTransition(self.t_createUser_to_userLogin, self.userLogin_state)
		self.adminSessions_state.addTransition(self.t_adminSessions_to_createPatient, self.createPatient_state)
		self.adminSessions_state.addTransition(self.t_adminSessions_to_waitSessionReady, self.waitSessionReady_state)
		self.adminSessions_state.addTransition(self.t_adminSessions_to_consultPatient, self.consultPatient_state)
		self.consultPatient_state.addTransition(self.t_consultPatient_to_adminSessions, self.adminSessions_state)
		self.createPatient_state.addTransition(self.t_createPatient_to_adminSessions, self.adminSessions_state)
		self.waitSessionReady_state.addTransition(self.t_waitSessionReady_to_adminTherapies, self.adminTherapies_state)
		self.adminTherapies_state.addTransition(self.t_adminTherapies_to_waitingStart, self.waitingStart_state)
		self.adminTherapies_state.addTransition(self.t_adminTherapies_to_endSession, self.endSession_state)
		self.waitingStart_state.addTransition(self.t_waitingStart_to_performingTherapy, self.performingTherapy_state)
		self.waitingStart_state.addTransition(self.t_waitingStart_to_endSession, self.endSession_state)
		self.performingTherapy_state.addTransition(self.t_performingTherapy_to_pausedTherapy, self.pausedTherapy_state)
		self.performingTherapy_state.addTransition(self.t_performingTherapy_to_endTherapy, self.endTherapy_state)
		self.pausedTherapy_state.addTransition(self.t_pausedTherapy_to_adminTherapies, self.adminTherapies_state)
		self.pausedTherapy_state.addTransition(self.t_pausedTherapy_to_performingTherapy, self.performingTherapy_state)
		self.pausedTherapy_state.addTransition(self.t_pausedTherapy_to_endTherapy, self.endTherapy_state)
		self.endTherapy_state.addTransition(self.t_endTherapy_to_adminTherapies, self.adminTherapies_state)
		self.endSession_state.addTransition(self.t_endSession_to_adminSessions, self.adminSessions_state)
		self.waitingFrame_state.addTransition(self.t_waitingFrame_to_waitingFrame, self.waitingFrame_state)
		self.waitingFrame_state.addTransition(self.t_waitingFrame_to_savingFrame, self.savingFrame_state)
		self.savingFrame_state.addTransition(self.t_savingFrame_to_waitingFrame, self.waitingFrame_state)
		self.savingFrame_state.addTransition(self.t_savingFrame_to_showingResults, self.showingResults_state)
		self.showingResults_state.addTransition(self.t_showingResults_to_waitingFrame, self.waitingFrame_state)


		self.admin_state.entered.connect(self.sm_admin)
		self.appEnd_state.entered.connect(self.sm_appEnd)
		self.userLogin_state.entered.connect(self.sm_userLogin)
		self.createUser_state.entered.connect(self.sm_createUser)
		self.adminSessions_state.entered.connect(self.sm_adminSessions)
		self.consultPatient_state.entered.connect(self.sm_consultPatient)
		self.createPatient_state.entered.connect(self.sm_createPatient)
		self.waitSessionReady_state.entered.connect(self.sm_waitSessionReady)
		self.adminTherapies_state.entered.connect(self.sm_adminTherapies)
		self.waitingStart_state.entered.connect(self.sm_waitingStart)
		self.performingTherapy_state.entered.connect(self.sm_performingTherapy)
		self.pausedTherapy_state.entered.connect(self.sm_pausedTherapy)
		self.endTherapy_state.entered.connect(self.sm_endTherapy)
		self.endSession_state.entered.connect(self.sm_endSession)
		self.waitingFrame_state.entered.connect(self.sm_waitingFrame)
		self.savingFrame_state.entered.connect(self.sm_savingFrame)
		self.showingResults_state.entered.connect(self.sm_showingResults)

		self.manager_machine.setInitialState(self.admin_state)
		self.admin_state.setInitialState(self.userLogin_state)
		self.performingTherapy_state.setInitialState(self.waitingFrame_state)

#------------------

#Slots funtion State Machine
	@QtCore.Slot()
	def sm_n(self):
		print "Error: lack sm_n in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_o(self):
		print "Error: lack sm_o in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_n(self):
		print "Error: lack sm_n in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_e(self):
		print "Error: lack sm_e in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_admin(self):
		print "Error: lack sm_admin in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_appEnd(self):
		print "Error: lack sm_appEnd in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_createUser(self):
		print "Error: lack sm_createUser in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_adminSessions(self):
		print "Error: lack sm_adminSessions in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_consultPatient(self):
		print "Error: lack sm_consultPatient in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_createPatient(self):
		print "Error: lack sm_createPatient in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_waitSessionReady(self):
		print "Error: lack sm_waitSessionReady in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_adminTherapies(self):
		print "Error: lack sm_adminTherapies in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_waitingStart(self):
		print "Error: lack sm_waitingStart in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_performingTherapy(self):
		print "Error: lack sm_performingTherapy in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_pausedTherapy(self):
		print "Error: lack sm_pausedTherapy in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_endTherapy(self):
		print "Error: lack sm_endTherapy in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_endSession(self):
		print "Error: lack sm_endSession in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_userLogin(self):
		print "Error: lack sm_userLogin in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_savingFrame(self):
		print "Error: lack sm_savingFrame in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_showingResults(self):
		print "Error: lack sm_showingResults in Specificworker"
		sys.exit(-1)

	@QtCore.Slot()
	def sm_waitingFrame(self):
		print "Error: lack sm_waitingFrame in Specificworker"
		sys.exit(-1)


#-------------------------
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
