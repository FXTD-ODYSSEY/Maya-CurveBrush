"""created by Yuriy Sivalnev. Its free!!! Totally...i mean it"""

"""
----------------------------------------------------------------------------------------INSTALLATION:     
put archive content in prefs folder C:\\Users\__SOME_NAME__\Documents\maya\2016.5    

If shelf 'ysvTools' not loaded, load it manually from 'prefs/shelfs' folder

click on shelf button to shoot tool, double click for options UI

----------------------------------------------------------------------------------------
USAGE:   
LMB click-drag :        
    for paint curve on the virtual plane that has current camera "point of interest" and is parallel to view plane        
    if start or/and end curve is on top of some poly(it must be visible at the moment you start tool),
    cvs will snap to that poly object 

Ctrl+LMB click-drag:         
    paint on poly surface(no need to select or make live)   
    poly must be visible at the moment you start tool

Shift+LMB click drag:           
    smooth curve from start click to release mouse button(you just mark cv on which start cmooth operation and end cv - it is NOT      BRUSH)        

CTRL+Shift+ LMB: 
    same effect but much stronger        

CTRL_SHIFT_ALT LMB click: 
    deselect curve

MMB : 
    tweak curve CV that is closest to cursor    

Ctrl MMB: 
    change soft selection radius

Shift MMB: 
    tweak curve with soft selection    

Ctrl Shift MMB: 
    tweak curves that is on screen with soft selection        

Ctrl Shift Alt MMB: 
    move curve ends with soft selection

Thats all, happy tweaking!!!



 
"""
import maya.cmds as mc

import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import math
from pymel.core import *
import pymel.core.datatypes as dt
import pymel.core.nodetypes as nt
from maya.mel import eval as mEval

from . import ysvPolyOps
from . import ysvCurvesOps
from . import ysvCtx

# import ysvApiWrapers
from . import ysvView
from . import ysvMath

mEval("source softSelectValues.mel")


def getMods():
    mods = getModifiers()

    Ctrl, Alt, Shift, Wnd = 0, 0, 0, 0
    if (mods & 1) > 0:
        Shift = 1
    if (mods & 4) > 0:
        Ctrl = 1
    if (mods & 8) > 0:
        Alt = 1
    if mods & 16:
        Wnd = 1

    return Ctrl, Alt, Shift


class UI:
    def __init__(self):
        self.winName = "ysvPaintCurveOnPoly"
        self.winTitle = "Paint curve on poly UI"

    def create(self):
        if not optionVar(ex="ysvPaintCurveStep"):
            optionVar(fv=("ysvPaintCurveStep", 1.0))
        elif not isinstance(optionVar(q="ysvPaintCurveStep"), float):
            optionVar(fv=("ysvPaintCurveStep", 1.0))

        if not optionVar(ex="ysvPaintCurveSliderMin"):
            optionVar(fv=("ysvPaintCurveSliderMin", 1.0))
        elif not isinstance(optionVar(q="ysvPaintCurveSliderMin"), float):
            optionVar(fv=("ysvPaintCurveSliderMin", 0.0))

        if not optionVar(ex="ysvPaintCurveSliderMax"):
            optionVar(fv=("ysvPaintCurveSliderMax", 20.0))
        elif not isinstance(optionVar(q="ysvPaintCurveSliderMax"), float):
            optionVar(fv=("ysvPaintCurveSliderMax", 20.0))

        if not optionVar(ex="ysvPaintCurveSelectBehavior"):
            optionVar(iv=("ysvPaintCurveSelectBehavior", 1))
        elif not isinstance(optionVar(q="ysvPaintCurveSelectBehavior"), int):
            optionVar(iv=("ysvPaintCurveSelectBehavior", 1))

        if not optionVar(ex="ysvPaintCurveShowCVs"):
            optionVar(sv=("ysvPaintCurveShowCVs", "No"))
        elif not isinstance(optionVar(q="ysvPaintCurveShowCVs"), str):
            optionVar(sv=("ysvPaintCurveShowCVs", "No"))

        if not optionVar(ex="ysvLockEndCVs"):
            optionVar(iv=("ysvLockEndCVs", 1))
        elif not isinstance(optionVar(q="ysvLockEndCVs"), int):
            optionVar(iv=("ysvLockEndCVs", 1))

        if not optionVar(ex="ysvSnapToCurves"):
            optionVar(iv=("ysvSnapToCurves", 1))
        elif not isinstance(optionVar(q="ysvSnapToCurves"), int):
            optionVar(iv=("ysvSnapToCurves", 1))

        if not optionVar(ex="ysvSnapToMeshes"):
            optionVar(iv=("ysvSnapToMeshes", 1))
        elif not isinstance(optionVar(q="ysvSnapToMeshes"), int):
            optionVar(iv=("ysvSnapToMeshes", 1))

        if not optionVar(ex="ysvCutCurves"):
            optionVar(iv=("ysvCutCurves", 1))
        elif not isinstance(optionVar(q="ysvCutCurves"), int):
            optionVar(iv=("ysvCutCurves", 1))

        if not optionVar(ex="ysvSnapToEnds"):
            optionVar(iv=("ysvSnapToEnds", 1))
        elif not isinstance(optionVar(q="ysvSnapToEnds"), int):
            optionVar(iv=("ysvSnapToEnds", 1))

        if window(self.winName, exists=True):
            deleteUI(self.winName)

        with window(self.winName, title=self.winTitle):
            with columnLayout():
                with rowLayout(nc=5):
                    sliderMinValue = optionVar(q="ysvPaintCurveSliderMin")
                    sliderMaxValue = optionVar(q="ysvPaintCurveSliderMax")

                    text(l="Slider min:")
                    self.sliderMinFloatField = floatField(
                        v=sliderMinValue, cc=Callback(self.setMinSlider)
                    )

                    stepVal = optionVar(q="ysvPaintCurveStep")
                    self.stepSlider = floatSliderGrp(
                        label="Step : ",
                        field=1,
                        columnWidth=(1, 40),
                        min=sliderMinValue,
                        max=sliderMaxValue,
                        value=stepVal,
                        pre=2,
                        cc=Callback(self.setStep),
                    )

                    text(l="Slider max:")
                    self.sliderMaxFloatField = floatField(
                        v=sliderMaxValue, cc=Callback(self.setMaxSlider)
                    )

                selectionBehavior = optionVar(q=("ysvPaintCurveSelectBehavior"))
                self.behCheckBox = checkBox(
                    l="Tweak all(or selected only)",
                    v=selectionBehavior,
                    cc=Callback(self.setSelectBehavior),
                )

                showCVs = optionVar(q=("ysvPaintCurveShowCVs"))
                if showCVs == "Yes":
                    checkBoxEn = 1
                elif showCVs == "No":
                    checkBoxEn = 0
                self.showCVoption = checkBox(
                    l="Leave cvs visible",
                    v=checkBoxEn,
                    cc=Callback(self.setCVvisibility),
                )

                checkBoxEn = optionVar(q=("ysvLockEndCVs"))
                self.lockEndsOption = checkBox(
                    l="Lock ends", v=checkBoxEn, cc=Callback(self.setLockEnds)
                )

                checkBoxEn = optionVar(q=("ysvSnapToCurves"))
                self.snapToCurvesOption = checkBox(
                    l="Snap to curves", v=checkBoxEn, cc=Callback(self.setSnapToCurves)
                )

                checkBoxEn = optionVar(q=("ysvSnapToMeshes"))
                self.snapToMeshesOption = checkBox(
                    l="Snap to meshes", v=checkBoxEn, cc=Callback(self.setSnapToMeshes)
                )

                checkBoxEn = optionVar(q=("ysvCutCurves"))
                self.cutCurvesOption = checkBox(
                    l="Cut curves while snapping",
                    v=checkBoxEn,
                    cc=Callback(self.setCutCurves),
                )

                checkBoxEn = optionVar(q=("ysvSnapToEnds"))
                self.snapToEndsOption = checkBox(
                    l="Snap to ends", v=checkBoxEn, cc=Callback(self.setSnapToEnds)
                )

        showWindow(self.winName)

    def setStep(self):
        value = floatSliderGrp(self.stepSlider, q=1, v=1)
        optionVar(fv=("ysvPaintCurveStep", value))

    def setMinSlider(self):
        value = floatField(self.sliderMinFloatField, q=1, v=1)
        floatSliderGrp(self.stepSlider, e=1, min=value)
        optionVar(fv=("ysvPaintCurveSliderMin", value))

    def setMaxSlider(self):
        value = floatField(self.sliderMaxFloatField, q=1, v=1)
        floatSliderGrp(self.stepSlider, e=1, max=value)
        optionVar(fv=("ysvPaintCurveSliderMax", value))

    def setSelectBehavior(self):
        checkBoxEn = checkBox(self.behCheckBox, q=1, v=1)
        optionVar(iv=("ysvPaintCurveSelectBehavior", checkBoxEn))

    def setCVvisibility(self):
        checkBoxEn = checkBox(self.showCVoption, q=1, v=1)
        if checkBoxEn == 1:
            optionVar(sv=("ysvPaintCurveShowCVs", "Yes"))

        else:
            optionVar(sv=("ysvPaintCurveShowCVs", "No"))

    def setLockEnds(self):
        state = checkBox(self.lockEndsOption, q=1, v=1)
        optionVar(iv=("ysvLockEndCVs", state))

    def setSnapToCurves(self):
        state = checkBox(self.snapToCurvesOption, q=1, v=1)
        optionVar(iv=("ysvSnapToCurves", state))

    def setSnapToMeshes(self):
        state = checkBox(self.snapToMeshesOption, q=1, v=1)
        optionVar(iv=("ysvSnapToMeshes", state))

    def setCutCurves(self):
        state = checkBox(self.cutCurvesOption, q=1, v=1)
        optionVar(iv=("ysvCutCurves", state))

    def setSnapToEnds(self):
        state = checkBox(self.snapToEndsOption, q=1, v=1)
        optionVar(iv=("ysvSnapToEnds", state))


class paintCtx(ysvCtx.baseDraggerCtx):
    def __init__(self, ctxName):
        # ysvCtx.baseDraggerCtx.__init__(self, ctxName)
        ysvCtx.baseDraggerCtx.__init__(self, ctxName)

        # modelEditor(getPanel(wf=1), e=1, xray=1)
        for mp in getPanel(type="modelPanel"):
            if modelEditor(mp, q=1, av=1):
                modelEditor(mp, e=1, nurbsCurves=1)
                break

        tmpGroupName = "CHistory_curves_gr"
        if not objExists(tmpGroupName):
            self.tmpGroup = createNode(nt.Transform, name=tmpGroupName)
        else:
            self.tmpGroup = PyNode(tmpGroupName)

        liveMeshes = ls(lv=1, dag=1, et=nt.Mesh, ni=1)
        if liveMeshes:
            self.liveMesh = liveMeshes[0]
        else:
            self.liveMesh = None

        self.inMeshes = ls(sl=1, dag=1, et=nt.Mesh, ni=1)

        if not self.inMeshes:
            self.inMeshes = ls(self.initInViewObjs, dag=1, et=nt.Mesh, ni=1)

        self.inMeshes += liveMeshes

        self.meshFns = [mesh.__apimfn__() for mesh in self.inMeshes]

        # self.step = optionVar(q='ysvPaintCurveStep')
        print("in view objs: ", self.initInViewObjs)
        print("in view meshes:", self.inMeshes)
        print("liveMeshes: ", liveMeshes)

    def paintOnPress(self):
        self.startScreenWSPos = self.cursorWPos
        self.step = optionVar(q="ysvPaintCurveStep")

        pnt = self.planeIsect(self.centerOfInterest, self.viewDir)
        self.crv = curve(p=[pnt])
        self.crv.dispCV.set(1)

        liveMeshes = ls(lv=1, dag=1, et=nt.Mesh, ni=1)

        self.inMeshes = ls(ysvCtx.getInViewObjs(), dag=1, et=nt.Mesh, ni=1) + liveMeshes

        self.meshFns = [mesh.__apimfn__() for mesh in self.inMeshes]

        self.prevPnt = pnt

    def paintOnDrag(self):
        if not self.crv:
            return
        pnt = self.planeIsect(self.centerOfInterest, self.viewDir)
        if pnt:
            if (pnt - self.prevPnt).length() > self.step:
                curve(self.crv, a=1, p=pnt)
                self.prevPnt = pnt

    def paintOnRelease(self):
        if not self.crv:
            return
        sPnt = pointPosition(self.crv.cv[0])
        xform(self.crv, sp=sPnt, rp=sPnt, a=1, ws=1)

        self.endScreenWSPos = self.cursorWPos

        crvLen = self.crv.length()

        sCVPos = pointPosition(self.crv.cv[0])
        eCVPos = pointPosition(self.crv.cv[-1])

        sMeshHit = ysvView.closestHitToMeshes(
            self.meshFns, self.startScreenWSPos, sCVPos - self.startScreenWSPos
        )
        eMeshHit = ysvView.closestHitToMeshes(
            self.meshFns, self.endScreenWSPos, eCVPos - self.endScreenWSPos
        )

        if sMeshHit:
            move(self.crv, sMeshHit - sCVPos, r=1, ws=1)

        if eMeshHit:
            setToolTo("moveSuperContext")
            softSelect(e=1, sse=1, ssf=1, ssc="1,0,2,0,1,2", ssd=crvLen / 1.3)
            select(self.crv.cv[-1])
            move(eMeshHit, a=1, ws=1)

        select(self.crv)

        showCVs = optionVar(q=("ysvPaintCurveShowCVs"))
        if showCVs == "Yes":
            self.crv.dispCV.set(1)
        elif showCVs == "No":
            self.crv.dispCV.set(0)

        softSelect(e=1, sse=0)
        setToolTo(self.ctxName)

    def paintOnPolyOnPress(self):
        self.step = optionVar(q="ysvPaintCurveStep")

        meshHit = ysvView.closestHitToMeshes(
            self.meshFns, self.cursorWPos, self.cursorWDir
        )

        if meshHit:
            self.paintCrv = curve(p=(meshHit))
            self.snapToCurves(self.paintCrv.cv[0])

            select(self.paintCrv)
            self.paintCrv.dispCV.set(1)

            self.prevHit = meshHit

    def paintOnPolyOnDrag(self):
        if not self.paintCrv:
            return
        meshHit = ysvView.closestHitToMeshes(
            self.meshFns, self.cursorWPos, self.cursorWDir
        )
        try:
            if meshHit and self.paintCrv:
                if (meshHit - self.prevHit).length() > self.step:
                    if self.paintCrv:
                        curve(self.paintCrv, append=1, p=(meshHit))
                    else:
                        self.paintCrv = curve(p=(meshHit))
                        self.snapToCurves(self.paintCrv.cv[0])
                        select(self.paintCrv)

                    self.prevHit = meshHit

        except:
            pass

    def paintOnPolyOnRelease(self):
        if not self.paintCrv:
            return
        showCVs = str(optionVar(q=("ysvPaintCurveShowCVs")))

        if showCVs == str("Yes"):
            self.paintCrv.dispCV.set(1)
        elif showCVs == str("No"):
            self.paintCrv.dispCV.set(0)

        print("snapping end")
        self.snapToCurves(self.paintCrv.cv[-1])

    def getCVNearCursor(self, exactCurves=[]):
        xScr, yScr = self.cursorScreenCoords
        scrPnt = dt.Point(xScr, yScr, 0)

        currView = omui.M3dView.active3dView()

        distances = []
        if exactCurves:
            curves = exactCurves
        else:
            curves = self.curves

        for crv in curves:
            for i in range(crv.numCVs()):

                cvPos = pointPosition(crv.cv[i])

                xu, yu = om.MScriptUtil(), om.MScriptUtil()
                xPtr, yPtr = xu.asShortPtr(), yu.asShortPtr()

                mPnt = om.MPoint(cvPos[0], cvPos[1], cvPos[2])
                notClipped = currView.worldToView(mPnt, xPtr, yPtr)

                if notClipped:
                    x = xu.getShort(xPtr)
                    y = yu.getShort(yPtr)

                    crvScrPnt = dt.Point(x, y, 0)
                    dist = (scrPnt - crvScrPnt).length()

                    try:
                        if self.startClickCv == crv.cv[i]:
                            continue
                    except:
                        pass

                    distances.append([dist, crv, i])

        if distances:
            crv, cvId = min(distances, key=lambda x: x[0])[1:]
            return crv.cv[cvId]
        else:
            return []

    def getClosestPointToCurves(self, pnt, curves):
        # print pnt
        crvs = []
        for crv in curves:
            tol = crv.__apimfn__().length() / crv.numCVs()
            if optionVar(q="ysvSnapToEnds"):
                tol = 0.4 * crv.__apimfn__().length()

            dist = crv.distanceToPoint(pnt, "world")
            if dist < tol:
                crvs.append((dist, crv))

        closestCurve = min(crvs, key=lambda x: x[0])[1]

        curveFn = closestCurve.__apimfn__()
        curveLen = curveFn.length()

        sPar = curveFn.findParamFromLength(0)
        ePar = curveFn.findParamFromLength(curveLen)
        spans = closestCurve.numCVs()
        tolerance = abs(ePar - sPar) / (spans * 0.75)

        if optionVar(q="ysvSnapToEnds"):
            tolerance = 0.4 * abs(ePar - sPar)
        # sPar, ePar = closestCurve.

        dPtr = om.MScriptUtil().asDoublePtr()

        print(" ")
        curveFn.closestPoint(
            om.MPoint(pnt[0], pnt[1], pnt[2]), dPtr, 0.01, om.MSpace.kWorld
        )
        print(" ")
        param = om.MScriptUtil(dPtr).asFloat()

        # print 'tolerance: ', tolerance
        # print  'dist to start:', abs(sPar-param)
        # print  'dist to end:', abs(ePar-param)

        if abs(sPar - param) < tolerance:
            param = sPar
        elif abs(ePar - param) < tolerance:
            param = ePar

        try:
            return pointPosition(closestCurve.u[param]), closestCurve.u[param]
        except:
            return None, None

    def snapToCurves(self, cv):
        snapState = optionVar(q="ysvSnapToCurves")

        if not snapState:
            return
        # print 'snappig cv: ', cv

        tweakedCurve = cv.node()
        cvNum = tweakedCurve.numCVs()
        if not cv.index() == 0 and not cv.index() == cvNum - 1:
            return
        curvesToChooseFrom = [c for c in self.inViewCurves if not c == tweakedCurve]
        try:
            closestPoint, curveParamPnt = self.getClosestPointToCurves(
                pointPosition(cv, w=1), curvesToChooseFrom
            )
            if not closestPoint:
                return

            move(cv, closestPoint, ws=1, a=1)

            cutState = optionVar(q="ysvCutCurves")
            if not cutState:
                return
            cuttedCurve = curveParamPnt.node()
            cuttedCurveFn = cuttedCurve.__apimfn__()
            par = cuttedCurveFn.findParamFromLength(0)
            sPar = cuttedCurve.u[par]

            par = cuttedCurveFn.findParamFromLength(cuttedCurveFn.length())
            ePar = cuttedCurve.u[par]

            if curveParamPnt == sPar or curveParamPnt == ePar:
                return
            cuttedCurves = detachCurve(curveParamPnt, ch=1, cos=1, rpo=0)
            # print res
            parent(curveParamPnt.node().getParent(), self.tmpGroup)
            hide(curveParamPnt.node().getParent())

            for crv in ls(cuttedCurves, dag=1, et=nt.NurbsCurve, ni=1):
                crv.dispCV.set(1)

        except:
            pass

    def smoothOpOnPress(self):
        selectBeh = optionVar(q="ysvPaintCurveSelectBehavior")
        if selectBeh:
            self.curves = ls(ysvView.getInViewObjs(), dag=1, et=nt.NurbsCurve, ni=1)
        else:
            self.curves = ls(sl=1, dag=1, et=nt.NurbsCurve, ni=1)
            if not self.curves:
                self.curves = ls(ysvView.getInViewObjs(), dag=1, et=nt.NurbsCurve, ni=1)

        self.startClickCv = self.getCVNearCursor()
        select(self.startClickCv.node().getParent())

    def smoothOpOnRelease(self, iterations):
        crv = self.startClickCv.node()
        self.endClickCv = self.getCVNearCursor([crv])
        # select(self.endClickCv, add=1)

        sId, eId = self.startClickCv.index(), self.endClickCv.index()

        s = min(sId, eId)
        e = max(sId, eId)

        cvs = [cv for cv in crv.cv[s:e]]
        pnts = [pointPosition(cv) for cv in cvs]

        for i in range(iterations):
            ysvCurvesOps.smoothCrvPoints(pnts)

        for cv, pnt in zip(cvs, pnts):
            move(cv, pnt, ws=1, a=1)

        if self.liveMesh:
            ysvPolyOps.projectsCVsToMesh(cvs, self.liveMesh)

        # select(crv)

    def moveOpOnPress(self, option="singlePoint"):
        selectBeh = optionVar(q="ysvPaintCurveSelectBehavior")
        if selectBeh:
            self.curves = ls(ysvView.getInViewObjs(), dag=1, et=nt.NurbsCurve, ni=1)
        else:
            self.curves = ls(sl=1, dag=1, et=nt.NurbsCurve, ni=1)
            if not self.curves:
                self.curves = ls(ysvView.getInViewObjs(), dag=1, et=nt.NurbsCurve, ni=1)

        self.ssOption = option
        if option == "softSelectionGlobal" or option == "adjustRadius":
            self.protectShapes = []

            protectObjs = ysvView.getInViewObjs()
            liveObjShape = ls(lv=1)
            if liveObjShape:
                protectObjs.append(liveObjShape[0].getParent())

            for shape in protectObjs:
                if not shape.getShape().type() == "nurbsCurve":
                    if not shape.overrideEnabled.get():
                        self.protectShapes.append(shape)
                        shape.overrideEnabled.set(1)
                        shape.overrideDisplayType.set(1)
                    elif (
                        shape.overrideEnabled.get()
                        and not shape.ovverrideDisplayType.get()
                    ):
                        self.protectShapes.append(shape)
                        shape.overrideEnabled.set(1)
                        shape.overrideDisplayType.set(1)

        self.startClickCv = self.getCVNearCursor()

        self.crv = self.startClickCv.node()

        select(self.crv.getParent())
        midId = self.startClickCv.index()

        self.midCvWPos = pointPosition(self.startClickCv)

        l0 = self.cursorWPos
        l1 = l0 + self.cursorWDir * (self.midCvWPos - self.cursorWPos).length() * 10

        self.startPlaneProjPnt = ysvMath.linePlaneIntersect(
            l0, l1, self.midCvWPos, self.cursorWDir
        )

        self.lockEndCVsStartState = optionVar(q=("ysvLockEndCVs"))

        if option == "singlePoint" or option == "softSelectionSurface":
            optionVar(iv=("ysvLockEndCVs", 0))

        elif self.lockEndCVsStartState:
            for crv in self.inViewCurves:
                for cv in [crv.cv[0], crv.cv[-1]]:
                    cv = str(cv)
                    setAttr(cv + ".xv", lock=1)
                    setAttr(cv + ".yv", lock=1)
                    setAttr(cv + ".zv", lock=1)

    def moveOpOnDrag(self, option=""):
        l0 = self.cursorWPos
        l1 = l0 + self.cursorWDir * (self.midCvWPos - self.cursorWPos).length() * 10

        dragPlaneProjPnt = ysvMath.linePlaneIntersect(
            l0, l1, self.midCvWPos, self.cursorWDir
        )
        self.offsetVec = dragPlaneProjPnt - self.startPlaneProjPnt

        select(self.startClickCv)

        if option == "singlePoint":
            softSelect(e=1, softSelectEnabled=0, enableFalseColor=1)

            optionVar(iv=("ysvLockEndCVs", 0))
            for crv in self.inViewCurves:
                for cv in [crv.cv[0], crv.cv[-1]]:
                    cv = str(cv)
                    setAttr(cv + ".xv", lock=0)
                    setAttr(cv + ".yv", lock=0)
                    setAttr(cv + ".zv", lock=0)

        elif option == "adjustRadius":
            softSelect(e=1, softSelectEnabled=1, enableFalseColor=1)
            mEval('setSoftSelectFalloffMode( "Global")')

        elif option == "softSelectionGlobal":
            softSelect(e=1, softSelectEnabled=1, enableFalseColor=0)
            mEval('setSoftSelectFalloffMode( "Global")')

        elif option == "softSelectionVolume":
            softSelect(e=1, softSelectEnabled=1, enableFalseColor=0)
            mEval('setSoftSelectFalloffMode( "Volume")')

        elif option == "softSelectionSurface":
            softSelect(e=1, softSelectEnabled=1, enableFalseColor=0)
            mEval('setSoftSelectFalloffMode( "Surface")')

        if option == "adjustRadius":
            radius = (dragPlaneProjPnt - self.midCvWPos).length()
            softSelect(e=1, softSelectDistance=radius)
        else:
            move(self.offsetVec, r=1)
            select(self.crv)

        self.startPlaneProjPnt = dragPlaneProjPnt

        if not option == "adjustRadius":
            # print 'projecting on drag second operation'
            cvNum = self.crv.numCVs()

            if self.startClickCv.index() == 0 or self.startClickCv.index() == cvNum - 1:

                if self.liveMesh:
                    if self.startClickCv.index() == 0:
                        ysvPolyOps.projectsCVsToMesh(self.crv.cv[1:], self.liveMesh)

                    elif self.startClickCv.index() == cvNum - 1:
                        ysvPolyOps.projectsCVsToMesh(self.crv.cv[:-1], self.liveMesh)

                if optionVar(q="ysvSnapToMeshes"):
                    meshHit = ysvView.closestHitToMeshes(
                        self.meshFns, self.cursorWPos, self.cursorWDir
                    )
                    if meshHit:
                        select(self.startClickCv)
                        softSelect(e=1, softSelectEnabled=0)
                        move(meshHit, a=1, ws=1)
                        select(self.crv)

            else:
                if self.liveMesh:
                    if optionVar(q="ysvSnapToCurves"):
                        ysvPolyOps.projectsCVsToMesh(self.crv.cv[1:-1], self.liveMesh)
                    else:
                        ysvPolyOps.projectsCVsToMesh(self.crv, self.liveMesh)

    def moveOpOnRelease(self, option=""):
        softSelect(e=1, softSelectEnabled=0, enableFalseColor=1)
        mEval('setSoftSelectFalloffMode( "Volume")')
        select(self.crv)
        # print self.ssOption
        if self.ssOption == "softSelectionGlobal" or self.ssOption == "adjustRadius":
            # print 'protected shapes: ', self.protectShapes
            for shape in self.protectShapes:
                shape.overrideDisplayType.set(0)
                shape.overrideEnabled.set(0)

        optionVar(iv=("ysvLockEndCVs", self.lockEndCVsStartState))

        for crv in self.inViewCurves:
            for cv in [crv.cv[0], crv.cv[-1]]:
                cv = str(cv)
                setAttr(cv + ".xv", lock=0)
                setAttr(cv + ".yv", lock=0)
                setAttr(cv + ".zv", lock=0)

        if not option == "adjustRadius":
            self.snapToCurves(self.startClickCv)

    def onPress(self):
        self.crv = None
        self.paintCrv = None
        self.inViewCurves = ls(ysvView.getInViewObjs(), dag=1, ni=1, et=nt.NurbsCurve)

        xScreen, yScreen, dummy = draggerContext(self.ctxName, q=1, ap=1)
        self.setCursorData(xScreen, yScreen)

        self.btn = draggerContext(self.ctxName, q=1, bu=1)
        cntrl, alt, shift = getMods()

        if self.btn == 1:
            if not cntrl and not alt and not shift:
                self.paintOnPress()

            elif shift and not alt:
                self.smoothOpOnPress()

            elif cntrl and not shift and not alt:
                self.paintOnPolyOnPress()

            elif cntrl and shift and alt:
                select(cl=1)

        elif self.btn == 2:
            if not cntrl and not shift and not alt:
                self.moveOpOnPress("singlePoint")
            elif cntrl and not shift and not alt:
                self.moveOpOnPress("adjustRadius")
            elif not cntrl and shift and not alt:
                self.moveOpOnPress("softSelectionVolume")
            elif cntrl and shift and not alt:
                self.moveOpOnPress("softSelectionGlobal")

            elif cntrl and shift and alt:
                # self.moveEndsOpPress()
                self.moveOpOnPress(option="softSelectionSurface")

    def onDrag(self):
        xScreen, yScreen, dummy = draggerContext(self.ctxName, q=1, dp=1)
        self.setCursorData(xScreen, yScreen)

        cntrl, alt, shift = getMods()

        if self.btn == 1:
            if not cntrl and not alt and not shift:
                self.paintOnDrag()
            elif cntrl and not shift and not alt:
                self.paintOnPolyOnDrag()

            # curve(self.crv, append=1, p=[pnt])
        elif self.btn == 2:
            if not cntrl and not shift and not alt:
                self.moveOpOnDrag("singlePoint")
            elif cntrl and not shift and not alt:
                self.moveOpOnDrag("adjustRadius")
            elif not cntrl and shift and not alt:
                self.moveOpOnDrag("softSelectionVolume")
            elif cntrl and shift and not alt:
                self.moveOpOnDrag("softSelectionGlobal")

            elif cntrl and shift and alt:
                self.moveOpOnDrag(option="softSelectionSurface")
                # self.moveEndsOpDrag()

        mc.refresh(cv=True)

    def onRelease(self):
        # baseDraggerCtx.onRelease(self)
        cntrl, alt, shift = getMods()
        if self.btn == 1:
            if not cntrl and not shift and not alt:
                self.paintOnRelease()

            if cntrl and not shift and not alt:
                self.paintOnPolyOnRelease()

            elif shift and not cntrl and not alt:
                self.smoothOpOnRelease(1)

            elif shift and cntrl and not alt:
                self.smoothOpOnRelease(7)

        elif self.btn == 2:
            """
            if not alt:
                self.moveOpOnRelease()

            if cntrl and shift and alt:
                self.moveOpOnRelease(snapToCurves=True)
                optionVar(iv=('ysvLockEndCVs', 1))
            """

            if not cntrl and not shift and not alt:
                self.moveOpOnRelease("singlePoint")
            elif cntrl and not shift and not alt:
                self.moveOpOnRelease("adjustRadius")
            elif not cntrl and shift and not alt:
                self.moveOpOnRelease("softSelectionVolume")
            elif cntrl and shift and not alt:
                self.moveOpOnRelease("softSelectionGlobal")

            elif cntrl and shift and alt:
                self.moveOpOnRelease(option="softSelectionSurface")

        self.startClickCv = None

    def finalize(self):
        # baseDraggerCtx.finalize(self)
        # modelEditor(getPanel(wf=1), e=1, xray=0)
        pass

    def run(self):
        ysvCtx.baseDraggerCtx.run(self)
