import QtQuick 2.15

Item {
    id: controlPanel
    
    signal settingsRequested()
    signal batchModeRequested()
    signal resetRequested()
    
    Rectangle {
        anchors.fill: parent
        color: "#000a00"
        border.color: "#44ff44"
        border.width: 2
        opacity: 0.9
    }
    
    Text {
        id: panelTitle
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: 8
        text: "CONTROL PANEL"
        font.family: "Courier New"
        font.pixelSize: 12
        font.bold: true
        color: "#44ff44"
    }
    
    // Circuit pattern background
    Canvas {
        anchors.fill: parent
        anchors.margins: 10
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.strokeStyle = "#44ff4444"
            ctx.lineWidth = 1
            
            // Draw circuit-like pattern
            ctx.beginPath()
            
            // Horizontal lines
            ctx.moveTo(0, height/4)
            ctx.lineTo(width/3, height/4)
            ctx.moveTo(2*width/3, height/4)
            ctx.lineTo(width, height/4)
            
            ctx.moveTo(0, 3*height/4)
            ctx.lineTo(width/4, 3*height/4)
            ctx.moveTo(3*width/4, 3*height/4)
            ctx.lineTo(width, 3*height/4)
            
            // Vertical connections
            ctx.moveTo(width/3, height/4)
            ctx.lineTo(width/3, height/2)
            ctx.lineTo(2*width/3, height/2)
            ctx.lineTo(2*width/3, height/4)
            
            ctx.moveTo(width/2, height/2)
            ctx.lineTo(width/2, 3*height/4)
            
            ctx.stroke()
            
            // Circuit nodes
            ctx.fillStyle = "#44ff44"
            ctx.beginPath()
            ctx.arc(width/3, height/4, 2, 0, 2 * Math.PI)
            ctx.fill()
            ctx.beginPath()
            ctx.arc(2*width/3, height/4, 2, 0, 2 * Math.PI)
            ctx.fill()
            ctx.beginPath()
            ctx.arc(width/2, height/2, 2, 0, 2 * Math.PI)
            ctx.fill()
            ctx.beginPath()
            ctx.arc(width/2, 3*height/4, 2, 0, 2 * Math.PI)
            ctx.fill()
        }
    }
    
    Column {
        anchors.centerIn: parent
        anchors.topMargin: 25
        spacing: 12
        width: parent.width - 20
        
        // Settings button
        Rectangle {
            width: parent.width
            height: 35
            color: "transparent"
            border.color: "#44ff44"
            border.width: 1
            
            Text {
                anchors.centerIn: parent
                text: "SETTINGS"
                font.family: "Courier New"
                font.pixelSize: 11
                font.bold: true
                color: "#44ff44"
            }
            
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                
                onEntered: {
                    parent.color = "#44ff4422"
                }
                onExited: {
                    parent.color = "transparent"
                }
                onClicked: {
                    settingsRequested()
                }
            }
        }
        
        // Batch mode button
        Rectangle {
            width: parent.width
            height: 35
            color: "transparent"
            border.color: "#44ff44"
            border.width: 1
            
            Text {
                anchors.centerIn: parent
                text: "BATCH MODE"
                font.family: "Courier New"
                font.pixelSize: 11
                font.bold: true
                color: "#44ff44"
            }
            
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                
                onEntered: {
                    parent.color = "#44ff4422"
                }
                onExited: {
                    parent.color = "transparent"
                }
                onClicked: {
                    batchModeRequested()
                }
            }
        }
        
        // Reset button
        Rectangle {
            width: parent.width
            height: 35
            color: "transparent"
            border.color: "#ff4444"
            border.width: 1
            
            Text {
                anchors.centerIn: parent
                text: "RESET"
                font.family: "Courier New"
                font.pixelSize: 11
                font.bold: true
                color: "#ff4444"
            }
            
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                
                onEntered: {
                    parent.color = "#ff444422"
                }
                onExited: {
                    parent.color = "transparent"
                }
                onClicked: {
                    resetRequested()
                }
            }
        }
    }
    
    // Status LEDs
    Row {
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.margins: 8
        spacing: 4
        
        Rectangle {
            width: 4
            height: 4
            color: "#00ff41"
            
            SequentialAnimation on opacity {
                loops: Animation.Infinite
                PropertyAnimation { to: 0.3; duration: 2000 }
                PropertyAnimation { to: 1.0; duration: 2000 }
            }
        }
        
        Rectangle {
            width: 4
            height: 4
            color: "#ffaa00"
            opacity: 0.6
        }
        
        Rectangle {
            width: 4
            height: 4
            color: "#ff4444"
            opacity: 0.3
        }
    }
}