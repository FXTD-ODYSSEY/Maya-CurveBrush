# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
import math
import random

# Import third-party modules
import maya.OpenMaya as om
import maya.cmds as mc
from maya.mel import eval as mEval
from pymel.core import *
import pymel.core.datatypes as dt
import pymel.core.nodetypes as nt

from . import ysvCurvesOps as yCrv
from . import ysvPolyOps as yPoly
from . import ysvUtils


def RestoreTMoveValues():
    for obj in ls(sl=1, dag=1, et=nt.Transform):
        wPos = xform(obj, q=1, ws=1, sp=1)
        move(obj, 0, 0, 0, rpr=1)
        makeIdentity(obj, a=1, t=1, s=0, r=0)
        move(obj, wPos, ws=1)


def MultiGeoConstrain():
    sel = ls(sl=1, o=1)
    last = sel[len(sel) - 1]
    for obj in sel:
        if not obj == last:
            select([last, obj])
            geometryConstraint(weight=1)
            normalConstraint(w=1, aimVector=(0, 1, 0))
    select(sel[0 : len(sel) - 1])


def multiTangentConstraint():
    sel = ls(sl=1, o=1)


def tngConstraint(objs=None, crv=None):
    if objs == None:
        objs = [
            s
            for s in ls(sl=1, dag=1, et=nt.Transform)
            if not type(s.getShape()) == nt.NurbsCurve
        ]
    if crv == None:
        crv = ls(sl=1, dag=1, et=nt.NurbsCurve)
        if crv:
            crv = crv[0].getParent()
    if objs == None or crv == None:
        return

    node = createNode(nt.TangentConstraint)
    for obj in objs:
        connectAttr(obj.rotateOrder, node.constraintRotateOrder)
        connectAttr(obj.rotatePivot, node.constraintRotatePivot)
        connectAttr(obj.rotatePivotTranslate, node.constraintRotateTranslate)
        connectAttr(obj.parentInverseMatrix[0], node.constraintParentInverseMatrix)
        connectAttr(obj.translate, node.constraintTranslate)
        connectAttr(node.constraintRotateY, obj.rotateY)
        connectAttr(node.constraintRotateZ, obj.rotateZ)
        connectAttr(node.constraintRotateX, obj.rotateX)
        connectAttr(crv.getShape().worldSpace[0], node.target[0].targetGeometry)
        # custom
        addAttr(node, at="double", ln=crv + "W0", min=0, dv=1)
        connectAttr(node + "." + crv + "W0", node.target[0].targetWeight)


# ---------------------------------------------          Duplications-----------------------------------
def duplicateWithConstraints(obj, makeInst=0):
    cons = [
        node
        for node in listConnections(obj, s=1, d=0)
        if isinstance(node, nt.Constraint)
    ]
    if not cons:
        return duplicate(obj)[0]

    dupObj = None

    if makeInst:
        objConstraints = [c for c in ls(obj, dag=1) if isinstance(c, nt.Constraint)]
        parent(objConstraints, w=1)
        dupObj = instance(obj)[0]
        parent(objConstraints, obj)
    else:
        dupObj = duplicate(obj)[0]
        dupConstraints = [c for c in ls(dupObj, dag=1) if isinstance(c, nt.Constraint)]
        delete(dupConstraints)

    for constr in set(cons):
        # print [constr]
        dupNode = duplicate(constr)[0]
        # print '\t\tdup node:', dupNode
        parent(dupNode, dupObj)

        inConns = listConnections(constr, p=1, c=1, s=1, d=0)
        outConns = listConnections(constr, p=1, c=1, s=0, d=1)

        # print '\t\t\tins'
        for p1, p2 in inConns:
            if p1.isDestination():
                # print "source:", p2, "dest:", p1
                if p2.node() == constr:
                    source = dupNode.attr(p2.shortName())
                elif p2.node() == obj:
                    source = dupObj.attr(p2.shortName())
                else:
                    source = p2

                dest = dupNode.attr(p1.shortName())
            else:
                # print "source:", p1, "dest:", p2

                if p1.node() == constr:
                    source = dupNode.attr(p1.shortName())
                elif p1.node() == obj:
                    source = dupObj.attr(p1.shortName())
                else:
                    source = p1

                dest = dupNode.attr(p2.shortName())

            source.connect(dest)
        # print '\t\t\touts'
        for p1, p2 in outConns:
            if p1.isDestination():
                # print "source:", p2, "dest:", p1
                if p1.node() == constr:
                    dest = dupNode.attr(p1.shortName())
                elif p1.node() == obj:
                    dest = dupObj.attr(p1.shortName())
                else:
                    dest = p1

                source = dupNode.attr(p2.shortName())
            else:
                # print "source:", p1, "dest:", p2
                # print 'old source:', p1, 'old dest:', p2
                if p2.node() == constr:
                    dest = dupNode.attr(p2.shortName())
                elif p2.node() == obj:
                    dest = dupObj.attr(p2.shortName())
                else:
                    dest = p2

                source = dupNode.attr(p1.shortName())

            if source.isConnectedTo(dest):
                continue
            if dest.isConnectedTo(source):
                continue
            if isinstance(dest.node(), nt.HyperLayout):
                continue

            source.connect(dest)
    # print 'dupWConst: ', dupObj
    return dupObj


def dimension(deleteAll=0):
    verts = ls(polyListComponentConversion(tv=1), fl=1)

    sets = [
        objSet
        for objSet in ls(et=nt.ObjectSet)
        if not objSet.name() == "defaultLightSet"
        and not objSet.name() == "defaultObjectSet"
    ]
    for objSet in sets:
        meshes = ls(listFuture(objSet), et=nt.Mesh)
        if meshes:
            emmiters = ls(listFuture(meshes[0]), et=nt.PointEmitter)
            if not emmiters:
                delete(objSet)

    if not objExists("dimensionsGr"):
        allDimsGroup = createNode(nt.Transform, n="dimensionsGr")
    else:
        allDimsGroup = PyNode("dimensionsGr")

    if deleteAll:
        select(ls(et=nt.PointEmitter))
        sets = [
            objSet
            for objSet in ls(et=nt.ObjectSet)
            if not objSet.name() == "defaultLightSet"
            and not objSet.name() == "defaultObjectSet"
        ]
        select(sets, add=1, ne=1)
        delete()

        if allDimsGroup.getChildren():
            delete(allDimsGroup.getChildren())
        return

    if len(verts) < 2:
        vis = allDimsGroup.visibility.get()
        allDimsGroup.visibility.set(1 - vis)
    else:
        v1, v2 = verts[:2]
        pos1 = v1.getPosition("world")
        pos2 = v2.getPosition("world")

        dimNode = createNode(nt.DistanceDimShape)

        loc1 = spaceLocator()
        loc2 = spaceLocator()

        select(v1)
        emitter()
        em1 = ls(sl=1)[0]

        select(v2)
        emitter()
        em2 = ls(sl=1)[0]

        move(loc1, pos1, rpr=1)
        move(loc2, pos2, rpr=1)

        pointConstraint(em1, loc1, mo=1, w=1)
        pointConstraint(em2, loc2, mo=1, w=1)

        loc1.worldPosition[0].connect(dimNode.startPoint)
        loc2.worldPosition[0].connect(dimNode.endPoint)

        parent(group(loc1, loc2, dimNode, n="dimension"), allDimsGroup)

        hide(loc1, loc2, em1, em2)
        allDimsGroup.overrideEnabled.set(1)
        allDimsGroup.overrideColor.set(1)


def placeAlongCurveConnect(obj, crvSh, paramStartDim, paramEndDim, pos):

    motionPath1 = createNode("motionPath", n="motionPath1")
    addDoubleLinear22 = createNode("addDoubleLinear", n="addDoubleLinear22")
    addDoubleLinear23 = createNode("addDoubleLinear", n="addDoubleLinear23")
    addDoubleLinear24 = createNode("addDoubleLinear", n="addDoubleLinear24")

    paramLength = createNode("plusMinusAverage", n="paramLength")
    paramStep = createNode("multiplyDivide", n="paramStep")
    paramStep_x_currCount = createNode("multiplyDivide", n="paramStep_x_currCount")
    currParamPos = createNode("plusMinusAverage", n="currParamPos")

    motionPath1.attr("follow").set(True)
    motionPath1.attr("frontAxis").set(2)
    motionPath1.attr("upAxis").set(1)

    setAttr(motionPath1.attr("bank"), k=1)
    setAttr(motionPath1.attr("bankLimit"), k=1)
    setAttr(motionPath1.attr("bankScale"), k=1)
    setAttr(motionPath1.attr("frontAxis"), k=1)
    setAttr(motionPath1.attr("inverseFront"), k=1)
    setAttr(motionPath1.attr("inverseUp"), k=1)
    setAttr(motionPath1.attr("normal"), k=1)
    setAttr(motionPath1.attr("upAxis"), k=1)
    setAttr(motionPath1.attr("worldUpType"), k=1)
    setAttr(motionPath1.attr("worldUpVectorX"), k=1)
    setAttr(motionPath1.attr("worldUpVectorY"), k=1)
    setAttr(motionPath1.attr("worldUpVectorZ"), k=1)

    paramLength.attr("operation").set(2)
    paramStep.attr("operation").set(2)
    paramStep_x_currCount.attr("input2X").set(pos)

    """-------------------Connecting attributes """

    connectAttr(
        obj.attr("transMinusRotatePivotX"), addDoubleLinear22.attr("input1"), f=1
    )
    connectAttr(
        obj.attr("transMinusRotatePivotY"), addDoubleLinear23.attr("input1"), f=1
    )
    connectAttr(
        obj.attr("transMinusRotatePivotZ"), addDoubleLinear24.attr("input1"), f=1
    )

    connectAttr(addDoubleLinear22.attr("output"), obj.attr("translateX"), f=1)
    connectAttr(addDoubleLinear24.attr("output"), obj.attr("translateZ"), f=1)
    connectAttr(addDoubleLinear23.attr("output"), obj.attr("translateY"), f=1)

    connectAttr(motionPath1.attr("xCoordinate"), addDoubleLinear22.attr("input2"), f=1)
    connectAttr(motionPath1.attr("yCoordinate"), addDoubleLinear23.attr("input2"), f=1)
    connectAttr(motionPath1.attr("zCoordinate"), addDoubleLinear24.attr("input2"), f=1)
    connectAttr(motionPath1.attr("message"), obj.attr("specifiedManipLocation"), f=1)
    connectAttr(motionPath1.attr("rotateX"), obj.attr("rotateX"), f=1)
    connectAttr(motionPath1.attr("rotateY"), obj.attr("rotateY"), f=1)
    connectAttr(motionPath1.attr("rotateZ"), obj.attr("rotateZ"), f=1)
    connectAttr(motionPath1.attr("rotateOrder"), obj.attr("rotateOrder"), f=1)

    connectAttr(crvSh.attr("worldSpace[0]"), motionPath1.attr("geometryPath"), f=1)

    connectAttr(paramEndDim.attr("uParamValue"), paramLength.attr("input1D[0]"), f=1)

    connectAttr(paramStartDim.attr("uParamValue"), currParamPos.attr("input1D[0]"), f=1)
    connectAttr(paramStartDim.attr("uParamValue"), paramLength.attr("input1D[1]"), f=1)

    connectAttr(paramLength.attr("output1D"), paramStep.attr("input1X"), f=1)
    connectAttr(
        paramStartDim.attr("ysvDupAlongCount_minus1"), paramStep.attr("input2X"), f=1
    )

    connectAttr(
        paramStep_x_currCount.attr("outputX"), currParamPos.attr("input1D[1]"), f=1
    )

    connectAttr(paramStep.attr("outputX"), paramStep_x_currCount.attr("input1X"), f=1)

    connectAttr(currParamPos.attr("output1D"), motionPath1.attr("uValue"), f=1)


def placeAlongCurve(multiSource=False, seq=True, orderMatters=False):
    crvSh = ls(sl=1, dag=1, et=nt.NurbsCurve)
    if crvSh:
        crvSh = crvSh[-1]

    if orderMatters:
        sourceObjects = [
            tr for tr in ls(sl=1, dag=1, et=nt.Transform) if not tr.getShape() == crvSh
        ]
    else:
        sourceObjects = [
            tr
            for tr in ls(sl=1, dag=1, et=nt.Transform)
            if type(tr.getShape()) == nt.Mesh
        ]

    paramDims = ls(sl=1, dag=1, et=nt.ParamDimension)

    crvPointTypes = [NurbsCurveCV, NurbsCurveEP, NurbsCurveParameter, NurbsCurveKnot]
    crvPoints = [pnt for pnt in ls(sl=1, fl=1) if type(pnt) in crvPointTypes]

    if multiSource:
        objs = []
        objsCount = int(optionVar(q="ysvDupAlongCurvesCount"))
        j = 0
        currSource = sourceObjects[j]
        for i in range(objsCount):
            if seq:
                j += 1
                if j > len(sourceObjects) - 1:
                    j = 0
                currSource = sourceObjects[j]
            else:
                r = random.Random()
                currSource = r.choice(sourceObjects)

            objs.append(instance(currSource)[0])

    else:
        if len(sourceObjects) > 1:
            objs = sourceObjects
            objsCount = len(objs)
        elif len(sourceObjects) == 1:
            objsCount = int(optionVar(q="ysvDupAlongCurvesCount"))
            objs = [instance(sourceObjects[0])[0] for i in range(objsCount)]
        else:
            return

    if crvSh:
        paramStartDim = paramDimension(crvSh.u[0])
        paramEndDim = paramDimension(crvSh.u[1])
    elif len(paramDims) == 2:
        crvSh = paramDims[0].getParent().getParent()

        if paramDims[0].uParamValue.get() > paramDims[1].uParamValue.get():
            paramStartDim = paramDims[1]
            paramEndDim = paramDims[0]
        else:
            paramStartDim = paramDims[0]
            paramEndDim = paramDims[1]
    elif len(crvPoints) == 2:
        crvSh = crvPoints[0].node()

        params = [
            crvSh.getParamAtPoint(pointPosition(pnt), "world") for pnt in crvPoints
        ]
        params.sort()

        paramStartDim = paramDimension(crvSh.u[params[0]])
        paramEndDim = paramDimension(crvSh.u[params[1]])

    if not paramStartDim or not paramEndDim:
        return

    if not paramStartDim.hasAttr("ysvDupAlongCount_minus1"):
        try:
            addAttr(paramStartDim, at="long", ln="ysvDupAlongCount_minus1")
        except:
            print("fail to add attribute:ysvDupAlongCount_minus1")
    if paramStartDim.attr("ysvDupAlongCount_minus1"):
        paramStartDim.attr("ysvDupAlongCount_minus1").set(objsCount - 1)
    for pos, obj in enumerate(objs):
        placeAlongCurveConnect(obj, crvSh, paramStartDim, paramEndDim, pos)

    gr = group(objs, n="objects")
    group(crvSh.getParent(), gr, n="placedAlong_{0}".format(crvSh.getParent()))

    hide(paramStartDim, paramEndDim)
    select(paramStartDim, paramEndDim)
    setToolTo("moveSuperContext")


def placeAlongCurves(multiSource=False, seq=True):
    crvs = ls(sl=1, dag=1, et=nt.NurbsCurve)
    sourceMeshes = ls(sl=1, dag=1, et=nt.Mesh)

    dims = []
    for crvSh in crvs:
        gr = createNode(nt.Transform, n="placeAlong_{0}".format(crvSh.getParent()))
        # xform(rp = , sp=, ws=1)

        step = optionVar(q="ysvDupAlongCurvesStep")
        objsCount = int(crvSh.length() / step + 1)

        if multiSource:
            objs = []
            j = 0
            currSource = sourceMeshes[j]
            for i in range(objsCount):
                if seq:
                    j += 1
                    if j > len(sourceMeshes) - 1:
                        j = 0
                    currSource = sourceMeshes[j]
                else:
                    r = random.Random()
                    currSource = r.choice(sourceMeshes)

                objs.append(instance(currSource)[0])

        else:
            objs = [instance(sourceMeshes[0])[0] for i in range(objsCount)]

        parent(objs, crvSh.getParent(), gr)

        paramDims = [
            sh.getParent() for sh in ls(listFuture(crvSh), et=nt.ParamDimension)
        ]
        delete(paramDims)

        paramStartDim = paramDimension(crvSh.u[0])
        paramEndDim = paramDimension(crvSh.u[1])
        dims += [paramStartDim, paramEndDim]

        if not paramStartDim.hasAttr("ysvDupAlongCount_minus1"):
            try:
                addAttr(paramStartDim, at="short", ln="ysvDupAlongCount_minus1", min=1)
            except:
                print("fail to add attribute:ysvDupAlongCount_minus1")
        if paramStartDim.attr("ysvDupAlongCount_minus1"):
            if objsCount == 1:
                paramStartDim.attr("ysvDupAlongCount_minus1").set(1)
            else:
                paramStartDim.attr("ysvDupAlongCount_minus1").set(objsCount - 1)

        for pos, obj in enumerate(objs):
            placeAlongCurveConnect(obj, crvSh, paramStartDim, paramEndDim, pos)

    hide(dims)
    select(dims)
    setToolTo("moveSuperContext")


def disconnectFromCurve():
    crvs = ls(sl=1, dag=1, et=nt.NurbsCurve)
    for crvSh in crvs:
        crv = crvSh.getParent()
        fut = listFuture(crv)
        depsTypes = [
            nt.AddDoubleLinear,
            nt.MotionPath,
            nt.MultiplyDivide,
            nt.PlusMinusAverage,
        ]

        deps = [node for node in fut if type(node) in depsTypes]
        paramDims = [sh.getParent() for sh in ls(fut, et=nt.ParamDimension)]

        delete(deps + paramDims)


def setDupsOptVar(slider=None):
    if not slider:
        if not optionVar(ex="ysvDupAlongCurvesStep"):
            optionVar(fv=("ysvDupAlongCurvesStep", 5))
        return

    val = floatSliderGrp(slider, q=1, v=1)
    optionVar(fv=("ysvDupAlongCurvesStep", val))


def setDistrOptVar(slider=None):
    if not slider:
        if not optionVar(ex="ysvDupAlongCurvesCount"):
            optionVar(fv=("ysvDupAlongCurvesCount", 5))
        return

    val = floatSliderButtonGrp(slider, q=1, v=1)
    optionVar(fv=("ysvDupAlongCurvesCount", val))


def calcCountFromStep(sliderStep, sliderCount):
    setDupsOptVar(sliderStep)

    crvPointTypes = [NurbsCurveCV, NurbsCurveEP, NurbsCurveParameter, NurbsCurveKnot]
    crvPoints = [pnt for pnt in ls(sl=1, fl=1) if type(pnt) in crvPointTypes]

    step = floatSliderGrp(sliderStep, q=1, v=1)

    if ls(sl=1, dag=1, et=nt.NurbsCurve):
        crv = ls(sl=1, dag=1, et=nt.NurbsCurve)[0]
        lng = crv.length()
        count = lng / step

    elif len(crvPoints) == 2:
        crvSh = crvPoints[0].node()
        params = [
            crvSh.getParamAtPoint(pointPosition(pnt), "world") for pnt in crvPoints
        ]
        params.sort()

        lng = crvSh.length() * (params[1] - params[0])
        count = lng / step

    else:
        count = 0

    optionVar(fv=("ysvDupAlongCurvesCount", count))
    floatSliderGrp(sliderCount, e=1, v=count)


# ===============================================================================
# def duplicateAlongCurves(doInstance=1):
#     selectPref(tso=1)
#     for obj in ls(sl=1, dag=1, et=nt.Transform):
#         wPos = xform(obj, q=1, ws=1, sp=1)
#         move(obj, 0, 0, 0, rpr=1)
#         makeIdentity(obj, a=1, t=1, s=1, r=1)
#         move(obj, wPos, ws=1)
#
#     if ls(sl=1, dag=1, et=nt.Mesh):
#         mesh = [m for m in ls(sl=1, dag=1, et=nt.Mesh) if not m.isIntermediate()][0]
#
#     crvs = ls(sl=1, dag=1, et=nt.NurbsCurve)
#     if not mesh or not crvs:return
#
#     step = optionVar(q='ysvDupAlongCurvesStep')
#     instGroups = []
#     for crvSh in crvs:
#         instances = []
#         if crvSh.f.get()>0:
#             res = crvSh.numCVs()
#             crvSh=yCrv.crvDetachGentle(crvSh, res)
#
#         crvLen = crvSh.length()
#         numCopies = int(math.floor(crvLen/step)+1)
#         print 'numCopies:', numCopies
#         parStep = 1.0/numCopies
#
#         dup = duplicate(mesh)[0]
#         for i in range(numCopies):
#             par = i*parStep
#             pos = crvSh.getPointAtParam(par, 'world')
#
#             if doInstance:
#                 inst = instance(dup)[0]
#             else:
#                 inst = duplicate(dup)[0]
#
#             move(inst, pos, a=1, ws=1)
#
#             geometryConstraint(crvSh, inst, w=1)
#             tangConstr=tangentConstraint (crvSh, inst, w=1, aim=(-1,0,0), wut='object')
#
#
#             setAttr(tangConstr.aimVectorX, k=1, cb=1)
#             setAttr(tangConstr.aimVectorY, k=1, cb=1)
#             setAttr(tangConstr.aimVectorZ, k=1, cb=1)
#
#             instances.append(inst)
#         delete(dup)
#
#         instGroups.append(group(instances, n='DupAlong_{0}'.format(crvSh.getParent().name())))
#
#     select(instGroups)
#
#
# def decodeCrvPar(par):
#     value = par.split('[')[1].split(']')[0]
#     return float(value)
# ===============================================================================


def distributeAlongCurve():
    objs = [
        s
        for s in ls(sl=1, dag=1, et=nt.Transform)
        if not isinstance(s.getShape(), nt.NurbsCurve)
        and not isinstance(s, nt.Constraint)
    ]
    if not objs:
        return

    crvParams = [s for s in ls(sl=1) if isinstance(s, NurbsCurveParameter)]

    if crvParams:
        params = [float(p.split("u[")[1].split("]")[0]) for p in crvParams]
        if params[0] > params[1]:
            tmp = params[1]
            params[1] = params[0]
            params[0] = tmp

        crv = crvParams[0].node()
        paramStep = (math.fabs(params[1] - params[0])) / (len(objs) - 1)

        for i, obj in enumerate(objs):
            par = params[0] + paramStep * i
            pnt = pointPosition(crv.u[par], w=1)
            move(obj, pnt, a=1, ws=1)

    else:
        crvSh = ls(sl=1, dag=1, et=nt.NurbsCurve)
        if crvSh:
            crvSh = crvSh[0]
        if not crvSh:
            return

        parStep = 1.0 / (len(objs) - 1)
        for i, obj in enumerate(objs):
            par = float(i) * parStep
            pos = pointPosition(crvSh.u[par], w=1)
            move(obj, pos, a=1, ws=1)


def revertConstrAxis():
    for tCon in ls(sl=1, dag=1, et=nt.TangentConstraint):
        tCon.aimVector.set(-tCon.aimVector.get())


def flipAroundY():
    for obj in ls(sl=1, o=1):
        verts = obj.getShape().vtx
        rotate(verts, 0, 180, 0, r=1, p=xform(obj, q=1, rp=1, ws=1))


def motionPathInversAttr(attrName):
    trs = ls(sl=1, dag=1, et=nt.Transform)
    motionNodes = set(
        [
            hNode
            for tr in trs
            for hNode in set(ls(listConnections(tr), et=nt.MotionPath))
        ]
    )
    for node in motionNodes:
        try:
            val = node.attr(attrName).get()
            node.attr(attrName).set(1 - val)
        except:
            pass


def wrapVertLoop():

    edges = [edge for edge in ls(sl=1) if type(edge) == MeshEdge]
    crvSh = ls(sl=1, dag=1, et=nt.NurbsCurve)[0]
    verts = yPoly.getOrderedLoopVerts(edges)

    p0 = verts[0].getPosition("world")
    p1 = verts[1].getPosition("world")
    s0 = pointPosition(crvSh.u[0])
    if (p0 - s0).length() > (p1 - s0).length():
        verts.reverse()

    gr = createNode(nt.Transform, n="vertWrapperHandlers")
    handlers = []

    for v in verts:
        pos = v.getPosition("world")
        edge = v.connectedEdges().currentItem()
        eLen = edge.getLength() * 0.1

        crv = curve(d=1, p=(pos, pos + dt.Vector(0, 1, 0) * eLen))
        xform(crv, sp=pos, rp=pos)
        handlers.append(crv)
        parent(crv, gr)

        select(v, crv)
        mc.CreateWrap()
    select(handlers, crvSh.getParent())
    placeAlongCurve(orderMatters=True)
    gr.hide()


def dupAlongCurvesWnd():
    setDupsOptVar()
    step = optionVar(q="ysvDupAlongCurvesStep")
    count = optionVar(q="ysvDupAlongCurvesCount")
    if window("ysvDupAlongCrvWnd", ex=1):
        deleteUI("ysvDupAlongCrvWnd")
        return

    with window(
        "ysvDupAlongCrvWnd",
        t="duplicate Along curves (front -Z, side X)",
        mnb=0,
        mxb=0,
        rtf=1,
        w=300,
        h=30,
    ) as wnd:
        with columnLayout():
            with rowLayout(nc=7):

                # slider = floatSliderGrp(l='Step', field=True, min=0,max=50, fmx=10000, value=step, pre = 2)
                # floatSliderGrp(slider, e=1, cc=Callback(setDupsOptVar, slider) )
                # setBtn = button(l="Duplicate", c=Callback(duplicateAlongCurves))

                slider = floatSliderButtonGrp(
                    label="Step: ",
                    bl="multiCurves",
                    bc=Callback(placeAlongCurves),
                    f=True,
                    cw4=(40, 60, 149, 3),
                    w=250,
                    min=0.5,
                    max=100,
                    fmx=100000,
                    v=step,
                    pre=2,
                )

                pMenu = popupMenu(p=slider)
                menuItem(
                    p=pMenu,
                    l="MultiSourceSeq",
                    c=Callback(placeAlongCurves, True, True),
                )
                menuItem(
                    p=pMenu,
                    l="MultiSourceRand",
                    c=Callback(placeAlongCurves, True, False),
                )
                menuItem(
                    p=pMenu,
                    l="Select tangentConstraints",
                    c="select(ls(sl=1, dag=1, et=nt.TangentConstraint))",
                )
                menuItem(p=pMenu, l="Revert tangent Axis", c=Callback(revertConstrAxis))
                # button(l="Distribute", c=Callback(distributeAlongCurve))

                slider1 = floatSliderButtonGrp(
                    label="Count : ",
                    f=True,
                    bl="PlaceAlong",
                    cw=(1, 40),
                    w=250,
                    min=0,
                    max=50,
                    fmx=5000,
                    v=count,
                    pre=0,
                )
                floatSliderButtonGrp(
                    slider1,
                    e=1,
                    cc=Callback(setDistrOptVar, slider1),
                    bc=Callback(placeAlongCurve),
                )
                pMenu = popupMenu(p=slider1)
                menuItem(
                    p=pMenu, l="MultiSourceSeq", c=Callback(placeAlongCurve, True, True)
                )
                menuItem(
                    p=pMenu,
                    l="MultiSourceRand",
                    c=Callback(placeAlongCurve, True, False),
                )
                menuItem(
                    p=pMenu, l="Clear selected curves", c=Callback(disconnectFromCurve)
                )
                menuItem(
                    p=pMenu,
                    l="Invers inverseUp",
                    c=Callback(motionPathInversAttr, "inverseUp"),
                )
                menuItem(p=pMenu, l="Flip aroundY", c=Callback(flipAroundY))

                button(l="EdgeLoop2Crv", c=Callback(wrapVertLoop))

                floatSliderButtonGrp(
                    slider, e=1, cc=Callback(calcCountFromStep, slider, slider1)
                )

    showWindow(wnd)


def viewAxis(obj, camPos):
    pos = xform(obj, q=1, sp=1, ws=1)
    matr = obj.getMatrix(ws=1)
    camView = (pos - camPos).normal()

    xang = camView.dot(dt.Vector(1, 0, 0) * matr)
    yang = camView.dot(dt.Vector(0, 1, 0) * matr)
    zang = camView.dot(dt.Vector(0, 0, 1) * matr)

    angles0 = [xang, yang, zang]

    angles = [math.fabs(xang), math.fabs(yang), math.fabs(zang)]
    maxAng = max(angles)

    id = angles.index(maxAng)
    axes = ["x", "y", "z"]
    return axes[id], angles0[id] < 0


def mirrorScale(obj, axis, direct, keepPivot):
    objPos = dt.Point(xform(obj, q=1, sp=1, ws=1))

    bb = obj.getShape().boundingBox()
    xMin, yMin, zMin = bb.min()
    xMax, yMax, zMax = bb.max()

    piv0Pos = xform(obj, q=1, sp=1)
    piv0PosWS = xform(obj, q=1, sp=1, ws=1)
    xC, yC, zC = bb.center()

    axes = [(-1, 1, 1), (1, -1, 1), (1, 1, -1)]
    pivots = [
        [(xMin, yC, zC), (xMax, yC, zC)],
        [(xC, yMin, zC), (xC, yMax, zC)],
        [(xC, yC, zMin), (xC, yC, zMax)],
    ]

    vec = axes[axis]

    print("startPiv:", xform(obj, q=1, sp=1, ws=1))
    if keepPivot:
        scale(obj, vec, r=1)

    else:
        if piv0PosWS == [0, 0, 0]:
            xform(obj, rp=piv0PosWS, sp=piv0PosWS, ws=1)
            scale(obj, vec, r=1)
            xform(obj, rp=piv0Pos, sp=piv0Pos)

        else:
            pivPos = pivots[axis][direct]

            xform(obj, rp=pivPos, sp=pivPos)
            scale(obj, vec, r=1)
            xform(obj, rp=piv0Pos, sp=piv0Pos)


def mirror(obj, direct, keepPivot):
    currCam = PyNode(modelPanel(getPanel(wf=1), q=1, cam=1))
    camMatr = currCam.getMatrix(ws=1)

    # objMatr = obj.getMatrix(ws=1)
    objMatr = dt.Matrix(obj.__apimdagpath__().inclusiveMatrix())
    print("objMat: ", objMatr)
    # ------------------------------ RIGHT ---------------------------
    camRight = dt.Vector(1, 0, 0) * camMatr

    xang = camRight.dot(dt.Vector(1, 0, 0) * objMatr)
    yang = camRight.dot(dt.Vector(0, 1, 0) * objMatr)
    zang = camRight.dot(dt.Vector(0, 0, 1) * objMatr)

    angles = [math.fabs(xang), math.fabs(yang), math.fabs(zang)]
    maxAng = max(angles)

    idRht = angles.index(maxAng)
    rightDir = ["x", "y", "z"][idRht]

    isRightOpposite = [xang, yang, zang][idRht] < 0

    print("right:\t\t ", rightDir, "\t\topposite:", isRightOpposite)

    # ------------------------------ Up ---------------------------
    camUp = dt.Vector(0, 1, 0) * camMatr
    xang = camUp.dot(dt.Vector(1, 0, 0) * objMatr)
    yang = camUp.dot(dt.Vector(0, 1, 0) * objMatr)
    zang = camUp.dot(dt.Vector(0, 0, 1) * objMatr)

    angles = [math.fabs(xang), math.fabs(yang), math.fabs(zang)]
    maxAng = max(angles)

    idUp = angles.index(maxAng)
    upDir = ["x", "y", "z"][idUp]

    isUpOpposite = [xang, yang, zang][idUp] < 0

    """
    if upDir == rightDir:
        if idRht==0: angles = angles[1:]
        elif idRht==1: angles = angles[0, 2]
        elif idRht==2: angles = angles[:-1]
        
        print 'angles after :', angles
        maxAng = max(angles)
        idUp = angles.index(maxAng)
        
        print 'axes after: ', 
        if idRht==0: 
            print 'y, z'
            upDir = ['y', 'z'][idUp]
            isUpOpposite = [yang, zang][idUp] < 0
        elif idRht==1: 
            print 'x, z'
            upDir = ['x', 'z'][idUp]
            isUpOpposite = [xang, zang][idUp] < 0
        elif idRht==2: 
            print 'x, y'
            upDir = ['x', 'y' ][idUp]
            isUpOpposite = [xang, yang][idUp] < 0
    """

    print("up:\t\t ", upDir, "\t\topposite: ", isUpOpposite)

    if direct == "up":
        mirrorScale(obj, idUp, 1 - isUpOpposite, keepPivot)
    elif direct == "down":
        mirrorScale(obj, idUp, isUpOpposite, keepPivot)
    elif direct == "right":
        mirrorScale(obj, idRht, 1 - isRightOpposite, keepPivot)
    elif direct == "left":
        mirrorScale(obj, idRht, isRightOpposite, keepPivot)


def mirrorSimple(direct, keepPivot=False):
    objs = ls(sl=1, o=1)
    if not objs:
        return

    for obj in objs:
        isMesh = False
        if type(obj.getShape()) == nt.Mesh:
            dup = PyNode(polyDuplicateAndConnect(obj)[0])
            isMesh = True
        else:
            dup = instance(obj)[0]

        mirror(dup, direct, keepPivot)

        if isMesh:
            polyNormal(dup, nm=0, unm=0)
            dup.getShape().doubleSided.set(1)
            # obj.getShape().displaySmoothMesh.connect(dup.getShape().displaySmoothMesh, f=1)

    select(objs)


def mirrorExact(direct, isOpposite, keepPivot):
    objs = ls(sl=1, o=1)
    if not objs:
        return

    for obj in objs:
        isMesh = False
        if type(obj.getShape()) == nt.Mesh:
            dup = PyNode(polyDuplicateAndConnect(obj)[0])
            isMesh = True
        else:
            dup = instance(obj)[0]

        mirrorScale(dup, direct, isOpposite, keepPivot)

        if isMesh:
            polyNormal(dup, nm=0, unm=0)
            dup.getShape().doubleSided.set(1)
            # obj.getShape().displaySmoothMesh.connect(dup.getShape().displaySmoothMesh, f=1)

    select(objs)


def bakeCompsAxisToObj():
    faces = [f for f in ls(sl=1, fl=1) if type(f) == MeshFace]
    edges = [e for e in ls(sl=1, fl=1) if type(e) == MeshEdge]

    if faces and not edges:
        face = faces[0]
        v0, v1, v2 = [v for v in face.connectedVertices()][0:3]

    elif faces and edges:
        edge = edges[0]
        face = faces[0]

        fConnEdges = [e for e in face.connectedEdges()]
        eConnEdges = [e for e in edge.connectedEdges() if e in fConnEdges]

        edge1 = edge
        edge2 = eConnEdges[0]

        verts1 = [v for v in edge1.connectedVertices()]
        verts2 = [v for v in edge2.connectedVertices()]

        midVert = [v for v in verts1 if v in verts2][0]

        midVertId1 = verts1.index(midVert)
        midVertId2 = verts2.index(midVert)

        v0 = midVert
        v1 = verts1[1 - midVertId1]
        v2 = verts2[1 - midVertId2]
    else:
        return

    mesh = face.node()
    tr = mesh.getParent()

    par = tr.getParent()
    parent(tr, w=1)

    makeIdentity(tr, a=1, r=1)

    startPnts = [v.getPosition("world") for v in (v0, v1, v2)]

    triMesh = polyCreateFacet(ch=0, s=1, p=[(100, 0, 0), (0, 0, 0), (0, 0, 100)])[0]
    triMesh = PyNode(triMesh).getShape()

    tv0, tv1, tv2 = [v for v in triMesh.vtx]
    # print ls(triMesh.vtx, fl=1)

    select(v0, v1, v2, tv0, tv1, tv2)
    mc.Snap3PointsTo3Points(0)
    delete(triMesh.getParent())

    makeIdentity(tr, a=1, r=1)

    triMesh = polyCreateFacet(ch=0, s=1, p=startPnts)[0]
    triMesh = PyNode(triMesh).getShape()
    tv0, tv1, tv2 = [v for v in triMesh.vtx]
    # print ls(triMesh.vtx, fl=1)

    select(v0, v1, v2, tv0, tv1, tv2)
    mc.Snap3PointsTo3Points(0)
    delete(triMesh.getParent())

    parent(tr, par)
    select(tr)


def manipHandle2Component():
    currTool = currentCtx()
    selComp = ls(sl=1, fl=1)[0]

    selTypeEdges = selectType(q=1, pe=1)
    selTypeFaces = selectType(q=1, pf=1)

    if type(selComp) == MeshFace:
        normal = selComp.getNormal("world")
    elif type(selComp) == MeshEdge:
        normal = selComp.getPoint(1, "world") - selComp.getPoint(0, "world")
    elif type(selComp) == MeshVertex:
        normal = selComp.getNormal("world")

    try:
        manipMoveContext("Move", e=1, aa=normal, mode=6)
        manipScaleContext("Scale", e=1, aa=normal, mode=6)
        manipRotateContext("Rotate", e=1, aa=normal, mode=6)
    except:
        warning("wrong selection")

    setToolTo(currTool)
    selectType(pe=selTypeEdges)
    selectType(pf=selTypeFaces)
