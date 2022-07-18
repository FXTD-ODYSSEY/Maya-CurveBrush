import maya.cmds as mc
import maya.OpenMaya as om

from pymel.core import *
import pymel.core.datatypes as dt
import pymel.core.nodetypes as nt
import math
from ysvUtils import SEL

import itertools as it
import operator

# LOOK FOR SOME SOURCES IN:
#                          modifySelectedCurves.mel

def forceHistory(cmd, *args, **kwargs):
    if not str(type(cmd)) == '<type \'function\'>': return
    
    print listHistory(args[0])
    
    #===========================================================================
    # if len(listHistory(args[0]))>2:
    #     kwargs['rpo'] = 1
    #     return cmd(*args, **kwargs)
    # else:
    #===========================================================================
    oldCrvSh = args[0].getShape()
    # outs = oldCrvSh.outputs(p=1)
    outs = oldCrvSh.listConnections(d=1, s=0, p=1)
    
    parGr = args[0].getParent()
    kwargs['rpo'] = 0
    newObj, histNode = cmd(*args, **kwargs)
    histNode.rename(cmd.__name__)
    newCrvSh = newObj.getShape()
    
    shName = oldCrvSh.name()
    oldCrvSh.rename(shName + '_in')
    newCrvSh.rename(shName)
    
    parent(oldCrvSh, newObj, s=1, r=1)
    parent(newCrvSh, args[0], s=1, r=1)

    oldCrvSh.io.set(1)
    parent(oldCrvSh, args[0], s=1, r=1)
    
    delete(newObj)
    

    for dest in outs: 
        sources = [src for src in dest.inputs(p=1) if src.node() == oldCrvSh]
        for s in sources:
            newCrvSh.attr(s.shortName()).connect(dest, f=1)
        # newCrvSh.attr(src.shortName()).connect(dest, f=1) 
    newCrvSh.dispCV.set(oldCrvSh.dispCV.get())
    
    return args[0], histNode

def forceHistoryCos(cmd, *args, **kwargs):
    print 'getting history for: ', args[0]
    if not str(type(cmd)) == '<type \'function\'>': return
    
    if len(listHistory(args[0])) > 2:
        kwargs['rpo'] = 1
        return cmd(*args, **kwargs)
    else:
        kwargs['rpo'] = 0
        newObj, histNode = cmd(*args, **kwargs)
        crvSh = args[0].getShape()
        
        crvSh.io.set(1)
        
        crvName = args[0].name().split('->')[1]
        hide(args[0])
                
        newObj.rename(crvName)
        return newObj, histNode

def smthCrv():
    curves = ls(filterExpand(sm=9))
    for crv in curves:
        oldCrvSh = crv.getShape()
        # outs = oldCrvSh.outputs(p=1)
        outs = oldCrvSh.listConnections(d=1, s=0, p=1)
        
        parGr = crv.getParent()
        
        newObj, histNode = smoothCurve(crv.cv, ch=1, rpo=0, s=10)
        histNode.rename(smoothCurve.__name__)
        newCrvSh = newObj.getShape()
        
        shName = oldCrvSh.name()
        oldCrvSh.rename(shName + '_in')
        newCrvSh.rename(shName)
        
        parent(oldCrvSh, newObj, s=1, r=1)
        parent(newCrvSh, crv, s=1, r=1)
        
        oldCrvSh.io.set(1)
        parent(oldCrvSh, crv, s=1, r=1)
        
        delete(newObj)
        '''
        for dest in outs: 
        sources = [src for src in dest.inputs(p=1) if src.node() == oldCrvSh]
        for s in sources:
            newCrvSh.attr(s.shortName()).connect(dest, f=1)
        # newCrvSh.attr(src.shortName()).connect(dest, f=1) 
        newCrvSh.dispCV.set(oldCrvSh.dispCV.get())
        
        return args[0], histNode
        '''
        
    smoothNodes = ls(listHistory(curves), et=nt.SmoothCurve)
    select(smoothNodes+curves)
    setToolTo('ShowManips')
    
        
        

def rbldRange01(*args, **kwargs):
    
    kwargs['replaceOriginal'] = 1
    kwargs['keepRange'] = 0
    kwargs['keepControlPoints'] = 1
    
    return rebuildCurve(*args, **kwargs)

def rbldSimple(*args, **kwargs):
    kwargs['ch'] = 1 
    kwargs['replaceOriginal'] = 1 
    kwargs['rebuildType'] = 0 
    kwargs['endKnots'] = 1 
    kwargs['keepRange'] = 0 
    kwargs['keepControlPoints'] = 0 
    kwargs['keepEndPoints'] = 1 
    kwargs['keepTangents'] = 1 
    kwargs['degree'] = 3 
    kwargs['tolerance'] = 0.01 

    return rebuildCurve(*args, **kwargs)

def crvDetachGentle(crv, res):
    curves = detachCurve(crv.u[0.95], crv.u[0.951], ch=0, cos=1, rpo=1)[:-1]
    maxLen = 0
    resCurve = None
    for c in curves:
        c = ls(c, dag=1, et=nt.NurbsCurve)[0]
        if c.length() > maxLen:
            maxLen = c.length()
            resCurve = c
    select(curves)
    select(resCurve.getParent(), d=1)
    print 'resCurve:', resCurve
    delete()
    resCurve.dispCV.set(1)
    rebuildCurve(resCurve, ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=res, d=3, tol=0.01)
    return resCurve

def detachFromPoints():
    cvs = ls(sl=1, fl=1)
    params = [cv.node().getParamAtPoint(pointPosition(cv), 'world') for cv in cvs]
    crvPoints = [cv.node().u[param] for param in params]
    select(crvPoints)
    mc.DetachCurve()

def setOptVar(slider):
    val = floatSliderGrp(slider, q=1, v=1)
    print val
    optionVar(fv=('ysvRebuildCurveStep', val))        

def setRebuildCurveStepWnd():
    with window(t='set step for rebuilding curve', mnb=0, mxb=0, s=0, rtf=1, w=400, h=30) as wnd:
        with columnLayout():
            with rowLayout(nc=2):
                if not optionVar(ex='ysvRebuildCurveStep'):
                    optionVar(fv=('ysvRebuildCurveStep', 0.25))        
                val = optionVar(q='ysvRebuildCurveStep')
                
                slider = floatSliderGrp(l='Width', field=True, min=0, max=100, value=val, pre=2)
                floatSliderGrp(slider, e=1, cc=Callback(setOptVar, slider))
                
    showWindow(wnd)

def projectCurves(res):
    polyShapes = mc.ls(sl=1, dag=1, et="mesh")
    curvesShapes = mc.ls(sl=1, dag=1, et="nurbsCurve")
    
    polyObj = mc.listRelatives(polyShapes[0], p=1)[0]
    curves = mc.listRelatives(curvesShapes, p=1)
    print curves
    print curvesShapes
    
    prjCurvesParents = []
    
    for c in curves:
        prjCurvesParents.append(mc.polyProjectCurve(polyObj, c, ch=0)[0])
    
    mc.select(prjCurvesParents, r=1)
    mc.pickWalk(d="Down")
    mc.parent(w=1)
    
    prjCurves = mc.ls(sl=1, o=1)
    mc.delete(prjCurvesParents)
    
    mc.select(cl=1)
    mc.makeLive()
    
    return prjCurves

def rebuildWithStep(step=None, degree=3):
    if not step:
        if not optionVar(ex='ysvPaintCurveStep'):
            optionVar(iv=('ysvPaintCurveStep', 3))
        step = optionVar(q='ysvPaintCurveStep')
    sel = ls(sl=1)
    curveShapes = ls(sl=1, dag=1, et=nt.NurbsCurve)
    curves = [sh.getParent() for sh in curveShapes]
    for crv in curves:
        length = arclen(crv, ch=0)
        res = length / step
        rebuildCurve(crv, ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=res, d=degree, tol=0.01)
    select(sel)

def filletCurves(curves, circ=1, tol=0.001):
    nodes = []
    lng = reduce(operator.add, [crv.length() for crv in curves])
    lng /= len(curves)
    rad = lng * 0.15
        
    pairs = it.combinations(curves, 2)
    for c1, c2 in pairs:
        s1 = pointPosition(c1.cv[0], w=1)
        e1 = pointPosition(c1.cv[-1], w=1)

        s2 = pointPosition(c2.cv[0], w=1)
        e2 = pointPosition(c2.cv[-1], w=1)
        
        c1Max = c1.maxValue.get()
        c1Min = c1.minValue.get()
        c2Max = c2.maxValue.get()
        c2Min = c2.minValue.get()
        
        c1Range = c1Max - c1Min
        c2Range = c2Max - c2Min
        
        
        if (s1 - s2).length() < tol:
            par1 = c1Min + 0.2 * c1Range
            par2 = c2Min + 0.2 * c2Range
            nodes += filletCurve(c1.u[par1], c2.u[par2], ch=1, rpo=1, t=1, jn=0, cir=circ, r=rad, bc=0)
            
        elif (s1 - e2).length() < tol:
            par1 = c1Min + 0.2 * c1Range
            par2 = c2Max - 0.2 * c2Range
            nodes += filletCurve(c1.u[par1], c2.u[par2], ch=1, rpo=1, t=1, jn=0, cir=circ, r=rad, bc=0)
            
        elif (e1 - s2).length() < tol:
            par1 = c1Max - 0.2 * c1Range
            par2 = c2Min + 0.2 * c2Range
            nodes += filletCurve(c1.u[par1], c2.u[par2], ch=1, rpo=1, t=1, jn=0, cir=circ, r=rad, bc=0)
        
        elif (e1 - e2).length() < tol:
            par1 = c1Max - 0.2 * c1Range
            par2 = c2Max - 0.2 * c2Range
            nodes += filletCurve(c1.u[par1], c2.u[par2], ch=1, rpo=1, t=1, jn=0, cir=circ, r=rad, bc=0)
    
    filletNodes = [node for node in listHistory(nodes) if type(node) == nt.FilletCurve]
    curves = [node for node in nodes if type(node) == nt.Transform]
    map(lambda n:n.dispCV.set(0), curves)
    select(filletNodes)
    setToolTo('ShowManips')
        
def extendCurvesFromParamPoints(pnts):
    curves = []
    nodes = []    
    for pnt in pnts:
        shape = pnt.node()
        tr = shape.getParent()
        
        parMin = shape.minValue.get()
        parMax = shape.maxValue.get()
        
        range = parMax - parMin
        
        pntPar = float(pnt.name().split('.u[')[1].split(']')[0])
        
        if pntPar - parMin < parMax - pntPar:
            extendDir = 1  # from curveStart
        else:
            extendDir = 0  # from curve End
        if '->' in pnt.node().name(): 
            curve, node = forceHistoryCos(extendCurve, tr, cos=1, ch=1, em=0, et=0, d=0.1, s=extendDir, jn=1, rmk=1)
        else:
            curve, node = forceHistory(extendCurve, tr, cos=0, ch=1, em=0, et=0, d=0.1, s=extendDir, jn=1, rmk=1)
        curves.append(curve)
        nodes.append(node)
    
    select(curves, nodes)
    setToolTo('ShowManips')
    
def extedCurvesBidirectional(curves):
    resCurves = []
    nodes = []
    for crv in curves:
        if '->' in crv.name(): 
            curve, node = forceHistoryCos(extendCurve, crv, cos=1, ch=1, em=0, et=2, d=0.1, s=2, rmk=1)
        else:
            curve, node = forceHistory(extendCurve, crv, cos=0, ch=1, em=0, et=0, d=0.1, s=2, rmk=1)
        resCurves.append(curve)
        nodes.append(node)
    
    select(curves, nodes)
    setToolTo('ShowManips')
    
def offsetCurves(curves):
    results = []
    for crv in curves:
        bb = crv.boundingBox()
        dist = (bb.width() + bb.height() + bb.depth()) * 0.05
        
        if '->' in crv.name():
            res = offsetCurveOnSurface(crv, ch=1, rn=0, cb=2, st=1, cl=1, d=dist, tol=0.0001, sd=5)
            crv.getShape().io.set(1)
            results += res
            
        else:
            res = offsetCurve(crv, ch=1, rn=0, cb=2, st=1, cl=1, cr=dist * 0.2, d=dist, tol=0.01, sd=5, ugn=0)
            expression(s="{0}.cutRadius={0}.distance*0.2".format(res[1].name()), o=res[0], ae=1, uc='all')
            
            crv.getShape().io.set(1)
            parent(crv.getShape(), res[0], r=1, s=1)
            
            name = crv.name()
            delete(crv)
            res[0].rename(name + '_offs')
            
        results += res
        
    select(results)
    setToolTo('ShowManips')                

def getTrimEdgeIds(edge):
    if not type(edge) == Component and not type(edge.node()) == nt.NurbsSurface:
        return 0, 0, -1
    
    name = edge.name()
    regId = int(name.split('[')[1].split(']')[0])
    bndId = int(name.split('[')[2].split(']')[0])
    edgeId = int(name.split('[')[3].split(']')[0])
    
    return regId, bndId, edgeId

def getIsoUVParams(iso):
    name = iso.name()
    
    if '.uv[' in name:
        uPar = float(name.split('.uv[')[1].split(']')[0])
        vPar = float(name.split('.vv[')[2].split(']')[0])
        return uPar, vPar
    
    elif '.u[' in name:
        uPar = float(name.split('.u[')[1].split(']')[0])
        return uPar
    
    elif '.v[' in name:
        vPar = float(name.split('.u[')[1].split(']')[0])
        return uPar
    
    else:return

def curveFromTrimEdge(edges, isAllEdgesInBoundary=0):
    curves = []
    nodes = []
    for edge in edges:
        crvSh = createNode(nt.NurbsCurve)
        crvFS = createNode(nt.CurveFromSurfaceBnd)
        surfSh = edge.node()
        
        surfSh.worldSpace[0].connect(crvFS.inputSurface, f=1)
        crvFS.outputCurve.connect(crvSh.create)
            
        reg, bnd, edge = getTrimEdgeIds(edge)
        crvFS.face.set(reg)
        crvFS.boundary.set(bnd)
        
        if not isAllEdgesInBoundary: crvFS.edge.set(edge)
        else: crvFS.edge.set(-1)
        
        center = pointPosition(crvSh.cv[0], w=1)
        xform(crvSh.getParent(), rp=center, sp=center, ws=1, a=1)
        crvSh.dispCV.set(1)
        
        curves.append(crvSh.getParent())
        nodes.append(crvFS)
    select(curves, nodes)
    setToolTo('ShowManips')

def rebuildCurves(curves):
    results = []
    for c in curves:
        if '->' in c.name(): 
            print 'cos rebuild'
            res = forceHistoryCos(rebuildCurve, c, ch=1, rpo=1, rt=4, end=1, kr=0, kcp=0, kep=1, kt=0, s=64, d=3, tol=0.01)[0]
        else:
            print 'curve rebuild'
            #res = forceHistory(rebuildCurve, c, ch=1, rpo=1, rt=4, end=1, kr=0, kcp=0, kep=1, kt=0, s=64, d=3, tol=0.01)[0]
            if not optionVar(ex='ysvPaintCurveStep'):
                optionVar(iv=('ysvPaintCurveStep', 3))
            step = optionVar(q='ysvPaintCurveStep')
            length = arclen(c, ch=0)
            res = length / step            
            
            tDeg = c.attr('degree').get()
            res = forceHistory(rebuildCurve, c, ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=res, d=tDeg, tol=0.01)[0]

        res.dispCV.set(1)
        results.append(res)
    select(results)
    return results

def smoothCrvPoints(points):
    for i in range(1, len(points)-1):
        points[i]  = points[i] * 0.4 + (points[i+1] + points[i-1]) * 0.3
        
def smoothCrvOrCVs():
    crvCvs = []
    clearHistoryCurves = []
    
    curves = SEL.curves() 
    if curves:
        clearHistoryCurves += curves
        for crv in curves: crvCvs.append(crv.cv)
    else:
        cvs = SEL.cvs()
        crvCvs.append(cvs)
        clearHistoryCurves.append(cvs[0].node())
        
    delete(clearHistoryCurves, cn=1, e=1, ch=1, c=1)
    delete(ls(clearHistoryCurves, dag=1, s=1, io=1))
    
    iterations = optionVar(q = 'smoothHairCurvesSmoothFactor')
    for cvs in crvCvs:
        for i in range(iterations+1):
            pnts = [pointPosition(cv) for cv in cvs]
            
            smoothCrvPoints(pnts)
            for cv, pos in zip(cvs, pnts): move(cv, pos, a=1, ws=1)
                
def findClosestPointAlongRay(sPoint, rayDir, crv, toler):
    crvFn = crv.__apimfn__()
    
    makeIdentity(crv, t=1, r=1, s=1, a=1)
    bounds =  xform(crv, q=1, a=1, ws=1, bb=1)
    crvBB = dt.BoundingBox(dt.Point(bounds[:3]), dt.Point(bounds[3:]))
    
    toCrvDist = (sPoint - dt.Point(crvBB.center())).length()

    currOffset = max(crvBB.width(), crvBB.height(), crvBB.depth ()) * 1.5 # magic number
    
    currCenterPoint = sPoint + rayDir * toCrvDist
    currFarPoint = currCenterPoint + rayDir * Offset
    currNearPoint = currCenterPoint - rayDir * Offset
    currDist = crv.distanceToPoint(currCenterPoint, space='world')
    minDist = currOffset * 10  # magic number
    
    print 'minDist: ', minDist
    
    #                    START BINARY SEARCH
    iterNum = 0
    while (abs(minDist-currDist)>toler and iterNum<100):
        #TODO: choose currDist here
        
        if currDist < minDist:
            minDist = currDist
        pass

    print 'iterNum: ', iterNum
    print 'minDist: ', minDist
    
    
#currCam = PyNode(modelPanel(getPanel(wf=1), q=1, cam=1))
#viewDir = currCam.viewDirection(space='world')
#eyePnt = currCam.getEyePoint(space='world')

#crv = ls(sl=1, dag=1, s=1)[0]
#findClosestPointAlongRay(eyePoint, viewDir, crv, 1.0)


class CurveCorner():
    def __init__(self, pnts):
        self.pnts = set(pnts)
        
    def __eq__(self, other):
        return self.pnts == other.pnts
        
    def __hash__(self):
        hSrc = ''
        for pnt in self.pnts:
            hSrc += str(pnt)
        return hSrc.__hash__()

def connectEnds(curves=None, tol=0.1):
    if not curves:
        curves = SEL.curves()
    
    if not curves:return
    lng = 0
    for crv in curves:
        lng += crv.length()
        
    tol *= lng
    
    corners = set()
    
    for crv in curves:
        for crvEnd in [ crv.cv[0], crv.cv[-1] ]:
            pntPos = pointPosition(crvEnd)
            corner = set()
            for crvOther in curves:
                if crvOther == crv:continue
                
                otherSt = pointPosition(crvOther.cv[0])
                otherEnd = pointPosition(crvOther.cv[-1])
                
                dSt = (pntPos - otherSt).length()
                dEnd = (pntPos - otherEnd).length()
                # print dSt, dEnd
                
                if dSt < tol or dEnd < tol:
                    corner.add(crvEnd)
                    if dSt < dEnd:
                        corner.add(crvOther.cv[0])
                    else:
                        corner.add(crvOther.cv[-1])
                
            corners.add(CurveCorner(corner))
        
        for corner in corners:
            pos = dt.Vector()
            for pnt in corner.pnts:
                pos += pointPosition(pnt)
            pos = pos / len(corner.pnts)
            
            for pnt in corner.pnts:
                move(pnt, pos, a=1, ws=1)
            
        # end = pointPosition(crv.cv[-1])
def detachWHistory(crvPoints):
    duplicate(crvPoints[0].node().getParent())
    #print crvPoints
    crvSh = crvPoints[0].node()
    inCrvTr = crvSh.getParent()
    
    try: resPar = crvSh.getParent().getParent()
    except: resPar = None
    
    #print ins, outs
    
    res = detachCurve(crvPoints, ch=1, cos=1, rpo=0)
    cuttedCurves = res[:-1]
    detachNode = res[-1]
    
    delete(cuttedCurves[0])
    if len(cuttedCurves)>2:
        delete(cuttedCurves[-1])
        
    resCrv = cuttedCurves[1].getShape()
    resCrvTr = cuttedCurves[1]
    resTrName = inCrvTr.shortName()
    resShName = crvSh.shortName()    
    
    parent(crvSh, cuttedCurves[1], r=1, s=1)
    delete(inCrvTr)
    
    crvSh.rename(resShName+'_in')
    resCrv.rename(resShName)
    resCrvTr.rename(resTrName)
    
    crvSh.intermediateObject.set(1)
    
    if resPar:
        parent(resCrv.getParent(), resPar)
        
    select(cuttedCurves[1], detachNode)
    setToolTo('ShowManips')
        
    outs = crvSh.outputs(p=1, c=1)
    for _out in outs: 
        if 'hyperLayout' in _out[1].node().name():continue
        if resCrv==_out[1].node():continue
        if detachNode==_out[1].node():continue
        
        attrName = _out[0].shortName()
        resCrv.attr(attrName).connect(_out[1], f=1)
        #print 'connecting: ', resCrv.attr(attrName)
        #print 'to: ', _out[1]
        
    
        
def dropEndsOnNeighbours():
    print 'i am empty, code me!!!!!!!!!!'
    pass
            
