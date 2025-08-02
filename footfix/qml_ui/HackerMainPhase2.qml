import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: mainWindow
    width: 1400
    height: 900
    visible: true
    title: "FootFix - Phase 2 Hacker Interface"
    color: "#0a0a0a"

    property string currentPreset: "editorial_web"
    property string currentImagePath: ""
    property real processingProgress: 0.0
    property bool isProcessing: false

    // Matrix-like animated background (enhanced)
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        
        // Multiple layers of matrix rain
        Repeater {
            model: 30
            
            Column {
                id: matrixColumn
                x: (index * mainWindow.width / 30) + Math.random() * 30
                y: -300
                spacing: 8
                
                Repeater {
                    model: 20
                    
                    Text {
                        text: String.fromCharCode(0x30A0 + Math.random() * 96)
                        color: {
                            if (index < 2) return "#00ff41"
                            else if (index < 5) return "#00cc33"
                            else return "#003311"
                        }
                        font.family: "Courier New"
                        font.pixelSize: 10 + Math.random() * 4
                        opacity: index < 2 ? 1.0 : (index < 5 ? 0.6 : 0.2)
                    }
                }
                
                PropertyAnimation on y {
                    from: -300
                    to: mainWindow.height + 300
                    duration: 4000 + Math.random() * 3000
                    running: true
                    loops: Animation.Infinite
                }
            }
        }
    }

    // Main layout
    Item {
        anchors.fill: parent
        anchors.margins: 20

        // Enhanced title area with system status
        Item {
            id: titleArea
            width: parent.width
            height: 100
            
            Rectangle {
                width: parent.width * 0.6
                height: 70
                anchors.horizontalCenter: parent.horizontalCenter
                color: "transparent"
                border.color: "#00ff41"
                border.width: 3
                opacity: 0.9
                
                // Enhanced glitch animation
                SequentialAnimation on x {
                    loops: Animation.Infinite
                    NumberAnimation { to: parent.width * 0.2 + 3; duration: 80 }
                    NumberAnimation { to: parent.width * 0.2 - 2; duration: 120 }
                    NumberAnimation { to: parent.width * 0.2; duration: 100 }
                    PauseAnimation { duration: 3000 }
                    NumberAnimation { to: parent.width * 0.2 + 1; duration: 60 }
                    NumberAnimation { to: parent.width * 0.2; duration: 40 }
                    PauseAnimation { duration: 5000 }
                }
            }
            
            Text {
                anchors.centerIn: parent
                text: "F00TF1X - ADV4NC3D 1M4G3 PR0C3SS0R"
                font.family: "Courier New"
                font.pixelSize: 28
                font.bold: true
                color: "#00ff41"
                style: Text.Outline
                styleColor: "#004422"
            }
            
            // System status indicators
            Row {
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.topMargin: 10
                spacing: 15
                
                SystemStatusIndicator {
                    label: "CORE"
                    status: "ONLINE"
                    color: "#00ff41"
                }
                
                SystemStatusIndicator {
                    label: "PROC"
                    status: isProcessing ? "ACTIVE" : "IDLE"
                    color: isProcessing ? "#ffaa00" : "#00ff41"
                }
                
                SystemStatusIndicator {
                    label: "IMG"
                    status: currentImagePath !== "" ? "LOADED" : "EMPTY"
                    color: currentImagePath !== "" ? "#00ff41" : "#666666"
                }
            }
        }

        // Main content area with drag and drop
        Rectangle {
            id: contentArea
            anchors.top: titleArea.bottom
            anchors.topMargin: 20
            anchors.bottom: terminalArea.top
            anchors.bottomMargin: 20
            anchors.left: parent.left
            anchors.right: parent.right
            color: "transparent"
            border.color: "#00ff41"
            border.width: 1
            opacity: 0.8
            
            // Drag and drop visual feedback
            states: [
                State {
                    name: "dragActive"
                    PropertyChanges {
                        target: contentArea
                        border.color: "#ffaa00"
                        border.width: 4
                        opacity: 1.0
                    }
                }
            ]
            
            transitions: [
                Transition {
                    PropertyAnimation {
                        properties: "border.color,border.width,opacity"
                        duration: 200
                    }
                }
            ]
            
            DropArea {
                anchors.fill: parent
                
                onEntered: {
                    contentArea.state = "dragActive"
                }
                
                onExited: {
                    contentArea.state = ""
                }
                
                onDropped: {
                    contentArea.state = ""
                    if (drop.hasUrls) {
                        var url = drop.urls[0].toString()
                        var filePath = url.replace("file://", "")
                        hackerController.selectImage(filePath)
                    }
                }
            }
            
            // Three-column layout
            Row {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 20
                
                // Left column - File operations
                Column {
                    width: (parent.width - 40) / 3
                    height: parent.height
                    spacing: 20
                    
                    // File selection with enhanced feedback
                    Item {
                        width: parent.width
                        height: 180
                        
                        HackerFileSelector {
                            id: fileSelector
                            anchors.fill: parent
                            hasFile: currentImagePath !== ""
                            fileName: currentImagePath ? currentImagePath.split('/').pop() : ""
                            
                            onFileSelectRequested: {
                                hackerController.showFileDialog()
                            }
                        }
                    }
                    
                    // Image preview
                    ImagePreviewFrame {
                        id: previewFrame
                        width: parent.width
                        height: 300
                        imagePath: currentImagePath
                        imageInfo: hackerController.getImageInfo()
                    }
                }
                
                // Center column - Preset selection
                Column {
                    width: (parent.width - 40) / 3
                    height: parent.height
                    spacing: 20
                    
                    HackerPresetPanel {
                        id: presetPanel
                        width: parent.width
                        height: 420
                        selectedPreset: currentPreset
                        
                        onPresetSelected: {
                            currentPreset = presetId
                        }
                    }
                }
                
                // Right column - Processing and controls
                Column {
                    width: (parent.width - 40) / 3
                    height: parent.height
                    spacing: 20
                    
                    // Processing button with enhanced effects
                    HackerProcessButton {
                        id: processButton
                        width: parent.width
                        height: 150
                        enabled: currentImagePath !== "" && !isProcessing
                        processing: isProcessing
                        
                        onProcessRequested: {
                            hackerController.processImage(currentPreset)
                        }
                    }
                    
                    // Progress visualization
                    MatrixProgressBar {
                        id: progressBar
                        width: parent.width
                        height: 80
                        progress: processingProgress
                        status: {
                            if (isProcessing) {
                                if (processingProgress < 0.3) return "ANALYZING"
                                else if (processingProgress < 0.7) return "PROCESSING"
                                else return "FINALIZING"
                            }
                            return "READY"
                        }
                        processing: isProcessing
                        visible: isProcessing || processingProgress > 0
                    }
                    
                    // Settings and controls
                    HackerControlPanel {
                        width: parent.width
                        height: 180
                        
                        onSettingsRequested: {
                            hackerController.showSettings()
                        }
                        
                        onBatchModeRequested: {
                            // TODO: Switch to batch processing view
                        }
                        
                        onResetRequested: {
                            currentImagePath = ""
                            processingProgress = 0.0
                            isProcessing = false
                        }
                    }
                }
            }
        }

        // Enhanced terminal area
        Rectangle {
            id: terminalArea
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            height: 140
            color: "#001100"
            border.color: "#00ff41"
            border.width: 2
            
            // Terminal header
            Rectangle {
                width: parent.width
                height: 25
                color: "#002200"
                border.color: "#00ff41"
                border.width: 1
                
                Text {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 10
                    text: "SYSTEM TERMINAL - FOOTFIX v2.0"
                    font.family: "Courier New"
                    font.pixelSize: 10
                    color: "#00ff41"
                }
                
                Row {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.rightMargin: 10
                    spacing: 5
                    
                    Rectangle { width: 6; height: 6; color: "#ff4444"; radius: 3 }
                    Rectangle { width: 6; height: 6; color: "#ffaa00"; radius: 3 }
                    Rectangle { width: 6; height: 6; color: "#00ff41"; radius: 3 }
                }
            }
            
            ScrollView {
                anchors.top: parent.top
                anchors.topMargin: 25
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: 10
                
                TextArea {
                    id: terminalText
                    text: "> FootFix Advanced Processing System v2.0 initialized\n> Matrix interface loaded successfully\n> Awaiting image input and processing commands..."
                    font.family: "Courier New"
                    font.pixelSize: 11
                    color: "#00ff41"
                    selectByMouse: true
                    readOnly: true
                    background: Rectangle {
                        color: "transparent"
                    }
                    
                    // Enhanced blinking cursor
                    Rectangle {
                        width: 8
                        height: 14
                        color: "#00ff41"
                        x: terminalText.contentWidth + 2
                        y: terminalText.contentHeight - 14
                        
                        SequentialAnimation on opacity {
                            loops: Animation.Infinite
                            PropertyAnimation { to: 0; duration: 400 }
                            PropertyAnimation { to: 1; duration: 600 }
                        }
                    }
                }
            }
        }
    }

    // Connections to Python controller
    Connections {
        target: hackerController
        
        function onImageLoaded(imagePath) {
            currentImagePath = imagePath
            terminalText.append("> Image loaded: " + imagePath.split('/').pop())
            terminalText.append("> " + hackerController.getImageInfo())
        }
        
        function onProcessingStarted() {
            isProcessing = true
            processingProgress = 0.0
            terminalText.append("> Processing initiated with preset: " + currentPreset.toUpperCase())
        }
        
        function onProcessingProgress(progress) {
            processingProgress = progress
        }
        
        function onProcessingFinished(success, errorMessage) {
            isProcessing = false
            if (success) {
                processingProgress = 1.0
                terminalText.append("> Processing completed successfully!")
                terminalText.append("> " + errorMessage)
            } else {
                terminalText.append("> ERROR: Processing failed - " + errorMessage)
                processingProgress = 0.0
            }
        }
        
        function onStatusUpdate(statusMessage) {
            terminalText.append(statusMessage)
            terminalText.cursorPosition = terminalText.length
        }
    }
}