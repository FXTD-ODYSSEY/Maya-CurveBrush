#include "curveBrushContextCmd.h"

/////////////////////////////////////////////////////////////
//
// Context creation command
//
//  This is the command that will be used to create instances
//  of our context.
//
/////////////////////////////////////////////////////////////

curveBrushContextCmd::curveBrushContextCmd() {}

MPxContext *curveBrushContextCmd::makeObj()
//
// Description
//    When the context command is executed in maya, this method
//    be used to create a context.
//
{
    mContext = new curveBrushContext();
    return mContext;
    //mContext = std::make_shared<curveBrushContext>(new curveBrushContext);
    //return mContext.get();
}

void *curveBrushContextCmd::creator()
//
// Description
//    This method creates the context command.
//
{
    return new curveBrushContextCmd;
}

MStatus curveBrushContextCmd::doEditFlags()
{
    MStatus status = MS::kSuccess;

    MArgParser argData = parser();

    if (argData.isFlagSet(kRadiusFlag))
    {
        double radius;
        status = argData.getFlagArgument(kRadiusFlag, 0, radius);
        if (!status)
        {
            status.perror("radius flag parsing failed.");
            return status;
        }
        mContext->mBrushConfig.setSize(radius);
    }

    if (argData.isFlagSet(kStrengthFlag))
    {
        double strength;
        status = argData.getFlagArgument(kStrengthFlag, 0, strength);
        if (!status)
        {
            status.perror("strength flag parsing failed.");
            return status;
        }
        mContext->mBrushConfig.setStrength(strength);
    }

    return MS::kSuccess;
}

MStatus curveBrushContextCmd::doQueryFlags()
{
    MArgParser argData = parser();

    if (argData.isFlagSet(kStrengthFlag))
    {
        setResult(static_cast<double>(mContext->mBrushConfig.strength()));
    }
    if (argData.isFlagSet(kRadiusFlag))
    {
        setResult(static_cast<double>(mContext->mBrushConfig.size()));
    }

    return MS::kSuccess;
}

MStatus curveBrushContextCmd::appendSyntax()
{
    MSyntax syntaxInstance = syntax();
    CHECK_MSTATUS_AND_RETURN_IT(syntaxInstance.addFlag(kStrengthFlag, kStrengthFlagLong, MSyntax::kDouble));
    CHECK_MSTATUS_AND_RETURN_IT(syntaxInstance.addFlag(kRadiusFlag, kRadiusFlagLong, MSyntax::kDouble));
    return MS::kSuccess;
}
