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
