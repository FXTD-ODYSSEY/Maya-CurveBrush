#include "curveBrushContext.h"

/////////////////////////////////////////////////////////////
//
// The user Context
//
//   Contexts give the user the ability to write functions
//   for handling events.
//
//   Contexts aren't registered in the plugin, instead a
//   command class (MPxContextCommand) is registered and is used
//   to create instances of the context.
//
/////////////////////////////////////////////////////////////

curveBrushContext::curveBrushContext() : bInStroke(false), bFalloffMode(true)
{
	setTitleString("Curve Brush Tool");

	setCursor(MCursor::defaultCursor);

	// Tell the context which XPM to use so the tool can properly
	// be a candidate for the 6th position on the mini-bar.
	setImage("pythonFamily.png", MPxContext::kImage1);
}

void curveBrushContext::toolOnSetup(MEvent &event)
{
	setHelpString(helpString);
	QCoreApplication *app = qApp;
	app->installEventFilter(this);
	// NOTE(timmyliang): get current selected the object as handle object
	MSelectionList activeList;
	MGlobal::getActiveSelectionList(activeList);
	meshArray.clear();
	for (MItSelectionList curveIter(activeList, MFn::kMesh); !curveIter.isDone(); curveIter.next())
	{
		MDagPath curDag;
		MObject curCompObj;
		curveIter.getDagPath(curDag, curCompObj);
		meshArray.append(curDag);
	}
	if (meshArray.length() == 0)
	{
		MGlobal::displayWarning("No mesh selected.");
	}
}

void curveBrushContext::toolOffCleanup()
{
	QCoreApplication *app = qApp;
	app->removeEventFilter(this);
}

bool curveBrushContext::eventFilter(QObject *object, QEvent *event)
{
	if (QKeyEvent *e = dynamic_cast<QKeyEvent *>(event))
	{
		if (e->type() == QEvent::KeyPress)
			doKeyPress(e);
		else if (e->type() == QEvent::KeyRelease)
			doKeyRelease(e);
	}
	return false;
}

bool curveBrushContext::doKeyPress(QKeyEvent *event)
{
	if (bInStroke)
		return false;

	if (event->key() == Qt::Key_B)
	{
		eDragMode = kBrushSize;
		return true;
	}

	return false;
}

bool curveBrushContext::doKeyRelease(QKeyEvent *event)
{
	if (bInStroke)
		return false;

	if (eDragMode != kNormal)
	{
		eDragMode = kNormal;
		return true;
	}

	return false;
}

MStatus curveBrushContext::doPress(MEvent &event, MHWRender::MUIDrawManager &drawMgr, const MHWRender::MFrameContext &context)
{
	view = M3dView::active3dView();
	event.getPosition(startPosX, startPosY);
	fStartBrushSize = mBrushConfig.size();

	return MS::kSuccess;
}

MStatus curveBrushContext::doRelease(MEvent &event, MHWRender::MUIDrawManager &drawMgr, const MHWRender::MFrameContext &context)
{
	view.refresh(false, true);
	return MS::kSuccess;
}

MStatus curveBrushContext::doDrag(MEvent &event, MHWRender::MUIDrawManager &drawMgr, const MHWRender::MFrameContext &context)
{
	view.refresh(false, true);
	short currentPosX, currentPosY;
	event.getPosition(currentPosX, currentPosY);
	auto currentPos = MPoint(currentPosX, currentPosY);

	drawMgr.beginDrawable();
	drawMgr.setColor(MColor(1.f, 1.f, 1.f));
	drawMgr.setLineWidth(2.0f);

	if (eDragMode == kBrushSize)
	{
		MPoint start(startPosX, startPosY);
		auto delta = MVector(currentPos - start);
		// NOTE(timmyliang): calculate delta vector

		// NOTES(timmyliang): left mouse for size
		if (event.mouseButton() == MEvent::kLeftMouse)
		{
			mBrushConfig.setSize(fStartBrushSize + delta.length());
		}
		// NOTES(timmyliang): middle mouse for strength
		else if (event.mouseButton() == MEvent::kMiddleMouse)
		{
		}

		drawMgr.line2d(start, MPoint(startPosX, currentPosY - startPosY));
		drawMgr.circle2d(start, mBrushConfig.size());
	}

	drawMgr.endDrawable();
	return MS::kSuccess;
}

// MStatus curveBrushContext::drawFeedback(MHWRender::MUIDrawManager &drawMgr, const MHWRender::MFrameContext &context)
// {
// 	// to draw the brush ring.
// 	drawMgr.beginDrawable();

// 	drawMgr.setColor(MColor(1.f, 1.f, 1.f));
// 	drawMgr.setLineWidth(2.0f);
// 	drawMgr.circle2d(mBrushCenterScreenPoint, mBrushConfig.size());

// 	drawMgr.endDrawable();

// 	return MS::kSuccess;
// }

// inline void getSelected()
// {

// 	MSelectionList selectionList;
// 	MGlobal::getActiveSelectionList(selectionList);
// 	MObject mesh;
// 	selectionList.getDependNode(0, mesh);
// 	MFnMesh fnMesh(mesh);
// 	fnMesh.getPoints(meshPoints);
// 	fnMesh.getPolygonVertices(0, meshIndices);
// }

MStatus curveBrushContext::doPtrMoved(MEvent &event, MHWRender::MUIDrawManager &drawMgr, const MHWRender::MFrameContext &context)
{
	// view = M3dView::active3dView();
	// view.refresh(false, true);
	// MSelectionList incomingList, marqueeList;
	short x, y;
	event.getPosition(x, y);
	mBrushCenterScreenPoint = MPoint(x, y);
	auto radius = mBrushConfig.size();
	// if (bFalloffMode)
	// {
	// 	float start_x, start_y, last_x, last_y;
	// 	// NOTES(timmyliang): get selected objects
	// 	MGlobal::getActiveSelectionList(incomingList);
	// 	start_x = x - radius;
	// 	start_y = y - radius;
	// 	last_x = x + radius;
	// 	last_y = y + radius;
	// 	MGlobal::selectFromScreen(start_x, start_y, last_x, last_y,
	// 							  MGlobal::kReplaceList,
	// 							  MGlobal::kWireframeSelectMethod);

	// 	MGlobal::getActiveSelectionList(marqueeList);
	// 	MGlobal::setActiveSelectionList(incomingList, MGlobal::kReplaceList);
	// }

	drawMgr.beginDrawable();

	drawMgr.setColor(MColor(1.f, 1.f, 1.f));
	drawMgr.setLineWidth(2.0f);
	drawMgr.circle2d(mBrushCenterScreenPoint, radius);

	if (bFalloffMode)
	{
		for (unsigned int index = 0; index < meshArray.length(); ++index)
		{
			// MGlobal::displayInfo(meshArray[index].fullPathName());
			MFloatPointArray pointArray;
			MFloatVectorArray normalArray;
			MColorArray colorArray;
			MIntArray vertexCount, vertexList;
			MFnMesh mesh(meshArray[index]);

			mesh.getPoints(pointArray,MSpace::kWorld);
			mesh.getNormals(normalArray);
			mesh.getTriangles(vertexCount, vertexList);
			// NOTE(timmyliang): convert to MUintArray
			MUintArray vertexUList;
			for (unsigned int index2 = 0; index2 < vertexList.length(); ++index2)
				vertexUList.append((unsigned int)vertexList[index2]);

			for (MItMeshVertex vertexIter(meshArray[index]); !vertexIter.isDone(); vertexIter.next())
			{
				colorArray.append(MColor(std::rand() / double(RAND_MAX), std::rand() / double(RAND_MAX)));
			}
			// NOTE(timmyliang): draw falloff
			drawMgr.mesh(MHWRender::MUIDrawManager::kTriStrip, pointArray, &normalArray, &colorArray, &vertexUList);

			// drawMgr.points(pointArray,false);
		}
	}

	drawMgr.endDrawable();

	// printf("x:%d y:%d", x, y);
	return MS::kSuccess;
}

MStatus curveBrushContext::doEnterRegion(MEvent &)
{
	return setHelpString(helpString);
}

void curveBrushContext::getClassName(MString &name) const
{
	name.set("curveBrush");
}
