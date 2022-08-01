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
	fHelixContext = new curveBrushContext();
	return fHelixContext;
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

	// if (argData.isFlagSet(kNumberCVsFlag))
	// {
	// 	unsigned numCVs;
	// 	status = argData.getFlagArgument(kNumberCVsFlag, 0, numCVs);
	// 	if (!status)
	// 	{
	// 		status.perror("numCVs flag parsing failed.");
	// 		return status;
	// 	}
	// 	fHelixContext->setNumCVs(numCVs);
	// }

	// if (argData.isFlagSet(kUpsideDownFlag))
	// {
	// 	bool upsideDown;
	// 	status = argData.getFlagArgument(kUpsideDownFlag, 0, upsideDown);
	// 	if (!status)
	// 	{
	// 		status.perror("upsideDown flag parsing failed.");
	// 		return status;
	// 	}
	// 	fHelixContext->setUpsideDown(upsideDown);
	// }

	return MS::kSuccess;
}

MStatus curveBrushContextCmd::doQueryFlags()
{
	MArgParser argData = parser();

	// if (argData.isFlagSet(kNumberCVsFlag))
	// {
	// 	setResult((int)fHelixContext->numCVs());
	// }
	// if (argData.isFlagSet(kUpsideDownFlag))
	// {
	// 	setResult(fHelixContext->upsideDown());
	// }

	return MS::kSuccess;
}

MStatus curveBrushContextCmd::appendSyntax()
{
	MSyntax mySyntax = syntax();

	if (MS::kSuccess != mySyntax.addFlag(kNumberCVsFlag, kNumberCVsFlagLong,
										 MSyntax::kUnsigned))
	{
		return MS::kFailure;
	}
	if (MS::kSuccess !=
		mySyntax.addFlag(kUpsideDownFlag, kUpsideDownFlagLong,
						 MSyntax::kBoolean))
	{
		return MS::kFailure;
	}

	return MS::kSuccess;
}
