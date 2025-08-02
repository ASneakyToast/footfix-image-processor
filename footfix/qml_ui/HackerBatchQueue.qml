import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: batchQueue
    
    property var queueData: []
    property int activeItems: 0
    property int completedItems: 0
    property int failedItems: 0
    
    signal itemRemoved(int index)
    signal queueCleared()
    
    Rectangle {
        anchors.fill: parent
        color: "#000a00"
        border.color: "#00ff41"
        border.width: 2
        opacity: 0.95
    }
    
    // Header with queue stats
    Rectangle {
        id: queueHeader
        width: parent.width
        height: 35
        color: "#002200"
        border.color: "#00ff41"
        border.width: 1
        
        Row {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 10
            spacing: 20
            
            Text {
                text: "BATCH QUEUE"
                font.family: "Courier New"
                font.pixelSize: 12
                font.bold: true
                color: "#00ff41"
            }
            
            Text {
                text: "TOTAL: " + queueData.length
                font.family: "Courier New"
                font.pixelSize: 10
                color: "#00ff41"
            }
            
            Text {
                text: "ACTIVE: " + activeItems
                font.family: "Courier New"
                font.pixelSize: 10
                color: activeItems > 0 ? "#ffaa00" : "#666666"
            }
            
            Text {
                text: "COMPLETE: " + completedItems
                font.family: "Courier New"
                font.pixelSize: 10
                color: completedItems > 0 ? "#00ff41" : "#666666"
            }
            
            Text {
                text: "FAILED: " + failedItems
                font.family: "Courier New"
                font.pixelSize: 10
                color: failedItems > 0 ? "#ff4444" : "#666666"
            }
        }
        
        // Queue control buttons
        Row {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.rightMargin: 10
            spacing: 8
            
            Rectangle {
                width: 60
                height: 20
                color: "transparent"
                border.color: "#ff4444"
                border.width: 1
                
                Text {
                    anchors.centerIn: parent
                    text: "CLEAR"
                    font.family: "Courier New"
                    font.pixelSize: 9
                    color: "#ff4444"
                }
                
                MouseArea {
                    anchors.fill: parent
                    onClicked: queueCleared()
                }
            }
        }
    }
    
    // Scrollable queue list
    ScrollView {
        anchors.top: queueHeader.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 2
        
        ListView {
            id: queueListView
            model: queueData
            spacing: 2
            
            delegate: HackerBatchItem {
                width: queueListView.width
                height: 45
                itemData: modelData
                itemIndex: index
                
                onRemoveRequested: {
                    itemRemoved(index)
                }
            }
        }
    }
    
    // Empty queue message
    Column {
        anchors.centerIn: parent
        visible: queueData.length === 0
        spacing: 10
        
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "QUEUE EMPTY"
            font.family: "Courier New"
            font.pixelSize: 16
            font.bold: true
            color: "#666666"
        }
        
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "DRAG FILES TO ADD TO QUEUE"
            font.family: "Courier New"
            font.pixelSize: 10
            color: "#444444"
            
            SequentialAnimation on opacity {
                running: queueData.length === 0
                loops: Animation.Infinite
                PropertyAnimation { to: 0.3; duration: 1500 }
                PropertyAnimation { to: 1.0; duration: 1500 }
            }
        }
    }
    
    // Matrix-style data scrolling effect overlay
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        visible: queueData.length > 0
        
        Repeater {
            model: 5
            
            Column {
                x: index * (batchQueue.width / 5) + Math.random() * 30
                y: -50
                spacing: 15
                opacity: 0.1
                
                Repeater {
                    model: 10
                    
                    Text {
                        text: String.fromCharCode(0x30A0 + Math.random() * 96)
                        color: "#00ff41"
                        font.family: "Courier New"
                        font.pixelSize: 8
                    }
                }
                
                PropertyAnimation on y {
                    from: -50
                    to: batchQueue.height + 50
                    duration: 8000 + Math.random() * 4000
                    running: true
                    loops: Animation.Infinite
                }
            }
        }
    }
}