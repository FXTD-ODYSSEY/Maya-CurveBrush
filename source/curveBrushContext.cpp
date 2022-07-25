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

curveBrushContext::curveBrushContext()
{
	numCV = 20;
	upDown = false;
	setTitleString("Helix Tool");

	setCursor(MCursor::defaultCursor);

	// Tell the context which XPM to use so the tool can properly
	// be a candidate for the 6th position on the mini-bar.
	setImage("helixTool.xpm", MPxContext::kImage1);
}

void curveBrushContext::toolOnSetup(MEvent &)
{
	setHelpString(helpString);
}

MStatus curveBrushContext::doPress(MEvent &event)
{
	event.getPosition(startPos_x, startPos_y);
	view = M3dView::active3dView();
	firstDraw = true;
	return MS::kSuccess;
}

MStatus curveBrushContext::doDrag(MEvent &event)
{
	event.getPosition(endPos_x, endPos_y);

	return MS::kSuccess;
}

MStatus curveBrushContext::doRelease(MEvent &)
{
	curveBrushTool *cmd = (curveBrushTool *)newToolCommand();
	cmd->setPitch(height / numCV);
	cmd->setRadius(radius);
	cmd->setNumCVs(numCV);
	cmd->setUpsideDown(upDown);
	cmd->redoIt();
	cmd->finalize();
	return MS::kSuccess;
}

MStatus curveBrushContext::doEnterRegion(MEvent &)
{
	return setHelpString(helpString);
}

void curveBrushContext::getClassName(MString &name) const
{
	name.set("helix");
}

void curveBrushContext::setNumCVs(unsigned newNumCVs)
{
	numCV = newNumCVs;
	MToolsInfo::setDirtyFlag(*this);
}

void curveBrushContext::setUpsideDown(bool newUpsideDown)
{
	upDown = newUpsideDown;
	MToolsInfo::setDirtyFlag(*this);
}

unsigned curveBrushContext::numCVs()
{
	return numCV;
}

bool curveBrushContext::upsideDown()
{
	return upDown;
}
