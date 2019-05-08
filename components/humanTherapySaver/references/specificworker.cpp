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


#include "specificworker.h"
#include "MSKBody.h"
#include "../../../../classes/rcdraw/rcdraw.h"
#include "../../../../classes/rapplication/rapplication.h"
#include <boost/concept_check.hpp>
#include <osgGA/TrackballManipulator>

using namespace RoboCompMSKBody;
using namespace std;


double Prior_FE[5] = {-1.,-1.,-1.,-1.,-1.};

/**
* \brief Default constructor
*/

SpecificWorker::SpecificWorker(MapPrx& mprx) : GenericWorker(mprx) {

	reading = false; //readFromFile
	
//	LevelChosen = false;
	FirstIteration = true;
	Trained = false;
	Reference = false;
	AskNewExercise = true;
	SequenceDone = false;
	PassExercise = false;
	
	//Cargamos el mapa de  nombres//
	dictionaryNames ["Spine"] = "XN_SKEL_TORSO";
	dictionaryNames ["Head"] = "XN_SKEL_NECK";
	dictionaryNames ["ShoulderLeft"] = "XN_SKEL_LEFT_SHOULDER";
	dictionaryNames ["ShoulderRight"] = "XN_SKEL_RIGHT_SHOULDER";
	dictionaryNames ["ElbowLeft"] = "XN_SKEL_LEFT_ELBOW";
	 ["ElbowRight"] = "XN_SKEL_RIGHT_ELBOW";
	dictionaryNames ["HipLeft"] = "XN_SKEL_LEFT_HIP";
	dictionaryNames ["HipRight"] = "XN_SKEL_RIGHT_HIP";
	dictionaryNames ["KneeLeft"] = "XN_SKEL_LEFT_KNEE";
	dictionaryNames ["KneeRight"] = "XN_SKEL_RIGHT_KNEE";
	dictionaryNames ["HandRight"] = "XN_SKEL_RIGHT_HAND";
	dictionaryNames ["FootLeft"] = "XN_SKEL_LEFT_FOOT";
	dictionaryNames ["FootRight"] = "XN_SKEL_RIGHT_FOOT";
	dictionaryNames ["HandLeft"] = "XN_SKEL_LEFT_HAND";
	
	dictionaryEnum ["Spine"] = Spine;
	dictionaryEnum ["Head"] = Head;
	dictionaryEnum ["ShoulderLeft"] = ShoulderLeft;
	dictionaryEnum ["ShoulderRight"] = ShoulderRight;
	dictionaryEnum ["ElbowLeft"] = ElbowLeft;
	dictionaryEnum ["ElbowRight"] = ElbowRight;
	dictionaryEnum ["HipCenter"] = HipCenter;
	dictionaryEnum ["HipLeft"] = HipLeft;
	dictionaryEnum ["HipRight"] = HipRight;
	dictionaryEnum ["HandLeft"] = HandLeft;
	dictionaryEnum ["HandRight"] = HandRight;
	dictionaryEnum ["FootLeft"] = FootLeft;
	dictionaryEnum ["FootRight"] = FootRight;
	dictionaryEnum ["KneeLeft"] = KneeLeft;
	dictionaryEnum ["KneeRight"] = KneeRight;
	
	p=0, m=0;
	Level=0;
	SequenceLevel=0;
	KeepingExercise=0;
	ActualExerciseNotRepeated=0;
	
	//Vector con las posiciones 3D. Tendrá NFRAMES posiciones, que en 3D son NFRAMES*3 puntos. SkeletonPoint es una estructura que contiene 3 float, que serán
	//los tres puntos 3D de una posición. SkeletonPoint está definido en la interfaz de MSKBody
	RightHand = new SkeletonPoint [NFRAMES];
	LeftHand = new SkeletonPoint [NFRAMES];
	RightElbow = new SkeletonPoint [NFRAMES];
	LeftElbow = new SkeletonPoint [NFRAMES];
	RightShoulder = new SkeletonPoint [NFRAMES];
	LeftShoulder = new SkeletonPoint [NFRAMES];
	Chest = new SkeletonPoint [NFRAMES];
	Headd = new SkeletonPoint [NFRAMES];
	RightHip = new SkeletonPoint [NFRAMES];
	LeftHip = new SkeletonPoint [NFRAMES];
	RightFoot = new SkeletonPoint [NFRAMES];
	LeftFoot = new SkeletonPoint [NFRAMES];
	
	iteration=0;

	t=33;
	
	PushedExercise0=false;
	PushedExercise1=false;
	PushedExercise2=false;
	PushedExercise3=false;
	PushedExercise4=false;
	
	connect(&timer, SIGNAL(timeout()), this, SLOT(compute()));	
	timer.start(30); 
	
	connect(ButtonOpenFiles, SIGNAL(clicked(bool)),this, SLOT(OpenFiles(bool)));
	connect(ButtonCloseFiles, SIGNAL(clicked(bool)),this, SLOT(CloseFiles(bool)));
	connect(ButtonExit, SIGNAL(clicked(bool)),this, SLOT(Exit(bool)));
	
	connect(ButtonExercise1, SIGNAL(clicked(bool)),this, SLOT(Exercise1(bool)));
	connect(ButtonExercise2, SIGNAL(clicked(bool)),this, SLOT(Exercise2(bool)));
	connect(ButtonExercise3, SIGNAL(clicked(bool)),this, SLOT(Exercise3(bool)));
	connect(ButtonExercise4, SIGNAL(clicked(bool)),this, SLOT(Exercise4(bool)));
	connect(ButtonTrain, SIGNAL(clicked(bool)),this, SLOT(Train(bool)));
	//connect(ButtonAccuracy, SIGNAL(clicked(bool)),this, SLOT(Accuracy(bool)));
	
	connect(ButtonDoExercise1, SIGNAL(clicked(bool)),this, SLOT(DoExercise1(bool)));
	connect(ButtonDoExercise2, SIGNAL(clicked(bool)),this, SLOT(DoExercise2(bool)));
	connect(ButtonDoExercise3, SIGNAL(clicked(bool)),this, SLOT(DoExercise3(bool)));
	connect(ButtonDoExercise4, SIGNAL(clicked(bool)),this, SLOT(DoExercise4(bool)));
	connect(ButtonDoExercise0, SIGNAL(clicked(bool)),this, SLOT(DoExercise0(bool)));
	
	innerModel = new InnerModel("/home/computaex/robocomp/files/innermodel/person.xml");
	frame->show();
	osgView = new OsgView(frame);
	imv = new InnerModelViewer (innerModel, "root", osgView->getRootGroup());
	osgView->show();
	
	osgGA::TrackballManipulator *tb = new osgGA::TrackballManipulator;
        osg::Vec3d eye(osg::Vec3(4000.,4000.,-1000.));
        osg::Vec3d center(osg::Vec3(0.,0.,-0.));
        osg::Vec3d up(osg::Vec3(0.,1.,0.));
        tb->setHomePosition(eye, center, up, true);
        tb->setByMatrix(osg::Matrixf::lookAt(eye,center,up));
        osgView->setCameraManipulator(tb);
		
}


SpecificWorker::~SpecificWorker() {

}

void SpecificWorker::OpenFiles(bool) {
  
  char strfeatures [500] = "DataFiles/Features.m";
  char strposition [500] = "DataFiles/Positions.m";
  
	FileFeatures = fopen (strfeatures, "w");
	fprintf(FileFeatures,"QoMGeneric = 0;\n");  
	fprintf(FileFeatures,"ContractionIndex = 0;\n");  
	fprintf(FileFeatures,"AngleRightArm = 0;\n");  
	fprintf(FileFeatures,"AngleLeftArm = 0;\n");  
	fprintf(FileFeatures,"HeightRightHand = 0;\n");  
	fprintf(FileFeatures,"HeightLeftHand = 0;\n");  
	fprintf(FileFeatures,"DepthRightHand = 0;\n");  
	fprintf(FileFeatures,"DepthLeftHand = 0;\n");  
  
	FilePositions = fopen (strposition, "w");
	fprintf(FilePositions,"Position_RightHand_x = 0;\n");
	fprintf(FilePositions,"Position_RightHand_y = 0;\n");
	fprintf(FilePositions,"Position_RightHand_z = 0;\n");
	fprintf(FilePositions,"Position_LeftHand_x = 0;\n");
	fprintf(FilePositions,"Position_LeftHand_y = 0;\n");
	fprintf(FilePositions,"Position_LeftHand_z = 0;\n");
	fprintf(FilePositions,"Position_Head_x = 0;\n");
	fprintf(FilePositions,"Position_Head_y = 0;\n");
	fprintf(FilePositions,"Position_Head_z = 0;\n");
	fprintf(FilePositions,"Position_RightElbow_x = 0;\n");
	fprintf(FilePositions,"Position_RightElbow_y = 0;\n");
	fprintf(FilePositions,"Position_RightElbow_z = 0;\n");
	fprintf(FilePositions,"Position_LeftElbow_x = 0;\n");
	fprintf(FilePositions,"Position_LeftElbow_y = 0;\n");
	fprintf(FilePositions,"Position_LeftElbow_z = 0;\n");
	fprintf(FilePositions,"Position_RightShoulder_x = 0;\n");
	fprintf(FilePositions,"Position_RightShoulder_y = 0;\n");
	fprintf(FilePositions,"Position_RightShoulder_z = 0;\n");
	fprintf(FilePositions,"Position_LeftShoulder_x = 0;\n");
	fprintf(FilePositions,"Position_LeftShoulder_y = 0;\n");
	fprintf(FilePositions,"Position_LeftShoulder_z = 0;\n");
	fprintf(FilePositions,"Position_Chest_x = 0;\n");
	fprintf(FilePositions,"Position_Chest_y = 0;\n");
	fprintf(FilePositions,"Position_Chest_z = 0;\n");
	fprintf(FilePositions,"Position_RightHip_x = 0;\n");
	fprintf(FilePositions,"Position_RightHip_y = 0;\n");
	fprintf(FilePositions,"Position_RightHip_z = 0;\n");
	fprintf(FilePositions,"Position_LeftHip_x = 0;\n");
	fprintf(FilePositions,"Position_LeftHip_y = 0;\n");
	fprintf(FilePositions,"Position_LeftHip_z = 0;\n");
}


void SpecificWorker::CloseFiles(bool) {
  
	if (FileFeatures==NULL and FilePositions==NULL)
	  return;
  
	fprintf(FileFeatures,"t=[1:length(QoMGeneric)];\n");
	fprintf(FileFeatures,"plot(t,QoMGeneric,'r');\n");
	fprintf(FileFeatures,"title('QoM Generic');\n");
	fprintf(FileFeatures,"figure;\n");
	
	fprintf(FileFeatures,"t=[1:length(ContractionIndex)];\n");
	fprintf(FileFeatures,"plot(t,ContractionIndex,'r');\n");
	fprintf(FileFeatures,"title('Contraction Index');\n");
	fprintf(FileFeatures,"figure;\n");
	
	fprintf(FileFeatures,"t=[1:length(AngleRightArm)];\n");
	fprintf(FileFeatures,"plot(t,AngleRightArm,'r');\n");
	fprintf(FileFeatures,"title('Angle Right Arm');\n");
	fprintf(FileFeatures,"figure;\n");
	
	fprintf(FileFeatures,"t=[1:length(AngleLeftArm)];\n");
	fprintf(FileFeatures,"plot(t,AngleLeftArm,'r');\n");
	fprintf(FileFeatures,"title('Angle Left Arm');\n");
	fprintf(FileFeatures,"figure;\n");
	
	fprintf(FileFeatures,"t=[1:length(HeightRightHand)];\n");
	fprintf(FileFeatures,"plot(t,HeightRightHand,'r');\n");
	fprintf(FileFeatures,"title('Height Right Hand');\n");
	fprintf(FileFeatures,"figure;\n");
	
	fprintf(FileFeatures,"t=[1:length(HeightLeftHand)];\n");
	fprintf(FileFeatures,"plot(t,HeightLeftHand,'r');\n");
	fprintf(FileFeatures,"title('Height Left Hand');\n");
	fprintf(FileFeatures,"figure;\n");
	
	fprintf(FileFeatures,"t=[1:length(DepthRightHand)];\n");
	fprintf(FileFeatures,"plot(t,DepthRightHand,'r');\n");
	fprintf(FileFeatures,"title('Depth Right Hand');\n");
	fprintf(FileFeatures,"figure;\n");
	
	fprintf(FileFeatures,"t=[1:length(DepthLeftHand)];\n");
	fprintf(FileFeatures,"plot(t,DepthLeftHand,'r');\n");
	fprintf(FileFeatures,"title('Depth Left Hand');\n");
	fprintf(FileFeatures,"figure;\n");
  
	::fclose(FileFeatures);
  
	fprintf(FilePositions,"figure; hold on; grid on; zoom on; axis on;\n");
	fprintf(FilePositions,"plot3(Position_RightHand_x,Position_RightHand_z,Position_RightHand_y,'g*');\n");
	fprintf(FilePositions,"plot3(Position_LeftHand_x,Position_LeftHand_z,PositionLeft_Hand_y,'g*');\n");
	fprintf(FilePositions,"plot3(Position_Head_x,Position_Head_z,Position_Head_y,'b*');\n");
	fprintf(FilePositions,"plot3(Position_RightElbow_x,Position_RightElbow_z,Position_RightElbow_y,'g*');\n");
	fprintf(FilePositions,"plot3(Position_LeftElbow_x,Position_LeftElbow_z,Position_LeftElbow_y,'g*');\n");
	fprintf(FilePositions,"plot3(Position_RightShoulder_x,Position_RightShoulder_z,Position_RightShoulder_y,'g*');\n");
	fprintf(FilePositions,"plot3(Position_LeftShoulder_x,Position_LeftShoulder_z,Position_LeftShoulder_y,'g*');\n");
	fprintf(FilePositions,"plot3(Position_Chest_x,Position_Chest_z,Position_Chest_y,'b*');\n");
	fprintf(FilePositions,"plot3(Position_RightHip_x,Position_RightHip_z,Position_RightHip_y,'r*');\n");
	fprintf(FilePositions,"plot3(Position_LeftHip_x,Position_LeftHip_z,Position_LeftHip_y,'r*');\n");
	fprintf(FilePositions,"title('Poses');\n");
	::fclose(FilePositions);
	          
  
	FileFeatures=FilePositions=NULL;
}


void SpecificWorker::Exit(bool) {
	if (FileFeatures and FilePositions) {
	  CloseFiles(true);
	}
	if (FileTrain) {
	  fclose(FileTrain);
	  FileTrain=NULL;
	}
	exit (EXIT_SUCCESS);
}


void SpecificWorker::compute() {
  
	ReadFromFile(); 
	Features();
	GetExerciseData();
	SimonSays();
	Accuracy();
	PaintInMatlab();
	
}


bool SpecificWorker::setParams(RoboCompCommonBehavior::ParameterList params) {
 	timer.start(Period); //¿Dónde está definido Period?
	return true;
}; 


/**
 * @brief This method read from file the position of the joints and transform its to a PersonList struct.
 * 
 * @return void
 */
void SpecificWorker::ReadFromFile() {
  
  int i;
  int idModel;
  RoboCompMSKBody::TPerson p; //Definida en MSKBody
  RoboCompMSKBody::SkeletonPoint pose;
  RoboCompMSKBody::Joint joint;
  QStringList dataList;
  QString data = "";

	//If the file wasn't open in the previous interaction, this section open the file and read the first
	if (reading==false) {
		reading = true;
			
		file.setFileName ("/home/computaex/robocomp/components/mycomponents/therapyComp/data/TioCarlos20s.txt");
			
		if (!file.open (QIODevice::ReadOnly | QIODevice::Text)) qDebug() << "Error oppening the joints file";

		in.setDevice(&file);
			
		data = in.readLine();

		dataList = data.split ("#",QString::SkipEmptyParts);
			
		idModel = dataList[1].toInt();
			
		for (i=2;i<dataList.size();i+=4) {
			if (dictionaryEnum.find (dataList[i].toStdString())==dictionaryEnum.end()) {
				  
				pose.X = dataList[i+1].toFloat();
				pose.Y = dataList[i+2].toFloat();
				pose.Z = dataList[i+3].toFloat();
					
				joint.Position = pose;
				p.joints[dictionaryEnum[dataList[i].toStdString()]]=joint;
			}
		}
			
		personList[idModel] = p;
			
		time.start();
			
	}
		
	else {
		if (file.atEnd()) {
			in.seek(0);
			time.restart();
			in.readLine();
		}
		else {
			data = in.readLine();
			if (data==NULL)
				reading=not reading;
				
			dataList = data.split ("#", QString::SkipEmptyParts);
				
			if (dataList.size()>0) {
				idModel = dataList[1].toInt();
					
				for (i=2;i<dataList.size();i+=4) {
					if (dictionaryEnum.count (dataList[i].toStdString())!=0) {
							
						pose.X = dataList[i+1].toFloat();
						pose.Y = dataList[i+2].toFloat();
						pose.Z = dataList[i+3].toFloat();
							
						joint.Position = pose;
						p.joints[dictionaryEnum[dataList[i].toStdString()]]=joint;
					}
				}
				
				personList[idModel] = p;
					
			}
		}
	}
	
	PaintSkeleton(p);
		
}


void SpecificWorker::PaintSkeleton (TPerson &person) {
  
	RoboCompInnerModelManager::Pose3D pose;
	
	CalculateJointRotations (person);
	
	for (auto dictionaryNamesIt : dictionaryNames) {
		
		try {
			string idJoint = dictionaryNamesIt.first;
			QString TypeJoint = dictionaryNamesIt.second;
			
			SetPoses (pose, idJoint);
									
			innerModel->updateTransformValues(TypeJoint,pose.x,pose.y,pose.z,pose.rx,pose.ry,pose.rz);
			  
		}
		catch (Ice::Exception e) {
			qDebug()<<"Error in PaintSkeleton"<<e.what();
		}
		
	}
	
	imv->update();
	osgView->frame();
}


void SpecificWorker::CalculateJointRotations (TPerson &person) {
  
	RTMat kinect; 
	
	JointList jointList = person.joints;

	/// apunta el torso (inclinación alante/atrás y lateral del torso)
	mapJointRotations["Spine"] = RTMatFromJointPosition (kinect, jointList[Spine].Position, jointList[Head].Position, jointList[Spine].Position, 2);

	/// alineación de hombros (rotación en Z del torso), previa al cálculo de la transformacion final de los hombros. 
	RTMat LEFT_SHOULDER_PRE_Z = RTMatFromJointPosition (mapJointRotations["Spine"], jointList[ShoulderLeft].Position, jointList[ElbowLeft].Position, jointList[ShoulderLeft].Position, 2);
	RTMat RIGHT_SHOULDER_PRE_Z = RTMatFromJointPosition (mapJointRotations["Spine"], jointList[ShoulderRight].Position, jointList[ElbowRight].Position, jointList[ShoulderRight].Position, 2);

	RotateTorso (RIGHT_SHOULDER_PRE_Z.getTr(), LEFT_SHOULDER_PRE_Z.getTr());
	
	mapJointRotations["HipLeft"] = RTMatFromJointPosition (mapJointRotations["Spine"], jointList[HipLeft].Position, jointList[KneeLeft].Position, jointList[HipLeft].Position, 2);
	mapJointRotations["HipRight"] = RTMatFromJointPosition (mapJointRotations["Spine"], jointList[HipRight].Position, jointList[KneeRight].Position, jointList[HipRight].Position, 2);
	
	///Knee
	mapJointRotations["KneeLeft"] = RTMatFromJointPosition (mapJointRotations["Spine"]*mapJointRotations["HipLeft"], jointList[KneeLeft].Position, jointList[FootLeft].Position, jointList[KneeLeft].Position, 2);
	mapJointRotations["KneeRight"] = RTMatFromJointPosition (mapJointRotations["Spine"]*mapJointRotations["HipRight"], jointList[KneeRight].Position, jointList[FootRight].Position, jointList[KneeRight].Position, 2);

	///brazo izquierdo
	mapJointRotations["ShoulderLeft"] = RTMatFromJointPosition (mapJointRotations["Spine"], jointList[ShoulderLeft].Position, jointList[ElbowLeft].Position, jointList[ShoulderLeft].Position, 2);		
	mapJointRotations["ElbowLeft"] = RTMatFromJointPosition (mapJointRotations["Spine"]*mapJointRotations["ShoulderLeft"], jointList[ElbowLeft].Position, jointList[HandLeft].Position, jointList[ElbowLeft].Position, 2);		

	///brazo derecho
	///codo al hombro (p2 inicio p1 final)
	mapJointRotations["ShoulderRight"] = RTMatFromJointPosition (mapJointRotations["Spine"], jointList[ShoulderRight].Position, jointList[ElbowRight].Position, jointList[ShoulderRight].Position, 2);		
	mapJointRotations["ElbowRight"] = RTMatFromJointPosition (mapJointRotations["Spine"]*mapJointRotations["ShoulderRight"], jointList[ElbowRight].Position, jointList[HandRight].Position, jointList[ElbowRight].Position, 2);		
 
	///Manos derecha e izquierda
	mapJointRotations["HandRight"] = RTMatFromJointPosition (mapJointRotations["Spine"]*mapJointRotations["ShoulderRight"]*mapJointRotations["ElbowRight"], jointList[HandRight].Position, jointList[ElbowRight].Position, jointList[HandRight].Position, 2);
	mapJointRotations["HandLeft"] = RTMatFromJointPosition (mapJointRotations["Spine"]*mapJointRotations["ShoulderLeft"]*mapJointRotations["ElbowLeft"], jointList[HandLeft].Position, jointList[ElbowLeft].Position, jointList[HandLeft].Position, 2);

	///Pies derecho e izquierdo
	mapJointRotations["FootRight"] = RTMatFromJointPosition (mapJointRotations["Spine"]*mapJointRotations["HipRight"]*mapJointRotations["KneeRight"], jointList[FootRight].Position, jointList[KneeRight].Position, jointList[FootRight].Position, 2);
	mapJointRotations["FootLeft"] = RTMatFromJointPosition (mapJointRotations["Spine"]*mapJointRotations["HipLeft"]*mapJointRotations["KneeLeft"], jointList[FootLeft].Position, jointList[KneeLeft].Position, jointList[FootLeft].Position, 2);
	
}


RTMat SpecificWorker::RTMatFromJointPosition (RTMat rS, RoboCompMSKBody::SkeletonPoint p1, RoboCompMSKBody::SkeletonPoint p2, RoboCompMSKBody::SkeletonPoint translation, int axis) {
  
   	bool XClockWise=true, YClockWise=true, ZClockWise=true;
	float alpha, beta, gamma;
	
	RTMat rt(XClockWise,YClockWise, ZClockWise);
	QVec p1h = QVec::vec4(p1.X, p1.Y, p1.Z, 1);
	QVec p2h = QVec::vec4(p2.X, p2.Y, p2.Z,1);
	QVec translationH = QVec::vec4(translation.X, translation.Y, translation.Z,1);
	
	QMat aux = rS;
	aux = aux.invert();
	QVec translationT = aux * translationH;
	QVec p1t = aux * p1h;
	QVec p2t = aux * p2h;
	QVec v = p2t - p1t;
	
	v= v.normalize();
	
	///por filas
	switch(axis){
	case 0:
		alpha = 0;
		
		if(YClockWise) beta = atan2(-v.z(),v.x());
		else beta = atan2(v.z(),v.x());
		
		if(ZClockWise) gamma = asin(-v.y());
		else gamma = asin(v.y());
		
		break;
	case 1:
		if(XClockWise) alpha = atan2(v.z(),v.y());
		else alpha = atan2(-v.z(),v.y());
		
		beta = 0;
		
		if(ZClockWise) gamma = asin(v.x());
		else gamma = asin(-v.x());
		
		break;
	case 2:
		if(XClockWise) alpha =  atan2(-v.y(),v.z());
		else alpha =  atan2(v.y(),v.z());
		
		if(YClockWise) beta = asin(v.x());
		else beta = asin(-v.x());
		
		gamma = 0;
		
		break;
	}
	
	rt.setRT(alpha,beta,gamma,translationT);
	
	return rt;
}


bool SpecificWorker::RotateTorso (const QVec &lshoulder, const QVec &rshoulder) {
  
	QVec eje = lshoulder - rshoulder;	//Calculamos el eje que va de un hombro a otro
	
	eje.normalize();

	if(eje.x()==0) {
		return false;
	}

	float angulo = atan2(eje.y(),eje.x());	//Calculamos el giro necesario para alinear los hombros con el eje (arcotangente de y/x)
	
	mapJointRotations["Spine"].setRZ(angulo); // Aplicamos dicho giro al eje Z del torso
	
	return true;
}


void SpecificWorker::SetPoses (Pose3D &pose, string joint) {
  
  int height=0;
  int head=0;
  
	if (joint=="Spine") {
		height=1500;
	}
			
	if (joint=="Head") {
		head=140;
	}
  
	pose.x = 1000*mapJointRotations [joint].getTr().x();
	pose.y = 1000*mapJointRotations [joint].getTr().y()+height;
	pose.z = 1000*mapJointRotations [joint].getTr().z()-(2*height)+head;
  
	pose.rx = mapJointRotations [joint].getRxValue();
 	pose.ry = mapJointRotations [joint].getRyValue();
 	pose.rz = mapJointRotations [joint].getRzValue();
	
	if (RadioButtonTrain->isChecked()) {
	
	      cout<<"Tipo Joint "<<joint<<endl;
	      cout<<"Pose "<<pose.x<<" "<<pose.y<<" "<<pose.z<<" Rotacion "<<pose.rx<<" "<<pose.ry<<" "<<pose.rz<<endl;
	
	}
  
}


void SpecificWorker::Features() {
  
	//cout<<" El número de personas es "<<personList.size()<<endl;
  
	//cout<<"Número de iteración "<<m<<" "<<p<<endl<<endl;
  
	for (auto IteratorPerson : personList) {
		//int id = IteratorPerson.first;
		RoboCompMSKBody::TPerson Person = IteratorPerson.second;
		RoboCompMSKBody::JointList PersonJointsList = Person.joints;
		
		for (auto IteratorJoints : PersonJointsList) {
		
			RoboCompMSKBody::JointType PersonJointType = IteratorJoints.first;
			RoboCompMSKBody::Joint PersonJoint = IteratorJoints.second;
		
 			if (PersonJointType==Spine) {
			  
				SetPositions(Chest,PersonJoint);				
				QuantityOfMotion(Chest,QoMc);
				//cout<<endl<<" Chest.X "<<Chest[m].X<<" Chest.Y "<<Chest[m].Y<<" Chest.Z "<<Chest[m].Z<<endl;
			
 			}
 			
 			if (PersonJointType==Head) {
			  
				SetPositions(Headd,PersonJoint);
				QuantityOfMotion(Headd,QoMh);
				//cout<<" Head.X "<<Headd[m].X<<" Head.Y "<<Headd[m].Y<<" Head.Z "<<Headd[m].Z<<endl;
				      
			}

			if (PersonJointType==ShoulderLeft) {
			  
				SetPositions(LeftShoulder,PersonJoint);    
				//cout<<" LeftShoulder.X "<<LeftShoulder[m].X<<" LeftShoulder.Y "<<LeftShoulder[m].Y<<" LeftShoulder.Z "<<LeftShoulder[m].Z<<endl;
				      
			}
 			
 			if (PersonJointType==ElbowLeft) {
			  
				SetPositions(LeftElbow,PersonJoint);
 				QuantityOfMotion(LeftElbow,QoMle);
 				//cout<<" LeftElbow.X "<<LeftElbow[m].X<<" LeftElbow.Y "<<LeftElbow[m].Y<<" LeftElbow.Z "<<LeftElbow[m].Z<<endl;	  
				    
			}
			
			if (PersonJointType==HandLeft) {
			  
				SetPositions(LeftHand,PersonJoint);
 				QuantityOfMotion(LeftHand,QoMlh);
				//cout<<" LeftHand.X "<<LeftHand[m].X<<" LeftHand.Y "<<LeftHand[m].Y<<" LeftHand.Z "<<LeftHand[m].Z<<endl;
					  
			}
			
			if (PersonJointType==ShoulderRight) {
			  
				SetPositions(RightShoulder,PersonJoint);
				//cout<<" RightShoulder.X "<<RightShoulder[m].X<<" RightShoulder.Y "<<RightShoulder[m].Y<<" RightShoulder.Z "<<RightShoulder[m].Z<<endl;
					  
			}
			
			if (PersonJointType==ElbowRight) {
			  
				SetPositions(RightElbow,PersonJoint);	  
				QuantityOfMotion(RightElbow,QoMre);
				//cout<<" RightElbow.X "<<RightElbow[m].X<<" RightElbow.Y "<<RightElbow[m].Y<<" RightElbow.Z "<<RightElbow[m].Z<<endl;
				    
			}
			
			if (PersonJointType==HandRight) {
			  
				SetPositions(RightHand,PersonJoint);	  
 				QuantityOfMotion(RightHand,QoMrh);
				//cout<<" RightHand.X "<<RightHand[m].X<<" RightHand.Y "<<RightHand[m].Y<<" RightHand.Z "<<RightHand[m].Z<<endl;
				    
			}
			
			if (PersonJointType==HipLeft) {
			  
				SetPositions(LeftHip,PersonJoint);	    
				//cout<<" LeftHip.X "<<LeftHip[m].X<<" LeftHip.Y "<<LeftHip[m].Y<<" LeftHip.Z "<<LeftHip[m].Z<<endl;	
					    	 
			}
			
			if (PersonJointType==FootLeft) {
			  
				SetPositions(LeftFoot,PersonJoint);	    
				//cout<<" RightHip.X "<<RightHip[m].X<<" RightHip.Y "<<RightHip[m].Y<<" RightHip.Z "<<RightHip[m].Z<<endl<<endl;
					    
			}
			
			
			if (PersonJointType==HipRight) {
			  
				SetPositions(RightHip,PersonJoint);	    
				//cout<<" RightHip.X "<<RightHip[m].X<<" RightHip.Y "<<RightHip[m].Y<<" RightHip.Z "<<RightHip[m].Z<<endl<<endl;
					    
			}
			
			if (PersonJointType==FootRight) {
			  
				SetPositions(RightFoot,PersonJoint);	    
				//cout<<" RightHip.X "<<RightHip[m].X<<" RightHip.Y "<<RightHip[m].Y<<" RightHip.Z "<<RightHip[m].Z<<endl<<endl;
					    
			}
			
			
		}
		
		QoMRightArm = QoMrh + QoMre;
 		QoMLeftArm = QoMlh + QoMle;
 		QoMGeneric = QoMRightArm + QoMLeftArm + QoMh + QoMc;
 		
 		//cout<<" QoMGeneric "<<QoMGeneric<<endl;
		
		ContractionIndex(ContractionArea);		
 		//cout<<" ContractionIndex "<<ContractionArea<<endl;
		
		CalculateAngles(RightHand[m], RightElbow[m], RightShoulder[m], AngleRightArm);
		CalculateAngles(LeftHand[m], LeftElbow[m], LeftShoulder[m], AngleLeftArm);
		
		CalculateHeightHand(RightHand[m], RightElbow[m], RightShoulder[m], RightFoot[m], HeightRightHand);
		CalculateHeightHand(LeftHand[m], RightElbow[m], RightShoulder[m], RightFoot[m], HeightLeftHand);
		
		CalculateDepthHand(Chest[m].Z, RightHand[m].Z, DepthRightHand);
		CalculateDepthHand(Chest[m].Z, LeftHand[m].Z, DepthLeftHand);
		
		//Mostramos las QoM calculada por la interfaz
		NumberQoMGeneric->display(QoMGeneric);
		NumberContractionIndex->display(ContractionArea);
		NumberAngleRightArm->display(AngleRightArm);
		NumberAngleLeftArm->display(AngleLeftArm);
		NumberHeightRightHand->display(HeightRightHand); 
		NumberHeightLeftHand->display(HeightLeftHand); 
		NumberDepthRightHand->display(DepthRightHand);
		NumberDepthLeftHand->display(DepthLeftHand);
		
		
		if (FirstIteration==true) {
			FirstIteration=false;
		}
		else {
			p=m;
			if (m==(NFRAMES-1)){ //El vector de posiciones se llena de forma progresiva, sin desplazar los valores. El último valor incorporado es m y no NFRAMES-1
				m=0;
			}
			else {
				m++;
			} 
		}
			
	}
}


void SpecificWorker::SetPositions (SkeletonPoint *TypeJoint, RoboCompMSKBody::Joint PositionJoint) {
	
	TypeJoint[m].X=1000*PositionJoint.Position.X; //Las pasamos a mm multiplicando por 1000
 	TypeJoint[m].Y=1000*PositionJoint.Position.Y;
 	TypeJoint[m].Z=1000*PositionJoint.Position.Z;
	
	Discriminate(TypeJoint);

}


void SpecificWorker::Discriminate (SkeletonPoint *vector) { //Elimina los valores que se dan por imposibles, comparándolos con un umbral

      float diference_x, diference_y, diference_z;
      float threshold=500; //umbral en mm

	diference_x=fabs(vector[m].X-vector[p].X);
	diference_y=fabs(vector[m].Y-vector[p].Y);
	diference_z=fabs(vector[m].Z-vector[p].Z);
	  
	if (diference_x>threshold) {
		vector[m].X=vector[p].X;
	}
	
	if (diference_y>threshold) {
		vector[m].Y=vector[p].Y;
	}
	
	if (diference_z>threshold) {
		vector[m].Z=vector[p].Z;
	}
}


void SpecificWorker::QuantityOfMotion (SkeletonPoint *vector, float &QoM) { //Da erróneos los primeros valores hasta que se llena el vector
  
      QoM=0;
      int j; //i
    
      /*if (FirstIteration==false) {
	if (iteration<NFRAMES) {
	  cout << "Interacción " << iteration <<" m "<<m<<endl<<endl;
	  for (i=m+1; i<NFRAMES; i++) {
	    vector[i].X=0;
	    vector[i].Y=0;
	    vector[i].Z=0;
	  }
	  for (i=0; i<NFRAMES; i++) {
	    cout<<" Vector inicial QoM "<<vector[i].X<<" "<<vector[i].Y<<" "<<vector[i].Z<<endl;
	  }
	  iteration++;
	}
      }*/
      

	if (m==(NFRAMES-1)) {  
	  for (j=NFRAMES-1; j>0; j--) {
	    QoM=(sqrt(pow((vector[j].X-vector[j-1].X),2)+pow((vector[j].Y-vector[j-1].Y),2)+pow((vector[j].Z-vector[j-1].Z),2)))+QoM;
	  }
	}
	else {
	  for (j=(NFRAMES-1); j>(m+1); j--) {
	    QoM=(sqrt(pow((vector[j].X-vector[j-1].X),2)+pow((vector[j].Y-vector[j-1].Y),2)+pow((vector[j].Z-vector[j-1].Z),2)))+QoM;
	  }
	  for (j=m; j>0; j--) {
	    QoM=(sqrt(pow((vector[j].X-vector[j-1].X),2)+pow((vector[j].Y-vector[j-1].Y),2)+pow((vector[j].Z-vector[j-1].Z),2)))+QoM;
	  }
	  
	  QoM=(sqrt(pow((vector[0].X-vector[NFRAMES-1].X),2)+pow((vector[0].Y-vector[NFRAMES-1].Y),2)+pow((vector[0].Z-vector[NFRAMES-1].Z),2)))+QoM;
	}

	QoM=QoM/(NFRAMES);
	
}


void SpecificWorker::ContractionIndex (float &Area) { //Contar la coordenada Z o no???
  
  float LengthRightHandChest, LengthLeftHandChest, LengthRightHandLeftHand, SemiPerimeter;
  
	//LengthRightHandChest=sqrt(pow((Chest[p].X-RightHand[p].X),2)+pow((Chest[p].Y-RightHand[p].Y),2)+pow((Chest[p].Z-RightHand[p].Z),2));
	//LengthLeftHandChest=sqrt(pow((Chest[p].X-LeftHand[p].X),2)+pow((Chest[p].Y-LeftHand[p].Y),2)+pow((Chest[p].Z-LeftHand[p].Z),2));
	//LengthRightHandLeftHand=sqrt(pow((LeftHand[p].X-RightHand[p].X),2)+pow((LeftHand[p].Y-RightHand[p].Y),2)+pow((LeftHand[p].Z-RightHand[p].Z),2));
	
	LengthRightHandChest=sqrt(pow((Chest[m].X-RightHand[m].X),2)+pow((Chest[m].Y-RightHand[m].Y),2));
	LengthLeftHandChest=sqrt(pow((Chest[m].X-LeftHand[m].X),2)+pow((Chest[m].Y-LeftHand[m].Y),2));
	LengthRightHandLeftHand=sqrt(pow((LeftHand[m].X-RightHand[m].X),2)+pow((LeftHand[m].Y-RightHand[m].Y),2));
  
	SemiPerimeter=(LengthRightHandChest+LengthLeftHandChest+LengthRightHandLeftHand)/2;
	Area=sqrt(SemiPerimeter*(SemiPerimeter-LengthRightHandChest)*(SemiPerimeter-LengthLeftHandChest)*(SemiPerimeter-LengthRightHandLeftHand));
  
	Area=Area/1000000; //pasamos de mm2 a m2
}


void SpecificWorker::CalculateAngles (SkeletonPoint PositionHand, SkeletonPoint PositionElbow, SkeletonPoint PositionShoulder, float &Angle) {
  
  float DistanceShoulderHand;
  float Numerator;
  float Denominator;
  float absNumerator, absDenominator;
  
	CalculateDistanceArms (PositionHand, PositionElbow, PositionShoulder);
	
	DistanceShoulderHand=sqrt(pow(PositionHand.X-PositionShoulder.X,2)+pow(PositionHand.Y-PositionShoulder.Y,2)+pow(PositionHand.Z-PositionShoulder.Z,2));
	
	if (DistanceShoulderHand > LengthArm) {
	  DistanceShoulderHand = LengthArm;
	}
	
	Numerator = pow(DistanceShoulderElbow,2)+pow(DistanceElbowHand,2)-pow(DistanceShoulderHand,2);
	Denominator = 2*DistanceShoulderElbow*DistanceElbowHand;
	
	absNumerator = fabs(trunc(Numerator));
	absDenominator = fabs(trunc(Denominator));
	
	if (absNumerator==absDenominator) {
	  
	  if (Numerator > 0 && Denominator > 0) {  
	    Denominator = Denominator + 1;
	    //Numerator = Numerator - 1;
	  }
	  if (Numerator < 0 && Denominator < 0) {
	    Denominator = Denominator - 1;
	    //Numerator = Numerator + 1;
	  }
	  if (Numerator > 0 && Denominator < 0) {
	    Denominator = Denominator - 1;
	    //Numerator = Numerator - 1;
	  }
	  if (Numerator < 0 && Denominator > 0) {
	    Denominator = Denominator + 1;
	    //Numerator = Numerator + 1;
	  }
	}

	Angle = acos(Numerator/Denominator);
	Angle = (Angle*180)/PI; // Lo pasamos de radianes a grados
	
}

void SpecificWorker::CalculateDepthHand (float PositionHand, float PositionChest, float &Depth) {
  
  Depth = abs (PositionHand - PositionChest);
  
  Depth = Depth / 1000; //Lo pasamos a metros
  
}

void SpecificWorker::CalculateHeightHand (SkeletonPoint Hand, SkeletonPoint Elbow, SkeletonPoint Shoulder, SkeletonPoint Foot, float &Height) {
  
  float FloorHand, FloorShoulder;
  
	FloorHand = Hand.Y-Foot.Y;
	FloorShoulder = Shoulder.Y-Foot.Y;
	
	CalculateDistanceArms (Hand, Elbow, Shoulder);
	
	    Height = FloorHand/(FloorShoulder+LengthArm);
	 
}

void SpecificWorker::CalculateDistanceArms (SkeletonPoint PositionHand, SkeletonPoint PositionElbow, SkeletonPoint PositionShoulder) {
  
  if (FirstIteration == false) {
      
      if (Reference == false) {
  
	DistanceShoulderElbow=sqrt(pow(PositionElbow.X-PositionShoulder.X,2)+pow(PositionElbow.Y-PositionShoulder.Y,2)+pow(PositionElbow.Z-PositionShoulder.Z,2));
	DistanceElbowHand=sqrt(pow(PositionHand.X-PositionElbow.X,2)+pow(PositionHand.Y-PositionElbow.Y,2)+pow(PositionHand.Z-PositionElbow.Z,2));
	
	cout << endl << "DistanceShoulderElbow " << DistanceShoulderElbow << " DistanceElbowHand " << DistanceElbowHand << endl << endl;
	
	LengthArm=DistanceShoulderElbow+DistanceElbowHand;
	
	Reference = true;
	
      }
  }
}


void SpecificWorker::PaintInMatlab() {
  
	if (FileFeatures){
	    fprintf(FileFeatures,"QoMGeneric = [QoMGeneric %f];\n",QoMGeneric);
	    fprintf(FileFeatures,"ContractionIndex = [ContractionIndex %f];\n",ContractionArea);
	    fprintf(FileFeatures,"AngleRightArm = [AngleRightArm %f];\n",AngleRightArm);
	    fprintf(FileFeatures,"AngleLeftArm = [AngleLeftArm %f];\n",AngleLeftArm);
	    fprintf(FileFeatures,"HeightRightHand = [HeightRightHand %f];\n",HeightRightHand);
	    fprintf(FileFeatures,"HeightLeftHand = [HeightLeftHand %f];\n",HeightLeftHand);
	    fprintf(FileFeatures,"DepthRightHand = [DepthRightHand %f];\n",DepthRightHand);
	    fprintf(FileFeatures,"DepthLeftHand = [DepthLeftHand %f];\n",DepthLeftHand);
	      
	}
	
	if (FilePositions){ //probar
	    fprintf(FilePositions,"Position_RightHand_x = [Position_RightHand_x %f];\n",RightHand[m].X);
	    fprintf(FilePositions,"Position_RightHand_y = [Position_RightHand_y %f];\n",RightHand[m].Y);
	    fprintf(FilePositions,"Position_RightHand_z = [Position_RightHand_z %f];\n",RightHand[m].Z);
	    fprintf(FilePositions,"Position_LeftHand_x = [Position_LeftHand_x %f];\n",LeftHand[m].X);
	    fprintf(FilePositions,"Position_LeftHand_y = [Position_LeftHand_y %f];\n",LeftHand[m].Y);
	    fprintf(FilePositions,"Position_LeftHand_z = [Position_LeftHand_z %f];\n",LeftHand[m].Z);
	    fprintf(FilePositions,"Position_Head_x = [Position_Head_x %f];\n",Headd[m].X);
	    fprintf(FilePositions,"Position_Head_y = [Position_Head_y %f];\n",Headd[m].Y);
	    fprintf(FilePositions,"Position_Head_z = [Position_Head_z %f];\n",Headd[m].Z);
	    fprintf(FilePositions,"Position_RightElbow_x = [Position_RightElbow_x %f];\n",RightElbow[m].X);
	    fprintf(FilePositions,"Position_RightElbow_y = [Position_RightElbow_y %f];\n",RightElbow[m].Y);
	    fprintf(FilePositions,"Position_RightElbow_z = [Position_RightElbow_z %f];\n",RightElbow[m].Z);
	    fprintf(FilePositions,"Position_LeftElbow_x = [Position_LeftElbow_x %f];\n",LeftElbow[m].X);
	    fprintf(FilePositions,"Position_LeftElbow_y = [Position_LeftElbow_y %f];\n",LeftElbow[m].Y);
	    fprintf(FilePositions,"Position_LeftElbow_z = [Position_LeftElbow_z %f];\n",LeftElbow[m].Z);
	    fprintf(FilePositions,"Position_RightShoulder_x = [Position_RightShoulder_x %f];\n",RightShoulder[m].X);
	    fprintf(FilePositions,"Position_RightShoulder_y = [Position_RightShoulder_y %f];\n",RightShoulder[m].Y);
	    fprintf(FilePositions,"Position_RightShoulder_z = [Position_RightShoulder_z %f];\n",RightShoulder[m].Z);
	    fprintf(FilePositions,"Position_LeftShoulder_x = [Position_LeftShoulder_x %f];\n",LeftShoulder[m].X);
	    fprintf(FilePositions,"Position_LeftShoulder_y = [Position_LeftShoulder_y %f];\n",LeftShoulder[m].Y);
	    fprintf(FilePositions,"Position_LeftShoulder_z = [Position_LeftShoulder_z %f];\n",LeftShoulder[m].Z);
	    fprintf(FilePositions,"Position_Chest_x = [Position_Chest_x %f];\n",Chest[m].X);
	    fprintf(FilePositions,"Position_Chest_y = [Position_Chest_y %f];\n",Chest[m].Y);
	    fprintf(FilePositions,"Position_Chest_z = [Position_Chest_z %f];\n",Chest[m].Z);
	    fprintf(FilePositions,"Position_RightHip_x = [Position_RightHip_x %f];\n",RightHip[m].X);
	    fprintf(FilePositions,"Position_RightHip_y = [Position_RightHip_y %f];\n",RightHip[m].Y);
	    fprintf(FilePositions,"Position_RightHip_z = [Position_RightHip_z %f];\n",RightHip[m].Z);
	    fprintf(FilePositions,"Position_LeftHip_x = [Position_LeftHip_x %f];\n",LeftHip[m].X);
	    fprintf(FilePositions,"Position_LeftHip_y = [Position_LeftHip_y %f];\n",LeftHip[m].Y);
	    fprintf(FilePositions,"Position_LeftHip_z = [Position_LeftHip_z %f];\n",LeftHip[m].Z);
	    
	}
	
}


void SpecificWorker::Exercise1(bool) {
  
  char RoutTrain [50] = "DataFiles/Training.txt";
  char RoutLabel [50] = "DataFiles/Labels.txt";
  char RoutExercise1 [50] = "DataFiles/Exercise1.txt";
  float LabelExercise = 1;
  
  if (RadioButtonTrain->isChecked()) {
  
      FillDataFile(FileTrain, RoutTrain, false);
      FillDataFile(FileExercise1, RoutExercise1, false);
      FillLabelFile(FileLabels, RoutLabel, LabelExercise);
      
  }
  
}

void SpecificWorker::Exercise2(bool) {
  
  char RoutTrain [50] = "DataFiles/Training.txt";
  char RoutLabel [50] = "DataFiles/Labels.txt";
  char RoutExercise2 [50] = "DataFiles/Exercise2.txt";
  float LabelExercise = 2;
  
  if (RadioButtonTrain->isChecked()) {
  
      FillDataFile(FileTrain, RoutTrain, false);
      FillDataFile(FileExercise2, RoutExercise2, false);
      FillLabelFile(FileLabels, RoutLabel, LabelExercise);
      
  }
  
}

void SpecificWorker::Exercise3(bool) {
  
  char RoutTrain [50] = "DataFiles/Training.txt";
  char RoutLabel [50] = "DataFiles/Labels.txt";
  char RoutExercise3 [50] = "DataFiles/Exercise3.txt";
  float LabelExercise = 3;
  
  if (RadioButtonTrain->isChecked()) {
  
      FillDataFile(FileTrain, RoutTrain, false);
      FillDataFile(FileExercise3, RoutExercise3, false);
      FillLabelFile(FileLabels, RoutLabel, LabelExercise);
      
  }
  
}

void SpecificWorker::Exercise4(bool) {
  
  char RoutTrain [50] = "DataFiles/Training.txt";
  char RoutLabel [50] = "DataFiles/Labels.txt";
  char RoutExercise4 [50] = "DataFiles/Exercise4.txt";
  float LabelExercise = 4;
  
  if (RadioButtonTrain->isChecked()) {
  
      FillDataFile(FileTrain, RoutTrain, false);
      FillDataFile(FileExercise4, RoutExercise4, false);
      FillLabelFile(FileLabels, RoutLabel, LabelExercise);
      
  }
  
}

void SpecificWorker::FillDataFile (FILE *FileNameData, char RoutFileData [500], bool Detection) {
  
	if (FileNameData == NULL) {
	  
		if (Detection == false) { //Si es en entrenamiento, que escriba al final del fichero sin borrar
    
			FileNameData = fopen (RoutFileData, "a");
		}
		
		else { //Si es en detección, que sobreescriba el fichero para que haya siempre una única línea
		  
			FileNameData = fopen (RoutFileData, "w");
			
		}
    
	}
	
	if (FileNameData) { 
	  	  
		fprintf(FileNameData,"%f ",ContractionArea);
		fprintf(FileNameData,"%f ",AngleRightArm);
		fprintf(FileNameData,"%f ",AngleLeftArm);
		fprintf(FileNameData,"%f ",HeightRightHand);
		fprintf(FileNameData,"%f ",HeightLeftHand);
		fprintf(FileNameData,"%f ",DepthRightHand);
		fprintf(FileNameData,"%f ",DepthLeftHand);
		fprintf(FileNameData,"\n");
		
	}
	
	fclose(FileNameData);
	FileNameData=NULL;
  
}


void SpecificWorker::FillLabelFile (FILE *FileNameLabel, char RoutFileLabel [500], float Label) {
  
    	if (FileNameLabel==NULL) {
	  
		FileNameLabel = fopen (RoutFileLabel, "a");
		
	}
	
	if (FileNameLabel) {
	  
		fprintf(FileNameLabel,"%f\n",Label);
	  
	}
	
	fclose(FileNameLabel);
	FileNameLabel=NULL;
   
}


void SpecificWorker::Train (bool) {
  
   char RoutTrain [50] = "DataFiles/Training.txt";
   char RoutLabel [50] = "DataFiles/Labels.txt";
   int FileNumber;
   //int ColumnNumber;
  
   if (RadioButtonTrain->isChecked()) {
   
      FileNumber = GetLinesNumber(FileTrain, RoutTrain); //Da el número de líneas que tiene el fichero
      //ColumnNumber = GetColumnsNumber (FileTrain, RoutTrain); //Da el número de columnas que tiene el fichero
   
      cv::Mat TrainMatrix (FileNumber, 150, CV_32FC1); //Matriz Cv:Mat donde se guarda todo el fichero de movimientos. 
      cv::Mat LabelsMatrix (FileNumber, 1, CV_32FC1); //Matriz Cv:Mat donde se guarda todo el fichero de labels.
   
      GetCvMatrix (FileTrain, RoutTrain, TrainMatrix, FileNumber); //Fichero de entrenamiento
      GetCvMatrix (FileLabels, RoutLabel, LabelsMatrix, FileNumber); //Fichero de labels
      
      TrainKNN (TrainMatrix, LabelsMatrix);
      TrainSVM (TrainMatrix, LabelsMatrix);
      TrainDTree (TrainMatrix, LabelsMatrix);
      
      Trained=true;
      
  }
  
}


void SpecificWorker::GetExerciseData () {
  
   char RoutActualExercise [50] = "DataFiles/ActualExercise.txt";
   int FileNumber;
   //int ColumnNumber;
   float ResultData;
   int NumberExercise;
   
   if (RadioButtonDetect->isChecked()) {
     
	if (Trained == true) {
     
	    cout << endl << "Detection Mode" << endl << endl;
     
	    FillDataFile (FileActualExercise, RoutActualExercise, true);
     
	    FileNumber = GetLinesNumber (FileActualExercise, RoutActualExercise);  //Da el número de líneas que tiene el fichero
	    //ColumnNumber = GetColumnsNumber (FilePoses, RoutTrain); //Da el número de columnas que tiene el fichero
	
	    cv::Mat ActualExerciseMatrix (FileNumber, 150, CV_32FC1); //Matriz Cv::Mat donde se guarda la primera línea del fichero de movimientos 
	    cv::Mat Result (1,1, CV_32FC1);
	
	    GetCvMatrix (FileActualExercise, RoutActualExercise, ActualExerciseMatrix, FileNumber); //Fichero de Posiciones
	    
//	    PredictKNN (ActualExerciseMatrix, Result);
//	    PredictSVM (ActualExerciseMatrix, Result);
	    PredictDTree (ActualExerciseMatrix, Result);
	    
	    ResultData = Result.at<float>(0,0);
	    
	    NumberExercise = trunc(ResultData);
	
	    sprintf(str, "Exercise %d", NumberExercise); 
	
	    LabelNumberExercise->setText(str);
	
	}
	
	else {
	  
	  cout <<  endl << "Come back to Training Mode and train the component first" << endl << endl;
	  
	}
     
   }
   
}
   
   
int SpecificWorker::GetLinesNumber (FILE *File, char RoutFile[50]) {
  
  int LineNumber=0;
  int c;
  
  File = fopen (RoutFile, "r");
  
  if (File==NULL) {
      cout<<"Error opening the File to get the number of the lines"<<endl;
      system("pause");
      exit (EXIT_FAILURE);
  }
  
  while ((c=fgetc(File)) != EOF) {
    if (c == '\n') {
      LineNumber++;
    }
  }
  
  //cout << endl << "LineNumber " << LineNumber << endl << endl;
  
  fclose (File);
  
  return LineNumber;
  
}

int SpecificWorker::GetColumnsNumber (FILE *File, char RoutFile[50]) {
  
    char Line [90];
    char *DataLine = NULL;
    int ColumnNumber=0;
    int i;
    
    File = fopen (RoutFile, "r");
    
    if (File==NULL) {
      cout<<"Error opening the File to get the number of the columns"<<endl;
      system("pause");
      exit (EXIT_FAILURE);
    }
     
    fgets (Line, 90, File); //Coge la primera línea que lee del fichero, hasta un máximo de 90 caracteres o fin de línea. Error??
    
    cout << endl << "File Line: ";
    
    for (i=0; i<=90; i++) {
      cout << Line [i];
    }
    
    cout << endl;
     
     DataLine = strtok(Line, " "); //Divide la cadena de caracteres Line en argumentos separados por " "
     
     while (DataLine != NULL) { //Mientras que DataLine no sea NULL, lo sigue dividiendo en tokens. ERROR??
     
        cout << " DataLine "<<DataLine;
	DataLine = strtok(NULL, " ");
	ColumnNumber++;
     
     }
   
   free(DataLine);
   
   cout << endl << "ColumnNumber " << ColumnNumber << endl << endl;
     
   return ColumnNumber;
  
}
  

//Revisar
float SpecificWorker::StringToFloat(const std::string &s) {
  
	float ret;
	std::string str = s;
	
	replace(str.begin(), str.end(), ',', '.'); //Reemplazar las comas por puntos
	std::istringstream istr(str); //istringstream es una clase para flujo de entrada de memoria tipo char
	istr.imbue(std::locale("C")); //Cambia la localización a C
	istr >> ret; //Lo guarda en ret
	return ret;
}

void SpecificWorker::GetCvMatrix (FILE *File, char RoutFile [50], cv::Mat &ReadingMatrix, int End) {
  
   char Line [90];
   char *DataLine = NULL;
   float DataFloat;
   int FileNumber;
   int ColumnNumber;
  
    File = fopen (RoutFile, "r");
   
    if (File==NULL) {
     
      cout<<"Error opening the Training File"<<endl;
      system("pause");
      exit (EXIT_FAILURE);
    
    }
     
    FileNumber=0;
     
   //while (!feof(File)) { //ERROR??. Sale una línea de más (14)
   //while (fgetc(File) != EOF) { //ERROR??. No coge el primer valor de la primera línea
   while (FileNumber<End) {
     
      fgets (Line, 90, File); //Coge las líneas que lee del fichero, hasta un máximo de 90 caracteres o fin de línea 

      DataLine = strtok(Line, " "); //Divide la cadena de caracteres Line en argumentos separados por " "
   
      ColumnNumber = 0;
	  
      cout << endl;
	
      while (DataLine != NULL) { //Mientras que DataLine no sea NULL, lo sigue dividiendo en tokens. 

	  cout << "File: " << FileNumber << " Column: " << ColumnNumber << " DataLineTrain " << DataLine << endl;
	  DataFloat=StringToFloat(DataLine);
	  ReadingMatrix.at<float>(FileNumber,ColumnNumber)=DataFloat; //Transforma el contenido de la cadena a float
	  DataLine = strtok(NULL, " ");
	  ColumnNumber++;
     
	  }
   
      free(DataLine);
      FileNumber++;
    
      } 
}

void SpecificWorker::TrainKNN (cv::Mat TrainData, cv::Mat LabelsData) {
  
  KNN.train(TrainData, LabelsData);
  
  //KNN.train(TrainData, LabelsData, cv::Mat(), false, 120);
      
  //cv::KNearest KNN (ReadingTrain, ReadingLabel, cv::Mat(), false, 1); //Entrenarla o definirla así??
  
}


void SpecificWorker::PredictKNN (cv::Mat ActualExerciseData, cv::Mat &ResultData) {
  
  //KNN.find_nearest(ActualExerciseData, KNN.get_max_k()/2, &ResultData);
  KNN.find_nearest(ActualExerciseData, 15, &ResultData);
  //KNN.find_nearest(ActualExerciseData, 10, 0, 0, &ResultData);
  //KNN.find_nearest(ActualExerciseData, 10, cv::Mat(), cv::Mat(), &ResultData, cv::Mat());
	    
  //cout << "Result KNN " << ResultData << endl;
  cout << "Result KNN " << ResultData.at<float>(0,0) << endl; //Sin matriz
  
}


void SpecificWorker::TrainSVM (cv::Mat TrainData, cv::Mat LabelsData) {
  
  //CvSVMParams Param; 
//  CvSVMParams Param = CvSVMParams(); //Coge los valores por defecto?? 
  CvSVMParams Param = CvSVMParams();
  
  //Valores por defecto
  //svm_type(CvSVM::C_SVC), kernel_type(CvSVM::RBF), degree(0),
  //gamma(1), coef0(0), C(1), nu(0), p(0), class_weights(0)
  //term_crit = cvTermCriteria( CV_TERMCRIT_ITER+CV_TERMCRIT_EPS, 1000, FLT_EPSILON );
  
//  Param.svm_type = CvSVM::C_SVC; //Clasifinación de n clases, (n>2)
//  Param.kernel_type = CvSVM::LINEAR; //No se realiza el mapeo. La discriminación (o regresión) lineal se hace en el espacio original de las características. Es la opción más rápida
  //Param.kernel_type = CvSVM::RBF; //Función base radial, una buena opción en la mayoría de los casos
//  Param.term_crit = cvTermCriteria(CV_TERMCRIT_ITER, 100, 0.000001); //Terminación del criterio del proceso de entrenamiento iterativo, que resuelve un caso parcial del problema 
								     //limitado de optimización cuadrática. Se puede especificar la tolerancia y/o el número máximo de iteraciones.
  
  //Param.C=4;
  //Param.gamma = 4;
  //Param.gamma = 20; //Parámetro del kernel la función RFB
  //Param.C = 7; //Parámetro C del problema de optimización C_SVC
  
  SVM.train(TrainData, LabelsData, cv::Mat(), cv::Mat(), Param);
  
  //SVM.train(TrainData, LabelsData);
  //SVM.train_auto(TrainData, LabelsData, cv::Mat(), cv::Mat(), Param);
  
  // qDebug() << "Resultado:  " << SVM.predict(sample2);
    
}

void SpecificWorker::PredictSVM (cv::Mat ActualExerciseData, cv::Mat &ResultData) {
  
  ResultData = SVM.predict(ActualExerciseData);
  
  cout << "Result SVM " << ResultData << endl;
  
}

void SpecificWorker::TrainDTree (cv::Mat TrainData, cv::Mat LabelsData) {
  
   CvDTreeParams Param = CvDTreeParams(); //Coge los valores por defecto
  
//    cv::Mat var_type(3, 1, CV_8U);
// 
//    // define attributes as numerical
//    var_type.at<unsigned int>(0,0) = CV_VAR_NUMERICAL;
//    var_type.at<unsigned int>(0,1) = CV_VAR_NUMERICAL;
//    // define output node as numerical
//    var_type.at<unsigned int>(0,2) = CV_VAR_NUMERICAL;
  
  //DTree.train (TrainData,CV_ROW_SAMPLE, LabelsData, cv::Mat(), cv::Mat(), var_type, cv::Mat(), Param);
  DTree.train (TrainData, CV_ROW_SAMPLE, LabelsData, cv::Mat(), cv::Mat(), cv::Mat(), cv::Mat(), Param);
  
}

void SpecificWorker::PredictDTree (cv::Mat ActualExerciseData, cv::Mat &ResultData) {
  
  CvDTreeNode* prediction = DTree.predict(ActualExerciseData);
  ResultData = prediction->value;
  
  cout << "Result DTree " << ResultData << endl;
  
}


void SpecificWorker::Accuracy () {
  
  if (RadioButtonAccuracy->isChecked()) {
  
      char RoutAccuracyData [50] = "DataFiles/AccuracyData.txt";
      char RoutAccuracyLabels [50] = "DataFiles/AccuracyLabels.txt";
      char RoutAccuracyResults [50] = "DataFiles/AccuracyResults.txt";
      int AccuracyDTree;
      float RateDTree;
      //int AccuracyKNN, AccuracySVM;
      //float RateKNN, RateSVM; 
      int FileNumber, ColumnNumber, Iteration, i;
  
      if (Trained == true) {
  
	  //AccuracyKNN = AccuracySVM = AccuracyDTree = 0;
	  AccuracyDTree = 0;
      
	  FileNumber = GetLinesNumber (FileAccuracyData, RoutAccuracyData); 
	  ColumnNumber = GetColumnsNumber (FileAccuracyData, RoutAccuracyData);
   
	  cv::Mat DataMatrix (FileNumber, 150, CV_32FC1);  
	  cv::Mat LabelsMatrix (FileNumber, 1, CV_32FC1); 
	  cv::Mat FileDataMatrix (1, 150, CV_32FC1);
//        cv::Mat PreditedKNN (1,1, CV_32FC1);
//        cv::Mat PredictedSVM (1,1, CV_32FC1);
	  cv::Mat PredictedDTree (1,1, CV_32FC1);
   
	  GetCvMatrix (FileAccuracyData, RoutAccuracyData, DataMatrix, FileNumber); //Fichero de entrenamiento
	  GetCvMatrix (FileAccuracyLabels, RoutAccuracyLabels, LabelsMatrix, FileNumber); //Fichero de labels
      
	  Iteration = 0;

	  while (Iteration<FileNumber) {
	
	    for (i=0; i<ColumnNumber; i++) {
	  
	      FileDataMatrix.at<float>(0,i) = DataMatrix.at<float>(Iteration,i); 
	  
	    }
	
/*	    PredictKNN (FileDataMatrix, PreditedKNN);
	  
	    if (LabelsMatrix.at<float>(Iteration,0) == PreditedKNN.at<float>(0,0)) {
	      AccuracyKNN++;
	    }
*/	  
/*	    PredictSVM (FileDataMatrix, PredictedSVM);
	  
	    if (LabelsMatrix.at<float>(Iteration,0) == PredictedSVM.at<float>(0,0)) {
	      AccuracySVM++;
	    }
*/	    
	    PredictDTree (FileDataMatrix, PredictedDTree);
	  
	    if (LabelsMatrix.at<float>(Iteration,0) == PredictedDTree.at<float>(0,0)) {
	      AccuracyDTree++;
	    }
	  
	  Iteration++;
	  
	}
      
//      RateKNN = (AccuracyKNN/Iteration)*100;
//      RateSVM = (AccuracySVM/Iteration)*100;
	RateDTree = (AccuracyDTree/Iteration)*100; 
      
	FileAccuracyResults = fopen (RoutAccuracyResults, "w");
   
	if (FileAccuracyResults==NULL) {
     
	    cout<<"Error opening the Accuracy Results File"<<endl;
	    system("pause");
	    exit (EXIT_FAILURE);
    
	}
      
//      fprintf(FileAccuracyResults,"RateKK: %f \n",RateKNN);
//      fprintf(FileAccuracyResults,"Rate SVM: %f \n",RateSVM);
	fprintf(FileAccuracyResults,"RateDTree: %f \n",RateDTree);
	

    }
  
    else {
	  
	  cout <<  endl << "Come back to Training Mode and train the component first" << endl << endl;
	  
    }
  }
      
        
}


void SpecificWorker::SimonSays() {
  
     if (RadioButtonSimon->isChecked()) {
     
	if (Trained == true) {
	      
	    if (AskNewExercise == true) {
	      
		cout << endl << endl << "Well done! Let's do now the next Level!" << endl;
	     
		cout << endl << "Level " << Level << endl;
		
		NextExercise = rand() % 4 + 1;
		
		CheckRepeatedExercise();
	            	      
		cout << endl << endl << "The next exercise to realize is number " << NextExercise << endl << endl;

		ExerciseToDo[Level] = NextExercise;
	      
		if (Level<NUMBERLEVEL) {
		    Level++;
		}
		else {
		  Level=0;
		}	
		
		SequenceLevel = 0;
	      
		AskNewExercise = false;
	    
	    }
	  
	    else {
	      
	      	if (SequenceLevel<=Level) {
	   
		    CheckButtonExercisePushed(ExerciseToDo[SequenceLevel]);
		    
		    if (ExerciseCorrect == true) {
	    
			if (KeepingExercise >= 100) {
	      
			  cout << endl << "Well done! Let's do now the next exercise!" << endl;
			  ExerciseCorrect = false;
			  KeepingExercise = 0;
			  SequenceLevel++;
			  
			  if (SequenceLevel==Level) {
			    
			    AskNewExercise = true;
			    
			  }
	      
			}
			else {
	      
			  KeepingExercise++;
	      
			}
		    }
		
		}

	    }
	   
	}
	
	else {
	  
	  cout <<  endl << "Come back to Training Mode and train the component first" << endl << endl;
	  
	}
     
   }

}

void SpecificWorker::CheckButtonExercisePushed (int ExerciseSequence) {
  
	if (PushedExercise1==true) {
	      
		SetExercise(1, ExerciseSequence);
		PushedExercise1 = false;
	      
	}
	    
	if (PushedExercise2==true) {
	      
		SetExercise(2, ExerciseSequence);
		PushedExercise2 = false; 
	}
	    
	if (PushedExercise3==true) {
	      
		SetExercise(3, ExerciseSequence);
		PushedExercise3 = false; 
	}
	    
	if (PushedExercise4==true) {
	      
		SetExercise(4, ExerciseSequence);
		PushedExercise4 = false;
	      
	}
	    
	if (PushedExercise0==true) {
	      
		SetExercise(0, ExerciseSequence); 
		PushedExercise0 = false;
	      
	}    

}


void SpecificWorker::DoExercise1(bool) {
  
  if (RadioButtonSimon->isChecked()) {
  
      PushedExercise1=true;
      
  }
  
}

void SpecificWorker::DoExercise2(bool) {
  
  if (RadioButtonSimon->isChecked()) {
  
      PushedExercise2=true;
      
  }
  
}

void SpecificWorker::DoExercise3(bool) {
  
  if (RadioButtonSimon->isChecked()) {
  
      PushedExercise3=true;
      
  }
  
}

void SpecificWorker::DoExercise4(bool) {
  
  if (RadioButtonSimon->isChecked()) {
  
      PushedExercise4=true;
      
  }
  
}

void SpecificWorker::DoExercise0(bool) {
  
  if (RadioButtonSimon->isChecked()) {
  
      PushedExercise0=true;
      
  }
  
}

void SpecificWorker::SetExercise (int ExerciseDone, int ExerciseSequence) {
	      
	cout << endl << "Exercise realized has been the number " << ExerciseDone << endl;
	
	if (ExerciseDone == 0) {
		  
		cout << endl << "The exercise realized is not defined in the game. Try to remember the correct exercise!" << endl;
		  
	}
	
	else {
	      
		if (ExerciseDone == ExerciseSequence) {
		
			ExerciseCorrect = true;
		
			cout << endl << "Well done! Keep doing the exercise " << ExerciseDone << "!" << endl;
		
		}
	      
		else {
		
			cout << endl << "Try to remember the correct exercise!" << endl;
		
		}
	}
  
}

void SpecificWorker::CheckRepeatedExercise () {
  
  bool Repeated = true;
  
  		if ((Level+1)%4==0) {
		    while (Repeated==true) {
		      if (NextExercise!=ExerciseToDo[Level-1] && NextExercise!=ExerciseToDo[Level-2] && NextExercise!=ExerciseToDo[Level-3]) {
			Repeated=false;
		      }
		      else {
			NextExercise = rand() % 4 + 1;
		      }
		    }
		}
		else {
		
		    if ((Level+2)%4==0) {
			while (Repeated==true) {
			  if (NextExercise!=ExerciseToDo[Level-1] && NextExercise!=ExerciseToDo[Level-2]) {
			    Repeated=false;
			  }
			  else {
			    NextExercise = rand() % 4 + 1;
			  }
			}
		    }
		    else {
		      
			if ((Level+3)%4==0) {
			  while (Repeated==true) {
			    if (NextExercise!=ExerciseToDo[Level-1]) {
			      Repeated=false;
			    }
			    else {
			      NextExercise = rand() % 4 + 1;
			    }
			  }
			}
			else {
			  
			    if ((Level+4)%4==0) {
			      if (Level!=0) {
				  while (Repeated==true) {
				    if (NextExercise!=ExerciseToDo[Level-1]) {
				      Repeated=false;
				    }
				    else {
				      NextExercise = rand() % 4 + 1;
				    }
				  }
			      }
			    }
			} 
		    }
		}
  
}







 