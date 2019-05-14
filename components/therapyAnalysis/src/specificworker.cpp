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
	framesRecorded = 0;
	playForward = true;
	recording = false;
	this->stop_playing();
	auto palette = this->angle1_lcd->palette();
	palette.setColor(palette.WindowText, QColor(Qt::darkRed));
//	palette.setColor(palette.Background, QColor(0, 170, 255));
//	palette.setColor(palette.Light, QColor(255, 0, 0));
//	palette.setColor(palette.Dark, QColor(0, 255, 0));
	this->angle1_lcd->setPalette(palette);
	this->angle2_lcd->setPalette(palette);
	this->height1_lcd->setPalette(palette);
	this->height2_lcd->setPalette(palette);
	this->play_btn->setDefaultAction(this->play_action);
	this->stop_btn->setDefaultAction(this->stop_action);
	this->pause_btn->setDefaultAction(this->pause_action);
	this->fwd1_btn->setDefaultAction(this->fwd1_action);
	this->fwd5_btn->setDefaultAction(this->fwd5_action);
	this->bwd1_btn->setDefaultAction(this->bwd1_action);
	this->bwd5_btn->setDefaultAction(this->bwd5_action);

	this->fwd1_btn->setText(">>+1");
	this->fwd5_btn->setText(">>+5");
	this->bwd1_btn->setText("<<-1");
	this->bwd5_btn->setText("<<-5");


	connect(this->loadFile_action, SIGNAL(triggered()), this, SLOT(loadFileClicked()));
	connect(this->fwd1_action, SIGNAL(triggered()), this, SLOT(nextFrame()));
	connect(this->fwd5_action, SIGNAL(triggered()), this, SLOT(next5Frames()));
	connect(this->bwd1_action, SIGNAL(triggered()), this, SLOT(prevFrame()));
	connect(this->bwd5_action, SIGNAL(triggered()), this, SLOT(prev5Frames()));
	connect(this->start_btn, SIGNAL(clicked()), this, SLOT(startFrame()));
	connect(this->end_btn, SIGNAL(clicked()), this, SLOT(endFrame()));
	connect(this->playTimer, SIGNAL(timeout()), this, SLOT(playTimerTimeout()));
	connect(this->play_action, SIGNAL(triggered()), this, SLOT(start_playing()));
	connect(this->stop_action, SIGNAL(triggered()), this, SLOT(stop_playing()));
	connect(this->pause_action, SIGNAL(triggered()), this, SLOT(pause_playing()));
	connect(this->reverse_chck, SIGNAL(stateChanged(int)), this, SLOT(reverse_playing(int)));
	connect(this->recordMode_action, SIGNAL(triggered()), this, SLOT(record_mode()));
	connect(this->playbackMode_action, SIGNAL(triggered()), this, SLOT(playback_mode()));
	connect(this->record_btn, SIGNAL(clicked()), this, SLOT(record()));
	connect(this->reverse_chck, SIGNAL(stateChanged(int)), this, SLOT(reverse_playing(int)));
	connect(this->visualizeRecording_chck, SIGNAL(toggled(bool)), this, SLOT(visualizeRecordingToggled(bool)));
	connect(this->frames_slider, SIGNAL(valueChanged(int)), this, SLOT(framesSliderMoved(int)));
	connect(this->fps_spnbox, SIGNAL(valueChanged(double)), this, SLOT(changePlayFps(double)));
	connect(this->chart_pb, SIGNAL(clicked()), this, SLOT(load_chart()));

#ifdef USE_QTGUI
	innerModelViewer = NULL;
	osgView = new OsgView(this);
	this->osgLayout->addWidget(osgView);
	osgGA::TrackballManipulator *tb = new osgGA::TrackballManipulator;
	osg::Vec3d eye(osg::Vec3(4000.,4000.,-1000.));
	osg::Vec3d center(osg::Vec3(0.,0.,-0.));
	osg::Vec3d up(osg::Vec3(0.,1.,0.));
	tb->setHomePosition(eye, center, up, true);
	tb->setByMatrix(osg::Matrixf::lookAt(eye,center,up));
	osgView->setCameraManipulator(tb);
#endif

	this->playback_mode();
	this->relateJointsMeshes();
	playFps = this->fps_spnbox->value();
	this->setEnabledPlayControls(false);
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
		RoboCompCommonBehavior::Parameter par = params.at("InnerModelPath");
		std::string innermodel_path = par.value;
		innerModel = std::make_shared<InnerModel>(innermodel_path); //InnerModel creation example
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

	if(recording)
	{
		recordData();
	}
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
	this->obtainFeatures();
	this->loadVideoFrame(this->frames_slider->value());
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
	this->playTimer->start(1000/playFps);
	this->obtainFeatures();
}

void  SpecificWorker::pause_playing()
{
	this->play_btn->setEnabled(true);
	this->stop_btn->setEnabled(false);
	this->pause_btn->setEnabled(false);
	this->playTimer->stop();
	this->obtainFeatures();
}

void  SpecificWorker::stop_playing()
{
	this->play_btn->setEnabled(true);
	this->stop_btn->setEnabled(false);
	this->pause_btn->setEnabled(false);
	this->playTimer->stop();
	this->startFrame();
	this->obtainFeatures();
}

void  SpecificWorker::reverse_playing(int state)
{
	this->playForward = (state == 0);
}

float SpecificWorker::get_rand_float(float HI=-10, float LO=10)
{

	return (LO + static_cast <float> (rand()) /( static_cast <float> (RAND_MAX/(HI-LO))));
}

void SpecificWorker::update_metrics() {

	this->angle1_lcd->display(this->get_rand_float(-6.2831, 6.2831));
	this->angle2_lcd->display(this->get_rand_float(-6.2831, 6.2831));
	this->height1_lcd->display(this->get_rand_float(500, 2500));
	this->height2_lcd->display(this->get_rand_float(500, 2500));
	qDebug()<<"Updating metrics";
}


void SpecificWorker::playback_mode() {

	this->stackedWidget->setCurrentIndex(0);
	this->playbackMode_action->setEnabled(false);
	this->recordMode_action->setEnabled(true);
	this->osgLayout->addWidget(this->osgView);
}

void SpecificWorker::record_mode() {

	this->stackedWidget->setCurrentIndex(1);
	this->playbackMode_action->setEnabled(true);
	this->recordMode_action->setEnabled(false);
	this->osgLayout_2->addWidget(this->osgView);
}

void SpecificWorker::record() {
	if(recording) {
		this->recording = false;
		this->filePath_lnedit->setEnabled(true);
		this->record_btn->setText("Record");
		qDebug()<<"Stopping Recording...";
	} else
	{
		if(!this->filePath_lnedit->text().isEmpty())
			this->savePath = this->filePath_lnedit->text();
		else
		{
			if(QMessageBox::warning(this,tr("Save path problem"),tr("You have to set a valid path to record to a file"),
									QMessageBox::Ok,QMessageBox::Ok ) == QMessageBox::Ok)
			{
				this->record_mode();
				this->filePath_lnedit->setFocus();
				QString fileName = QFileDialog::getSaveFileName(this, tr("Save File"),"",tr("Recordings)"));
				this->filePath_lnedit->setText(fileName);
				this->savePath = fileName;
			}
		}
		//truncate file
		fstream jointfile;
		jointfile.open( (this->savePath+".txt").toStdString() , std::fstream::trunc);
		jointfile.close();
		this->videoWriter = cv::VideoWriter( (this->savePath+".avi").toStdString(), 0, 0, cv::Size(640, 480));

		this->recording = true;
		this->filePath_lnedit->setEnabled(false);
		this->record_btn->setText("Stop");
		qDebug()<<"Starting Recording...";
	}
}

void SpecificWorker::updateFramesRecorded()
{
	this->framesRecorded++;
	this->framesRecorded_lcd->display(this->framesRecorded);
}

void SpecificWorker::visualizeRecordingToggled(bool state)
{
	this->visualizeRecording = state;
}

void SpecificWorker::loadFileClicked()
{
	if (this->loadTrainingFromFile())
	{
		this->playback_mode();
		this->setEnabledPlayControls(true);
		this->frames_slider->setMaximum(this->loadedTraining.size()-1);
	}
}

void SpecificWorker::changePlayFps(double value)
{
	this->playFps = value;
	this->restartPlayTimer();
}

void SpecificWorker::restartPlayTimer()
{
	this->playTimer->stop();
	// Check if currently playing
	if(this->stop_btn->isEnabled())
		this->playTimer->start(1000/playFps);
}

void SpecificWorker::framesSliderMoved(int value)
{
	this->obtainFeatures();
	if((int)this->loadedTraining.size()>value) {
		auto person = this->loadedTraining[value];
		this->PaintSkeleton(person);
	}
	else{
		this->status->showMessage("No training loaded");
	}

}

void SpecificWorker::setEnabledPlayControls(bool enabled)
{
	this->frames_slider->setEnabled(enabled);

	this->play_btn->setEnabled(enabled);

	this->stop_btn->setEnabled(enabled);
	this->pause_btn->setEnabled(enabled);
	this->playTimer->stop();
	if(!enabled)
	{
		this->frames_slider->setToolTip("Load a training to enable this control");
		this->play_btn->setToolTip("Load a training to enable this control");
	}
	else
	{
		this->frames_slider->setToolTip("");
		this->play_btn->setToolTip("");
	}
}

void SpecificWorker::load_chart()
{
	chart = new Chart();
	chart->loadData();
}

//========================= Capture and save code ======================


void SpecificWorker::obtainFeatures()
{
	if(!upperTrunkFound) return;

//	ofstream file;
//	file.open ( "features.txt" , ios::app);

//	timeval curTime;
//	gettimeofday(&curTime, NULL);
//	int milli = curTime.tv_usec / 1000;

//	char buffer [80];
//	strftime(buffer, 80, "%H:%M:%S", localtime(&curTime.tv_sec));
//	char currentTime[84] = "";
//	sprintf(currentTime, "%s:%d", buffer, milli);


	qDebug()<<"Left "<<getElbowAngleVec("Left")<<getShoulderAngleVec("Left");
	qDebug()<<"Right "<<getElbowAngleVec("Right")<<getShoulderAngleVec("Right");
	this->angle1_lcd->display(getElbowAngleVec("Left"));
	this->angle2_lcd->display(getElbowAngleVec("Right"));
	this->height1_lcd->display(getShoulderAngleVec("Left"));
	this->height2_lcd->display(getShoulderAngleVec("Right"));

//	file << currentTime << ";"<< getElbowAngle("Left") << ";" << getShoulderAngle("Left")<<";"<<getElbowAngle("Right")<<";"<<getShoulderAngle("Right")<<"\n";
//	file.close();

}


//void SpecificWorker::calculateAllMetrics()
//{
//	this->cur
//}


//side must be "Right" or "Left"
float SpecificWorker::getElbowAngle(std::string side)
{
	return qRadiansToDegrees(innerModel->getTransform(mapJointMesh[side+"Elbow"])->getRxValue());
}

float SpecificWorker::getShoulderAngle(std::string side)
{
	float shoulderElevation = innerModel->getTranslationVectorTo(mapJointMesh["MidSpine"],mapJointMesh[side+"Shoulder"]).z();
	float elbowElevation = innerModel->getTranslationVectorTo(mapJointMesh["MidSpine"],mapJointMesh[side+"Elbow"]).z();
	float shoulderAngle = innerModel->getTransform(mapJointMesh[side+"Shoulder"])->getRyValue();

	if (side == "Right")
		shoulderAngle = -shoulderAngle;

	if(elbowElevation > shoulderElevation)
		return qRadiansToDegrees((M_PI + shoulderAngle));
	else
		return qRadiansToDegrees(-shoulderAngle);
}

float SpecificWorker::getElbowAngleVec(std::string side)
{

	auto v1  = innerModel->transform(mapJointMesh[side +"Elbow"],mapJointMesh[side+"Hand"]);
	auto v2  = innerModel->transform(mapJointMesh[side +"Elbow"],mapJointMesh[side+"Shoulder"]);


	float angle = getAngleBetweenVectors(v1,v2);

    QPalette palGreen;
    QPalette palRed;
    palRed.setColor(palRed.WindowText, QColor(Qt::darkRed));
    palGreen.setColor(palGreen.WindowText, QColor(Qt::darkGreen));

    if(side =="Left")
    {
        if (angle > 150)
            angle1_lcd->setPalette(palGreen);
        else
            angle1_lcd->setPalette(palRed);
    }

    else
    {
        if (angle > 150)
            angle2_lcd->setPalette(palGreen);
        else
            angle2_lcd->setPalette(palRed);
    }


    return angle;
}

float SpecificWorker::getShoulderAngleVec(std::string side)
{

	auto v1  = innerModel->transform(mapJointMesh["ShoulderSpine"],mapJointMesh[side +"Elbow"]);
	auto v2  = innerModel->transform(mapJointMesh["ShoulderSpine"],mapJointMesh["BaseSpine"]);

    float angle = getAngleBetweenVectors(v1,v2);

    QPalette palGreen;
    QPalette palRed;
    palRed.setColor(palRed.WindowText, QColor(Qt::darkRed));
    palGreen.setColor(palGreen.WindowText, QColor(Qt::darkGreen));

    if(side =="Left")
    {
        if (angle > 80 and angle < 120)
            height1_lcd->setPalette(palGreen);
        else
            height1_lcd->setPalette(palRed);
    }

    else
    {
        if (angle > 80 and angle < 120)
            height2_lcd->setPalette(palGreen);
        else
            height2_lcd->setPalette(palRed);
    }


    return angle;

}


float SpecificWorker::getAngleBetweenVectors(QVec v1, QVec v2)
{
    v1 = v1.normalize();
    v2 = v2.normalize();

    auto prod = v1.dotProduct(v2);
    float angle = acos(prod/(v1.norm2()*v2.norm2()));

    return qRadiansToDegrees(angle);
}

void SpecificWorker::relateJointsMeshes()
{
    mapJointMesh["Neck"] = "XN_SKEL_NECK";

    mapJointMesh["MidSpine"] = "XN_SKEL_TORSO";
    mapJointMesh["ShoulderSpine"] = "XN_SKEL_SHOULDER_SPINE";

    mapJointMesh["LeftShoulder"] = "XN_SKEL_LEFT_SHOULDER";
    mapJointMesh["RightShoulder"] = "XN_SKEL_RIGHT_SHOULDER";

    mapJointMesh["LeftElbow"] = "XN_SKEL_LEFT_ELBOW";
    mapJointMesh["RightElbow"] = "XN_SKEL_RIGHT_ELBOW";

    mapJointMesh["BaseSpine"] = "XN_SKEL_WAIST";

    mapJointMesh["LeftHip"] = "XN_SKEL_LEFT_HIP";
    mapJointMesh["RightHip"] = "XN_SKEL_RIGHT_HIP";

    mapJointMesh["LeftHand"] = "XN_SKEL_LEFT_HAND";
    mapJointMesh["RightHand"] = "XN_SKEL_RIGHT_HAND";

    mapJointMesh["LeftKnee"] = "XN_SKEL_LEFT_KNEE";
    mapJointMesh["RightKnee"] = "XN_SKEL_RIGHT_KNEE";

    mapJointMesh["LeftFoot"] = "XN_SKEL_LEFT_FOOT";
    mapJointMesh["RightFoot"] = "XN_SKEL_RIGHT_FOOT";


}


bool SpecificWorker::checkNecessaryJoints(TPerson &person)
{
	upperTrunkFound = false;
	lowerTrunkFound = false;
	jointListType joints = person.joints;


	for(auto upT : upperTrunk)
	{
		if(!joints.count(upT))
		{
//            qDebug()<< "Falta " << QString::fromStdString(upT);
			upperTrunkFound = false;
			break;
		}
		else
		{
			upperTrunkFound = true;
		}

	}

	for(auto lwT : lowerTrunk)
	{
		if(!joints.count(lwT))
		{
//            qDebug()<< "Falta " << QString::fromStdString(lwT);
			lowerTrunkFound = false;
			break;
		}
		else
		{lowerTrunkFound = true;}

	}

	if(upperTrunkFound or lowerTrunkFound)
		return true;
	else
		return false;

}

bool SpecificWorker::loadTrainingFromFile()
{
	QString fileName = QFileDialog::getOpenFileName(this, tr("Load file"),"",tr("Recordings (*.txt *.avi)"));
	QString jointFile, videoFile;
	if (fileName.size() > 0 and fileName.contains(".txt"))
	{
		jointFile = fileName;
		videoFile = fileName.replace(".txt", ".avi");
	}else if (fileName.size() > 0 and fileName.contains(".avi"))
	{
		videoFile = fileName;
		jointFile = fileName.replace(".avi", ".txt");
	}
	if (not (QFile::exists(videoFile) and QFile::exists(jointFile)))
	{
		QMessageBox::warning(this,tr("Load recorded data problem"),tr("You have to set a valid video/joint file"));
		qDebug() << "Unable to load recorded data, check filename";
		return false;
	}
	loadJointsFromFile(jointFile);
	loadVideoFromFile(videoFile);
	return true;
}
void SpecificWorker::loadJointsFromFile(QString filename)
{
	ifstream file;
	file.open(filename.toStdString());
	std::string line;
	while (std::getline(file, line))
	{
		TPerson person;
		jointListType all_joints;

		vector<string> parts = split(line,"#");

		for (auto p: parts)
		{
			vector<string> joints = split(p," ");

			if(joints.size()== 4)
			{
				joint poses;
				poses.push_back(QString::fromStdString(joints[1]).toFloat());
				poses.push_back(QString::fromStdString(joints[2]).toFloat());
				poses.push_back(QString::fromStdString(joints[3]).toFloat());

				all_joints[joints[0]] = poses;
			}
		}
		person.joints = all_joints;
		if(!checkNecessaryJoints(person))
		{
			qDebug()<<"Necessary joints not found";
		}
		else
		{
			loadedTraining.push_back(person);
		}
	}
}
void SpecificWorker::loadVideoFromFile(QString filename)
{
	videoReader = cv::VideoCapture(filename.toStdString());
	loadVideoFrame(0);
}
void SpecificWorker::loadVideoFrame(int frame_no)
{
	videoReader.set(CV_CAP_PROP_POS_FRAMES, frame_no);
	cv::Mat frame;
	videoReader >> frame;
	QImage img = QImage(frame.ptr(), VIDEO_WIDTH, VIDEO_HEIGHT, QImage::Format_RGB888);
    video_lb->setPixmap(QPixmap::fromImage(img));
}

vector<string> SpecificWorker::split(const string& str, const string& delim)
{
	vector<string> tokens;
	size_t prev = 0, pos = 0;
	do
	{
		pos = str.find(delim, prev);
		if (pos == string::npos) pos = str.length();
		string token = str.substr(prev, pos-prev);
		if (!token.empty()) tokens.push_back(token);
		prev = pos + delim.length();
	}
	while (pos < str.length() && prev < str.length());
	return tokens;
}

void SpecificWorker::recordData()
{
	//video
///TODO	==> //read frame data
cv::Mat frame(VIDEO_WIDTH, VIDEO_HEIGHT, CV_8UC3, cv::Scalar(10, 100, 150));
	videoWriter.write(frame);
	if(visualizeRecording)
	{
		QImage img = QImage(frame.ptr(), VIDEO_WIDTH, VIDEO_HEIGHT, QImage::Format_RGB888);
    	video2_lb->setPixmap(QPixmap::fromImage(img));
	}
	//joints
	fstream jointfile;
	jointfile.open( (this->savePath+".txt").toStdString() , ios::app);
	try
	{
		PersonList users;
//		humantracker_proxy->getUsersList(users);
		if(visualizeRecording)
		{
			for (auto person : users)
			{
				if(checkNecessaryJoints(person.second)) {
					PaintSkeleton(person.second);
				}
			}
		}

		if(users.size()== 0)
			this->status->showMessage("No human detected...");

		for (auto u : users)
		{
			auto id = u.first;
			auto joints = u.second.joints;

			jointfile << id <<"#";

			for (auto j: joints)
			{
				jointfile <<j.first <<" "<<j.second[0] << " " << j.second[1] << " " <<j.second[2];
				jointfile << "#";
			}
		}

		jointfile <<endl;
		this->updateFramesRecorded();
		this->status->showMessage("Saved "+QString::number(this->framesRecorded)+" frames - Visualize = "+QString::number(visualizeRecording));
	}

	catch(...){
		qDebug()<<"no connection to humantracker_proxy";
	}
	jointfile.close();
}


void SpecificWorker::PaintSkeleton (TPerson &person) {
	this->status->showMessage(__FUNCTION__);
	checkNecessaryJoints(person);
	this->status->showMessage(QString::fromStdString(__FUNCTION__)+": Checked necessary joints");
	CalculateJointRotations(person);
	this->status->showMessage(QString::fromStdString(__FUNCTION__)+": Calculated rotations");

	//Se comprueba que si el joint pertenece al tronco X se haya encontrado todo eltronco antes de actualizar
	if(!upperTrunkFound and !lowerTrunkFound)
	{
		this->status->showMessage("Full body not found");
		return;
	}

	for (auto personJoints : person.joints) {

		Pose3D pose;
		string idJoint = personJoints.first;
		if(mapJointRotations.count(idJoint) > 0) {
			QString TypeJoint = mapJointMesh[idJoint];
			auto itUp = std::find(upperTrunk.begin(), upperTrunk.end(), idJoint);
			auto itLw = std::find(lowerTrunk.begin(), lowerTrunk.end(), idJoint);
			if (itUp != upperTrunk.end() and itLw != lowerTrunk.end()) {
				this->status->showMessage("Joint " + QString::fromStdString(idJoint) + " is not upper not lower");
			}

			if (SetPoses(pose, idJoint)) {
				innerModel->updateTransformValues(TypeJoint, pose.x, pose.y, pose.z, pose.rx, pose.ry, pose.rz);
			} else {
				this->status->showMessage("Error updating pose for joint " + QString::fromStdString(idJoint));
			}
		} else{
//			this->status->showMessage("Trying to update not used joint " + QString::fromStdString(idJoint));
		}
	}

//	for (auto dictionaryNamesIt : mapJointMesh) {
//
//		try {
//			Pose3D pose;
//			string idJoint = dictionaryNamesIt.first;
//			QString TypeJoint = dictionaryNamesIt.second;
//			auto joints = person.joints;
//
//
//			if (joints.find(idJoint) != joints.end()) //Si se encuentra el joint
//			{
//
//				if (SetPoses (pose, idJoint))
//				{
////                        qDebug()<< "Actualizando " << QString::fromStdString(idJoint);
//					innerModel->updateTransformValues(TypeJoint,pose.x,pose.y,pose.z,pose.rx,pose.ry,pose.rz);
//				} else{
//					this->status->showMessage("Error updating skeleton for joint "+QString::fromStdString(idJoint));
//				}
//
//			}
//			else
//			{
//				this->status->showMessage(QString::fromStdString(__FUNCTION__)+": "+QString::fromStdString(idJoint)+" not found in person joints");
//			}
//		}
//		catch (...) {
//			this->status->showMessage("Error in PaintSkeleton");
//		}
//
//	}

	innerModel->update();
	innerModelViewer->update();

	osgView->frame();
	osgView->autoResize();

//    innerModel->save("SavedInnerModel.xml");
}


void SpecificWorker::CalculateJointRotations (TPerson &p) {

    RTMat orbbec;

    if (upperTrunkFound)
    {
//        qDebug()<<"-------------------------------- UPPER TRUNK --------------------------------";

        mapJointRotations["MidSpine"] = RTMatFromJointPosition (orbbec,p.joints["MidSpine"],p.joints["ShoulderSpine"], p.joints["MidSpine"], 2);
        mapJointRotations["ShoulderSpine"] = RTMatFromJointPosition (mapJointRotations["MidSpine"],p.joints["ShoulderSpine"],p.joints["Neck"],p.joints["ShoulderSpine"], 2);

        mapJointRotations["Neck"] = RTMatFromJointPosition (mapJointRotations["MidSpine"]*mapJointRotations["ShoulderSpine"],p.joints["Neck"],p.joints["Head"],p.joints["Neck"], 2);

        RTMat LEFT_SHOULDER_PRE_Z =  RTMatFromJointPosition(mapJointRotations["MidSpine"]*mapJointRotations["ShoulderSpine"],p.joints["LeftShoulder"],p.joints["LeftElbow"], p.joints["LeftShoulder"], 2);
        RTMat RIGHT_SHOULDER_PRE_Z = RTMatFromJointPosition(mapJointRotations["MidSpine"]*mapJointRotations["ShoulderSpine"],p.joints["RightShoulder"],p.joints["RightElbow"],p.joints["RightShoulder"], 2);

        RotateTorso (RIGHT_SHOULDER_PRE_Z.getTr(), LEFT_SHOULDER_PRE_Z.getTr());

        mapJointRotations["LeftShoulder"]=RTMatFromJointPosition (mapJointRotations["MidSpine"]*mapJointRotations["ShoulderSpine"],p.joints["LeftShoulder"],p.joints["LeftElbow"],p.joints["LeftShoulder"], 2);
        mapJointRotations["RightShoulder"] = RTMatFromJointPosition(mapJointRotations["MidSpine"]*mapJointRotations["ShoulderSpine"],p.joints["RightShoulder"], p.joints["RightElbow"],p.joints["RightShoulder"], 2);

        mapJointRotations["LeftElbow"]=RTMatFromJointPosition (mapJointRotations["MidSpine"]*mapJointRotations["ShoulderSpine"]*mapJointRotations["LeftShoulder"],p.joints["LeftElbow"],p.joints["LeftHand"],	p.joints["LeftElbow"], 2);
        mapJointRotations["RightElbow"] = RTMatFromJointPosition (mapJointRotations["MidSpine"]*mapJointRotations["ShoulderSpine"]*mapJointRotations["RightShoulder"],p.joints["RightElbow"],p.joints["RightHand"],p.joints["RightElbow"], 2);

        mapJointRotations["LeftHand"] = RTMatFromJointPosition(mapJointRotations["MidSpine"]*mapJointRotations["ShoulderSpine"]*mapJointRotations["LeftShoulder"]*mapJointRotations["LeftElbow"],p.joints["LeftHand"],p.joints["LeftElbow"],p.joints["LeftHand"], 2);
        mapJointRotations["RightHand"] = RTMatFromJointPosition(mapJointRotations["MidSpine"]*mapJointRotations["ShoulderSpine"]*mapJointRotations["RightShoulder"]*mapJointRotations["RightElbow"],p.joints["RightHand"],p.joints["RightElbow"],p.joints["RightHand"], 2);

    }

    if (lowerTrunkFound)
    {
//        qDebug()<<"-------------------------------- LOWER TRUNK --------------------------------";

        mapJointRotations["BaseSpine"]=RTMatFromJointPosition ( mapJointRotations["MidSpine"],p.joints["BaseSpine"],p.joints["MidSpine"] ,p.joints["BaseSpine"], 2);

        mapJointRotations["LeftHip"]=RTMatFromJointPosition (mapJointRotations["MidSpine"]*mapJointRotations["BaseSpine"],p.joints["LeftHip"],p.joints["LeftKnee"],p.joints["LeftHip"], 2);
        mapJointRotations["RightHip"]=RTMatFromJointPosition (mapJointRotations["MidSpine"]*mapJointRotations["BaseSpine"],p.joints["RightHip"],p.joints["RightKnee"],p.joints["RightHip"], 2);

        mapJointRotations["LeftKnee"]=RTMatFromJointPosition (mapJointRotations["MidSpine"]*mapJointRotations["BaseSpine"]*mapJointRotations["LeftHip"],p.joints["LeftKnee"],p.joints["LeftFoot"],p.joints["LeftKnee"], 2);
        mapJointRotations["RightKnee"]=RTMatFromJointPosition (mapJointRotations["MidSpine"]*mapJointRotations["BaseSpine"]*mapJointRotations["RightHip"],p.joints["RightKnee"],p.joints["RightFoot"],p.joints["RightKnee"], 2);

        mapJointRotations["LeftFoot"]=RTMatFromJointPosition(mapJointRotations["MidSpine"]*mapJointRotations["BaseSpine"]*mapJointRotations["LeftHip"]*mapJointRotations["LeftKnee"],p.joints["LeftFoot"],p.joints["LeftKnee"],p.joints["LeftFoot"], 2);
        mapJointRotations["RightFoot"]=RTMatFromJointPosition(mapJointRotations["MidSpine"]*mapJointRotations["BaseSpine"]*mapJointRotations["RightHip"]*mapJointRotations["RightKnee"],p.joints["RightFoot"],p.joints["RightKnee"],p.joints["RightFoot"], 2);

    }

}

RTMat SpecificWorker::RTMatFromJointPosition (RTMat rS,jointPos p1, jointPos p2, jointPos translation, int axis) {

	bool XClockWise=true, YClockWise=true, ZClockWise=true;
	float alpha, beta, gamma;

	RTMat rt(XClockWise,YClockWise, ZClockWise);
	QVec p1h = QVec::vec4(p1[0], p1[1], p1[2], 1);
	QVec p2h = QVec::vec4(p2[0], p2[1], p2[2],1);
	QVec translationH = QVec::vec4(translation[0], translation[1], translation[2],1);

	QMat aux = rS;
	aux = aux.invert();
	QVec translationT = aux * translationH;
	QVec p1t = aux * p1h;
	QVec p2t = aux * p2h;
	QVec vTh = p2t - p1t;
	QVec v= vTh.normalize();

	///por filas
	switch(axis)
	{
		case 0:
			alpha = 0;
			if (YClockWise) beta = atan2(-v.z(),v.x());
			else beta = atan2(v.z(),v.x());
			if (ZClockWise) gamma = asin(-v.y());
			else gamma = asin(v.y());
			break;
		case 1:
			if (XClockWise) alpha = atan2(v.z(),v.y());
			else alpha = atan2(-v.z(),v.y());
			beta = 0;
			if (ZClockWise) gamma = asin(v.x());
			else gamma = asin(-v.x());
			break;
		case 2:
			if (XClockWise) alpha =  atan2(-v.y(),v.z());
			else alpha =  atan2(v.y(),v.z());

			if (YClockWise) beta = asin(v.x());
			else beta = asin(-v.x());
			gamma = 0;
			break;
	}

	rt.setRT(alpha,beta,gamma,translationT);
	return rt;
}


bool SpecificWorker::RotateTorso (const QVec &lshoulder, const QVec &rshoulder) {

//	qDebug()<<__FUNCTION__;

	QVec eje = lshoulder - rshoulder;	//Calculamos el eje que va de un hombro a otro

	eje.normalize();

	if(eje.x()==0) {
		return false;
	}

	float angulo = atan2(eje.y(),eje.x());	//Calculamos el giro necesario para alinear los hombros con el eje (arcotangente de y/x)

	mapJointRotations["MidSpine"].setRZ(angulo); // Aplicamos dicho giro al eje Z del torso

	return true;
}

bool SpecificWorker::SetPoses (Pose3D &pose, string joint) {

	if (mapJointRotations.find(joint) != mapJointRotations.end()) //Si no se encuentra el joint
	{
		pose.x = mapJointRotations[joint].getTr().x();
		pose.y = mapJointRotations[joint].getTr().y();
		pose.z = mapJointRotations[joint].getTr().z();

		pose.rx = mapJointRotations[joint].getRxValue();
		pose.ry = mapJointRotations[joint].getRyValue();
		pose.rz = mapJointRotations[joint].getRzValue();

		return true;
	}

	else
	{
		qDebug()<<" NO EXISTE "<< QString::fromStdString(joint);
		return false;
	}
}