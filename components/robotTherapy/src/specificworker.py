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

from genericworker import *

# If RoboComp was compiled with Python bindings you can use InnerModel in Python
# sys.path.append('/opt/robocomp/lib')
# import librobocomp_qmat
# import librobocomp_osgviewer
# import librobocomp_innermodel

class SpecificWorker(GenericWorker):
	def __init__(self, proxy_map):
		super(SpecificWorker, self).__init__(proxy_map)
		self.Period = 2000
		self.timer.start(self.Period)

		self.robotTherapyMachine.start()

	def __del__(self):
		print 'SpecificWorker destructor'

	def setParams(self, params):
		#try:
		#	self.innermodel = InnerModel(params["InnerModelPath"])
		#except:
		#	traceback.print_exc()
		#	print "Error reading config params"
		return True


# =============== Slots methods for State Machine ===================
# ===================================================================
	#
	# sm_initialize
	#
	@QtCore.Slot()
	def sm_initialize(self):
		print("Entered state initialize")
		pass

	#
	# sm_finalizeTherapy
	#
	@QtCore.Slot()
	def sm_finalizeTherapy(self):
		print("Entered state finalizeTherapy")
		pass

	#
	# sm_loopTherapy
	#
	@QtCore.Slot()
	def sm_loopTherapy(self):
		print("Entered state loopTherapy")
		pass

	#
	# sm_pauseTherapy
	#
	@QtCore.Slot()
	def sm_pauseTherapy(self):
		print("Entered state pauseTherapy")
		pass

	#
	# sm_resetTherapy
	#
	@QtCore.Slot()
	def sm_resetTherapy(self):
		print("Entered state resetTherapy")
		pass

	#
	# sm_waitSession
	#
	@QtCore.Slot()
	def sm_waitSession(self):
		print("Entered state waitSession")
		pass

	#
	# sm_waitStartTherapy
	#
	@QtCore.Slot()
	def sm_waitStartTherapy(self):
		print("Entered state waitStartTherapy")
		pass

	#
	# sm_waitTherapy
	#
	@QtCore.Slot()
	def sm_waitTherapy(self):
		print("Entered state waitTherapy")
		pass

	#
	# sm_finalizeSession
	#
	@QtCore.Slot()
	def sm_finalizeSession(self):
		print("Entered state finalizeSession")
		pass


# =================================================================
# =================================================================

