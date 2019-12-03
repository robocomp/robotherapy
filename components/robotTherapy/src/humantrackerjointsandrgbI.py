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

import sys, os, Ice

ROBOCOMP = ''
try:
	ROBOCOMP = os.environ['ROBOCOMP']
except:
	print('$ROBOCOMP environment variable not set, using the default value /opt/robocomp')
	ROBOCOMP = '/opt/robocomp'
if len(ROBOCOMP)<1:
	print('ROBOCOMP environment variable not set! Exiting.')
	sys.exit()

additionalPathStr = ''
icePaths = []
try:
	icePaths.append('/opt/robocomp/interfaces')
	SLICE_PATH = os.environ['SLICE_PATH'].split(':')
	for p in SLICE_PATH:
		icePaths.append(p)
		additionalPathStr += ' -I' + p + ' '
except:
	print('SLICE_PATH environment variable was not exported. Using only the default paths')
	pass

ice_AdminTherapy = False
for p in icePaths:
	print('Trying', p, 'to load AdminTherapy.ice')
	if os.path.isfile(p+'/AdminTherapy.ice'):
		print('Using', p, 'to load AdminTherapy.ice')
		preStr = "-I/opt/robocomp/interfaces/ -I"+ROBOCOMP+"/interfaces/ " + additionalPathStr + " --all "+p+'/'
		wholeStr = preStr+"AdminTherapy.ice"
		Ice.loadSlice(wholeStr)
		ice_AdminTherapy = True
		break
if not ice_AdminTherapy:
	print('Couldn\'t load AdminTherapy')
	sys.exit(-1)
from RoboCompAdminTherapy import *
ice_HumanTrackerJointsAndRGB = False
for p in icePaths:
	print('Trying', p, 'to load HumanTrackerJointsAndRGB.ice')
	if os.path.isfile(p+'/HumanTrackerJointsAndRGB.ice'):
		print('Using', p, 'to load HumanTrackerJointsAndRGB.ice')
		preStr = "-I/opt/robocomp/interfaces/ -I"+ROBOCOMP+"/interfaces/ " + additionalPathStr + " --all "+p+'/'
		wholeStr = preStr+"HumanTrackerJointsAndRGB.ice"
		Ice.loadSlice(wholeStr)
		ice_HumanTrackerJointsAndRGB = True
		break
if not ice_HumanTrackerJointsAndRGB:
	print('Couldn\'t load HumanTrackerJointsAndRGB')
	sys.exit(-1)
from RoboCompHumanTrackerJointsAndRGB import *
ice_TherapyMetrics = False
for p in icePaths:
	print('Trying', p, 'to load TherapyMetrics.ice')
	if os.path.isfile(p+'/TherapyMetrics.ice'):
		print('Using', p, 'to load TherapyMetrics.ice')
		preStr = "-I/opt/robocomp/interfaces/ -I"+ROBOCOMP+"/interfaces/ " + additionalPathStr + " --all "+p+'/'
		wholeStr = preStr+"TherapyMetrics.ice"
		Ice.loadSlice(wholeStr)
		ice_TherapyMetrics = True
		break
if not ice_TherapyMetrics:
	print('Couldn\'t load TherapyMetrics')
	sys.exit(-1)
from RoboCompTherapyMetrics import *

class HumanTrackerJointsAndRGBI(HumanTrackerJointsAndRGB):
	def __init__(self, worker):
		self.worker = worker

	def newPersonListAndRGB(self, mixedData, c):
		return self.worker.newPersonListAndRGB(mixedData)
