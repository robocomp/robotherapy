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
#include "genericworker.h"
/**
* \brief Default constructor
*/
GenericWorker::GenericWorker(TuplePrx tprx) :
#ifdef USE_QTGUI
Ui_guiDlg()
#else
QObject()
#endif

{

//Initialization State machine
	initializeState->addTransition(this, SIGNAL(t_initialize_to_record()), recordState);
	initializeState->addTransition(this, SIGNAL(t_initialize_to_playback()), playbackState);
	initializeState->addTransition(this, SIGNAL(t_initialize_to_finalize()), finalizeState);
	recordState->addTransition(this, SIGNAL(t_record_to_playback()), playbackState);
	recordState->addTransition(this, SIGNAL(t_record_to_finalize()), finalizeState);
	playbackState->addTransition(this, SIGNAL(t_playback_to_finalize()), finalizeState);
	waitingStartState->addTransition(this, SIGNAL(t_waitingStart_to_processFrame()), processFrameState);
	processFrameState->addTransition(this, SIGNAL(t_processFrame_to_stop()), stopState);
	processFrameState->addTransition(this, SIGNAL(t_processFrame_to_pause()), pauseState);
	pauseState->addTransition(this, SIGNAL(t_pause_to_processFrame()), processFrameState);
	pauseState->addTransition(this, SIGNAL(t_pause_to_stop()), stopState);
	loadFilesState->addTransition(this, SIGNAL(t_loadFiles_to_showTherapy()), showTherapyState);

	therapyAnalysisMachine.addState(recordState);
	therapyAnalysisMachine.addState(playbackState);
	therapyAnalysisMachine.addState(initializeState);
	therapyAnalysisMachine.addState(finalizeState);

	therapyAnalysisMachine.setInitialState(initializeState);
	recordState->setInitialState(waitingStartState);
	playbackState->setInitialState(loadFilesState);

	QObject::connect(recordState, SIGNAL(entered()), this, SLOT(sm_record()));
	QObject::connect(playbackState, SIGNAL(entered()), this, SLOT(sm_playback()));
	QObject::connect(initializeState, SIGNAL(entered()), this, SLOT(sm_initialize()));
	QObject::connect(finalizeState, SIGNAL(entered()), this, SLOT(sm_finalize()));
	QObject::connect(waitingStartState, SIGNAL(entered()), this, SLOT(sm_waitingStart()));
	QObject::connect(pauseState, SIGNAL(entered()), this, SLOT(sm_pause()));
	QObject::connect(stopState, SIGNAL(entered()), this, SLOT(sm_stop()));
	QObject::connect(processFrameState, SIGNAL(entered()), this, SLOT(sm_processFrame()));
	QObject::connect(loadFilesState, SIGNAL(entered()), this, SLOT(sm_loadFiles()));
	QObject::connect(showTherapyState, SIGNAL(entered()), this, SLOT(sm_showTherapy()));

//------------------

	mutex = new QMutex(QMutex::Recursive);

	#ifdef USE_QTGUI
		setupUi(this);
		show();
	#endif
	Period = BASIC_PERIOD;
//	connect(&timer, SIGNAL(timeout()), this, SLOT(compute()));

}

/**
* \brief Default destructor
*/
GenericWorker::~GenericWorker()
{

}
void GenericWorker::killYourSelf()
{
	rDebug("Killing myself");
	emit kill();
}
/**
* \brief Change compute period
* @param per Period in ms
*/
void GenericWorker::setPeriod(int p)
{
	rDebug("Period changed"+QString::number(p));
	Period = p;
	timer.start(Period);
}

