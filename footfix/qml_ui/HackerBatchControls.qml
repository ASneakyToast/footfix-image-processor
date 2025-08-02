import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: batchControls
    
    property bool isProcessing: false
    property int totalItems: 0
    property int completedItems: 0
    property int failedItems: 0
    property string currentPreset: ""
    
    signal startBatchRequested()
    signal pauseBatchRequested()
    signal stopBatchRequested()
    signal addFilesRequested()
    signal addFolderRequested()
    signal presetChanged(string presetName)
    
    Rectangle {
        anchors.fill: parent
        color: "#000a00"
        border.color: "#44ff44"
        border.width: 2
        opacity: 0.95
    }
    
    Column {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 15
        
        // Title
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "BATCH CONTROL TERMINAL"
            font.family: "Courier New"
            font.pixelSize: 14
            font.bold: true
            color: "#44ff44"
            style: Text.Outline
            styleColor: "#002200"
        }
        
        // Status display
        Rectangle {
            width: parent.width
            height: 60
            color: "#001a00"
            border.color: "#44ff44"
            border.width: 1
            
            Column {
                anchors.centerIn: parent
                spacing: 5
                
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: isProcessing ? "BATCH PROCESSING ACTIVE" : "BATCH PROCESSING IDLE"
                    font.family: "Courier New"
                    font.pixelSize: 12
                    font.bold: true
                    color: isProcessing ? "#ffaa00" : "#44ff44"
                }
                
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 15
                    
                    Text {
                        text: "QUEUE: " + totalItems
                        font.family: "Courier New"
                        font.pixelSize: 10
                        color: "#44ff44"
                    }
                    
                    Text {
                        text: "DONE: " + completedItems
                        font.family: "Courier New"
                        font.pixelSize: 10
                        color: "#00ff41"
                    }
                    
                    Text {
                        text: "FAIL: " + failedItems
                        font.family: "Courier New"
                        font.pixelSize: 10
                        color: "#ff4444"
                    }
                }
            }
            
            // Processing indicator
            Rectangle {
                width: 6
                height: 6
                radius: 3
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 5
                color: isProcessing ? "#ffaa00" : "#444444"
                
                SequentialAnimation on opacity {
                    running: isProcessing
                    loops: Animation.Infinite
                    PropertyAnimation { to: 0.3; duration: 500 }
                    PropertyAnimation { to: 1.0; duration: 500 }
                }
            }
        }
        
        // File operations
        Row {
            width: parent.width
            spacing: 10
            
            Rectangle {
                width: (parent.width - 10) / 2
                height: 35
                color: "transparent"
                border.color: "#44ff44"
                border.width: 1
                
                Text {
                    anchors.centerIn: parent
                    text: "ADD FILES"
                    font.family: "Courier New"
                    font.pixelSize: 11
                    font.bold: true
                    color: "#44ff44"
                }
                
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: !isProcessing
                    
                    onEntered: {
                        parent.color = "#44ff4422"
                    }
                    onExited: {
                        parent.color = "transparent"
                    }
                    onClicked: {
                        addFilesRequested()
                    }
                }
            }
            
            Rectangle {
                width: (parent.width - 10) / 2
                height: 35
                color: "transparent"
                border.color: "#44ff44"
                border.width: 1
                
                Text {
                    anchors.centerIn: parent
                    text: "ADD FOLDER"
                    font.family: "Courier New"
                    font.pixelSize: 11
                    font.bold: true
                    color: "#44ff44"
                }
                
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: !isProcessing
                    
                    onEntered: {
                        parent.color = "#44ff4422"
                    }
                    onExited: {
                        parent.color = "transparent"
                    }
                    onClicked: {
                        addFolderRequested()
                    }
                }
            }
        }
        
        // Preset selection
        Rectangle {
            width: parent.width
            height: 50
            color: "#001100"
            border.color: "#44ff44"
            border.width: 1
            
            Column {
                anchors.centerIn: parent
                spacing: 5
                
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "PROCESSING PROTOCOL"
                    font.family: "Courier New"
                    font.pixelSize: 10
                    color: "#666666"
                }
                
                HackerComboBox {
                    id: presetCombo
                    width: parent.parent.width - 20
                    height: 25
                    
                    model: [
                        "EDITORIAL_WEB",
                        "EMAIL_COMPRESS", 
                        "INSTA_STORY",
                        "INSTA_FEED"
                    ]
                    
                    onActivated: {
                        var presetMap = {
                            "EDITORIAL_WEB": "editorial_web",
                            "EMAIL_COMPRESS": "email",
                            "INSTA_STORY": "instagram_story",
                            "INSTA_FEED": "instagram_feed_portrait"
                        }
                        presetChanged(presetMap[currentText] || "editorial_web")
                    }
                }
            }
        }
        
        // Processing controls
        Column {
            width: parent.width
            spacing: 8
            
            // Start/Stop button
            Rectangle {
                width: parent.width
                height: 45
                color: isProcessing ? "#220000" : "#001100"
                border.color: isProcessing ? "#ff4444" : "#00ff41"
                border.width: 3
                
                Text {
                    anchors.centerIn: parent
                    text: isProcessing ? "STOP PROCESSING" : "START BATCH"
                    font.family: "Courier New"
                    font.pixelSize: 14
                    font.bold: true
                    color: isProcessing ? "#ff4444" : "#00ff41"
                }
                
                MouseArea {
                    anchors.fill: parent
                    enabled: totalItems > 0
                    
                    onClicked: {
                        if (isProcessing) {
                            stopBatchRequested()
                        } else {
                            startBatchRequested()
                        }
                    }
                }
                
                // Pulse effect when processing
                Rectangle {
                    anchors.fill: parent
                    color: "transparent"
                    border.color: "#ff4444"
                    border.width: 4
                    visible: isProcessing
                    opacity: 0
                    
                    SequentialAnimation on opacity {
                        running: isProcessing
                        loops: Animation.Infinite
                        PropertyAnimation { to: 0.6; duration: 1000 }
                        PropertyAnimation { to: 0; duration: 1000 }
                    }
                }
            }
        }
        
        // Command line style progress
        Rectangle {
            width: parent.width
            height: 40
            color: "#000000"
            border.color: "#44ff44"
            border.width: 1
            visible: isProcessing
            
            Column {
                anchors.centerIn: parent
                spacing: 3
                
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "> Processing batch operations..."
                    font.family: "Courier New"
                    font.pixelSize: 10
                    color: "#44ff44"
                }
                
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 2
                    
                    Repeater {
                        model: 20
                        
                        Rectangle {
                            width: 8
                            height: 4
                            color: index < ((completedItems / Math.max(totalItems, 1)) * 20) ? "#00ff41" : "#003311"
                            
                            SequentialAnimation on opacity {
                                running: isProcessing
                                loops: Animation.Infinite
                                PropertyAnimation { 
                                    to: 0.3
                                    duration: 500 + (index * 100)
                                }
                                PropertyAnimation { 
                                    to: 1.0
                                    duration: 500 + (index * 100)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}