//therapyComp//

/*
 *    Copyright (C) 2006-2010 by RoboLab - University of Extremadura
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

#ifndef SPECIFICWORKER_H
#define SPECIFICWORKER_H

#include "genericworker.h"

#include <opencv/cv.h>//
#include <opencv/ml.h> //Incluye CvkNearest
#include <opencv/cxcore.h>//
#include <opencv/highgui.h>//

#include "opencv2/ml/ml.hpp"//
#include "opencv2/highgui/highgui.hpp"//

#include <rcdraw/rcdraw.h> //en robocomp/classes//
#include <iostream>//
#include <stdio.h>//
#include <../../opt/robocomp/include/innermodel/innermodel.h>//

#include "MSKBody.h"
#include "innermodel/innermodel.h"//
#include <qmat/qrtmat.h>//

#include <osgviewer/osgview.h>
#include <innermodel/innermodelviewer.h>

#include <math.h>//
#include <qt4/QtGui/QFrame>//
#include <QTime>//


#define NFRAMES 3
#define PI 3.14159
#define NCHARACTERICTICS 12
#define NUMBERLEVEL 5

/**
       \brief
       @author authorname
*/


class SpecificWorker : public GenericWorker {
  
  
  Q_OBJECT
  
	map<string,RoboCompMSKBody::JointType> dictionaryEnum; //Mapa que relaciona el nombre de las partes con los mesh
	
	map<string,RTMat> mapJointRotations; //Mapa que guarda las rotaciones calculadas
	
	map<string,QString> dictionaryNames; //Mapa que relaciona el nombre de las partes con los meshs
  

  public:

	SpecificWorker(MapPrx& mprx); //Constructor	
	~SpecificWorker(); //Destructor	
	
	//readFromfile
	QTime time;
	QFile file;
	QTextStream in;
	bool reading;
	
	RoboCompMSKBody::PersonList personList;
	
	//SkeletonPoint es una estructura definida en MSKBody que contiene tres float para almacenar los puntos del esqueleto
	RoboCompMSKBody::SkeletonPoint *RightHand;
	RoboCompMSKBody::SkeletonPoint *LeftHand;
	RoboCompMSKBody::SkeletonPoint *RightElbow;
	RoboCompMSKBody::SkeletonPoint *LeftElbow;
	RoboCompMSKBody::SkeletonPoint *RightShoulder;
	RoboCompMSKBody::SkeletonPoint *LeftShoulder;
	RoboCompMSKBody::SkeletonPoint *Chest;
	RoboCompMSKBody::SkeletonPoint *Headd;
	RoboCompMSKBody::SkeletonPoint *RightHip;
	RoboCompMSKBody::SkeletonPoint *LeftHip;
	RoboCompMSKBody::SkeletonPoint *RightFoot;
	RoboCompMSKBody::SkeletonPoint *LeftFoot;
	
	int m, p;
	int iteration;
	int t;
	
	float QoM, QoMrh, QoMlh, QoMre, QoMle, QoMc, QoMh;
	float QoMRightArm, QoMLeftArm, QoMGeneric;
	float ContractionArea;
	
	
	float AngleRightArm, AngleLeftArm;
	//float DifferenceShoulderHandRightY, DifferenceShoulderHandLeftY, DifferenceHipHandRightY, DifferenceHipHandLeftY, DifferenceChestHandRightZ, DifferenceChestHandLeftZ;
	float DepthRightHand, DepthLeftHand;
	float HeightRightHand, HeightLeftHand;
	float LengthArm;
	float DistanceShoulderElbow;
	float DistanceElbowHand;
	
	float ExerciseToDo [NUMBERLEVEL];
	int Level;
	int SequenceLevel;
	int KeepingExercise;
	int NextExercise;
	int ActualExerciseNotRepeated;
	
	char NumberOfExerciseString[15000];
//	QString Level;
	QString UserName;
//	char DifficultyLevel[500];
		
//	bool LevelChosen;
	bool FirstIteration;
	bool Trained;
	bool ReferenceAngles, ReferenceHeight, Reference;
	
	bool PushedExercise0;
	bool PushedExercise1;
	bool PushedExercise2;
	bool PushedExercise3;
	bool PushedExercise4;
	bool ExerciseCorrect;
	bool PassExercise;
	bool AskNewExercise;
	bool SequenceDone;
	
	char str[15000];
	
	InnerModel *innerModel;
	OsgView *osgView;
	InnerModelViewer *imv;
	
	FILE *FileFeatures, *FilePositions, *FileActualExercise, *FileTrain, *FileLabels, *FileAccuracyLabels, *FileAccuracyResults;
	FILE *FileExercise1, *FileExercise2, *FileExercise3, *FileExercise4, *FileAccuracyData; //Punteros a los archivos de texto
	
	cv::KNearest KNN;
	CvSVM SVM;
	//CvANN_MLP MLP; 
	CvNormalBayesClassifier Bayes;
	//cv::NormalBayesClassifier NormalBayes;
	CvDTree DTree;

		
  private:

	
  public slots:
	
	void compute(); 
	
	bool setParams(RoboCompCommonBehavior::ParameterList params);
	
	void ReadFromFile(); //This method read from file the position of the joints and transform its to a PersonList struct
	void PaintSkeleton (RoboCompMSKBody::TPerson &person);
	void CalculateJointRotations (RoboCompMSKBody::TPerson &person);
	RTMat RTMatFromJointPosition (RTMat rS, RoboCompMSKBody::SkeletonPoint p1, RoboCompMSKBody::SkeletonPoint p2, RoboCompMSKBody::SkeletonPoint translation, int axis); //This method calculates the rotation of a Joint given some points
	bool RotateTorso (const QVec &lshoulder, const QVec &rshoulder); //This method allows to rotate the torso from the position and rotation of the shoulders
	void SetPoses (Pose3D &pose, string joint);
	
	void OpenFiles(bool);
	void CloseFiles(bool);
	void Exit(bool); 
	
	void Features();
	void SetPositions (RoboCompMSKBody::SkeletonPoint *TypeJoint, RoboCompMSKBody::Joint PositionJoint);
	void Discriminate(RoboCompMSKBody::SkeletonPoint *vector);
	void PaintInMatlab();
	
	/////////////////////////////////// Simon /////////////////////////////////////////////////
	void Exercise1(bool); //Guarda en un fichero los datos para realizar el entrenamiento
	void Exercise2(bool); //Guarda en un fichero los datos para realizar el entrenamiento
	void Exercise3(bool); //Guarda en un fichero los datos para realizar el entrenamiento
	void Exercise4(bool); //Guarda en un fichero los datos para realizar el entrenamiento
	void FillDataFile (FILE *FileNameData, char RoutFileData [500], bool Detection);
	void FillLabelFile (FILE *FileNameLabel, char RoutFileLabel [500], float Label);
	void CalculateAngles (RoboCompMSKBody::SkeletonPoint PositionHand, RoboCompMSKBody::SkeletonPoint PositionElbow, RoboCompMSKBody::SkeletonPoint PositionShoulder, float &Angle);
	void CalculateDepthHand (float PositionHand, float PositionChest, float &Depth);;
	void CalculateHeightHand (RoboCompMSKBody::SkeletonPoint Hand, RoboCompMSKBody::SkeletonPoint Elbow, RoboCompMSKBody::SkeletonPoint Shoulder, RoboCompMSKBody::SkeletonPoint Foot, float &Height); 
	void CalculateDistanceArms (RoboCompMSKBody::SkeletonPoint PositionHand, RoboCompMSKBody::SkeletonPoint PositionElbow, RoboCompMSKBody::SkeletonPoint PositionShoulder);
	void Train (bool);
	float StringToFloat(const std::string &s); 
	int GetLinesNumber (FILE *File, char RoutFile[50]);
	int GetColumnsNumber (FILE *File, char RoutFile[50]);
	void GetCvMatrix (FILE *File, char RoutFile [50], cv::Mat &ReadingMatrix, int End);
	void GetExerciseData ();
	void Accuracy ();
	void SimonSays ();
	void DoExercise1 (bool);
	void DoExercise2 (bool);
	void DoExercise3 (bool);
	void DoExercise4 (bool);
	void DoExercise0 (bool);
	void SetExercise (int ExerciseDone, int ExerciseSequence);
	void CheckButtonExercisePushed (int ExerciseSequence);
	void CheckRepeatedExercise ();
	
	//////////////////////////////// Algorithms //////////////////////////////////////////////
	void TrainKNN (cv::Mat TrainData, cv::Mat LabelsData);
	void PredictKNN (cv::Mat ActualExerciseData, cv::Mat &ResultData);
	void TrainSVM (cv::Mat TrainData, cv::Mat LabelsData);
	void PredictSVM (cv::Mat ActualExerciseData, cv::Mat &ResultData);
	void TrainDTree (cv::Mat TrainData, cv::Mat LabelsData);
	void PredictDTree (cv::Mat ActualExerciseData, cv::Mat &ResultData);

	///////////////////////////////// Features ///////////////////////////////////////////////
	void QuantityOfMotion(RoboCompMSKBody::SkeletonPoint *vector, float &QoM);
	void ContractionIndex(float &Area);

	
};

#endif