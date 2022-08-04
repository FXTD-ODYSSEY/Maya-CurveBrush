#ifndef __curveBrushContextTool_H__
#define __curveBrushContextTool_H__

#include <stdio.h>
#include <math.h>
#include <map>

#include <maya/MIOStream.h>
#include <maya/MString.h>
#include <maya/MArgList.h>
#include <maya/MEvent.h>
#include <maya/MGlobal.h>
#include <maya/M3dView.h>
#include <maya/MPoint.h>
#include <maya/MPointArray.h>
#include <maya/MDoubleArray.h>
#include <maya/MDagPath.h>

#include <maya/MPxContext.h>
#include <maya/MPxContextCommand.h>
#include <maya/MPxToolCommand.h>
#include <maya/MToolsInfo.h>

#include <maya/MSyntax.h>
#include <maya/MArgParser.h>
#include <maya/MArgDatabase.h>
#include <maya/MCursor.h>

#include <maya/MFnMesh.h>
#include <maya/MFnNurbsCurve.h>
#include <maya/MItSelectionList.h>
#include <maya/MItCurveCV.h>
#include <maya/MColorArray.h>
#include <maya/MDagPathArray.h>

#include <maya/MGL.h>

#define kRadiusFlag "-r"
#define kRadiusFlagLong "-radius"
#define kStrengthFlag "-s"
#define kStrengthFlagLong "-strength"

class curveBrushTool : public MPxToolCommand
{
public:
    curveBrushTool();
    ~curveBrushTool() override;
    static void *creator();

    MStatus doIt(const MArgList &args) override;
    MStatus parseArgs(const MArgList &args);
    MStatus redoIt() override;
    MStatus undoIt() override;
    bool isUndoable() const override;
    MStatus finalize() override;
    static MSyntax newSyntax();

    void setRadius(double value);
    void setStrength(double value);
    void setStartPoint(MPoint value);
    void setMoveVector(MVector value);
    void setDagPathArray(MDagPathArray value);

private:
    double radius;
    double strength;
    MPoint startPoint;
    MVector moveVector;
    MDagPathArray dagPathArray;
    std::map<int, std::map<int,MPoint>> curvePointMap;
};

#endif
