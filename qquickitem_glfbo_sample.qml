import QtQuick 2.3
import HelloGLWorld 1.0

Item {
    width:  400
    height: 400

    Timer {
        interval: 1; running: true; repeat: true
        onTriggered: { helloGlWorld.update(); }
    }

    HelloGLWorldItem{
        id: helloGlWorld
        anchors.fill: parent
    }

    Text {
        anchors.bottom: helloGlWorld.bottom
        x: 20
        wrapMode: Text.WordWrap

        text: "This is an openGl rendering with QQuickFrameBufferObject"
    }
}