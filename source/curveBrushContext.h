#ifndef __curveBrushContext_H__
#define __curveBrushContext_H__

#include "curveBrushContextTool.h"

// ---------------------------------------------------------------------
// the context
// ---------------------------------------------------------------------

const char helpString[] = "Click and drag to draw helix";

class curveBrushContext : public MPxContext
{
public:
	curveBrushContext();
	void toolOnSetup(MEvent &event) override;

	MStatus doPress(MEvent &event) override;
	MStatus doDrag(MEvent &event) override;
	MStatus doRelease(MEvent &event) override;
	MStatus doEnterRegion(MEvent &event) override;

	void getClassName(MString &name) const override;

	void setNumCVs(unsigned newNumCVs);
	void setUpsideDown(bool newUpsideDown);
	unsigned numCVs();
	bool upsideDown();

private:
	void drawGuide();

	bool firstDraw;
	short startPos_x, startPos_y;
	short endPos_x, endPos_y;
	unsigned numCV;
	bool upDown;
	M3dView view;
	GLdouble height, radius;
};


#endif

