////////////////////////////////////////////////////////////////////////
//
// DESCRIPTION:
//
// Interactive tool to draw a helix. Uses OpenGL to draw a guideline for the helix.
//
// Produces the MEL commands: helixToolCmd and helixToolContext.
//
// This example takes the helix example one large step forward by wrapping the command in a context.
// This allows you to drag out the region in which you want the helix drawn.
// To use it, you must first execute the command "source helixTool".
// This will create a new entry in the "Shelf1" tab of the tool shelf called "Helix Tool".
// Click on the new icon, then move the cursor into the perspective window and drag out a cylinder
// which defines the volume in which the helix will be generated.
// This plug-in is an example of building a context around a command.
//
// To create a tool command:
//
//	(1) Create a tool command class.
//		Same process as an MPxCommand except define 2 methods
//		for interactive use: cancel and finalize.
//		There is also an addition constructor MPxToolCommand(), which
//		is called from your context when the command needs to be invoked.
//
//	(2) Define your context.
//		This is accomplished by deriving off of MPxContext and overriding
//		whatever methods you need.
//
//	(3) Create a command class to create your context.
//		You will call this command in Maya to create and name a context.
//
////////////////////////////////////////////////////////////////////////

#include "curveBrushContextTool.h"


/////////////////////////////////////////////////////////////
// The users tool command
/////////////////////////////////////////////////////////////

void *curveBrushTool::creator()
{
	return new curveBrushTool;
}

curveBrushTool::~curveBrushTool() {}

curveBrushTool::curveBrushTool()
{
	numCV = 20;
	upDown = false;
	setCommandString("helixToolCmd");
}

MSyntax curveBrushTool::newSyntax()
{
	MSyntax syntax;

	syntax.addFlag(kPitchFlag, kPitchFlagLong, MSyntax::kDouble);
	syntax.addFlag(kRadiusFlag, kRadiusFlagLong, MSyntax::kDouble);
	syntax.addFlag(kNumberCVsFlag, kNumberCVsFlagLong, MSyntax::kUnsigned);
	syntax.addFlag(kUpsideDownFlag, kUpsideDownFlagLong, MSyntax::kBoolean);

	return syntax;
}

MStatus curveBrushTool::doIt(const MArgList &args)
//
// Description
//     Sets up the helix parameters from arguments passed to the
//     MEL command.
//
{
	MStatus status;

	status = parseArgs(args);

	if (MS::kSuccess != status)
		return status;

	return redoIt();
}

MStatus curveBrushTool::parseArgs(const MArgList &args)
{
	MStatus status;
	MArgDatabase argData(syntax(), args);

	if (argData.isFlagSet(kPitchFlag))
	{
		double tmp;
		status = argData.getFlagArgument(kPitchFlag, 0, tmp);
		if (!status)
		{
			status.perror("pitch flag parsing failed");
			return status;
		}
		pitch = tmp;
	}

	if (argData.isFlagSet(kRadiusFlag))
	{
		double tmp;
		status = argData.getFlagArgument(kRadiusFlag, 0, tmp);
		if (!status)
		{
			status.perror("radius flag parsing failed");
			return status;
		}
		radius = tmp;
	}

	if (argData.isFlagSet(kNumberCVsFlag))
	{
		unsigned tmp;
		status = argData.getFlagArgument(kNumberCVsFlag, 0, tmp);
		if (!status)
		{
			status.perror("numCVs flag parsing failed");
			return status;
		}
		numCV = tmp;
	}

	if (argData.isFlagSet(kUpsideDownFlag))
	{
		bool tmp;
		status = argData.getFlagArgument(kUpsideDownFlag, 0, tmp);
		if (!status)
		{
			status.perror("upside down flag parsing failed");
			return status;
		}
		upDown = tmp;
	}

	return MS::kSuccess;
}

MStatus curveBrushTool::redoIt()
//
// Description
//     This method creates the helix curve from the
//     pitch and radius values
//
{
	MStatus stat;

	const unsigned deg = 3;						 // Curve Degree
	const unsigned ncvs = numCV;				 // Number of CVs
	const unsigned spans = ncvs - deg;			 // Number of spans
	const unsigned nknots = spans + 2 * deg - 1; // Number of knots
	unsigned i;
	MPointArray controlVertices;
	MDoubleArray knotSequences;

	int upFactor;
	if (upDown)
		upFactor = -1;
	else
		upFactor = 1;

	// Set up cvs and knots for the helix
	//
	for (i = 0; i < ncvs; i++)
		controlVertices.append(MPoint(radius * cos((double)i),
									  upFactor * pitch * (double)i,
									  radius * sin((double)i)));

	for (i = 0; i < nknots; i++)
		knotSequences.append((double)i);

	// Now create the curve
	//
	MFnNurbsCurve curveFn;

	curveFn.create(controlVertices, knotSequences, deg,
				   MFnNurbsCurve::kOpen, false, false,
				   MObject::kNullObj, &stat);

	if (!stat)
	{
		stat.perror("Error creating curve");
		return stat;
	}

	stat = curveFn.getPath(path);

	return stat;
}

MStatus curveBrushTool::undoIt()
//
// Description
//     Removes the helix curve from the model.
//
{
	MStatus stat;
	MObject transform = path.transform();
	stat = MGlobal::deleteNode(transform);
	return stat;
}

bool curveBrushTool::isUndoable() const
//
// Description
//     Set this command to be undoable.
//
{
	return true;
}

MStatus curveBrushTool::finalize()
//
// Description
//     Command is finished, construct a string for the command
//     for journaling.
//
{
	MArgList command;
	command.addArg(commandString());
	command.addArg(MString(kRadiusFlag));
	command.addArg(radius);
	command.addArg(MString(kPitchFlag));
	command.addArg(pitch);
	command.addArg(MString(kNumberCVsFlag));
	command.addArg((int)numCV);
	command.addArg(MString(kUpsideDownFlag));
	command.addArg(upDown);
	return MPxToolCommand::doFinalize(command);
}

void curveBrushTool::setRadius(double newRadius)
{
	radius = newRadius;
}

void curveBrushTool::setPitch(double newPitch)
{
	pitch = newPitch;
}

void curveBrushTool::setNumCVs(unsigned newNumCVs)
{
	numCV = newNumCVs;
}

void curveBrushTool::setUpsideDown(bool newUpsideDown)
{
	upDown = newUpsideDown;
}
