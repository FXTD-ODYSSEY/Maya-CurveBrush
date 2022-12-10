# coding=utf-8

import maya.cmds as cmds

def runScript(*args, **kw):
    for pluginName in ("curveBrush", "CurveBrush", "curvebrush"):
        if cmds.pluginInfo(pluginName, q=1, l=1):
            break
    else:
        cmds.loadPlugin("curveBrush.mll")
        # import curve_brush_porperties as curve_brush_porperties
        # curve_brush_porperties.setup_mel()

    # check if selected a curve content
    hasCurveSelected = False
    curSel = cmds.ls(sl=1)
    if curSel :
        for sel in curSel :
            if cmds.listRelatives(sel, c=True, type='nurbsCurve'):
                hasCurveSelected=True
                break
        
    if hasCurveSelected:
        ctx = cmds.curveBrushContext()
        cmds.setToolTo(ctx)
    else :
        cmds.inViewMessage(smg=u"至少选择一条曲线", pos="midCenter", bkc=0x11111111, alpha=0.5, fade=True,fst=500)

if __name__ == "__main__":
    runScript()