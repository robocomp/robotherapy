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

/**
       \brief
       @author authorname
*/



#ifndef SPECIFICWORKER_H
#define SPECIFICWORKER_H

#include <chart.h>
#include <genericworker.h>
#include <innermodel/innermodel.h>
#include <QTimer>
#include <QMetaType>
#include <fstream>
#include <unistd.h>
#include <qmat/qrtmat.h>
#include <QMessageBox>
#include <QFileDialog>
#include <opencv2/opencv.hpp>

#ifdef USE_QTGUI
	#include <osgviewer/osgview.h>
	#include <innermodel/innermodelviewer.h>
#endif

#define VIDEO_WIDTH 640
#define VIDEO_HEIGHT 480

struct Pose3D
{
	float x;
	float y;
	float z;
	float rx;
	float ry;
	float rz;
};

class SpecificWorker : public GenericWorker
{

	map<string,QString> mapJointMesh; //Mapa que relaciona el nombre de las partes con los meshs
	map<string,RTMat> mapJointRotations; //Mapa que guarda las rotaciones calculadas
	map<string,std::vector<float>> currentMetrics; //Map with calculated metrics

	using jointPos = std::vector<float> ;
	vector<string> upperTrunk = {"MidSpine","ShoulderSpine", "Head", "Neck", "LeftShoulder", "RightShoulder","LeftElbow","RightElbow" , "LeftHand", "RightHand" };
	vector<string> lowerTrunk = {"MidSpine", "BaseSpine" ,"LeftHip","RightHip","LeftKnee","RightKnee","LeftFoot","RightFoot" };

	struct sincPerson
    {
	    std::string currentTime;
        RoboCompHumanTrackerJointsAndRGB::TPerson personDet;
	    cv::Mat *image;
    };

	vector<sincPerson> loadedTraining;

	bool upperTrunkFound = false;
	bool lowerTrunkFound = false;

Q_OBJECT
public:
	SpecificWorker(TuplePrx tprx);
	~SpecificWorker();
	bool setParams(RoboCompCommonBehavior::ParameterList params);
	void forwardFrames(int numFrames);


public slots:
//	void compute();
	void initialize(int period);
    //Specification slot methods State Machine
    void sm_record();
    void sm_playback();
    void sm_initialize();
    void sm_finalize();
    void sm_pause();
    void sm_stop();
    void sm_processFrame();
    void sm_waitingStart();
    void sm_showTherapy();
    void sm_loadFiles();
//--------------------

	void loadFileClicked();
    void nextFrame();
    void next5Frames();
    void prevFrame();
    void prev5Frames();
    void startFrame();
    void endFrame();
    void playTimerTimeout();
    void start_playing();
    void stop_playing();
    void pause_playing();
    void reverse_playing(int state);
    void record();
    void visualizeRecordingToggled(bool);

    void framesSliderMoved(int value);
    void changePlayFps(double value);
    void setEnabledPlayControls(bool enabled);
    void load_chart();
    void recordData(RoboCompHumanTrackerJointsAndRGB::MixedJointsRGB mixedData);


signals:
	void newMixDetected(RoboCompHumanTrackerJointsAndRGB::MixedJointsRGB mixedData);

private:
	QSettings *settings;
	osgGA::TrackballManipulator *manipulator;
	Chart *chart;
	//record
	bool recording;
	bool visualizeRecording=false;
	int framesRecorded;
	QString savePath;
	cv::VideoWriter videoWriter;
	//playback
	cv::VideoCapture videoReader;

	std::shared_ptr<InnerModel> innerModel;
	QTimer *playTimer;
	bool playForward;
	float playFps;
	void updateFramesRecorded();
	void restartPlayTimer();
	void obtainFeatures();
	float getShoulderAngle(std::string side);
	float getElbowAngle(std::string side);
	float getShoulderAngleVec(std::string side);
	float getElbowAngleVec(std::string side);
	float getAngleBetweenVectors(QVec v1, QVec v2);
	float getDeviation(std::string part);
	void saveActualFrameMetrics(float time);
	void initializeMetrics();
	void closeEvent(QCloseEvent *event);
//	void calculateAllMetrics();


//	=============== Capture Methods ===========
	void HumanTrackerJointsAndRGB_newPersonListAndRGB(RoboCompHumanTrackerJointsAndRGB::MixedJointsRGB mixedData);
	void relateJointsMeshes();
	void PaintSkeleton (RoboCompHumanTrackerJointsAndRGB::TPerson &person);
	void CalculateJointRotations (RoboCompHumanTrackerJointsAndRGB::TPerson &person);
	RTMat RTMatFromJointPosition (RTMat rS, jointPos p1, jointPos p2, jointPos translation, int axis); //This method calculates the rotation of a Joint given some points
	bool RotateTorso (const QVec &lshoulder, const QVec &rshoulder); //This method allows to rotate the torso from the position and rotation of the shoulders
	bool SetPoses (Pose3D &pose, string joint);
	bool checkNecessaryJoints(RoboCompHumanTrackerJointsAndRGB::TPerson &person);
	bool loadTrainingFromFile();
	int loadJointsFromFile(QString filename);
	int loadVideoFromFile(QString filename);
	void loadVideoFrame(int frame);
	vector<string>split(const string& str, const string& delim);
//	void recordData(RoboCompHumanTrackerJointsAndRGB::MixedJointsRGB mixedData);
	void printJointsFromAstra();
#ifdef USE_QTGUI
	OsgView *osgView;
	InnerModelViewer *innerModelViewer;

#endif

};

#endif
