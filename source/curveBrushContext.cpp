#include "curveBrushContext.h"

// NOTE(timmyliang): ignore sprintf_s wraning
#ifdef _WIN64
#define sprintf sprintf_s
#endif

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
    bFalloffMode = true;
    setTitleString("Curve Brush Tool");

    setCursor(MCursor::defaultCursor);

    // Tell the context which XPM to use so the tool can properly
    // be a candidate for the 6th position on the mini-bar.
    setImage("paintFXtoCurve.png", MPxContext::kImage1);
}

void curveBrushContext::toolOnSetup(MEvent &event)
{
    view = M3dView::active3dView();
    setHelpString(helpString);
    QCoreApplication *app = qApp;
    app->installEventFilter(this);
    // NOTE(timmyliang): get current selected the object as handle object
    MSelectionList activeList;
    MGlobal::getActiveSelectionList(activeList);
    objDagPathArray.clear();
    for (MItSelectionList curveIter(activeList, MFn::kNurbsCurve); !curveIter.isDone(); curveIter.next())
    {
        MDagPath curDag;
        MObject curCompObj;
        curveIter.getDagPath(curDag, curCompObj);
        objDagPathArray.append(curDag);
    }
    if (objDagPathArray.length() == 0)
    {
        MGlobal::displayWarning("No NURBS Curve selected.");
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
        auto lEventEnumType = e->type();
        if (lEventEnumType == QEvent::KeyPress)
        {
            if (e->key() == Qt::Key_B)
                eDragMode = kBrushSize;
        }
        else if (lEventEnumType == QEvent::KeyRelease)
        {
            if (eDragMode != kNormal)
                eDragMode = kNormal;
        }
    }
    return false;
}

MStatus curveBrushContext::doPress(MEvent &event, MHWRender::MUIDrawManager &drawMgr, const MHWRender::MFrameContext &context)
{
    view = M3dView::active3dView();
    event.getPosition(startPosX, startPosY);
    fStartBrushSize = mBrushConfig.size();
    fStartBrushStrength = mBrushConfig.strength();

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

    MPoint start(startPosX, startPosY);
    MVector delta = MVector(currentPos - start);

    drawMgr.beginDrawable();
    drawMgr.setColor(MColor(1.f, 1.f, 1.f));
    drawMgr.setLineWidth(2.0f);
    // NOTE(timmyliang): hold down `B` key
    if (eDragMode == kBrushSize)
    {
        float deltaValue;
        char info[64];
        // NOTES(timmyliang): left mouse for size
        if (event.mouseButton() == MEvent::kLeftMouse)
        {
            deltaValue = delta.x > 0 ? delta.length() : -delta.length();
            mBrushConfig.setSize(fStartBrushSize + deltaValue);
            sprintf(info, "Brush Size: %.2f", mBrushConfig.size());
            drawMgr.text2d(currentPos, info);
        }
        // NOTES(timmyliang): middle mouse for strength
        else if (event.mouseButton() == MEvent::kMiddleMouse)
        {
            deltaValue = delta.y > 0 ? delta.length() : -delta.length();
            mBrushConfig.setStrength(fStartBrushStrength + deltaValue);
            sprintf(info, "Brush Strength: %.2f", mBrushConfig.strength());
            drawMgr.text2d(currentPos, info);
        }
        drawMgr.line2d(start, MPoint(startPosX, startPosY + mBrushConfig.strength() * 2));
    }
    else
    {
        MPoint startNearPos, startFarPos, currNearPos, currFarPos;
        view.viewToWorld(currentPosX, currentPosY, currNearPos, currFarPos);
        view.viewToWorld(startPosX, startPosY, startFarPos, startFarPos);
        // NOTE(timmyliang): use tool command for undo
        curveBrushTool* cmd = static_cast<curveBrushTool*> (newToolCommand());
        cmd->setStrength(mBrushConfig.strength());
        cmd->setRadius(mBrushConfig.size());
        cmd->setMoveVector((currFarPos - startFarPos).normal());
        cmd->setStartPoint(start);
        cmd->setDagPathArray(objDagPathArray);
        cmd->redoIt();
        cmd->finalize();
    }

    drawMgr.circle2d(start, mBrushConfig.size());
    drawMgr.endDrawable();
    return MS::kSuccess;
}

MStatus curveBrushContext::doPtrMoved(MEvent &event, MHWRender::MUIDrawManager &drawMgr, const MHWRender::MFrameContext &context)
{
    short x, y;
    event.getPosition(x, y);
    mBrushCenterScreenPoint = MPoint(x, y);
    float &&radius = mBrushConfig.size();

    drawMgr.beginDrawable();
    if (bFalloffMode)
    {
        for (unsigned int index = 0; index < objDagPathArray.length(); ++index)
        {
            MPointArray pointArray;
            MColorArray colorArray;
            MFnNurbsCurve curveFn(objDagPathArray[index]);
            unsigned int &&segmentCount = 100;
            for (unsigned int pointIndex = 0; pointIndex < segmentCount; ++pointIndex)
            {
                MPoint point;
                auto param = curveFn.findParamFromLength(curveFn.length() * pointIndex / segmentCount);
                curveFn.getPointAtParam(param, point, MSpace::kWorld);
                pointArray.append(point);

                // NOTE(timmyliang): draw falloff
                short x_pos, y_pos;
                view.worldToView(point, x_pos, y_pos);
                MPoint screenPoint(x_pos, y_pos);
                auto distance = (mBrushCenterScreenPoint - screenPoint).length();
                auto field = 1 - distance / radius;
                // NOTE(timmyliang): transparent
                colorArray.append(distance > radius ? MColor(0.04f) : MColor(0.75f, .55f, .15f)* field);
            }

            drawMgr.setLineWidth(10.0f);
            drawMgr.mesh(MHWRender::MUIDrawManager::kLineStrip, pointArray, NULL, &colorArray);
        }
    }

    drawMgr.setColor(MColor(1.f, 1.f, 1.f));
    drawMgr.setLineWidth(2.0f);
    drawMgr.circle2d(mBrushCenterScreenPoint, radius);

    drawMgr.endDrawable();
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
