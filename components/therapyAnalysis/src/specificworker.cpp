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
Q_DECLARE_METATYPE(RoboCompHumanTrackerJointsAndRGB::MixedJointsRGB)
SpecificWorker::SpecificWorker(TuplePrx tprx) : GenericWorker(tprx)
{
	qRegisterMetaType<RoboCompHumanTrackerJointsAndRGB::MixedJointsRGB>("MixedJointsRGB");

	innerModelViewer = NULL;
	osgView = new OsgView(this);
	this->osgLayout->addWidget(osgView);
	this->manipulator = new osgGA::TrackballManipulator;
	osgView->setCameraManipulator(manipulator);

	// Restore previous camera position
	settings = new QSettings("RoboComp", "TherapyAnalysis");

	//restore matrix view
	QStringList l = settings->value("matrix").toStringList();
	if (l.size() > 0)
	{
		osg::Matrixd m;
		for (int i=0; i<4; i++ )
		{
			for (int j=0; j<4; j++ )
			{
				m(i,j)=l.takeFirst().toDouble();
			}
		}
		manipulator->setByMatrix(m);
	}
	else
	{
		osg::Vec3d eye(osg::Vec3(0, 0, -2000));
		osg::Vec3d center(osg::Vec3(0,0,0));
		osg::Vec3d up(osg::Vec3(0.,1.,0.));
		manipulator->setHomePosition(eye, center, up, false);
		manipulator->setByMatrix(osg::Matrixf::lookAt(eye,center,up));
	}

    connect(this, SIGNAL(newMixDetected(RoboCompHumanTrackerJointsAndRGB::MixedJointsRGB)), this, SLOT(recordData(RoboCompHumanTrackerJointsAndRGB::MixedJointsRGB)));
	this->relateJointsMeshes();


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
	try
	{
		RoboCompCommonBehavior::Parameter par = params.at("InnerModelPath");
		std::string innermodel_path = par.value;
		innerModel = std::make_shared<InnerModel>(innermodel_path);
	}
	catch(std::exception e) { qFatal("Error reading config params %s",e.what()); }


#ifdef USE_QTGUI
	innerModelViewer = new InnerModelViewer (innerModel, "root", osgView->getRootGroup(), true);
#endif

	therapyAnalysisMachine.start();
	return true;
}

void SpecificWorker::initialize(int period)
{
	std::cout << "Initialize worker" << std::endl;
	this->Period = period;
	timer.start(Period);
}


//void SpecificWorker::compute()
//{
//#ifdef USE_QTGUI
//	if (innerModelViewer) innerModelViewer->update();
//	osgView->frame();
//#endif
//}



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


//void SpecificWorker::playback_mode() {
//
//	this->stackedWidget->setCurrentIndex(0);

//	this->recordMode_action->setEnabled(true);
//	this->osgLayout->addWidget(this->osgView);
//}
//
//void SpecificWorker::record_mode() {
//
//	this->stackedWidget->setCurrentIndex(1);
//	this->playbackMode_action->setEnabled(true);
//	this->recordMode_action->setEnabled(false);
//	this->osgLayout_2->addWidget(this->osgView);
//}

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
//				this->record_mode();
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
		this->videoWriter = cv::VideoWriter( (this->savePath+".avi").toStdString(), CV_FOURCC('M','J','P','G'), 30, cv::Size(VIDEO_WIDTH, VIDEO_HEIGHT));

		this->recording = true;
		this->filePath_lnedit->setEnabled(false);
		this->record_btn->setText("Stop");
		qDebug()<<"Starting Recording...";
	}
}

void SpecificWorker::updateFramesRecorded()
{
	//cout<<"Recorded "<<framesRecorded<<endl;
	this->framesRecorded = this->framesRecorded + 1;
	this->framesRecorded_lcd->display(this->framesRecorded);
}

void SpecificWorker::visualizeRecordingToggled(bool state)
{
	this->visualizeRecording = state;
}

void SpecificWorker::loadFileClicked()
{
    printf("LoadFileClicked");

	if (this->loadTrainingFromFile())
	{
		if(this->loadedTraining.size()>0)
		{
//			this->playback_mode();
			this->setEnabledPlayControls(true);
			qDebug()<<"Setting maximum to"<<this->loadedTraining.size()-1<<endl;
			this->frames_slider->setMaximum(this->loadedTraining.size()-1);
			this->frames_slider->setValue(0);
			this->loadVideoFrame(0);
		}
		else
		{
				QMessageBox::warning(this,tr("File load problem"),tr("No pose loaded from files.\nPlease, check these are valid files\n"));
		}
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
		auto person = this->loadedTraining[value].personDet;
		this->PaintSkeleton(person);
		//TODO: Remove. Only for Debug
//		this->innerModel->save("lapatata.xml");
		this->loadVideoFrame(value);
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
	qDebug()<<"LoadChart clicked";
	QWidget *widget = new QWidget();
	widget->setAttribute( Qt::WA_QuitOnClose, false );
	chart = new Chart(widget);
	widget->show();
	chart->loadData(this->currentMetrics);
//	chart->saveChart("prueba");



}



void SpecificWorker::closeEvent(QCloseEvent *event)
{
	event->accept();
	osg::Matrixd m = manipulator->getMatrix();
	QString s="";
	QStringList l;
	for (int i=0; i<4; i++ )
	{
		for (int j=0; j<4; j++ )
		{
			l.append(s.number(m(i,j)));
		}
	}
	settings->setValue("matrix", l);
	settings->sync();

}

//========================= Capture and save code ======================


void SpecificWorker::obtainFeatures()
{
    if (!upperTrunkFound) return;

//	ofstream file;
//	file.open ( "features.txt" , ios::app);

//	timeval curTime;
//	gettimeofday(&curTime, NULL);
//	int milli = curTime.tv_usec / 1000;

//	char buffer [80];
//	strftime(buffer, 80, "%H:%M:%S", localtime(&curTime.tv_sec));
//	char currentTime[84] = "";
//	sprintf(currentTime, "%s:%d", buffer, milli);


//	qDebug()<<"Left "<<getElbowAngleVec("Left")<<getShoulderAngleVec("Left");
//	qDebug()<<"Right "<<getElbowAngleVec("Right")<<getShoulderAngleVec("Right");

    this->angle1_lcd->display(getArmFlexion("Left"));
    this->angle2_lcd->display(getArmFlexion("Right"));
    this->height1_lcd->display(getArmElevation("Left"));
    this->height2_lcd->display(getArmElevation("Right"));

    this->spinedev_lcd->display(getDeviation("Spine"));
    this->shoulderdev_lcd->display(getDeviation("Shoulder"));
    this->hipsdev_lcd->display(getDeviation("Hip"));
    this->kneesdev_lcd->display(getDeviation("Knee"));


}

//side must be "Right" or "Left"
float SpecificWorker::getArmFlexion(std::string side)
{

    vector<string> jointList = {side + "Elbow", side + "Shoulder", side + "Hand"};

	if (!checkJointList(jointList))
	{
		return std::numeric_limits<T>::quiet_NaN();
	}

	auto elbow = innerModel->transform("world", mapJointMesh[side +"Elbow"]);
	auto shoulder = innerModel->transform("world", mapJointMesh[side +"Shoulder"]);
	auto hand = innerModel->transform("world", mapJointMesh[side +"Hand"]);

//	auto elbow = QVec::vec3(currentJoints[side + "Elbow"][0],currentJoints[side + "Elbow"][1],currentJoints[side + "Elbow"][2]);
//	auto shoulder = QVec::vec3(currentJoints[side + "Shoulder"][0],currentJoints[side + "Shoulder"][1],currentJoints[side + "Shoulder"][2]);
//	auto hand = QVec::vec3(currentJoints[side + "Hand"][0], currentJoints[side + "Hand"][1], currentJoints[side + "Hand"][2]);

    auto v1 = elbow - hand;
    auto v2 = shoulder - elbow;

    return getAngleBetweenVectors(v1,v2);

}

float SpecificWorker::getLegFlexion(std::string side)
{

    vector<string> jointList = {side + "Knee", side + "Hip", side + "Foot"};

    if (!checkJointList(jointList))
    {
		return std::numeric_limits<T>::quiet_NaN();
    }

    auto knee = innerModel->transform("world", mapJointMesh[side+"Knee"]);
    auto hip = innerModel->transform("world", mapJointMesh[side+"Hip"]);
    auto foot = innerModel->transform("world", mapJointMesh[side+"Foot"]);


//    auto knee = QVec::vec3(currentJoints[side + "Knee"][0],currentJoints[side + "Knee"][1],currentJoints[side + "Knee"][2]);
//    auto hip = QVec::vec3(currentJoints[side + "Hip"][0],currentJoints[side + "Hip"][1],currentJoints[side + "Hip"][2]);
//    auto foot = QVec::vec3(currentJoints[side + "Foot"][0], currentJoints[side + "Foot"][1], currentJoints[side + "Foot"][2]);

    auto v1 = knee - foot;
    auto v2 = hip - foot;

    return getAngleBetweenVectors(v1, v2);
}

float SpecificWorker::getArmElevation(std::string side)
{
	vector<string> jointList = {side + "Elbow", side + "Shoulder"};

	if (!checkJointList(jointList))
	{
		return std::numeric_limits<T>::quiet_NaN();
	}

    auto elbow = innerModel->transform("world",mapJointMesh[side +"Elbow"]);
    auto shoulder = innerModel->transform("world",mapJointMesh[side +"Shoulder"]);

//	auto elbow = QVec::vec3(currentJoints[side + "Elbow"][0],currentJoints[side + "Elbow"][1],currentJoints[side + "Elbow"][2]);
//	auto shoulder = QVec::vec3(currentJoints[side + "Shoulder"][0],currentJoints[side + "Shoulder"][1],currentJoints[side + "Shoulder"][2]);
    auto vertical =  QVec::vec3(shoulder.x(),elbow.y(),shoulder.z());

    QVec v1 = shoulder - elbow;
    QVec v2 = shoulder - vertical;


    return getAngleBetweenVectors(v1,v2);

}

float SpecificWorker::getLegElevation(std::string side)
{

	vector<string> jointList = {side + "Knee", side + "Hip"};

	if (!checkJointList(jointList))
	{
		return std::numeric_limits<T>::quiet_NaN();
	}

    auto knee = innerModel->transform("world",mapJointMesh[side +"Knee"]);
    auto hip = innerModel->transform("world",mapJointMesh[side +"Hip"]);
//	auto knee = QVec::vec3(currentJoints[side + "Knee"][0],currentJoints[side + "Knee"][1],currentJoints[side + "Knee"][2]);
//	auto hip = QVec::vec3(currentJoints[side + "Hip"][0],currentJoints[side + "Hip"][1],currentJoints[side + "Hip"][2]);
    auto vertical =  QVec::vec3(hip.x(),knee.y(),hip.z());

    QVec v1 = hip - knee;
    QVec v2 = hip - vertical;


    return getAngleBetweenVectors(v1,v2);

}

//part must be Shoulder, Hip, Knee or Spine
float SpecificWorker::getDeviation(std::string part)
{
    float angle;

    if(part == "Spine")
    {
		vector<string> jointList = {"BaseSpine", "ShoulderSpine"};

		if (!checkJointList(jointList))
		{
			return std::numeric_limits<T>::quiet_NaN();
		}

		auto baseS = innerModel->transform("world",mapJointMesh["BaseSpine"]);
		auto upperS = innerModel->transform("world",mapJointMesh["ShoulderSpine"]);

//		auto baseS = QVec::vec3(currentJoints["BaseSpine"][0],currentJoints["BaseSpine"][1],currentJoints["BaseSpine"][2]);
//		auto upperS = QVec::vec3(currentJoints["ShoulderSpine"][0],currentJoints["ShoulderSpine"][1],currentJoints["ShoulderSpine"][2]);

        auto vertical =  QVec::vec3(upperS.x(),baseS.y(),upperS.z());

        QVec v1 = upperS- baseS;
        QVec v2 = upperS - vertical;

        return getAngleBetweenVectors(v1,v2);
    }

    else
    {
		vector<string> jointList = {"Left" + part, "Right" + part};

		if (!checkJointList(jointList))
		{
			return std::numeric_limits<T>::quiet_NaN();
		}


        auto left = innerModel->transform("world",mapJointMesh["Left"+ part]);
        auto right = innerModel->transform("world",mapJointMesh["Right"+ part]);

//		auto left = QVec::vec3(currentJoints["Left" + part][0],currentJoints["Left" + part][1],currentJoints["Left" + part][2]);
//		auto right = QVec::vec3(currentJoints["Right" + part][0],currentJoints["Right" + part][1],currentJoints["Right" + part][2]);

        auto horizontal = QVec::vec3(right.x(),left.y(),right.z());


        QVec v1 = left - right ;
        QVec v2 = left - horizontal;

        return getAngleBetweenVectors(v1,v2);
    }


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

bool SpecificWorker::checkJointList(vector<string> list)
{
    for (auto joint: list)
    {
        if (!currentJoints.count(joint))  // joint is  not found
        {
            return false;
        }
    }

    return true;
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
	}
	else if (fileName.size() > 0 and fileName.contains(".avi"))
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
	//Load from joints file needs to be executed before load video becuause it creates the main structure
	int n_joint_frames = loadJointsFromFile(jointFile);
	int n_video_frames = loadVideoFromFile(videoFile);
	if(n_joint_frames != n_video_frames)
	{
		this->status->showMessage("WARNING: Loaded "+QString::number(n_joint_frames)+" Joint frames vs "+QString::number(n_video_frames)+" Video Frames. It can be a problem.");
//		QMessageBox::warning(this,tr("Files loaded problem"),"Incoherent number of frames for video and joints ("+QString::number(n_video_frames)+", "+QString::number(n_joint_frames)+")",
//			QMessageBox::Ok,QMessageBox::Ok );
	}
	return true;
}

//Clear metrics structure and create new one
void SpecificWorker::initializeMetrics()
{
	currentMetrics.clear();
	currentMetrics["Time"] = std::vector<float>();
	currentMetrics["LeftArmFlexion"] = std::vector<float>();
	currentMetrics["RightArmFlexion"] = std::vector<float>();
    currentMetrics["LeftArmElevation"] = std::vector<float>();
    currentMetrics["RightArmElevation"] = std::vector<float>();
    currentMetrics["LeftLegFlexion"] = std::vector<float>();
    currentMetrics["RightLegFlexion"] = std::vector<float>();
    currentMetrics["LeftLegElevation"] = std::vector<float>();
    currentMetrics["RightLegElevation"] = std::vector<float>();
    currentMetrics["SpineDeviation"] = std::vector<float>();
	currentMetrics["ShoulderDeviation"] = std::vector<float>();
	currentMetrics["HipDeviation"] = std::vector<float>();
	currentMetrics["KneeDeviation"] = std::vector<float>();

}

void SpecificWorker::saveActualFrameMetrics(float time){

	currentMetrics["Time"].push_back(float(time));

	currentMetrics["LeftArmFlexion"].push_back(getArmFlexion("Left"));
	currentMetrics["RightArmFlexion"].push_back(getArmFlexion("Right"));

	currentMetrics["LeftLegFlexion"].push_back(getLegFlexion("Left"));
	currentMetrics["RightLegFlexion"].push_back(getLegFlexion("Right"));

	currentMetrics["LeftArmElevation"].push_back(getArmElevation("Left"));
	currentMetrics["RightArmElevation"].push_back(getArmElevation("Right"));

    currentMetrics["LeftLegElevation"].push_back(getLegElevation("Left"));
    currentMetrics["RightLegElevation"].push_back(getLegElevation("Right"));

	currentMetrics["SpineDeviation"].push_back(getDeviation("Spine"));
	currentMetrics["ShoulderDeviation"].push_back(getDeviation("Shoulder"));
	currentMetrics["HipDeviation"].push_back(getDeviation("Hip"));
	currentMetrics["KneeDeviation"].push_back(getDeviation("Knee"));
}

int SpecificWorker::loadJointsFromFile(QString filename)
{
	ifstream file;
	file.open(filename.toStdString());
	std::string line;
	//metrics
	initializeMetrics();
	while (std::getline(file, line))
	{
	    currentJoints.clear();
		sincPerson persontoload;
		TPerson person;
		jointListType all_joints;
		vector<string> parts = split(line,"#");
		long int currTime = std::stol(parts[0]);
		static long int firstTime = currTime;
		persontoload.currentTime = currTime;
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
        currentJoints = all_joints;

		persontoload.personDet = person;
		loadedTraining.push_back(persontoload);
		//calcule innerModel and save Metrics
		this->PaintSkeleton(person);
		saveActualFrameMetrics((currTime-firstTime)/1000.);
	}
	return int(loadedTraining.size());
}
int SpecificWorker::loadVideoFromFile(QString filename)
{
	videoReader = cv::VideoCapture(filename.toStdString());
	int frame_pos = 0;

	for(;;)
	{
		cv::Mat frame;
		videoReader >> frame;
		if (!frame.empty()) {
			if(frame_pos < this->loadedTraining.size())
			{
				cv::cvtColor(frame, frame, cv::COLOR_BGR2RGB);
				//TODO: Can be obtimized?
				loadedTraining[frame_pos].image= new  cv::Mat();
				frame.copyTo(*loadedTraining[frame_pos].image);
//				qDebug()<<"Loaded video frame"<<frame_pos<<endl;
				frame_pos+=1;
			}
			else{
				this->status->showMessage("WARNING: There's more video frames than joint frames. Truncating");
				break;
			}
		}
		else{
			break;
		}
	}
//	qDebug()<<"Finished loading video"<<endl;
//	int prop_length = int(videoReader.get(cv::CAP_PROP_FRAME_COUNT));
	return frame_pos;
}

void SpecificWorker::loadVideoFrame(int frame_no)
{
//	videoReader.set(CV_CAP_PROP_POS_FRAMES, frame_no);
//	cv::Mat frame;
//	videoReader >> frame;
//	if(!frame.empty()) {
//		cv::cvtColor(frame, frame, cv::COLOR_BGR2RGB);
//		QImage img = QImage(frame.ptr(), VIDEO_WIDTH, VIDEO_HEIGHT, QImage::Format_RGB888);
//		video_lb->setPixmap(QPixmap::fromImage(img));
//	}
	if(frame_no < this->loadedTraining.size())
	{
		cv::Mat *frame = this->loadedTraining[frame_no].image;
		QImage img = QImage(frame->ptr(), VIDEO_WIDTH, VIDEO_HEIGHT, QImage::Format_RGB888);
		video_lb->setPixmap(QPixmap::fromImage(img));
	}
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


void SpecificWorker::recordData(RoboCompHumanTrackerJointsAndRGB::MixedJointsRGB mixedData)
{
qDebug()<<"Data"<<mixedData.rgbImage.height<<mixedData.rgbImage.width<<mixedData.persons.size();
qDebug()<<"timeStamp"<<mixedData.timeStamp<<"image size"<<mixedData.rgbImage.image.size();
	if(mixedData.rgbImage.height == 0 or mixedData.rgbImage.width == 0)
	{
		qDebug()<<"Invalid rgd frame";
		return;
	}
	//video
	cv::Mat frame(mixedData.rgbImage.height, mixedData.rgbImage.width, CV_8UC3,  &(mixedData.rgbImage.image)[0]);
	cv::cvtColor(frame, frame, CV_BGR2RGB);
	videoWriter.write(frame);

	if(visualizeRecording)
	{
		QImage img = QImage(&(mixedData.rgbImage.image)[0], VIDEO_WIDTH, VIDEO_HEIGHT, QImage::Format_RGB888);
    	video_lb->setPixmap(QPixmap::fromImage(img));
	}
	//joints
	fstream jointfile;
	jointfile.open( (this->savePath+".txt").toStdString() , ios::app);
	jointfile << mixedData.timeStamp <<"#";
	try
	{
		PersonList users = mixedData.persons;
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
//		this->status->showMessage("Saved "+QString::number(this->framesRecorded)+" frames - Visualize = "+QString::number(visualizeRecording));
	}
	catch(...){
		qDebug()<<"no connection to humantracker_proxy";
	}
	jointfile.close();
}


void SpecificWorker::PaintSkeleton (RoboCompHumanTrackerJointsAndRGB::TPerson &person) {
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


void SpecificWorker::CalculateJointRotations (RoboCompHumanTrackerJointsAndRGB::TPerson &p) {

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

//--------------State Machine methods------------------

void SpecificWorker::sm_initialize()
{
    std::cout<<"Entered initial state initialize"<<std::endl;

    playTimer = new QTimer();
    framesRecorded = 0;
    playForward = true;
    recording = false;
    this->stop_playing();
    auto palette = this->angle1_lcd->palette();
    palette.setColor(palette.WindowText, QColor(Qt::darkRed));

    this->angle1_lcd->setPalette(palette);
    this->angle2_lcd->setPalette(palette);
    this->height1_lcd->setPalette(palette);
    this->height2_lcd->setPalette(palette);
    this->spinedev_lcd->setPalette(palette);
    this->shoulderdev_lcd->setPalette(palette);
    this->hipsdev_lcd->setPalette(palette);
    this->kneesdev_lcd->setPalette(palette);



    connect(this->record_btn, SIGNAL(clicked()), this, SLOT(record()));
    connect(this->visualizeRecording_chck, SIGNAL(toggled(bool)), this, SLOT(visualizeRecordingToggled(bool)));

    connect(this->playback_action, SIGNAL(triggered()), this, SIGNAL(t_record_to_playback()));
    connect(this->record_action, SIGNAL(triggered()),this, SIGNAL(t_playback_to_record()));

    emit this->t_initialize_to_playback();


}

void SpecificWorker::sm_closeApp()
{
    std::cout<<"Entered final state closeApp"<<std::endl;
}

void SpecificWorker::sm_record()
{
	std::cout<<"Entered state record"<<std::endl;
	recordMode = true;
    this->playback_gBox->hide();
    this->record_gBox->show();

    this->playback_action->setEnabled(true);
    this->record_action->setEnabled(false);

}


//------------Playback sub states----------------
void SpecificWorker::sm_playback()
{
	std::cout<<"Entered state playback"<<std::endl;
	recordMode = false;
    playFps = this->fps_spnbox->value();
	this->stop_playing();

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

    connect(this->reverse_chck, SIGNAL(stateChanged(int)), this, SLOT(reverse_playing(int)));
    connect(this->frames_slider, SIGNAL(valueChanged(int)), this, SLOT(framesSliderMoved(int)));
    connect(this->fps_spnbox, SIGNAL(valueChanged(double)), this, SLOT(changePlayFps(double)));
    connect(this->chart_pb, SIGNAL(clicked()), this, SLOT(load_chart()));


    this->playback_gBox->show();
    this->record_gBox->hide();

    this->playback_action->setEnabled(false);
    this->record_action->setEnabled(true);

//	this->setEnabledPlayControls(false);

}

void SpecificWorker::sm_loadFiles()
{
    std::cout<<"Entered state loadFiles"<<std::endl;


}

void SpecificWorker::sm_showTherapy()
{
	std::cout<<"Entered state showTherapy"<<std::endl;
}



//subscribesToCODE
void SpecificWorker::HumanTrackerJointsAndRGB_newPersonListAndRGB(RoboCompHumanTrackerJointsAndRGB::MixedJointsRGB mixedData)
{
	if(recording)
	{
		emit newMixDetected(mixedData);
	}

}
