/*
 *    Copyright (C)2019 by YOUR NAME HERE
 *
 *    This file is part of RoboComp
 *
 *    RoboComp is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU General Public License as published by
 *    the Free Software Foundation, either version 3 of the License, or
 *    (at your option) any later version.
 *
 *    RoboComp is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU General Public License for more details.
 *
 *    You should have received a copy of the GNU General Public License
 *    along with RoboComp.  If not, see <http://www.gnu.org/licenses/>.
 */
#ifndef GENERICWORKER_H
#define GENERICWORKER_H

#include "config.h"
#include <stdint.h>
#include <qlog/qlog.h>

#if Qt5_FOUND
	#include <QtWidgets>
#else
	#include <QtGui>
#endif
#include <ui_mainUI.h>
#include <QStateMachine>
#include <QState>
#include <CommonBehavior.h>

#include <HumanTrackerJointsAndRGB.h>

#define CHECK_PERIOD 5000
#define BASIC_PERIOD 100

using namespace std;
using namespace RoboCompHumanTrackerJointsAndRGB;

using TuplePrx = std::tuple<>;


class GenericWorker :
#ifdef USE_QTGUI
	public QMainWindow, public Ui_guiDlg
#else
	public QObject
 #endif
{
Q_OBJECT
public:
	GenericWorker(TuplePrx tprx);
	virtual ~GenericWorker();
	virtual void killYourSelf();
	virtual void setPeriod(int p);

	virtual bool setParams(RoboCompCommonBehavior::ParameterList params) = 0;
	QMutex *mutex;



	virtual void HumanTrackerJointsAndRGB_newPersonListAndRGB(MixedJointsRGB mixedData) = 0;

protected:
//State Machine
	QStateMachine therapyAnalysisMachine;

	QState *recordState = new QState();
	QState *playbackState = new QState();
	QState *initializeState = new QState();
	QFinalState *closeAppState = new QFinalState();
	QState *showTherapyState = new QState(playbackState);
	QState *loadFilesState = new QState(playbackState);

//-------------------------

	QTimer timer;
	int Period;

private:


public slots:
//Slots funtion State Machine
	virtual void sm_record() = 0;
	virtual void sm_playback() = 0;
	virtual void sm_initialize() = 0;
	virtual void sm_closeApp() = 0;
	virtual void sm_showTherapy() = 0;
	virtual void sm_loadFiles() = 0;

//-------------------------
    virtual void initialize(int period) = 0;
	
signals:
	void kill();
//Signals for State Machine
	void t_initialize_to_record();
	void t_initialize_to_playback();
	void t_initialize_to_closeApp();
	void t_record_to_playback();
	void t_record_to_closeApp();
	void t_playback_to_closeApp();
	void t_playback_to_record();
	void t_loadFiles_to_showTherapy();

//-------------------------
};

#endif
