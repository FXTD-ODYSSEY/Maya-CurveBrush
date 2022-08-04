#include <maya/MFnPlugin.h>
#include "curveBrushContextTool.h"
#include "curveBrushContextCmd.h"

static const char *kVERSION = "1.0.0";
static const char *kAUTHOR = "TimmyLiang";

// ---------------------------------------------------------------------
// initialization
// ---------------------------------------------------------------------
MStatus initializePlugin(MObject obj)
{
    MStatus status;
    MFnPlugin plugin(obj, PLUGIN_COMPANY, "3.0", "Any");

    // Register the context creation command and the tool command
    // that the helixContext will use.
    //
    status = plugin.registerContextCommand("curveBrushContext",
                                           curveBrushContextCmd::creator,
                                           "curveBrushToolCmd",
                                           curveBrushTool::creator,
                                           curveBrushTool::newSyntax);
    if (!status)
    {
        status.perror("registerContextCommand");
        return status;
    }

    return status;
}

MStatus uninitializePlugin(MObject obj)
{
    MStatus status;
    MFnPlugin plugin(obj);

    // Deregister the tool command and the context creation command
    //
    status = plugin.deregisterContextCommand("curveBrushContext",
                                             "curveBrushToolCmd");
    if (!status)
    {
        status.perror("deregisterContextCommand");
        return status;
    }

    return status;
}

