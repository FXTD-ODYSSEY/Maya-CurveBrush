#ifndef __curveBrushContextCmd_H__
#define __curveBrushContextCmd_H__

#include "curveBrushContext.h"

class curveBrushContextCmd : public MPxContextCommand
{
public:
    curveBrushContextCmd();
    MStatus doEditFlags() override;
    MStatus doQueryFlags() override;
    MPxContext *makeObj() override;
    MStatus appendSyntax() override;
    static void *creator();

protected:
    curveBrushContext *mContext;
    //std::shared_ptr<curveBrushContext> mContext;
};

#endif
