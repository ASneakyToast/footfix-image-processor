import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: matrixProgress
    width: 400
    height: 60
    
    property real progress: 0.0  // 0.0 to 1.0
    property string status: "READY"
    property bool processing: false
    property string accentColor: "#00ff41"
    
    Rectangle {
        anchors.fill: parent
        color: "#001100"
        border.color: accentColor
        border.width: 2
        opacity: 0.9
    }
    
    // Background matrix pattern
    Repeater {
        model: 25
        
        Text {
            x: (index % 5) * (matrixProgress.width / 5) + Math.random() * 20
            y: Math.floor(index / 5) * 12 + 5
            text: String.fromCharCode(0x30A0 + Math.random() * 96)
            color: "#003311"
            font.family: "Courier New"
            font.pixelSize: 8
            opacity: 0.3
            
            PropertyAnimation on opacity {
                running: processing
                loops: Animation.Infinite
                from: 0.1
                to: 0.5
                duration: 1000 + Math.random() * 2000
            }
        }
    }
    
    // Progress fill with matrix effect
    Rectangle {
        id: progressFill
        x: 2
        y: 2
        width: (parent.width - 4) * progress
        height: parent.height - 4
        color: accentColor + "33"
        
        Behavior on width {
            PropertyAnimation { duration: 300; easing.type: Easing.OutCubic }
        }
        
        // Moving scan line effect
        Rectangle {
            id: progressScanLine
            width: 3
            height: parent.height
            color: accentColor
            x: parent.width - 3
            visible: processing && progress > 0
            
            SequentialAnimation on opacity {
                running: progressScanLine.visible
                loops: Animation.Infinite
                PropertyAnimation { to: 1.0; duration: 500 }
                PropertyAnimation { to: 0.3; duration: 500 }
            }
        }
        
        // Matrix characters in progress area
        Repeater {
            model: Math.floor(progressFill.width / 20)
            
            Text {
                x: index * 20 + Math.random() * 10
                y: Math.random() * (progressFill.height - 10) + 5
                text: String.fromCharCode(0x30A0 + Math.random() * 96)
                color: accentColor
                font.family: "Courier New"
                font.pixelSize: 10
                opacity: 0.6
                
                PropertyAnimation on opacity {
                    running: processing
                    loops: Animation.Infinite
                    from: 0.2
                    to: 0.8
                    duration: 800 + Math.random() * 1200
                }
            }
        }
    }
    
    // Status text overlay
    Text {
        anchors.centerIn: parent
        text: status + (processing ? "..." : "")
        font.family: "Courier New"
        font.pixelSize: 12
        font.bold: true
        color: processing ? accentColor : "#666666"
        style: Text.Outline
        styleColor: "#000000"
        
        SequentialAnimation on opacity {
            running: processing
            loops: Animation.Infinite
            PropertyAnimation { to: 0.7; duration: 1000 }
            PropertyAnimation { to: 1.0; duration: 1000 }
        }
    }
    
    // Progress percentage
    Text {
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.rightMargin: 10
        text: Math.round(progress * 100) + "%"
        font.family: "Courier New"
        font.pixelSize: 10
        font.bold: true
        color: accentColor
        visible: processing && progress > 0
    }
    
    // Circuit-like corner decorations
    Canvas {
        anchors.fill: parent
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.strokeStyle = accentColor + "66"
            ctx.lineWidth = 1
            
            // Top left corner
            ctx.beginPath()
            ctx.moveTo(10, 0)
            ctx.lineTo(0, 0)
            ctx.lineTo(0, 10)
            ctx.stroke()
            
            // Top right corner
            ctx.beginPath()
            ctx.moveTo(width - 10, 0)
            ctx.lineTo(width, 0)
            ctx.lineTo(width, 10)
            ctx.stroke()
            
            // Bottom left corner
            ctx.beginPath()
            ctx.moveTo(10, height)
            ctx.lineTo(0, height)
            ctx.lineTo(0, height - 10)
            ctx.stroke()
            
            // Bottom right corner
            ctx.beginPath()
            ctx.moveTo(width - 10, height)
            ctx.lineTo(width, height)
            ctx.lineTo(width, height - 10)
            ctx.stroke()
        }
    }
}