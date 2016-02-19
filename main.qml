import QtQuick 2.3
import GlFboViewport 1.0

Item {
    width:  400
    height: 400

    Timer {
        interval: 1; running: true; repeat: true
        onTriggered: { glFboViewportAdapter.update(); }
    }

    GlFboViewportAdapter{
        id: glFboViewportAdapter
        objectName: "glFboViewportAdapter"
        anchors.fill: parent
        anchors.margins: 20
        rotation: 5
    }
}