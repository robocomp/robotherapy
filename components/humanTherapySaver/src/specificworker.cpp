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
SpecificWorker::SpecificWorker(MapPrx& mprx) : GenericWorker(mprx)
{

#ifdef USE_QTGUI
	innerModelViewer = NULL;
	osgView = new OsgView(this);
	osgGA::TrackballManipulator *tb = new osgGA::TrackballManipulator;
	osg::Vec3d eye(osg::Vec3(4000.,4000.,-1000.));
	osg::Vec3d center(osg::Vec3(0.,0.,-0.));
	osg::Vec3d up(osg::Vec3(0.,1.,0.));
	tb->setHomePosition(eye, center, up, false);
	tb->setByMatrix(osg::Matrixf::lookAt(eye,center,up));
	osgView->setCameraManipulator(tb);
#endif

relateJointsMeshes();

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
        innerModel = std::make_shared<InnerModel>(innermodel_path);
	}
	catch(std::exception e) { qFatal("Error reading config params"); }


#ifdef USE_QTGUI
	innerModelViewer = new InnerModelViewer (innerModel, "root", osgView->getRootGroup(), false);
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

    printJointsFromAstra();
//    saveJointsFromAstra();
//    paintJointsFromFile();


#ifdef USE_QTGUI
	if (innerModelViewer) innerModelViewer->update();
	osgView->frame();
	osgView->autoResize();

#endif
}


void SpecificWorker::printJointsFromAstra()
{

    	try {
		PersonList users;
		humantracker_proxy->getUsersList(users);

		for (auto person : users)
		{
            if(!checkNecessaryJoints(person.second)) {
                return;
            }

            PaintSkeleton(person.second);
		}
	}

	catch(...) {}
}



void SpecificWorker::relateJointsMeshes()
{
    mapJointMesh["Neck"] = "XN_SKEL_NECK";
    mapJointMesh["MidSpine"] = "XN_SKEL_TORSO";

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
    jointListType joints = person.joints;



    for(auto upT : upperTrunk)
    {
        if(!joints.count(upT))
        {
            qDebug()<< "Falta " << QString::fromStdString(upT);
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
            qDebug()<< "Falta " << QString::fromStdString(lwT);
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

void SpecificWorker::paintJointsFromFile(){

    ifstream file;
    file.open("/home/robocomp/robocomp/components/human-detection/components/humanGame/joints.txt");

    if (!file) {
        cout << "Unable to open file";
        return;
    }

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
                poses.push_back( QString::fromStdString(joints[1]).toFloat());
                poses.push_back(QString::fromStdString(joints[2]).toFloat());
                poses.push_back(QString::fromStdString(joints[3]).toFloat());

                all_joints[joints[0]] = poses;
            }

        }

        person.joints = all_joints;
        if(!checkNecessaryJoints(person))
        {
            qDebug()<<"No se han encontrado todos los joints necesarios";
            continue;
        }

        PaintSkeleton(person);

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


void SpecificWorker::saveJointsFromAstra()
{

    fstream jointfile;
    jointfile.open ( "joints.txt" , ios::app);

    try
    {
        PersonList users;
        humantracker_proxy-> getUsersList(users);

        if(users.size()== 0)
            return;

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
    }

    catch(...) {}

    jointfile.close();

}


void SpecificWorker::PaintSkeleton (TPerson &person) {

    qDebug()<<__FUNCTION__;

    CalculateJointRotations(person);

    for (auto dictionaryNamesIt : mapJointMesh) {

        try {
            Pose3D pose;
            string idJoint = dictionaryNamesIt.first;
            QString TypeJoint = dictionaryNamesIt.second;

            auto joints = person.joints;

            if (joints.find(idJoint) != joints.end()) //Si se encuentra el joint
            {
                auto itUp = std::find(upperTrunk.begin(), upperTrunk.end(), idJoint);
                auto itLw = std::find(lowerTrunk.begin(), lowerTrunk.end(), idJoint);

                if ((itUp != upperTrunk.end() and upperTrunkFound) or (itLw  != lowerTrunk.end() and lowerTrunkFound)) //Se comprueba que si el joint pertenece al tronco X se haya encontrado todo eltronco antes de actualizar
                {
                    if (SetPoses (pose, idJoint))
                    {
                        qDebug()<< "Actualizando " << QString::fromStdString(idJoint);
                        innerModel->updateTransformValues(TypeJoint,pose.x,pose.y,pose.z,pose.rx,pose.ry,pose.rz);
                    }
                }

            }
        }
        catch (...) {
            qDebug()<<"Error in PaintSkeleton";
        }

    }

    innerModel->update();

    innerModelViewer->update();
    osgView->frame();
    osgView->autoResize();

    innerModel->save("SavedInnerModel.xml");

    upperTrunkFound = false;
    lowerTrunkFound = false;

}





void SpecificWorker::CalculateJointRotations (TPerson &p) {

    RTMat orbbec;

    if (upperTrunkFound)
    {
        qDebug()<<"-------------------------------- UPPER TRUNK --------------------------------";

        mapJointRotations["MidSpine"] = RTMatFromJointPosition (orbbec,p.joints["MidSpine"],p.joints["Neck"], p.joints["MidSpine"], 2);
        mapJointRotations["Neck"] = RTMatFromJointPosition (mapJointRotations["MidSpine"],p.joints["Neck"],p.joints["Head"],p.joints["Neck"], 2);

        RTMat LEFT_SHOULDER_PRE_Z =  RTMatFromJointPosition(mapJointRotations["MidSpine"],p.joints["LeftShoulder"],p.joints["LeftElbow"], p.joints["LeftShoulder"], 2);
        RTMat RIGHT_SHOULDER_PRE_Z = RTMatFromJointPosition(mapJointRotations["MidSpine"],p.joints["RightShoulder"],p.joints["RightElbow"],p.joints["RightShoulder"], 2);

        RotateTorso (RIGHT_SHOULDER_PRE_Z.getTr(), LEFT_SHOULDER_PRE_Z.getTr());

        mapJointRotations["LeftShoulder"]=RTMatFromJointPosition (mapJointRotations["MidSpine"],p.joints["LeftShoulder"],p.joints["LeftElbow"],p.joints["LeftShoulder"], 2);
        mapJointRotations["RightShoulder"] = RTMatFromJointPosition(mapJointRotations["MidSpine"],p.joints["RightShoulder"], p.joints["RightElbow"],p.joints["RightShoulder"], 2);

        mapJointRotations["LeftElbow"]=RTMatFromJointPosition (mapJointRotations["MidSpine"]*mapJointRotations["LeftShoulder"],p.joints["LeftElbow"],p.joints["LeftHand"],	p.joints["LeftElbow"], 2);
        mapJointRotations["RightElbow"] = RTMatFromJointPosition (mapJointRotations["MidSpine"]*mapJointRotations["RightShoulder"],p.joints["RightElbow"],p.joints["RightHand"],p.joints["RightElbow"], 2);

        mapJointRotations["LeftHand"] = RTMatFromJointPosition(mapJointRotations["MidSpine"]*mapJointRotations["LeftShoulder"]*mapJointRotations["LeftElbow"],p.joints["LeftHand"],p.joints["LeftElbow"],p.joints["LeftHand"], 2);
        mapJointRotations["RightHand"] = RTMatFromJointPosition(mapJointRotations["MidSpine"]*mapJointRotations["RightShoulder"]*mapJointRotations["RightElbow"],p.joints["RightHand"],p.joints["RightElbow"],p.joints["RightHand"], 2);

    }

    if (lowerTrunkFound)
    {
        qDebug()<<"-------------------------------- LOWER TRUNK --------------------------------";

        mapJointRotations["BaseSpine"]=RTMatFromJointPosition (mapJointRotations["MidSpine"],p.joints["BaseSpine"],p.joints["MidSpine"] ,p.joints["BaseSpine"], 2);

        mapJointRotations["LeftHip"]=RTMatFromJointPosition (mapJointRotations["MidSpine"]*mapJointRotations["BaseSpine"],p.joints["LeftHip"],p.joints["LeftKnee"],p.joints["LeftHip"], 2);
        mapJointRotations["RightHip"]=RTMatFromJointPosition (mapJointRotations["MidSpine"]*mapJointRotations["BaseSpine"],p.joints["RightHip"],p.joints["RightKnee"],p.joints["RightHip"], 2);

        mapJointRotations["LeftKnee"]=RTMatFromJointPosition (mapJointRotations["MidSpine"]*mapJointRotations["BaseSpine"]*mapJointRotations["LeftHip"],p.joints["LeftKnee"],p.joints["LeftFoot"],p.joints["LeftKnee"], 2);
        mapJointRotations["RightKnee"]=RTMatFromJointPosition (mapJointRotations["MidSpine"]*mapJointRotations["BaseSpine"]*mapJointRotations["RightHip"],p.joints["RightKnee"],p.joints["RightFoot"],p.joints["RightKnee"], 2);

        mapJointRotations["LeftFoot"]=RTMatFromJointPosition(mapJointRotations["MidSpine"]*mapJointRotations["BaseSpine"]*mapJointRotations["LeftHip"]*mapJointRotations["LeftKnee"],p.joints["LeftFoot"],p.joints["LeftKnee"],p.joints["LeftFoot"], 2);
        mapJointRotations["RightFoot"]=RTMatFromJointPosition(mapJointRotations["MidSpine"]*mapJointRotations["BaseSpine"]*mapJointRotations["RightHip"]*mapJointRotations["RightKnee"],p.joints["RightFoot"],p.joints["RightKnee"],p.joints["RightFoot"], 2);

    }


qDebug()<<"  ";
qDebug()<<"  ";
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

    qDebug()<<__FUNCTION__;

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
