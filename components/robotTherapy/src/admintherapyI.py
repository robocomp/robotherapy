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
#

import sys, os, Ice

ROBOCOMP = ''
try:
    ROBOCOMP = os.environ['ROBOCOMP']
except:
    print('$ROBOCOMP environment variable not set, using the default value /opt/robocomp')
    ROBOCOMP = '/opt/robocomp'
if len(ROBOCOMP)<1:
    raise RuntimeError('ROBOCOMP environment variable not set! Exiting.')


Ice.loadSlice("-I ./src/ --all ./src/AdminTherapy.ice")

from RoboCompAdminTherapy import *

class AdminTherapyI(AdminTherapy):
    def __init__(self, worker):
        self.worker = worker


    def adminContinueTherapy(self, c):
        return self.worker.AdminTherapy_adminContinueTherapy()

    def adminEndSession(self, c):
        return self.worker.AdminTherapy_adminEndSession()

    def adminPauseTherapy(self, c):
        return self.worker.AdminTherapy_adminPauseTherapy()

    def adminResetTherapy(self, c):
        return self.worker.AdminTherapy_adminResetTherapy()

    def adminStartSession(self, player, c):
        return self.worker.AdminTherapy_adminStartSession(player)

    def adminStartTherapy(self, therapy, c):
        return self.worker.AdminTherapy_adminStartTherapy(therapy)

    def adminStopApp(self, c):
        return self.worker.AdminTherapy_adminStopApp()

    def adminStopTherapy(self, c):
        return self.worker.AdminTherapy_adminStopTherapy()
