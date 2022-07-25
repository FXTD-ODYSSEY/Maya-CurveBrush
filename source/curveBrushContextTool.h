#ifndef __curveBrushContextTool_H__
#define __curveBrushContextTool_H__

#include <stdio.h>
#include <maya/MIOStream.h>
#include <math.h>

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

#include <maya/MFnNurbsCurve.h>

#include <maya/MSyntax.h>
#include <maya/MArgParser.h>
#include <maya/MArgDatabase.h>
#include <maya/MCursor.h>

#include <maya/MGL.h>

#define kPitchFlag "-p"
#define kPitchFlagLong "-pitch"
#define kRadiusFlag "-r"
#define kRadiusFlagLong "-radius"
#define kNumberCVsFlag "-ncv"
#define kNumberCVsFlagLong "-numCVs"
#define kUpsideDownFlag "-ud"
#define kUpsideDownFlagLong "-upsideDown"

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

	void setRadius(double newRadius);
	void setPitch(double newPitch);
	void setNumCVs(unsigned newNumCVs);
	void setUpsideDown(bool newUpsideDown);

private:
	double radius;	// Helix radius
	double pitch;	// Helix pitch
	unsigned numCV; // Helix number of CVs
	bool upDown;	// Helix upsideDown
	MDagPath path;	// The dag path to the curve.
					// Don't save the pointer!
};

#endif
