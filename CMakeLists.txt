cmake_minimum_required(VERSION 3.5)

# set the project name and version
project(CurveBrush LANGUAGES CXX VERSION 1.0 DESCRIPTION "MayaBrushForSplineCurve")

# set maya path
set(MayaPath "$ENV{AutodeskDirPath}/Maya$ENV{MayaVersion}")
set(Maya_Head "${MayaPath}/include/")
set(Maya_Qt_Head "${MayaPath}/include/qt5")
set(MAYA_LIBRARY_DIR "${MayaPath}/lib")

# Set output dir
set(EXECUTABLE_OUTPUT_PATH "${PROJECT_SOURCE_DIR}/plug-ins/$ENV{MayaVersion}")
set(LIBRARY_OUTPUT_PATH "${PROJECT_SOURCE_DIR}/plug-ins/$ENV{MayaVersion}")

# specify the C++ standard
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

message(WARNING "Start build project" ...)

#自动查找头文件路径函数(没有去重)
macro(FIND_INCLUDE_DIR result curdir)  # 定义函数,2个参数:存放结果result；指定路径curdir；
    file(GLOB_RECURSE children "${curdir}/*.hpp" "${curdir}/*.h" )      # 遍历获取{curdir}中*.hpp和*.h文件列表
    message(STATUS "children= ${children}")                             #打印*.hpp和*.h的文件列表
    set(dirlist "")                                                     #定义dirlist中间变量，并初始化
    foreach(child ${children})                                          #for循环
        string(REGEX REPLACE "(.*)/.*" "\\1" LIB_NAME ${child})         #字符串替换,用/前的字符替换/*h
        if(IS_DIRECTORY ${LIB_NAME})                                    #判断是否为路径
            LIST(APPEND dirlist ${LIB_NAME})                            #将合法的路径加入dirlist变量中
        endif()                                                         #结束判断
    endforeach()                                                        #结束for循环
    set(${result} ${dirlist})                                           #dirlist结果放入result变量中
endmacro()                                                              #函数结束

#查找include目录下的所有*.hpp,*.h头文件,并路径列表保存到 INCLUDE_DIR_LIST 变量中
# FIND_INCLUDE_DIR(INCLUDE_DIR_LIST ${PROJECT_SOURCE_DIR}/source)         #调用函数，指定参数
# message(STATUS "INCLUDE_DIR_LIST = ${INCLUDE_DIR_LIST}")                #打印INCLUDE_DIR_LIST中列表信息


# 查找source目录下的所有*.cpp,*.c源文件,并将文件列表保存到 SRC_DIR_LIST 变量
file(GLOB_RECURSE SRC_DIR_LIST "${PROJECT_SOURCE_DIR}/source/*.cpp" "${PROJECT_SOURCE_DIR}/source/*.c" "${PROJECT_SOURCE_DIR}/source/*.h") 

#将SRC_DIR_LIST中文件列表以静态库的方式加入工程
add_library(${PROJECT_NAME} SHARED ${SRC_DIR_LIST})

message(STATUS "SRC_DIR_LIST = ${SRC_DIR_LIST}") #打印SRC_DIR_LIST中列表信息


#添加同文件路径 
include_directories(
        ${Maya_Head}
        ${Maya_Qt_Head}
)

# 查找Lib文件
#Find maya individual libs
foreach(MAYA_LIB_NAME OpenMaya OpenMayaAnim OpenMayaFX OpenMayaRender OpenMayaUI Foundation)
	find_library(MAYA_${MAYA_LIB_NAME}_LIBRARY NAMES ${MAYA_LIB_NAME} PATHS ${MAYA_LIBRARY_DIR} NO_DEFAULT_PATH)
	set(MAYA_LIBRARIES ${MAYA_LIBRARIES} ${MAYA_${MAYA_LIB_NAME}_LIBRARY}) #append a lib to MAYA_LIBRARIES list
endforeach()
#Find Qt individual libs
foreach(QT_LIB_NAME Qt53DAnimation Qt53DCore Qt53DExtras Qt53DInput Qt53DLogic Qt53DQuick Qt53DQuickAnimation Qt53DQuickExtras Qt53DQuickInput Qt53DQuickRender Qt53DQuickScene2D Qt53DRender Qt5AxBase Qt5AxContainer Qt5AxServer Qt5Bluetooth Qt5Concurrent Qt5Core Qt5DBus Qt5Gamepad Qt5Gui Qt5Help Qt5Location Qt5Multimedia Qt5MultimediaQuick Qt5MultimediaWidgets Qt5Network Qt5Nfc Qt5OpenGL Qt5OpenGLExtensions Qt5Positioning Qt5PositioningQuick Qt5PrintSupport Qt5Qml Qt5QmlModels Qt5QmlWorkerScript Qt5Quick Qt5QuickControls2 Qt5QuickParticles Qt5QuickShapes Qt5QuickTemplates2 Qt5QuickTest Qt5QuickWidgets Qt5RemoteObjects Qt5Scxml Qt5Sensors Qt5SerialBus Qt5SerialPort Qt5Sql Qt5Svg Qt5Test Qt5TextToSpeech Qt5ThemeSupport Qt5UiTools Qt5WebChannel Qt5WebEngine Qt5WebEngineCore Qt5WebEngineWidgets Qt5WebSockets Qt5WebView Qt5Widgets Qt5WindowsUIAutomationSupport Qt5WinExtras Qt5Xml Qt5XmlPatterns)
	find_library(MAYA_${QT_LIB_NAME}_LIBRARY NAMES ${QT_LIB_NAME} PATHS ${MAYA_LIBRARY_DIR} NO_DEFAULT_PATH)
	set(MAYA_LIBRARIES ${MAYA_LIBRARIES} ${MAYA_${QT_LIB_NAME}_LIBRARY}) #append a lib to MAYA_LIBRARIES list
endforeach()

#添加链接目录
target_link_directories(${PROJECT_NAME} PUBLIC ${MAYA_LIBRARY_DIR})
target_link_libraries(${PROJECT_NAME} ${MAYA_LIBRARIES})

set_target_properties(
    ${PROJECT_NAME}
    PROPERTIES 
        OUTPUT_NAME "curveBrush"
        SUFFIX ".mll"
)