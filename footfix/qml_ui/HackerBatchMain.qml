import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: mainWindow
    width: 1600
    height: 1000
    visible: true
    title: "FootFix - Phase 3 Hacker Batch Interface"
    color: "#0a0a0a"

    property var batchQueue: []
    property bool isProcessing: false
    property int completedItems: 0
    property int failedItems: 0
    property string currentPreset: "editorial_web"

    // Enhanced matrix background with more layers
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        
        // Multiple matrix rain layers
        Repeater {
            model: 40
            
            Column {
                id: matrixColumn
                x: (index * mainWindow.width / 40) + Math.random() * 20
                y: -400
                spacing: 6
                
                Repeater {
                    model: 25
                    
                    Text {
                        text: String.fromCharCode(0x30A0 + Math.random() * 96)
                        color: {
                            if (index < 3) return "#00ff41"
                            else if (index < 6) return "#00cc33"
                            else if (index < 10) return "#008822"
                            else return "#003311"
                        }
                        font.family: "Courier New"
                        font.pixelSize: 8 + Math.random() * 4
                        opacity: {
                            if (index < 3) return 1.0
                            else if (index < 6) return 0.7
                            else if (index < 10) return 0.4
                            else return 0.15
                        }
                    }
                }
                
                PropertyAnimation on y {
                    from: -400
                    to: mainWindow.height + 400
                    duration: 5000 + Math.random() * 4000
                    running: true
                    loops: Animation.Infinite
                }
            }
        }
    }

    // Main interface layout
    Item {
        anchors.fill: parent
        anchors.margins: 15

        // Enhanced title with system monitoring
        Item {
            id: titleArea
            width: parent.width
            height: 80
            
            Rectangle {
                width: parent.width * 0.7
                height: 60
                anchors.horizontalCenter: parent.horizontalCenter
                color: "transparent"
                border.color: "#00ff41"
                border.width: 3
                opacity: 0.9
                
                // Enhanced glitch with different patterns
                SequentialAnimation on x {
                    loops: Animation.Infinite
                    NumberAnimation { to: parent.width * 0.15 + 4; duration: 60 }
                    NumberAnimation { to: parent.width * 0.15 - 3; duration: 90 }
                    NumberAnimation { to: parent.width * 0.15 + 2; duration: 80 }
                    NumberAnimation { to: parent.width * 0.15; duration: 70 }
                    PauseAnimation { duration: 2500 }
                    NumberAnimation { to: parent.width * 0.15 + 1; duration: 40 }
                    NumberAnimation { to: parent.width * 0.15; duration: 30 }
                    PauseAnimation { duration: 4000 }
                }
            }
            
            Text {
                anchors.centerIn: parent
                text: "F00TF1X - B4TCH PR0C3SS1NG SY5T3M"
                font.family: "Courier New"
                font.pixelSize: 24
                font.bold: true
                color: "#00ff41"
                style: Text.Outline
                styleColor: "#004422"
            }
            
            // Enhanced system status
            Row {
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.topMargin: 8
                spacing: 12
                
                SystemStatusIndicator {
                    label: "CORE"
                    status: "ONLINE"
                    color: "#00ff41"
                }
                
                SystemStatusIndicator {
                    label: "BATCH"
                    status: isProcessing ? "ACTIVE" : "IDLE"
                    color: isProcessing ? "#ffaa00" : "#00ff41"
                }
                
                SystemStatusIndicator {
                    label: "QUEUE"
                    status: batchQueue.length > 0 ? "LOADED" : "EMPTY"
                    color: batchQueue.length > 0 ? "#00ff41" : "#666666"
                }
                
                SystemStatusIndicator {
                    label: "PROC"
                    status: completedItems + "/" + batchQueue.length
                    color: completedItems > 0 ? "#00ff41" : "#666666"
                }
            }
        }

        // Main content area with enhanced drag-drop
        Rectangle {
            id: contentArea
            anchors.top: titleArea.bottom
            anchors.topMargin: 15
            anchors.bottom: multiTerminalArea.top
            anchors.bottomMargin: 15
            anchors.left: parent.left
            anchors.right: parent.right
            color: "transparent"
            border.color: "#00ff41"
            border.width: 2
            opacity: 0.9
            
            // Enhanced drag and drop states
            states: [
                State {
                    name: "dragActive"
                    PropertyChanges {
                        target: contentArea
                        border.color: "#ffaa00"
                        border.width: 5
                        opacity: 1.0
                    }
                },
                State {
                    name: "dragAccept"
                    PropertyChanges {
                        target: contentArea
                        border.color: "#00ff41"
                        border.width: 6
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
                    contentArea.state = "dragAccept"
                    if (drop.hasUrls) {
                        hackerBatchController.addFiles(drop.urls)
                    }
                    
                    // Reset state after brief feedback
                    resetStateTimer.start()
                }
                
                Timer {
                    id: resetStateTimer
                    interval: 500
                    onTriggered: contentArea.state = ""
                }
            }
            
            // Three-panel layout for batch processing
            Row {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10
                
                // Left panel - Batch queue
                Rectangle {
                    width: (parent.width - 20) * 0.4
                    height: parent.height
                    color: "transparent"
                    border.color: "#00ff41"
                    border.width: 1
                    
                    Column {
                        anchors.fill: parent
                        spacing: 0
                        
                        // Queue header
                        Rectangle {
                            width: parent.width
                            height: 30
                            color: "#002200"
                            border.color: "#00ff41"
                            border.width: 1
                            
                            Text {
                                anchors.centerIn: parent
                                text: "PROCESSING QUEUE"
                                font.family: "Courier New"
                                font.pixelSize: 12
                                font.bold: true
                                color: "#00ff41"
                            }
                        }
                        
                        // Queue content
                        HackerBatchQueue {
                            id: batchQueueDisplay
                            width: parent.width
                            height: parent.height - 30
                            queueData: batchQueue
                            activeItems: isProcessing ? 1 : 0
                            completedItems: completedItems
                            failedItems: failedItems
                            
                            onItemRemoved: {
                                hackerBatchController.removeItem(index)
                            }
                            
                            onQueueCleared: {
                                hackerBatchController.clearQueue()
                            }
                        }
                    }
                }
                
                // Center panel - Controls and status
                Rectangle {
                    width: (parent.width - 20) * 0.3
                    height: parent.height
                    color: "transparent"
                    border.color: "#44ff44"
                    border.width: 1
                    
                    HackerBatchControls {
                        id: batchControls
                        anchors.fill: parent
                        isProcessing: mainWindow.isProcessing
                        totalItems: batchQueue.length
                        completedItems: mainWindow.completedItems
                        failedItems: mainWindow.failedItems
                        currentPreset: mainWindow.currentPreset
                        
                        onStartBatchRequested: {
                            hackerBatchController.startBatch()
                        }
                        
                        onStopBatchRequested: {
                            hackerBatchController.stopBatch()
                        }
                        
                        onAddFilesRequested: {
                            hackerBatchController.showFileDialog()
                        }
                        
                        onAddFolderRequested: {
                            hackerBatchController.showFolderDialog()
                        }
                        
                        onPresetChanged: {
                            mainWindow.currentPreset = presetName
                        }
                    }
                }
                
                // Right panel - Live statistics and monitoring
                Rectangle {
                    width: (parent.width - 20) * 0.3
                    height: parent.height
                    color: "transparent"
                    border.color: "#ff4444"
                    border.width: 1
                    
                    HackerBatchStats {
                        id: batchStats
                        anchors.fill: parent
                        queueData: batchQueue
                        isProcessing: mainWindow.isProcessing
                        completedItems: mainWindow.completedItems
                        failedItems: mainWindow.failedItems
                    }
                }
            }
        }

        // Multi-terminal display area
        Rectangle {
            id: multiTerminalArea
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            height: 200
            color: "transparent"
            border.color: "#00ff41"
            border.width: 2
            
            MultiTerminalDisplay {
                id: multiTerminal
                anchors.fill: parent
                isProcessing: mainWindow.isProcessing
            }
        }
    }

    // Connections to Python batch controller
    Connections {
        target: hackerBatchController
        
        function onQueueUpdated(queueData) {
            batchQueue = queueData
            multiTerminal.addLog(0, "> Queue updated: " + queueData.length + " items")
        }
        
        function onBatchStarted() {
            isProcessing = true
            completedItems = 0
            failedItems = 0
            multiTerminal.addLog(0, "> Batch processing initiated")
            multiTerminal.addLog(1, "> Processing " + batchQueue.length + " items with " + currentPreset + " preset")
        }
        
        function onBatchStopped() {
            isProcessing = false
            multiTerminal.addLog(0, "> Batch processing terminated by user")
        }
        
        function onBatchCompleted(results) {
            isProcessing = false
            completedItems = results.completed || 0
            failedItems = results.failed || 0
            
            multiTerminal.addLog(0, "> Batch processing completed")
            multiTerminal.addLog(0, "> Results: " + completedItems + " success, " + failedItems + " failed")
            
            if (results.failed > 0) {
                multiTerminal.addLog(2, "> " + results.failed + " items failed to process")
            }
        }
        
        function onItemProgress(item, progress) {
            // Update individual item progress
            multiTerminal.addLog(1, "> Processing: " + item.fileName + " (" + Math.round(progress * 100) + "%)")
        }
        
        function onItemCompleted(item, success, message) {
            if (success) {
                completedItems++
                multiTerminal.addLog(1, "> Completed: " + item.fileName)
            } else {
                failedItems++
                multiTerminal.addLog(2, "> Failed: " + item.fileName + " - " + message)
            }
        }
        
        function onStatusUpdate(message) {
            multiTerminal.addLog(0, message)
        }
        
        function onDebugMessage(message) {
            multiTerminal.addLog(3, "> " + message)
        }
    }
}