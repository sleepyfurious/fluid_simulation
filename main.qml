import QtQuick 2.3
import GlFboViewport 1.0

Item {
    width:  512
    height: 512

    Timer {
        interval: 1; running: true; repeat: true
        onTriggered: { glFboViewportAdapter.update(); }
    }

    GlFboViewportAdapter{
        id: glFboViewportAdapter
        objectName: "glFboViewportAdapter"
        anchors.fill: parent
    }
}