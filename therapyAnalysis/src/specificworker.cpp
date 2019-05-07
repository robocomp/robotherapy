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
#include "specificworker.h"

/**
* \brief Default constructor
*/
SpecificWorker::SpecificWorker(TuplePrx tprx) : GenericWorker(tprx)
{
	playTimer = new QTimer();
	playForward = true;
	this->stop_playing();
	connect(this->fwd1_btn, SIGNAL(clicked()), this, SLOT(nextFrame()));
	connect(this->fwd5_btn, SIGNAL(clicked()), this, SLOT(next5Frames()));
	connect(this->bwd1_btn, SIGNAL(clicked()), this, SLOT(prevFrame()));
	connect(this->bwd5_btn, SIGNAL(clicked()), this, SLOT(prev5Frames()));
	connect(this->start_btn, SIGNAL(clicked()), this, SLOT(startFrame()));
	connect(this->end_btn, SIGNAL(clicked()), this, SLOT(endFrame()));
	connect(this->playTimer, SIGNAL(timeout()), this, SLOT(playTimerTimeout()));
	connect(this->play_btn, SIGNAL(clicked()), this, SLOT(start_playing()));
	connect(this->stop_btn, SIGNAL(clicked()), this, SLOT(stop_playing()));
	connect(this->pause_btn, SIGNAL(clicked()), this, SLOT(stop_playing()));
	connect(this->reverse_chck, SIGNAL(stateChanged(int)), this, SLOT(reverse_playing(int)));


#ifdef USE_QTGUI
	innerModelViewer = NULL;
	osgView = new OsgView();
	this->osgLayout->addWidget(osgView);
	osgGA::TrackballManipulator *tb = new osgGA::TrackballManipulator;
	osg::Vec3d eye(osg::Vec3(4000.,4000.,-1000.));
	osg::Vec3d center(osg::Vec3(0.,0.,-0.));
	osg::Vec3d up(osg::Vec3(0.,1.,0.));
	tb->setHomePosition(eye, center, up, true);
	tb->setByMatrix(osg::Matrixf::lookAt(eye,center,up));
	osgView->setCameraManipulator(tb);
#endif
}

/**
* \brief Default destructor
*/
SpecificWorker::~SpecificWorker()
{
	std::cout << "Destroying SpecificWorker" << std::endl;
}

bool SpecificWorker::setParams(RoboCompCommonBehavior::ParameterList params)
{
//       THE FOLLOWING IS JUST AN EXAMPLE
//	To use innerModelPath parameter you should uncomment specificmonitor.cpp readConfig method content
	try
	{
//		RoboCompCommonBehavior::Parameter par = params.at("InnerModelPath");
//		std::string innermodel_path = par.value;
		innerModel = std::make_shared<InnerModel>(); //InnerModel creation example
	}
	catch(std::exception e) { qFatal("Error reading config params %s",e.what()); }


#ifdef USE_QTGUI
	innerModelViewer = new InnerModelViewer (innerModel, "root", osgView->getRootGroup(), true);
#endif
	return true;
}

void SpecificWorker::initialize(int period)
{
	std::cout << "Initialize worker" << std::endl;
	this->Period = period;
	timer.start(Period);
}



void SpecificWorker::compute()
{
	//computeCODE
//	QMutexLocker locker(mutex); 
// 	try
// 	{
// 		camera_proxy->getYImage(0,img, cState, bState);
// 		memcpy(image_gray.data, &img[0], m_width*m_height*sizeof(uchar));
// 		searchTags(image_gray);
// 	}
// 	catch(const Ice::Exception &e)
// 	{
// 		std::cout << "Error reading from Camera" << e << std::endl;
// 	}
#ifdef USE_QTGUI
	if (innerModelViewer) innerModelViewer->update();
	osgView->frame();
#endif
}



void  SpecificWorker::nextFrame()
{
	this->forwardFrames(1);
}

void  SpecificWorker::next5Frames()
{
	this->forwardFrames(5);
}

void  SpecificWorker::prevFrame()
{
	this->forwardFrames(-1);
}

void  SpecificWorker::prev5Frames()
{
	this->forwardFrames(-5);
}

void  SpecificWorker::startFrame()
{
	this->frames_slider->setValue(this->frames_slider->minimum());
}

void  SpecificWorker::endFrame()
{
	this->frames_slider->setValue(this->frames_slider->maximum());
}

void  SpecificWorker::forwardFrames(int numFrames)
{
	this->frames_slider->setValue(this->frames_slider->value()+numFrames);
}

void  SpecificWorker::playTimerTimeout()
{
	if(playForward)
	{
		this->nextFrame();
	}
	else
	{
		this->prevFrame();
	}
}

void  SpecificWorker::start_playing()
{
	this->play_btn->setEnabled(false);
	this->stop_btn->setEnabled(true);
	this->pause_btn->setEnabled(true);
	this->playTimer->start(1000);
}

void  SpecificWorker::stop_playing()
{
	this->play_btn->setEnabled(true);
	this->stop_btn->setEnabled(false);
	this->pause_btn->setEnabled(false);
	this->playTimer->stop();
}

void  SpecificWorker::reverse_playing(int state)
{
	playForward = (state == 0);
}