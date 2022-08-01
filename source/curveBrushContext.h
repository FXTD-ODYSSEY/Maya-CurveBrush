#ifndef __curveBrushContext_H__
#define __curveBrushContext_H__

#include "curveBrushContextTool.h"

#include <maya/MString.h>
#include <maya/MUIDrawManager.h>
#include <maya/MFrameContext.h>
#include <maya/MColor.h>

#include <maya/MFnMesh.h>
#include <maya/MFnNurbsCurve.h>
#include <maya/MItSelectionList.h>
#include <maya/MItMeshVertex.h>
#include <maya/MColorArray.h>
#include <maya/MDagPathArray.h>
#include <maya/MFloatPointArray.h>
#include <maya/MUintArray.h>

#include <QtCore/QObject>
#include <QtWidgets/QApplication>
#include <QtCore/QEvent>
#include <QtGui/QKeyEvent>

// ---------------------------------------------------------------------
// the context
// ---------------------------------------------------------------------

const char helpString[] = "Click and drag to draw helix";

struct BrushConfig
{
	BrushConfig() : fSize(50.0f), fStrength(25.0f){};
	float size() const { return fSize; }
	void setSize(float value) { fSize = value > 0 ? value : 0; }
	float strength() const { return fStrength; }
	void setStrength(float value) { fStrength = value > 0 ? value : 0; }

private:
	float fSize;
	float fStrength;
};

class curveBrushContext : public QObject, public MPxContext
{
public:
	curveBrushContext();
	void toolOnSetup(MEvent &event) override;
	void toolOffCleanup() override;

	// MStatus doPress(MEvent &event) override;
	// MStatus doDrag(MEvent &event) override;
	// MStatus doRelease(MEvent &event) override;
	MStatus doEnterRegion(MEvent &event) override;

	void getClassName(MString &name) const override;

	MStatus doPress(MEvent &event,
					MHWRender::MUIDrawManager &drawManager,
					const MHWRender::MFrameContext &context);
	MStatus doDrag(MEvent &event,
				   MHWRender::MUIDrawManager &drawManager,
				   const MHWRender::MFrameContext &context);
	MStatus doRelease(MEvent &event,
					  MHWRender::MUIDrawManager &drawManager,
					  const MHWRender::MFrameContext &context);

	MStatus doPtrMoved(MEvent &event, MHWRender::MUIDrawManager &drawMgr, const MHWRender::MFrameContext &context);
	bool eventFilter(QObject *object, QEvent *event);

	bool doKeyPress(QKeyEvent *event);
	bool doKeyRelease(QKeyEvent *event);

private:
	void drawGuide();

	enum DragMode
	{
		kNormal,
		kBrushSize
	};
	DragMode eDragMode;
	BrushConfig mBrushConfig;
	MPoint mBrushCenterScreenPoint;
	bool bInStroke;
	bool bFalloffMode = true;
	float fStartBrushSize;
	float fStartBrushStrength;

	MDagPathArray objDagPathArray;

	short startPosX, startPosY;
	short endPosX, endPosY;
	M3dView view;
};

#endif
