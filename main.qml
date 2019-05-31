import QtQuick 2.3
import QtQuick.Window 2.0
import GlFboViewport 1.0

Window {
    width:  600
    height: 700

    property alias fpsDisplay: fpsDisplay.text

    Timer {
        interval: 1; running: true; repeat: true
        onTriggered: { glFboViewportAdapter.update(); }
    }

    GlFboViewportAdapter{
        id: glFboViewportAdapter
        objectName: "glFboViewportAdapter"
        anchors.fill: parent
    }

    Text {
        color: "white"
        anchors.left: parent.left
        anchors.bottom : parent.bottom
        anchors.margins: 8

        Text {
            id: fpsLabel
            text: "FPS: "
            color: parent.color
        }
        Text {
            id: fpsDisplay
            text: "-"
            anchors.left: fpsLabel.right
            color: parent.color
        }
    }
}