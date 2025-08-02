import QtQuick 2.15

Item {
    id: fileSelector
    
    property bool hasFile: false
    property string fileName: ""
    
    signal fileSelectRequested()
    
    Rectangle {
        anchors.fill: parent
        color: hasFile ? "#001a00" : "#0a0a00"
        border.color: hasFile ? "#00ff41" : "#666666"
        border.width: 2
        opacity: 0.9
        
        Behavior on color { PropertyAnimation { duration: 300 } }
        Behavior on border.color { PropertyAnimation { duration: 300 } }
    }
    
    // Hexagonal selection area
    Canvas {
        id: hexCanvas
        anchors.centerIn: parent
        width: Math.min(parent.width - 40, parent.height - 40)
        height: width
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            
            var centerX = width / 2
            var centerY = height / 2
            var radius = width / 3
            
            ctx.strokeStyle = hasFile ? "#00ff41" : "#666666"
            ctx.lineWidth = 3
            ctx.fillStyle = hasFile ? "#00ff4122" : "transparent"
            
            ctx.beginPath()
            for (var i = 0; i < 6; i++) {
                var angle = (Math.PI / 3) * i
                var x = centerX + radius * Math.cos(angle)
                var y = centerY + radius * Math.sin(angle)
                if (i === 0) ctx.moveTo(x, y)
                else ctx.lineTo(x, y)
            }
            ctx.closePath()
            ctx.fill()
            ctx.stroke()
        }
        
        Connections {
            target: fileSelector
            function onHasFileChanged() {
                hexCanvas.requestPaint()
            }
        }
    }
    
    Column {
        anchors.centerIn: hexCanvas
        spacing: 8
        
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: hasFile ? "FILE LOADED" : "SELECT FILE"
            font.family: "Courier New"
            font.pixelSize: 14
            font.bold: true
            color: hasFile ? "#00ff41" : "#666666"
        }
        
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: hasFile ? fileName : "DRAG & DROP\nOR CLICK"
            font.family: "Courier New"
            font.pixelSize: 10
            color: hasFile ? "#00cc33" : "#444444"
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            width: hexCanvas.width * 0.8
        }
    }
    
    // Scanning line effect
    Rectangle {
        id: scanLine
        width: parent.width
        height: 2
        color: "#00ff41"
        visible: mouseArea.containsMouse && !hasFile
        opacity: 0.8
        
        SequentialAnimation on y {
            running: scanLine.visible
            loops: Animation.Infinite
            PropertyAnimation { from: 0; to: fileSelector.height; duration: 1200 }
            PropertyAnimation { from: fileSelector.height; to: 0; duration: 1200 }
        }
    }
    
    // Status indicators
    Row {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 5
        
        Rectangle {
            width: 6
            height: 6
            radius: 3
            color: hasFile ? "#00ff41" : "#444444"
        }
        
        Rectangle {
            width: 6
            height: 6
            radius: 3
            color: "#666666"
            
            SequentialAnimation on opacity {
                running: hasFile
                loops: Animation.Infinite
                PropertyAnimation { to: 0.3; duration: 800 }
                PropertyAnimation { to: 1.0; duration: 800 }
            }
        }
    }
    
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        
        onClicked: {
            fileSelectRequested()
        }
    }
}