import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: mainWindow
    width: 1200
    height: 800
    visible: true
    title: "FootFix - Hacker Interface"
    color: "#0a0a0a"

    // Matrix-like animated background
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        
        // Animated matrix rain effect
        Repeater {
            model: 20
            
            Column {
                id: matrixColumn
                x: (index * mainWindow.width / 20) + Math.random() * 50
                y: -200
                spacing: 10
                
                Repeater {
                    model: 15
                    
                    Text {
                        text: String.fromCharCode(0x30A0 + Math.random() * 96)
                        color: index < 3 ? "#00ff41" : "#003311"
                        font.family: "Courier New"
                        font.pixelSize: 12
                        opacity: index < 3 ? 1.0 : 0.3
                    }
                }
                
                PropertyAnimation on y {
                    from: -200
                    to: mainWindow.height + 200
                    duration: 3000 + Math.random() * 2000
                    running: true
                    loops: Animation.Infinite
                }
            }
        }
    }

    // Main content area with irregular layout
    Item {
        anchors.fill: parent
        anchors.margins: 40

        // Title area with glitch effect
        Item {
            id: titleArea
            width: parent.width
            height: 120
            
            Rectangle {
                width: parent.width * 0.8
                height: 80
                x: 20
                y: 20
                color: "transparent"
                border.color: "#00ff41"
                border.width: 2
                opacity: 0.8
                
                // Glitch animation
                SequentialAnimation on x {
                    loops: Animation.Infinite
                    NumberAnimation { to: 22; duration: 100 }
                    NumberAnimation { to: 18; duration: 100 }
                    NumberAnimation { to: 20; duration: 200 }
                    PauseAnimation { duration: 2000 }
                }
            }
            
            Text {
                anchors.centerIn: parent
                text: "F00TF1X - 1M4G3 PR0C3SS0R"
                font.family: "Courier New"
                font.pixelSize: 32
                font.bold: true
                color: "#00ff41"
                
                // Simple glow effect using drop shadow
                style: Text.Outline
                styleColor: "#004422"
            }
        }

        // Irregular button layout - hacker style
        Item {
            id: buttonArea
            anchors.top: titleArea.bottom
            anchors.topMargin: 60
            width: parent.width
            height: parent.height - titleArea.height - 100

            // File selection area - irregular shape
            Item {
                id: fileArea
                x: 50
                y: 50
                width: 400
                height: 200
                
                // Hexagonal button shape
                Canvas {
                    id: hexButton
                    anchors.fill: parent
                    
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.reset()
                        
                        // Draw hexagon
                        ctx.beginPath()
                        var centerX = width / 2
                        var centerY = height / 2
                        var radius = Math.min(width, height) / 3
                        
                        for (var i = 0; i < 6; i++) {
                            var angle = (Math.PI / 3) * i
                            var x = centerX + radius * Math.cos(angle)
                            var y = centerY + radius * Math.sin(angle)
                            if (i === 0) ctx.moveTo(x, y)
                            else ctx.lineTo(x, y)
                        }
                        ctx.closePath()
                        
                        // Style
                        ctx.strokeStyle = "#00ff41"
                        ctx.lineWidth = 3
                        ctx.fillStyle = "rgba(0, 255, 65, 0.1)"
                        ctx.fill()
                        ctx.stroke()
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        
                        onEntered: {
                            parent.opacity = 0.8
                            scanLine.visible = true
                        }
                        onExited: {
                            parent.opacity = 1.0
                            scanLine.visible = false
                        }
                        onClicked: {
                            hackerController.showFileDialog()
                        }
                    }
                }
                
                Text {
                    anchors.centerIn: hexButton
                    text: "SELECT\nIMAGE"
                    font.family: "Courier New"
                    font.pixelSize: 14
                    font.bold: true
                    color: "#00ff41"
                    horizontalAlignment: Text.AlignHCenter
                }
                
                // Scanning line effect
                Rectangle {
                    id: scanLine
                    width: parent.width
                    height: 2
                    color: "#00ff41"
                    visible: false
                    
                    SequentialAnimation on y {
                        loops: Animation.Infinite
                        running: scanLine.visible
                        NumberAnimation { from: 0; to: fileArea.height; duration: 1000 }
                        NumberAnimation { from: fileArea.height; to: 0; duration: 1000 }
                    }
                }
            }

            // Processing area - diamond shape
            Item {
                id: processArea
                x: 600
                y: 100
                width: 300
                height: 300
                
                Canvas {
                    id: diamondButton
                    anchors.fill: parent
                    
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.reset()
                        
                        // Draw diamond
                        ctx.beginPath()
                        ctx.moveTo(width / 2, 20)
                        ctx.lineTo(width - 20, height / 2)
                        ctx.lineTo(width / 2, height - 20)
                        ctx.lineTo(20, height / 2)
                        ctx.closePath()
                        
                        // Style
                        ctx.strokeStyle = "#ff4444"
                        ctx.lineWidth = 4
                        ctx.fillStyle = "rgba(255, 68, 68, 0.1)"
                        ctx.fill()
                        ctx.stroke()
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        
                        onEntered: {
                            pulseAnimation.running = true
                        }
                        onExited: {
                            pulseAnimation.running = false
                            parent.opacity = 1.0
                        }
                        onClicked: {
                            hackerController.processImage("editorial_web")
                        }
                    }
                    
                    // Pulse animation
                    SequentialAnimation {
                        id: pulseAnimation
                        loops: Animation.Infinite
                        
                        PropertyAnimation {
                            target: diamondButton
                            property: "opacity"
                            to: 0.5
                            duration: 500
                        }
                        PropertyAnimation {
                            target: diamondButton
                            property: "opacity"
                            to: 1.0
                            duration: 500
                        }
                    }
                }
                
                Text {
                    anchors.centerIn: diamondButton
                    text: "PROCESS\nIMAGE"
                    font.family: "Courier New"
                    font.pixelSize: 16
                    font.bold: true
                    color: "#ff4444"
                    horizontalAlignment: Text.AlignHCenter
                }
            }

            // Settings area - circuit-like design
            Item {
                id: settingsArea
                x: 100
                y: 350
                width: 250
                height: 150
                
                Rectangle {
                    width: parent.width
                    height: parent.height
                    color: "transparent"
                    border.color: "#44ff44"
                    border.width: 2
                    
                    // Circuit pattern overlay
                    Canvas {
                        anchors.fill: parent
                        anchors.margins: 10
                        
                        onPaint: {
                            var ctx = getContext("2d")
                            ctx.reset()
                            ctx.strokeStyle = "#44ff44"
                            ctx.lineWidth = 1
                            
                            // Draw circuit-like pattern
                            ctx.beginPath()
                            ctx.moveTo(0, height / 3)
                            ctx.lineTo(width / 3, height / 3)
                            ctx.lineTo(width / 3, 0)
                            ctx.moveTo(width / 3, height / 3)
                            ctx.lineTo(width, height / 3)
                            ctx.moveTo(width / 2, height / 3)
                            ctx.lineTo(width / 2, height)
                            ctx.stroke()
                            
                            // Circuit nodes
                            ctx.fillStyle = "#44ff44"
                            ctx.beginPath()
                            ctx.arc(width / 3, height / 3, 3, 0, 2 * Math.PI)
                            ctx.fill()
                            ctx.beginPath()
                            ctx.arc(width / 2, height / 3, 3, 0, 2 * Math.PI)
                            ctx.fill()
                        }
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        
                        onClicked: {
                            hackerController.showSettings()
                        }
                    }
                }
                
                Text {
                    anchors.centerIn: parent
                    text: "SETTINGS"
                    font.family: "Courier New"
                    font.pixelSize: 14
                    font.bold: true
                    color: "#44ff44"
                }
            }
        }

        // Status terminal at bottom
        Rectangle {
            id: terminal
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            height: 120
            color: "#001100"
            border.color: "#00ff41"
            border.width: 1
            
            ScrollView {
                anchors.fill: parent
                anchors.margins: 10
                
                TextArea {
                    id: terminalText
                    text: "> System initialized...\n> Waiting for image input...\n> Ready for processing..."
                    font.family: "Courier New"
                    font.pixelSize: 12
                    color: "#00ff41"
                    selectByMouse: true
                    readOnly: true
                    background: Rectangle {
                        color: "transparent"
                    }
                    
                    // Blinking cursor effect
                    Rectangle {
                        width: 8
                        height: 14
                        color: "#00ff41"
                        x: terminalText.contentWidth
                        y: terminalText.contentHeight - 14
                        
                        SequentialAnimation on opacity {
                            loops: Animation.Infinite
                            PropertyAnimation { to: 0; duration: 500 }
                            PropertyAnimation { to: 1; duration: 500 }
                        }
                    }
                }
            }
        }
    }

    // File selection - using simplified approach
    property string selectedImagePath: ""

    // Connections to Python controller
    Connections {
        target: hackerController
        
        function onImageLoaded(imagePath) {
            terminalText.append("> Image loaded: " + imagePath)
        }
        
        function onProcessingStarted() {
            terminalText.append("> Processing started...")
            // Disable process button during processing
            diamondButton.enabled = false
        }
        
        function onProcessingFinished(success, errorMessage) {
            terminalText.append(success ? "> Processing completed successfully!" : "> Processing failed: " + errorMessage)
            diamondButton.enabled = true
        }
        
        function onStatusUpdate(statusMessage) {
            terminalText.append(statusMessage)
            // Auto-scroll to bottom
            terminalText.cursorPosition = terminalText.length
        }
    }
}