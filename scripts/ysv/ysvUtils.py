import random as r
import colorsys
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import math

from maya.mel import eval as mEval
import maya.cmds as mc
from pymel.core import *
import pymel.core.uitypes as ui
import pymel.core.nodetypes as nt
import pymel.core.datatypes as dt
import pymel.mayautils as pu

import os

class ApiTypes():
    kInvalid = 0
    kNumeric = 1
    kPlugin = 2
    kPluginGeometry = 3
    kString = 4
    kMatrix = 5
    kStringArray = 6
    kDoubleArray = 7
    kFloatArray = 8
    kIntArray = 9
    kPointArray = 10
    kVectorArray = 11
    kComponentList = 12
    kMesh = 13
    kLattice = 14
    kNurbsCurve = 15
    kNurbsSurface = 16
    kSphere = 17
    kDynArrayAttrs = 18
    kDynSweptGeometry = 19
    kSubdSurface = 20
    kNObject = 21
    kNId = 22
    kAny = 23
    kLast = 24


def getObjectMats(obj):
    sh = ls(obj, dag=1, s=1)[0]
    at = Attribute(sh.name() + '.instObjGroups')
    sg = ls(listConnections(at, s=1, d=1), et=nt.ShadingEngine)
    if sg:
        mats = ls(listConnections(sg, s=1, d=1), mat=1)
        return mats

    else:
        at = Attribute(sh.name() + ".instObjGroups.objectGroups")
        atIds = at.get(mi=1)
        if not atIds:return []
        mats = []
        for i in atIds:
            sg = ls(listConnections(at[i], s=1, d=1), et=nt.ShadingEngine)
            if sg:
                sg = sg[0]
                mat = ls(listConnections(sg, s=1, d=1), mat=1)
                if mat:
                    mats.append(mat[0])

        return mats



def mayaAppDir():
    return pu.getMayaLocation().replace('\\', '/')

def prefsDir():
    prefsPath = pu.getUserPrefsDir()
    prefsPath = prefsPath.replace('\\', '/')
    prefsPath = prefsPath.replace('/prefs', '/')
    return prefsPath

def Dir():
    for p in mEval('getenv MAYA_MODULE_PATH').split(';'):
        try:
            pathes = os.listdir(p)
        except:continue 

        for path in pathes:
            if path == 'ysvTools':
                return p + '/ysvTools/'

def scriptDirToPlugDirCopy(name):
    scriptsDir = Dir() + 'scripts/'
    plugsDir = Dir() + 'plug-ins/'

    path0 = scriptsDir + name

    if os.path.exists(path0):
        print path0
        f0 = open(path0, 'r')
        txt = f0.read()
        f0.close()

        f1 = open(plugsDir + name, 'w')
        f1.write(txt)
        f1.close

        inViewMessage(amg=txt[:100], pos='topCenter', fade=1, fts=8, fst=10)
    else:
        warning('{0} not foud in ysvTools scripts path'.format(name))

def decodeShortFlags():
    currExecuter = ui.CmdScrollFieldExecuter(mEval("string $lExe = getCurrentExecuterControl()"))
    cmd = cmdScrollFieldExecuter(currExecuter, q=1, selectedText=1)

    splitted = cmd.split()
    cmdName = splitted[0]
    flags = mEval('help ' + cmdName)
    if not flags:return
    if not 'Command Type: Command' in flags:
        inViewMessage(msg='unkonwn command', pos='topCenter', fade=1)

    flagsTypes = ['Int', 'on|off', 'Command', 'String', 'Script', 'Float', 'Length', 'noValue']
    flags = flags.split('Flags:')[1].split('Command Type: Command')[0].split('\n')

    flagsInfo = dict()
    for i, flag in enumerate(flags):
        if flag:
            spl = flag.split()
            shrt = spl[0]
            lng = spl[1][1:]
            if len(spl) == 3:
                typ = spl[2]
            elif len(spl) == 2:
                typ = 'noValue'

            flagsInfo[shrt] = (lng, typ)

    # for k, v in flagsInfo.iteritems():
    #    print k, v
    # print splitted
    splittedShrt = splitted[:]
    def checkFlag(s, short):
        for flag in flagsInfo:
            if flag == s or '-' + flagsInfo[flag][0] == s:
                if short == 1:
                    return flag
                else:
                    return flagsInfo[flag][0]
        return False

    for i, s in enumerate(splitted):
        flag = checkFlag(s, 0)
        if flag:
            splitted[i] = '\n' + flag + '='
        else:
            splitted[i] = splitted[i] + ','

    for i, s in enumerate(splittedShrt):
        flag = checkFlag(s, 1)
        if flag:
            splittedShrt[i] = ' ' + flag[1:] + '='
        else:
            splittedShrt[i] = splittedShrt[i] + ','

    newCmdLong = ''.join(splitted)
    newCmdLong = newCmdLong.replace(cmdName, cmdName + '(')
    newCmdLong = newCmdLong.replace(';', ')')

    newCmdShort = ''.join(splittedShrt)
    newCmdShort = newCmdShort.replace(cmdName, cmdName + '(')
    newCmdShort = newCmdShort.replace(';,', ')')

    # print flagsInfo
    fldTxt = cmdScrollFieldExecuter(currExecuter, q=1, t=1).split('\n')
    txt = []
    for i, line in enumerate(fldTxt):
        if cmd in line:
            txt.append(line + '\n' + newCmdShort + '\n')
        else:
            txt.append(line)
    txt = '\n'.join(txt)

    cmdScrollFieldExecuter(currExecuter, e=1, t=txt)
    print newCmdLong, '\n\n' , newCmdShort

def pythonizeMM(menuFileName):
    prefsPath = pu.getUserPrefsDir()
    prefsPath = prefsPath.replace('\\', '/')

    path = prefsPath + '/markingMenus/' + menuFileName + '.mel'

    f = open(path, 'r')
    txt = f.read()
    f.close()  

    items = txt.split('menuItem')
    for i, item in enumerate(items):
        if '-command "#python' in item:
            items[i] = item.replace('-sourceType \"mel\"', '-sourceType \"python\"')

    txt = 'menuItem'.join(items)
    f = open(path, 'w')
    f.write(txt)
    f.close()
    print menuFileName, 'pythonized'

def pmH(pmType):
    try:pmModule = getattr(pmType, '__dict__')['__module__']
    except:pmModule = getattr(pmType, '__module__')

    pmName = getattr(pmType, '__name__')
    pmClass = str(getattr(pmType, '__class__')).split(' ')
    # print str(getattr(pmType, '__class__'))
    cls = ''
    if pmClass[0] == '<class':
        cls = 'classes'
    elif pmClass[0] == '<type' and pmClass[1] == '\'function\'>':
        cls = 'functions'
    else:
        pass
    print 'module:', pmModule
    print 'class:', pmClass
    print 'module:', pmName
    print 'decoded class:', cls

        # pmClass = str(type(pmType)).split()

    if cls and pmModule and pmName:
        mayaLocation = mayaAppDir()
        docsPath = mayaLocation + '/docs/en_US'
        # docsPath = 'C:/Program Files/Autodesk/Maya2015/docs/en_US'
        docsPath += '/PyMel/generated'
        docsPath += '/' + cls
        docsPath += '/' + pmModule
        docsPath += '/' + pmModule
        docsPath += '.' + pmName
        docsPath += '.html'

        print docsPath
        showHelp(docsPath, docs=1, a=1)

    else:
        print 'class string:', cls
        print 'module:', pmModule
        print 'pmName:', pmName
        print 'pmClass attribute', pmClass


def whatIs(procName, inMaya=0):
    lay = mEval('string $lExe = $gLastFocusedCommandExecuter;')
    formL = ui.CmdScrollFieldExecuter(lay).parent()
    tabL = formL.parent()

    procInfo = mEval('whatIs ' + procName)
    print procInfo
    if procInfo.startswith('Mel procedure found in: ') or procInfo.startswith('Script found in: '):
        fPath = procInfo.split('in: ')[1]
        txt = ''
        f = open(fPath, 'r')
        for line in f:
            txt += line
        f.close()

        ex = False
        for ch in tabL.children():
            if ex:break
            for executer in ui.FormLayout(ch).children():
                # print executer.getSourceType()
                if ex:break
                if executer.getSourceType() == 'mel':
                    print '***************************'
                    if inMaya:
                        executer.clear()
                        executer.insertText(txt)
                        print 'loading file in first mel tab'
                    else:
                        print 'loading file in notepad(++):'
                        os.startfile(fPath)
                    print '***************************'
                    ex = True
    elif procInfo.startswith('Command'):
        pFlags(procName)

def pmHelp():
    currExecuter = ui.CmdScrollFieldExecuter(mEval("string $lExe = getCurrentExecuterControl()"))
    txt = cmdScrollFieldExecuter(currExecuter, q=1, selectedText=1)
    eval('python(\"pmH({0})\") '.format(txt))  

def rapidScriptOpen():
    currExecuter = ui.CmdScrollFieldExecuter(mEval("string $lExe = getCurrentExecuterControl()"))
    txt = cmdScrollFieldExecuter(currExecuter, q=1, selectedText=1)
    eval('python(\"whatIs(\'{0}\')\") '.format(txt))

def pFlags(txt=None):
    if not txt:
        currExecuter = ui.CmdScrollFieldExecuter(mEval("string $lExe = getCurrentExecuterControl()"))
        txt = cmdScrollFieldExecuter(currExecuter, q=1, selectedText=1)

    for flag in mEval('help {0}'.format(txt)).split('Flags:')[1].split('\n'):
        print flag  

def sourceIfUnknown(proc, scriptName):
    allMelProcs = mc.melInfo()
    if not proc in allMelProcs:
        mEval('source ' + scriptName)

def writeFileIds(idFileName):
    plugDir = Dir() + 'plug-ins/'
    fTxt = ''
    plugIdInfo = []

    fNames = [fName for fName in os.listdir(plugDir) if fName.endswith('.py')]
    for fName in fNames:
        if fName == idFileName: continue

        fPath = os.path.join(plugDir, fName)

        with open(fPath, 'r') as f:
            ids = []
            for line in f:
                if 'MTypeId' in line:
                    id = line.split('MTypeId')[1][1:8]
                    ids.append(id)
            if not ids:
                ids = ['______NO IDS_____']
            plugIdInfo.append((fName, ids))

    plugIdInfo.sort(key=lambda x: x[1][0])
    for info in plugIdInfo:
        fName, ids = info
        fTxt += '\n\'\'\' {0} \n\t'.format(fName)
        for id in ids:
            fTxt += id + '    '
        fTxt += '\n\'\'\''

    idsFile = plugDir + idFileName
    with open(idsFile, 'w') as f:
        f.write(fTxt)
    print (fTxt)
#------------------------------ REF PlANEs
def TexturedPlane():
    fileTexNodes = mc.ls(sl=1, dag=1, et="file")
    if not fileTexNodes:
        return
    for f in fileTexNodes:
        sx = mc.getAttr(f + ".osx")
        sy = mc.getAttr(f + ".osy")
        plane = mc.polyPlane(ch=1, w=sx, h=sy, sw=1, sh=1, cuv=2)
        mc.polyProjection(ch=1, type="Planar", ibd=1, icx=0.5, icy=0.5, ra=0, isu=1, isv=1, md="y")

        mat = mc.shadingNode('lambert', asShader=1)
        mc.select(plane, r=1)
        mc.hyperShade(assign=mat)
        mc.connectAttr(f + ".outColor", mat + ".color")

        mc.rotate(90, 0, 0, plane, os=1, r=1)

        mc.FreezeTransformations(plane[0])
        bb = mc.xform(plane[0], q=1, bb=1, ws=1)
        mc.xform(plane[0], sp=((bb[0] + bb[3]) / 2, bb[1], bb[2]), rp=(((bb[0] + bb[3]) / 2, bb[1], bb[2])))

        mc.move(0, 0, 0, plane, rpr=1)

def FilterCornerVerts():
    sel = ls(sl=1, fl=1)
    hl = ls(hl=1)
    sl = ls(sl=1, o=1)
    hl.append(sl)
    cornerVerts = []
    verts = ls(polyListComponentConversion(sel, tv=1), fl=1)
    FilterHardEdges()
    hardEdges = ls(sl=1, fl=1)
    for v in verts:
        edges = ls(polyListComponentConversion(v, te=1), fl=1)
        if len([e for e in edges if e in hardEdges]) == 3:
            cornerVerts.append(v)        
    select(cl=1)
    hilite(hl)
    select(cornerVerts)

    mc.ConvertSelectionToVertices()

#===============================================================================
# def getRedundEdge(v, angle=3):
#     e1, e2, e3 = v.connectedEdges()
#     vec1 = e1.getPoint(0) - e1.getPoint(1)
#     vec2 = e2.getPoint(0) - e2.getPoint(1)
#     vec3 = e3.getPoint(0) - e3.getPoint(1)
#     
#     if abs(math.degrees(vec1.angle(vec2))) < angle:
#         return e3.index()
#     elif abs(math.degrees(vec1.angle(vec3))) < angle:
#         return e2.index()
#     elif abs(math.degrees(vec2.angle(vec3))) < angle:
#         return e1.index()
#     else:
#         return False
#     
# def cleanupBoolEdgeLoops(verts=None, angle=3):
#     mc.ConvertSelectionToVertices()
#     verts = SEL.verts()
#     
#     edgeIds = []
#     
#     
#     for vComp in verts:
#         for v in vComp:
#             num = v.numConnectedEdges()
#             if not num == 3: continue
#         
#             # edges = ls(v.connectedEdges(), fl=1)
#             edgeId = getRedundEdge(v, angle)
#             if edgeId:
#                 edgeIds.append(edgeId)
#     
#     if edgeIds:    
#         select(verts[0].node().e[edgeIds])
#     else:
#         select(cl=1)
#===============================================================================


def FilterWrongCornerVerts():
    FilterCornerVerts()
    sel = ls(sl=1, fl=1)
    hl = ls(hl=1)
    sl = ls(sl=1, o=1)
    hl.append(sl)

    wrongCornerVerts = []
    FilterCreasedEdges(3)
    creasedEdges = ls(sl=1, fl=1)
    if not creasedEdges:return

    for v in sel:
        edges = ls(polyListComponentConversion(v, te=1), fl=1)
        vertEdgesCount = len(edges)
        creasedEdgesCount = len([e for e in edges if e in creasedEdges])

        if creasedEdgesCount == 3 and vertEdgesCount > creasedEdgesCount:
            wrongCornerVerts.append(v)

    select(cl=1)
    hilite(hl)
    select(wrongCornerVerts)
    mc.ConvertSelectionToVertices()

def filterCurveCorners():
    crvs = ls(sl=1, dag=1, et=nt.NurbsCurve)
    cornerParams = []
    for crv in crvs:
        params = []
        for cv in crv.cv:
            cvPos = cv.getPosition('world')
            closPnt = crv.closestPoint(cvPos, tolerance=0.01, space='world')
            param = crv.getParamAtPoint(closPnt, 'world')
            params.append(param)

        for i, param in enumerate(params[1:-1]):

            thisPnt = pointPosition(crv.u[params[i]])
            nextPnt = pointPosition(crv.u[params[i + 1]])
            prevPnt = pointPosition(crv.u[params[i - 1]])

            prevTng = thisPnt - prevPnt
            nextTng = thisPnt - nextPnt

            angle = math.degrees(prevTng.angle(nextTng))

            if angle > 25 and angle < 90:  # or angleNext>20:
                cornerParams.append(crv.u[params[i]])
            elif angle > 90 and angle < 180 - 25:
                cornerParams.append(crv.u[params[i]])

    select(cornerParams)
    hilite(crv)
    selectMode(co=1)
    selectType(cpp=1)
    return cornerParams


def FilterHardEdges():
    objs = ls(sl=1, o=1)
    hl = ls(hl=1)

    edges = polyListComponentConversion(ls(sl=1), te=1)

    selectMode(co=1)
    selectType(pe=1)
    # select(cl=1)

    select(edges)

    hilite(hl + objs)

    polySelectConstraint(m=2, t=0x8000, sm=1)
    edges = ls(sl=1)
    polySelectConstraint(sm=0)
    polySelectConstraint(m=0)
    polySelectConstraint(dis=1)
    select(edges)

def FilterCreasedEdges(value):
    hl = ls(hl=1)
    sl = ls(sl=1, o=1)
    hl.append(sl)
    creasedEdges = []
    edges = polyListComponentConversion(te=1)
    edges = ls(edges, fl=1)
    for e in edges:
        if polyCrease(e, q=1, v=1)[0] >= value:
            creasedEdges.append(e)    
    hilite(hl)
    select(creasedEdges)  

def TriangulateObjects(objs):
    allSel = ls(sl=1)

    if len(objs) > 1:
        for obj in objs:
            select(obj)
            polySelectConstraint(m=3, t=8, sz=3)
            if ls(sl=1):
                polyTriangulate(ch=0)

    elif ls(sl=1):
        polySelectConstraint(m=3, t=8, sz=3)
        polyTriangulate(ch=0)        

    polySelectConstraint(m=0)
    polySelectConstraint(dis=1)
    select(allSel)

def rndPhong(object=None):
    sel0 = ls(sl=1)
    hil = ls(hl=1)
    if object:
        select(object)

    mEval('createAndAssignShader phong \"\"')
    hyperShade(smn=1)
    mat = ls(sl=1, mat=1)[0]

    hue = r.random()
    saturation = r.random() * 0.2 + 0.2
    col = colorsys.hsv_to_rgb(hue, saturation, .8)

    mat.color.set(col)

    select(sel0)
    hilite(hil)

def whitePhong(object=None):
    sel0 = ls(sl=1)
    hil = ls(hl=1)
    if object:
        select(object)

    mEval('createAndAssignShader phong \"\"')
    hyperShade(smn=1)
    mat = ls(sl=1, mat=1)[0]

    mat.color.set(1, 1, 1)

    select(sel0)
    hilite(hil)

def gozPrepare():    
    objs = ls(sl=1, o=1)
    mEval('polyCleanupArgList 3 { \"0\",\"2\",\"1\",\"0\",\"1\",\"0\",\"0\",\"0\",\"0\",\"1e-005\",\"0\",\"1e-005\",\"0\",\"1e-006\",\"0\",\"-1\",\"0\" };')
    TriangulateObjects(objs)

    for obj in objs:
        select(obj)
        FilterHardEdges()
        if ls(sl=1):
            polyCrease(v=10)

    select(objs)

def gozExport():
    currentUnit(l='meter')
    mEval ('source GoZBrushFromMaya.mel;')
    currentUnit(l='centimeter')

def generateZImportScript(fPath):
    objs = ls(sl=1, o=1)
    # fPath = 'D:/Export/ToZ/'
    cmd = ''
    # cmd += '[IPress,Tool:Make PolyMesh3D] \n'
    cmd += '[IButton,TempImport,"Press to play ", \n'


    for obj in objs:
        name = obj.shortName().replace('|', '')
        name = (fPath + name).replace('/', '\\')
        zName = name + '.ma'

        cmd += '[FileNameSetNext,\"' + zName + '\"][IPress,Tool:Import] \n'
        cmd += '[IPress,Tool:SubTool:Duplicate] \n'
        cmd += '[IPress,Tool:SubTool:SelectDown] \n'

    cmd += ']'

    filePath = 'C:\\Program Files (x86)\\Pixologic\\ZBrush 4R6\\ZScripts\\' + '___multiImportScript.txt'
    f = open(filePath, 'w')
    f.write(cmd)
    f.close

def zExportMulti(fPath):
    for f in os.listdir(fPath):
        os.remove(fPath + f)

    objs = ls(sl=1, o=1)
    for obj in objs:
        select(obj)
        name = obj.shortName().replace('|', '')
        mc.file(fPath + name, f=1, options="v=0;p=17;f=0", typ="mayaAscii", pr=1, es=1)
    select(objs)

    generateZImportScript(fPath)

def sendSelectionToModo():
    try:		
        import ModoSock
        lx = ModoSock.ModoSock('127.0.0.1', 8820)
    except: pass

    try:
        meshes = ls(sl=1, dag=1, ni=1, et=nt.Mesh)
        for mesh in meshes:
            select(mesh, r=1)
            fPath = "D:\\Export\\{0}.obj".format(mesh.getParent().longName())
            fPath = fPath.replace('|', '_')
            print fPath
            mc.file(fPath, es=1, f=1, op="groups=1;ptgroups=1;materials=1;smoothing=1;normals=1", typ="OBJexport", pr=1)  


            lx.eval('scene.open \"{0}\" import'.format(fPath))
        lx.close()

    except:
        print 'something wrong'
        raise

def setComponentAttr(attr, compLabel, ids, fromOtherCompAttr = False):
    if not fromOtherCompAttr:
        compsStr = str.join(', ', ['\'{0}[{1}]\''.format(compLabel, id) for id in ids])
    else:
        compsStr = str.join(', ', ['\'{0}\''.format(id) for id in ids])

    cmd = 'Attribute(\'{0}\').set({1}, {2}, type=\'componentList\') '.format(attr.__str__(),  len(ids), compsStr)
    print cmd
    eval(cmd)

#---------------------------------------------------------------------------------------------------------
#-------------------------------                   Geometry------------------------------------------------------------
def edgeToPointDist(edge, point):
    v0 = edge.getPoint(0, space='world')
    v1 = edge.getPoint(1, space='world')

    edgeVec = v0 - v1
    pnt2EdgeVec = v0 - point

    dist = (edgeVec.cross(pnt2EdgeVec).length()) / edge.length()

    return dist
#-----------------------------------------------------------------------
#---------------------------------                Hotkeys----------------------------
def IncrementAndSave():

    fullPath = mc.file(q=1, l=1)[0]

    fPath, name = os.path.split(fullPath)

    name = name.replace('.', '_', name.count('.') - 1)

    shName = name.split('.')[0]

    if shName == 'untitled':
        mc.SaveSceneAs()
    else:
        newName = None
        try:ext = name.split('.')[1]
        except:ext = None

        lastDigits = ''
        for ch in reversed(shName):
            if not ch.isdigit():break
            lastDigits += ch

        if lastDigits:
            lD = ''
            for ch in reversed(lastDigits):
                lD += ch

            nextIndex = int(lD) + 1
            nextIndex = str(nextIndex).zfill(4)
            newShName = shName[0:-len(lD)] + nextIndex + "." + ext

        else:
            newShName = shName + "_0001." + ext

        if newShName:
            # newName = fPath + newShName
            newName = os.path.join(fPath, newShName)
            try:
                mc.file(rename=newName)
                mc.file(save=1)
                inViewMessage(amg='<h1>{0}</h1>'.format(newShName), pos='topCenter', fade=True)
            except:
                inViewMessage(amg='<h1>failed to save {0}</h1>'.format(newShName), pos='topCenter', fade=True)


def projectPoints():
    sel = ls(sl=1)
    hil = ls(hl=1)

    liveMesh = ls(lv=1)
    if liveMesh:liveMesh = liveMesh[0]

    selMeshes = ls(sl=1, dag=1, et=nt.Mesh)

    if not sel:
        select(hil)
    selNext = ls(sl=1)
    # print selNext

    cvs = [s for s in sel if type(s) == NurbsCurveCV]
    curves = ls(selNext, dag=1, et=nt.NurbsCurve) 

    if  curves or cvs:
        print 'projecting curves'
        if liveMesh:
            projectsCVsToMesh(curves + cvs, liveMesh)
        elif selMeshes:
            projectsCVsToMesh(curves + cvs, selMeshes[0])
        else:
            projectsCVsToMesh(curves + cvs)

    else:
        if liveMesh:
            mc.ConvertSelectionToVertices()
            verts = [v for v in ls(sl=1) if type(v) == MeshVertex]
            select(verts)
            mEval('dR_shrinkWrap')

    select(sel)
    hilite(hil)        

def projectsCVsToMesh(sel, mesh=None):
    curves = ls(sel, dag=1, et=nt.NurbsCurve)
    cvs = [s for s in sel if type(s) == NurbsCurveCV]

    cvCurves = set()
    for cv in ls(cvs, fl=1):
        cvCurves.add(cv.node()) 
    allCurves = curves + list(cvCurves)

    if not mesh:
        for c in allCurves:c.updateCurve()
        return

    for crv in curves:
        cvs += [crv.cv]

    for cv in ls(cvs, fl=1):
        newPos, id = mesh.getClosestPoint(cv.getPosition(space='world'), space='world')
        cv.setPosition(newPos, space='world')

    for c in allCurves:c.updateCurve()

#---------------------------------------- ----------------------------------------
#------------------------                    Sketches Pipe ----------------------------------------
def reloadFileTextures():
    for obj in ls(sl=1, o=1):
        mats = getObjectMats(obj)
        for mat in mats:
            fileNodes = listConnections(mat, type=nt.File)
            for fileNode in fileNodes:
                fileNode.ftn.set(fileNode.ftn.get())

def openTexture():
    objs = ls(sl=1, o=1)
    if objs:
        obj = objs[0]
    else:return

    mats = getObjectMats(obj)
    if mats:mat = mats[0]
    else:return

    if type(mat) == nt.SurfaceShader:
        matColorAt = 'outColor'
    else:
        matColorAt = 'color'

    texNode = listConnections(mat.attr(matColorAt), s=1, d=0)
    if texNode:texNode = texNode[0]
    else:return

    filePath = texNode.ftn.get()

    os.startfile(filePath)

def renderOpenInSkchBook(toQImpDir=False):
    # mEval(' system(\"TASKKILL /F /IM SketchBookPro.exe \") ')

    PyNode('defaultRenderGlobals').imageFormat.set(3)  # tiff format

    PyNode('defaultResolution').width.set(1024)
    PyNode('defaultResolution').height.set(1024)
    PyNode('defaultResolution').deviceAspectRatio.set(1)     

    mEval('renderIntoNewWindow render')

    fName = mc.file(q=1, l=1)[0].split('/')[-1]
    projPath = workspace(q=1, rd=1)
    if not fName == 'untitled':
        fName = fName.split(".mb")[0]


    tmpRenderFilePath = projPath + 'images/tmp/' + fName + '.tif'

    if toQImpDir:
        filePath = Dir() + 'QImport/textures/quickImportRefPlane.tif'
    else:
        srcImDir = workspace(q=1, rd=1) + 'sourceimages/Doodles/'
        try:os.mkdir(srcImDir)
        except:pass

        files = [f for f in os.listdir(srcImDir) if 'doodle_' in f]
        i = 1
        fDupPath = 'doodle_1.tif'
        while(fDupPath in files):
            i += 1
            fDupPath = 'doodle_{0}.tif'.format(i)

        fDupPath = srcImDir + fDupPath

        filePath = fDupPath


    f0 = file(tmpRenderFilePath, 'r')
    txt = f0.read()
    f0.close()

    f1 = file(filePath, 'w')
    f1.write(txt)
    f1.close()

    if not toQImpDir:
        pln = polyPlane(ax=(0, 0, 1), w=100, h=100, sw=1, sh=1)[0]
        move(pln, 0, 50, 0, r=1, ws=1)

        newMat = shadingNode(nt.SurfaceShader, asShader=1)
        newTex = shadingNode(nt.File, asTexture=1)
        newTex.outColor.connect(newMat.outColor)

        newTex.ftn.set(filePath)

        select(pln)
        hyperShade(assign=newMat)

        if getPanel(typeOf=getPanel(wf=1)) == "modelPanel":
            modelEditor(getPanel(wf=1), e=1, da='smoothShaded', dtx=1, dl='default')

    deleteUI('renderViewWindow')
    os.startfile(filePath)

def duplicateConnectedTextures():
    srcImDir = workspace(q=1, rd=1) + 'sourceimages/Doodles/'
    try:os.mkdir(srcImDir)
    except:pass

    files = [f for f in os.listdir(srcImDir) if 'doodle_' in f]
    objs = ls(sl=1, o=1)

    for obj in objs:
        mat = getObjectMats(obj)
        if mat:mat = mat[0]
        if not mat:continue

        if type(mat) == nt.SurfaceShader:
            matColorAt = 'outColor'
        else:
            matColorAt = 'color'

        fileNode = listConnections(mat.attr(matColorAt), type=nt.File, s=1, d=0)
        if fileNode:fileNode = fileNode[0]
        if not fileNode:continue

        fPath = fileNode.ftn.get()
        print fPath

        fSrc = open(fPath, 'r')
        txt = fSrc.read()
        fSrc.close()

        i = 1
        fDupPath = 'doodle_1.tif'
        while(fDupPath in files):
            i += 1
            fDupPath = 'doodle_{0}.tif'.format(i)

        fDupPath = srcImDir + fDupPath

        fDup = open(fDupPath, 'w')
        fDup.write(txt)
        fDup.close()

        newMat = shadingNode(nt.SurfaceShader, asShader=1)
        newTex = shadingNode(nt.File, asTexture=1)
        newTex.outColor.connect(newMat.outColor)

        newTex.ftn.set(fDupPath)

        select(obj)
        hyperShade(assign=newMat)

        print files
        print fDupPath
    select(objs)

def clearDoodleTextures():
    srcImDir = workspace(q=1, rd=1) + 'sourceimages/'
    try:os.mkdir(srcImDir)
    except:pass

    srcImDir += 'Doodles/'
    try:os.mkdir(srcImDir)
    except:pass

    files = [f for f in os.listdir(srcImDir) if 'doodle_' in f]
    for f in files:
        try:os.remove(srcImDir + f)
        except:print 'skippedFile: ', f

def doodleTexPopup():
    srcImDir = workspace(q=1, rd=1) + 'sourceimages/'
    try:os.mkdir(srcImDir)
    except:pass

    srcImDir += 'Doodles/'
    try:os.mkdir(srcImDir)
    except:pass

    files = [f for f in os.listdir(srcImDir) if 'doodle_' in f]

    for f in files:
        menuItem(p='tempMM', l=f, c=Callback(os.startfile, srcImDir + f))

#-----------------------------------------------------------------------
#--------------------------           QuickImports----------------------------
def qImportDir():
    ysvToolsDir = Dir()
    return ysvToolsDir + 'QImport/'

def importColorMasks():
    path = qImportDir() + 'scenes/ColorMasksMaterials.mb'
    mc.file(path, i=1, typ="mayaBinary", iv=1, ra=1, options="v=1;", pr=1, lrd="all")

def rapidRefPlaneImport():
    path = qImportDir() + 'scenes/refPlane.mb'
    mc.file(path, i=1, type="mayaBinary")    

class SEL():
    @staticmethod        
    def curves(sel=None):
        if sel: return ls(filterExpand(sel, sm=9))
        else: return ls(filterExpand(sm=9))
    @staticmethod        
    def surfaces(sel=None):
        if sel: return ls(filterExpand(sel, sm=10))
        else: return ls(filterExpand(sm=10))
    @staticmethod        
    def cosCurves(sel=None):
        if sel: return ls(filterExpand(sel, sm=11))
        else: return ls(filterExpand(sm=11))
    @staticmethod        
    def polygons(sel=None):
        if sel: return ls(filterExpand(sel, sm=12))
        else: return ls(filterExpand(sm=12))
    @staticmethod        
    def cvs(sel=None):
        if sel: return ls(filterExpand(sel, sm=28))
        else: return ls(filterExpand(sm=28))
    @staticmethod        
    def ep(sel=None):
        if sel: return ls(filterExpand(sel, sm=30))
        else: return ls(filterExpand(sm=30))
    @staticmethod        
    def verts(sel=None):
        if sel: return ls(filterExpand(sel, sm=31))
        else: return ls(filterExpand(sm=31))
    @staticmethod        
    def edges(sel=None):
        if sel: return ls(filterExpand(sel, sm=32))
        else: return ls(filterExpand(sm=32))
    @staticmethod        
    def faces(sel=None):
        if sel: return ls(filterExpand(sel, sm=34))
        else: return ls(filterExpand(sm=34))
    @staticmethod        
    def uvs(sel=None):
        if sel: return ls(filterExpand(sel, sm=35))
        else: return ls(filterExpand(sm=35))
    @staticmethod        
    def subPnts(sel=None):
        if sel: return ls(filterExpand(sel, sm=36))
        else: return ls(filterExpand(sm=36))
    @staticmethod        
    def subEdges(sel=None):
        if sel: return ls(filterExpand(sel, sm=37))
        else: return ls(filterExpand(sm=37))
    @staticmethod        
    def subFaces(sel=None):
        if sel: return ls(filterExpand(sel, sm=38))
        else: return ls(filterExpand(sm=38))
    @staticmethod        
    def curveParams(sel=None):
        if sel: return ls(filterExpand(sel, sm=39))
        else: return ls(filterExpand(sm=39))
    @staticmethod        
    def curveKnots(sel=None):
        if sel: return ls(filterExpand(sel, sm=40))
        else: return ls(filterExpand(sm=40))
    @staticmethod        
    def surfParams(sel=None):
        if sel: return ls(filterExpand(sel, sm=41))
        else: return ls(filterExpand(sm=41))
    @staticmethod        
    def surfKnots(sel=None):
        if sel: return ls(filterExpand(sel, sm=42))
        else: return ls(filterExpand(sm=42))
    @staticmethod        
    def surfRange(sel=None):
        if sel: return ls(filterExpand(sel, sm=43))
        else: return ls(filterExpand(sm=43))
    @staticmethod        
    def surfTrimEdges(sel=None):
        if sel: return ls(filterExpand(sel, sm=44))
        else: return ls(filterExpand(sm=44))
    @staticmethod        
    def surfIsoparms(sel=None):
        if sel: return ls(filterExpand(sel, sm=45))
        else: return ls(filterExpand(sm=45))
    @staticmethod        
    def latticePoints(sel=None):
        if sel: return ls(filterExpand(sel, sm=46))
        else: return ls(filterExpand(sm=46))
    @staticmethod        
    def particles(sel=None):
        if sel: return ls(filterExpand(sel, sm=47))
        else: return ls(filterExpand(sm=47))
    @staticmethod        
    def scalePivots(sel=None):
        if sel: return ls(filterExpand(sel, sm=49))
        else: return ls(filterExpand(sm=49))
    @staticmethod        
    def rotatePivots(sel=None):
        if sel: return ls(filterExpand(sel, sm=50))
        else: return ls(filterExpand(sm=50))
    @staticmethod        
    def SelectHandles(sel=None):
        if sel: return ls(filterExpand(sel, sm=51))
        else: return ls(filterExpand(sm=51))
    @staticmethod        
    def SubdivisionSurface(sel=None):
        if sel: return ls(filterExpand(sel, sm=68))
        else: return ls(filterExpand(sm=68))
    @staticmethod        
    def PolygonVertexFace(sel=None):
        if sel: return ls(filterExpand(sel, sm=70))
        else: return ls(filterExpand(sm=70))
    @staticmethod        
    def surfacePatches(sel=None):
        if sel: return ls(filterExpand(sel, sm=72))
        else: return ls(filterExpand(sm=72))
    @staticmethod        
    def SubdivisionMeshUVs(sel=None):
        if sel: return ls(filterExpand(sel, sm=73))
        else: return ls(filterExpand(sm=73))

def pivot2CompCenter():
    bb = dt.BoundingBox()
    polyVerts = ls(polyListComponentConversion(tv=1), fl=1)
    pntsOther = ls(filterExpand(sm=(28, 30, 36, 37, 38, 39, 40, 41, 42, 46, 47, 73)))

    pnts = []
    if polyVerts:pnts += polyVerts
    if pntsOther:pnts += pntsOther
    # print len(pnts)
    objects = set()
    for pnt in pnts:
        pos = pointPosition(pnt, w=1)
        bb.expand(pos)
        objects.add(pnt.node().getParent())

    pos = bb.center()
    xform(pnts[-1].node().getParent(), sp=pos, rp=pos, a=1, ws=1)
    select(objects)

def inViewMes(icons, text):
    path = 'C:\\Users\\yursiv\\Documents\\maya\\2015-x64\\modules\\ysvTools\\icons\\AdjustPivot.bmp'

    mes = '''----------------
    <body align="center">
    1 
    <img src="{0}">
    2 
    <img src="{0}">
    3 
    <img src="{0}">
    </body>

    '''.format(path)
    print mes


    inViewMessage(amg=mes, fade=1, pos='midCenter') 
