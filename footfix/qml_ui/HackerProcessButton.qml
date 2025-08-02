import QtQuick 2.15

Item {
    id: processButton
    
    property bool processing: false
    
    signal processRequested()
    
    Rectangle {
        anchors.fill: parent
        color: processing ? "#002200" : (enabled ? "#001100" : "#110000")
        border.color: processing ? "#ffaa00" : (enabled ? "#ff4444" : "#664444")
        border.width: enabled ? 4 : 2
        opacity: enabled ? 1.0 : 0.5
        
        Behavior on color { PropertyAnimation { duration: 300 } }
        Behavior on border.color { PropertyAnimation { duration: 300 } }
    }
    
    // Diamond shape overlay
    Canvas {
        anchors.fill: parent
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            
            var centerX = width / 2
            var centerY = height / 2
            
            ctx.strokeStyle = processing ? "#ffaa00" : (enabled ? "#ff4444" : "#664444")
            ctx.lineWidth = enabled ? 5 : 3
            ctx.fillStyle = processing ? "#ffaa0033" : (enabled ? "#ff444433" : "transparent")
            
            ctx.beginPath()
            ctx.moveTo(centerX, 25)
            ctx.lineTo(width - 25, centerY)
            ctx.lineTo(centerX, height - 25)
            ctx.lineTo(25, centerY)
            ctx.closePath()
            ctx.fill()
            ctx.stroke()
        }
        
        Connections {
            target: processButton
            function onProcessingChanged() {
                requestPaint()
            }
            function onEnabledChanged() {
                requestPaint()
            }
        }
    }
    
    Column {
        anchors.centerIn: parent
        spacing: 8
        
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: processing ? "PROCESSING" : "PROCESS"
            font.family: "Courier New"
            font.pixelSize: 18
            font.bold: true
            color: processing ? "#ffaa00" : (enabled ? "#ff4444" : "#664444")
        }
        
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: processing ? "PLEASE WAIT..." : "EXECUTE"
            font.family: "Courier New"
            font.pixelSize: 12
            color: processing ? "#ffaa00" : (enabled ? "#ff4444" : "#664444")
        }
    }
    
    // Processing pulse effect
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        border.color: "#ffaa00"
        border.width: 6
        visible: processing
        opacity: 0
        
        SequentialAnimation on opacity {
            running: processing
            loops: Animation.Infinite
            PropertyAnimation { to: 0.8; duration: 800 }
            PropertyAnimation { to: 0; duration: 800 }
        }
    }
    
    // Energy build-up effect when hovering
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        border.color: "#ff4444"
        border.width: 3
        visible: mouseArea.containsMouse && enabled && !processing
        opacity: 0
        
        SequentialAnimation on opacity {
            running: mouseArea.containsMouse && enabled && !processing
            loops: Animation.Infinite
            PropertyAnimation { to: 0.6; duration: 500 }
            PropertyAnimation { to: 0.2; duration: 500 }
        }
    }
    
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        enabled: parent.enabled && !processing
        
        onClicked: {
            processRequested()
        }
    }
}