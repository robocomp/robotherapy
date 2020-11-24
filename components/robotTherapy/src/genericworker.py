#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2020 by YOUR NAME HERE
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
    print('$ROBOCOMP environment variable not set, using the default value /opt/robocomp')
    ROBOCOMP = '/opt/robocomp'

Ice.loadSlice("-I ./src/ --all ./src/CommonBehavior.ice")
import RoboCompCommonBehavior

Ice.loadSlice("-I ./src/ --all ./src/AdminTherapy.ice")
import RoboCompAdminTherapy
Ice.loadSlice("-I ./src/ --all ./src/HumanTrackerJointsAndRGB.ice")
import RoboCompHumanTrackerJointsAndRGB
Ice.loadSlice("-I ./src/ --all ./src/TherapyMetrics.ice")
import RoboCompTherapyMetrics

class ImgType(list):
    def __init__(self, iterable=list()):
        super(ImgType, self).__init__(iterable)

    def append(self, item):
        assert isinstance(item, byte)
        super(ImgType, self).append(item)

    def extend(self, iterable):
        for item in iterable:
            assert isinstance(item, byte)
        super(ImgType, self).extend(iterable)

    def insert(self, index, item):
        assert isinstance(item, byte)
        super(ImgType, self).insert(index, item)

setattr(RoboCompHumanTrackerJointsAndRGB, "ImgType", ImgType)

class RTMatrix(list):
    def __init__(self, iterable=list()):
        super(RTMatrix, self).__init__(iterable)

    def append(self, item):
        assert isinstance(item, float)
        super(RTMatrix, self).append(item)

    def extend(self, iterable):
        for item in iterable:
            assert isinstance(item, float)
        super(RTMatrix, self).extend(iterable)

    def insert(self, index, item):
        assert isinstance(item, float)
        super(RTMatrix, self).insert(index, item)

setattr(RoboCompHumanTrackerJointsAndRGB, "RTMatrix", RTMatrix)

class joint(list):
    def __init__(self, iterable=list()):
        super(joint, self).__init__(iterable)

    def append(self, item):
        assert isinstance(item, float)
        super(joint, self).append(item)

    def extend(self, iterable):
        for item in iterable:
            assert isinstance(item, float)
        super(joint, self).extend(iterable)

    def insert(self, index, item):
        assert isinstance(item, float)
        super(joint, self).insert(index, item)

setattr(RoboCompHumanTrackerJointsAndRGB, "joint", joint)


import admintherapyI
import humantrackerjointsandrgbI


try:
    from ui_mainUI import *
except:
    print("Can't import UI file. Did you run 'make'?")
    sys.exit(-1)



class GenericWorker(QtWidgets.QWidget):

    kill = QtCore.Signal()
    #Signals for State Machine
    t_main_to_appEnd = QtCore.Signal()
    t_initialize_to_waitSession = QtCore.Signal()
    t_waitSession_to_initializingSession = QtCore.Signal()
    t_initializingSession_to_waitTherapy = QtCore.Signal()
    t_waitTherapy_to_initializingTherapy = QtCore.Signal()
    t_waitTherapy_to_finalizeSession = QtCore.Signal()
    t_initializingTherapy_to_waitTherapy = QtCore.Signal()
    t_initializingTherapy_to_loopTherapy = QtCore.Signal()
    t_loopTherapy_to_resetTherapy = QtCore.Signal()
    t_loopTherapy_to_pauseTherapy = QtCore.Signal()
    t_loopTherapy_to_finalizeTherapy = QtCore.Signal()
    t_resetTherapy_to_waitTherapy = QtCore.Signal()
    t_pauseTherapy_to_loopTherapy = QtCore.Signal()
    t_pauseTherapy_to_resetTherapy = QtCore.Signal()
    t_pauseTherapy_to_finalizeTherapy = QtCore.Signal()
    t_finalizeTherapy_to_waitTherapy = QtCore.Signal()
    t_finalizeSession_to_waitSession = QtCore.Signal()
    t_captureFrame_to_captureFrame = QtCore.Signal()
    t_captureFrame_to_computeMetrics = QtCore.Signal()
    t_computeMetrics_to_updateMetrics = QtCore.Signal()
    t_updateMetrics_to_captureFrame = QtCore.Signal()

    #-------------------------

    def __init__(self, mprx):
        super(GenericWorker, self).__init__()

        self.therapymetrics_proxy = mprx["TherapyMetricsPub"]

        self.ui = Ui_guiDlg()
        self.ui.setupUi(self)
        self.show()

        self.mutex = QtCore.QMutex(QtCore.QMutex.Recursive)
        self.Period = 30
        self.timer = QtCore.QTimer(self)

        #State Machine
        self.main_machine= QtCore.QStateMachine()
        self.main_state = QtCore.QState(self.main_machine)

        self.appEnd_state = QtCore.QFinalState(self.main_machine)



        self.waitSession_state = QtCore.QState(self.main_state)
        self.initializingSession_state = QtCore.QState(self.main_state)
        self.waitTherapy_state = QtCore.QState(self.main_state)
        self.initializingTherapy_state = QtCore.QState(self.main_state)
        self.loopTherapy_state = QtCore.QState(self.main_state)
        self.resetTherapy_state = QtCore.QState(self.main_state)
        self.pauseTherapy_state = QtCore.QState(self.main_state)
        self.finalizeTherapy_state = QtCore.QState(self.main_state)
        self.finalizeSession_state = QtCore.QState(self.main_state)
        self.initialize_state = QtCore.QState(self.main_state)




        self.computeMetrics_state = QtCore.QState(self.loopTherapy_state)
        self.updateMetrics_state = QtCore.QState(self.loopTherapy_state)
        self.captureFrame_state = QtCore.QState(self.loopTherapy_state)



        #------------------
        #Initialization State machine
        self.main_state.addTransition(self.t_main_to_appEnd, self.appEnd_state)
        self.initialize_state.addTransition(self.t_initialize_to_waitSession, self.waitSession_state)
        self.waitSession_state.addTransition(self.t_waitSession_to_initializingSession, self.initializingSession_state)
        self.initializingSession_state.addTransition(self.t_initializingSession_to_waitTherapy, self.waitTherapy_state)
        self.waitTherapy_state.addTransition(self.t_waitTherapy_to_initializingTherapy, self.initializingTherapy_state)
        self.waitTherapy_state.addTransition(self.t_waitTherapy_to_finalizeSession, self.finalizeSession_state)
        self.initializingTherapy_state.addTransition(self.t_initializingTherapy_to_waitTherapy, self.waitTherapy_state)
        self.initializingTherapy_state.addTransition(self.t_initializingTherapy_to_loopTherapy, self.loopTherapy_state)
        self.loopTherapy_state.addTransition(self.t_loopTherapy_to_resetTherapy, self.resetTherapy_state)
        self.loopTherapy_state.addTransition(self.t_loopTherapy_to_pauseTherapy, self.pauseTherapy_state)
        self.loopTherapy_state.addTransition(self.t_loopTherapy_to_finalizeTherapy, self.finalizeTherapy_state)
        self.resetTherapy_state.addTransition(self.t_resetTherapy_to_waitTherapy, self.waitTherapy_state)
        self.pauseTherapy_state.addTransition(self.t_pauseTherapy_to_loopTherapy, self.loopTherapy_state)
        self.pauseTherapy_state.addTransition(self.t_pauseTherapy_to_resetTherapy, self.resetTherapy_state)
        self.pauseTherapy_state.addTransition(self.t_pauseTherapy_to_finalizeTherapy, self.finalizeTherapy_state)
        self.finalizeTherapy_state.addTransition(self.t_finalizeTherapy_to_waitTherapy, self.waitTherapy_state)
        self.finalizeSession_state.addTransition(self.t_finalizeSession_to_waitSession, self.waitSession_state)
        self.captureFrame_state.addTransition(self.t_captureFrame_to_captureFrame, self.captureFrame_state)
        self.captureFrame_state.addTransition(self.t_captureFrame_to_computeMetrics, self.computeMetrics_state)
        self.computeMetrics_state.addTransition(self.t_computeMetrics_to_updateMetrics, self.updateMetrics_state)
        self.updateMetrics_state.addTransition(self.t_updateMetrics_to_captureFrame, self.captureFrame_state)


        self.main_state.entered.connect(self.sm_main)
        self.appEnd_state.entered.connect(self.sm_appEnd)
        self.initialize_state.entered.connect(self.sm_initialize)
        self.waitSession_state.entered.connect(self.sm_waitSession)
        self.initializingSession_state.entered.connect(self.sm_initializingSession)
        self.waitTherapy_state.entered.connect(self.sm_waitTherapy)
        self.initializingTherapy_state.entered.connect(self.sm_initializingTherapy)
        self.loopTherapy_state.entered.connect(self.sm_loopTherapy)
        self.resetTherapy_state.entered.connect(self.sm_resetTherapy)
        self.pauseTherapy_state.entered.connect(self.sm_pauseTherapy)
        self.finalizeTherapy_state.entered.connect(self.sm_finalizeTherapy)
        self.finalizeSession_state.entered.connect(self.sm_finalizeSession)
        self.captureFrame_state.entered.connect(self.sm_captureFrame)
        self.computeMetrics_state.entered.connect(self.sm_computeMetrics)
        self.updateMetrics_state.entered.connect(self.sm_updateMetrics)

        self.main_machine.setInitialState(self.main_state)
        self.main_state.setInitialState(self.initialize_state)
        self.loopTherapy_state.setInitialState(self.captureFrame_state)

        #------------------

    #Slots funtion State Machine

    @QtCore.Slot()
    def sm_main(self):
        print("Error: lack sm_main in Specificworker")
        sys.exit(-1)

    @QtCore.Slot()
    def sm_appEnd(self):
        print("Error: lack sm_appEnd in Specificworker")
        sys.exit(-1)

    @QtCore.Slot()
    def sm_waitSession(self):
        print("Error: lack sm_waitSession in Specificworker")
        sys.exit(-1)

    @QtCore.Slot()
    def sm_initializingSession(self):
        print("Error: lack sm_initializingSession in Specificworker")
        sys.exit(-1)

    @QtCore.Slot()
    def sm_waitTherapy(self):
        print("Error: lack sm_waitTherapy in Specificworker")
        sys.exit(-1)

    @QtCore.Slot()
    def sm_initializingTherapy(self):
        print("Error: lack sm_initializingTherapy in Specificworker")
        sys.exit(-1)

    @QtCore.Slot()
    def sm_loopTherapy(self):
        print("Error: lack sm_loopTherapy in Specificworker")
        sys.exit(-1)

    @QtCore.Slot()
    def sm_resetTherapy(self):
        print("Error: lack sm_resetTherapy in Specificworker")
        sys.exit(-1)

    @QtCore.Slot()
    def sm_pauseTherapy(self):
        print("Error: lack sm_pauseTherapy in Specificworker")
        sys.exit(-1)

    @QtCore.Slot()
    def sm_finalizeTherapy(self):
        print("Error: lack sm_finalizeTherapy in Specificworker")
        sys.exit(-1)

    @QtCore.Slot()
    def sm_finalizeSession(self):
        print("Error: lack sm_finalizeSession in Specificworker")
        sys.exit(-1)

    @QtCore.Slot()
    def sm_initialize(self):
        print("Error: lack sm_initialize in Specificworker")
        sys.exit(-1)

    @QtCore.Slot()
    def sm_computeMetrics(self):
        print("Error: lack sm_computeMetrics in Specificworker")
        sys.exit(-1)

    @QtCore.Slot()
    def sm_updateMetrics(self):
        print("Error: lack sm_updateMetrics in Specificworker")
        sys.exit(-1)

    @QtCore.Slot()
    def sm_captureFrame(self):
        print("Error: lack sm_captureFrame in Specificworker")
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
        print("Period changed", p)
        self.Period = p
        self.timer.start(self.Period)
