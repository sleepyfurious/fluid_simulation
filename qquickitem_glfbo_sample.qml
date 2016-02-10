import QtQuick 2.3
import GlFboViewport 1.0

Item {
    width:  400
    height: 400

    Timer {
        interval: 1; running: true; repeat: true
        onTriggered: { helloOurViewportAdapter.update(); }
    }

    GlFboViewportAdapter{
        id: helloOurViewportAdapter
        objectName: "helloOurViewportAdapter"
        anchors.fill: parent
    }

    Text {
        anchors.bottom: helloOurViewportAdapter.bottom
        x: 20
        wrapMode: Text.WordWrap

        text: "This is an openGl rendering with QQuickFrameBufferObject"
    }
}