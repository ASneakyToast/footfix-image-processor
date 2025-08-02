import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: presetButton
    
    property string presetId: ""
    property string presetName: ""
    property string description: ""
    property string specs: ""
    property string accentColor: "#00ff41"
    property string threatLevel: "LOW"
    property string status: "READY"
    property bool selected: false
    property string shape: "hexagon" // hexagon, diamond, rectangle, octagon
    
    signal clicked()
    
    Rectangle {
        id: background
        anchors.fill: parent
        color: selected ? accentColor + "22" : "transparent"
        border.color: selected ? accentColor : accentColor + "88"
        border.width: selected ? 3 : 2
        opacity: mouseArea.containsMouse ? 0.9 : (selected ? 1.0 : 0.7)
        
        Behavior on opacity {
            PropertyAnimation { duration: 200 }
        }
        
        Behavior on border.width {
            PropertyAnimation { duration: 200 }
        }
    }
    
    // Shape overlay based on shape property
    Canvas {
        id: shapeOverlay
        anchors.fill: parent
        visible: shape !== "rectangle"
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            
            ctx.strokeStyle = selected ? accentColor : accentColor + "88"
            ctx.lineWidth = selected ? 3 : 2
            ctx.fillStyle = selected ? accentColor + "22" : "transparent"
            
            var centerX = width / 2
            var centerY = height / 2
            var radius = Math.min(width, height) / 3
            
            ctx.beginPath()
            
            if (shape === "hexagon") {
                // Draw hexagon
                for (var i = 0; i < 6; i++) {
                    var angle = (Math.PI / 3) * i
                    var x = centerX + radius * Math.cos(angle)
                    var y = centerY + radius * Math.sin(angle)
                    if (i === 0) ctx.moveTo(x, y)
                    else ctx.lineTo(x, y)
                }
            } else if (shape === "diamond") {
                // Draw diamond
                ctx.moveTo(centerX, 20)
                ctx.lineTo(width - 20, centerY)
                ctx.lineTo(centerX, height - 20)
                ctx.lineTo(20, centerY)
            } else if (shape === "octagon") {
                // Draw octagon
                var octRadius = Math.min(width, height) / 2.5
                for (var j = 0; j < 8; j++) {
                    var octAngle = (Math.PI / 4) * j
                    var octX = centerX + octRadius * Math.cos(octAngle)
                    var octY = centerY + octRadius * Math.sin(octAngle)
                    if (j === 0) ctx.moveTo(octX, octY)
                    else ctx.lineTo(octX, octY)
                }
            }
            
            ctx.closePath()
            ctx.fill()
            ctx.stroke()
        }
        
        // Redraw when selection changes
        Connections {
            target: presetButton
            function onSelectedChanged() {
                shapeOverlay.requestPaint()
            }
        }
    }
    
    // Content layout
    Column {
        anchors.centerIn: parent
        spacing: 8
        width: parent.width * 0.8
        
        // Preset name
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: presetName
            font.family: "Courier New"
            font.pixelSize: selected ? 14 : 12
            font.bold: true
            color: accentColor
            style: Text.Outline
            styleColor: "#001100"
            
            Behavior on font.pixelSize {
                PropertyAnimation { duration: 200 }
            }
        }
        
        // Description
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: description
            font.family: "Courier New"
            font.pixelSize: 10
            color: accentColor + "cc"
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            width: parent.width
        }
        
        // Specs
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: specs
            font.family: "Courier New"
            font.pixelSize: 9
            color: accentColor + "99"
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            width: parent.width
        }
        
        // Status indicators
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 15
            
            // Threat level indicator
            Row {
                spacing: 3
                
                Text {
                    text: "THREAT:"
                    font.family: "Courier New"
                    font.pixelSize: 8
                    color: "#666666"
                }
                
                Rectangle {
                    width: 30
                    height: 8
                    color: {
                        if (threatLevel === "LOW") return "#00ff41"
                        else if (threatLevel === "MEDIUM") return "#ffaa00"
                        else return "#ff4444"
                    }
                    border.color: "#333333"
                    border.width: 1
                }
            }
            
            // Status indicator
            Row {
                spacing: 3
                
                Text {
                    text: "STATUS:"
                    font.family: "Courier New"
                    font.pixelSize: 8
                    color: "#666666"
                }
                
                Text {
                    text: status
                    font.family: "Courier New"
                    font.pixelSize: 8
                    font.bold: true
                    color: accentColor
                }
            }
        }
    }
    
    // Selection pulse effect
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        border.color: accentColor
        border.width: 4
        visible: selected
        opacity: 0
        
        SequentialAnimation on opacity {
            running: selected
            loops: Animation.Infinite
            PropertyAnimation { to: 0.8; duration: 1000 }
            PropertyAnimation { to: 0; duration: 1000 }
        }
    }
    
    // Scanning line effect on hover
    Rectangle {
        id: scanLine
        width: parent.width
        height: 2
        color: accentColor
        visible: mouseArea.containsMouse && !selected
        opacity: 0.8
        
        SequentialAnimation on y {
            running: scanLine.visible
            loops: Animation.Infinite
            PropertyAnimation { from: 0; to: presetButton.height; duration: 1500 }
            PropertyAnimation { from: presetButton.height; to: 0; duration: 1500 }
        }
    }
    
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        
        onClicked: {
            presetButton.clicked()
        }
        
        onEntered: {
            if (shape === "rectangle") {
                background.opacity = 0.9
            }
        }
        
        onExited: {
            if (shape === "rectangle") {
                background.opacity = selected ? 1.0 : 0.7
            }
        }
    }
}