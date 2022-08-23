# Maya-CurveBrush

NURBS 曲线编辑笔刷，学习和探讨 Maya 笔刷开发的各种方式。

[博客总结](https://blog.l0v0.com/posts/cacaf61d.html)

[en_US](./README.md) | [zh_CN](./README_zh.md)

## 安装 

我使用了 Maya 的模块安装方法，借助 rj 大神的力量，可以去他的 [github仓库](https://github.com/robertjoosten/maya-module-installer) 查阅。    
只需要按照下面的步骤进行操作即可：

1. 执行 `git clone git@github.com:FXTD-ODYSSEY/Maya-CurveBrush.git` 克隆仓库到本地
2. 执行 `cd Maya-CurveBrush` 跳转到仓库目录
3. 执行 `git submodule update --init` 更新 submodule
4. 将 `CurveBrush.mel` 拖拽到 Maya 的视窗上 

mel 脚本会自动生成名为 `CurveBrush` 的工具架，每次启动都会自动生成

![image.png](https://pic.rmb.bdstatic.com/bjh/fb71bf67a116e2c0cda241d8e046349f.jpeg)

## 使用说明

工具架前两个是 [ysv曲线工具集](https://www.highend3d.com/maya/script/curve-paint-and-tweak-tool-for-maya#google_vignette) (我做了 Py2 Py3 兼容)  
om1 是 OpenMaya 1.0 基于 Qt 的绘制方案 [实现参考](https://github.com/wiremas/spore)  
om2 是 OpenMaya 2.0 基于 Viewport 2.0 的绘制方案  
cpp 是 Maya C++ API 基于 Viewport 2.0 的绘制方案  

## 使用视频

