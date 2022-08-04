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
    setCommandString("curveBrushToolCmd");
}

MSyntax curveBrushTool::newSyntax()
{
    MSyntax syntax;

    // TODO(timmyliang) specific syntax for the tool command
    syntax.addFlag(kStrengthFlag, kStrengthFlagLong, MSyntax::kDouble);
    syntax.addFlag(kRadiusFlag, kRadiusFlagLong, MSyntax::kDouble);
    return syntax;
}

MStatus curveBrushTool::doIt(const MArgList &args)
{
    MStatus status;

    status = parseArgs(args);

    if (MS::kSuccess != status)
        return status;

    return redoIt();
}

template <typename T>
inline MStatus getFlagArgument(MArgDatabase argData, char *flag, T &value)
{
    MStatus status;
    if (argData.isFlagSet(flag))
    {
        status = argData.getFlagArgument(flag, 0, value);
    }
    return status;
}

MStatus curveBrushTool::parseArgs(const MArgList &args)
{
    MStatus status;
    MArgDatabase argData(syntax(), args);

    CHECK_MSTATUS_AND_RETURN_IT(getFlagArgument(argData, kRadiusFlag, radius));
    CHECK_MSTATUS_AND_RETURN_IT(getFlagArgument(argData, kStrengthFlag, strength));

    return status;
}

MStatus curveBrushTool::redoIt()
{

    MVector offsetVector = moveVector * 0.002 * strength;
    M3dView view = M3dView::active3dView();

    // NOTE(timmyliang): move curves cv in radius
    short x_pos, y_pos;
    for (unsigned int index = 0; index < dagPathArray.length(); ++index)
    {
        MFnNurbsCurve curveFn(dagPathArray[index]);
        std::map<int, MVector> offsetMap;
        for (MItCurveCV cvIter(dagPathArray[index]); !cvIter.isDone(); cvIter.next())
        {
            MPoint pos = cvIter.position(MSpace::kWorld);
            int cvIndex = cvIter.index();
            curvePointMap[index][cvIndex] = pos;
            view.worldToView(pos, x_pos, y_pos);
            if ((startPoint - MPoint(x_pos, y_pos)).length() < radius)
            {
                offsetMap[cvIndex] = pos + offsetVector;
            }
        }
        for (const auto &it : offsetMap)
        {
            curveFn.setCV(it.first, it.second, MSpace::kWorld);
        }
        curveFn.updateCurve();
    }
    return MStatus::kSuccess;
}

MStatus curveBrushTool::undoIt()
{
    // NOTE(timmyliang): reset point position
    for (const auto &kv : curvePointMap)
    {
        MFnNurbsCurve curveFn(dagPathArray[kv.first]);
        for (const auto &it : kv.second)
        {
            int cvIndex = it.first;
            MPoint pos = it.second;
            curveFn.setCV(cvIndex, pos, MSpace::kWorld);
        }
    }

    return MStatus::kSuccess;
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
    command.addArg(MString(kStrengthFlag));
    command.addArg(strength);
    return MPxToolCommand::doFinalize(command);
}

void curveBrushTool::setRadius(double value)
{
    radius = value;
}

void curveBrushTool::setStrength(double value)
{
    strength = value;
}

void curveBrushTool::setMoveVector(MVector value)
{
    moveVector = value;
}

void curveBrushTool::setDagPathArray(MDagPathArray value)
{
    dagPathArray = value;
}

void curveBrushTool::setStartPoint(MPoint value)
{
    startPoint = value;
}
