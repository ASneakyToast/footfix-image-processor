import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: batchItem
    
    property var itemData: null
    property int itemIndex: 0
    
    signal removeRequested(int index)
    
    color: {
        if (!itemData) return "#001100"
        
        switch(itemData.status) {
            case "pending": return "#001100"
            case "processing": return "#002200"
            case "completed": return "#001a00"
            case "failed": return "#110000"
            case "skipped": return "#110011"
            default: return "#001100"
        }
    }
    
    border.color: {
        if (!itemData) return "#333333"
        
        switch(itemData.status) {
            case "pending": return "#666666"
            case "processing": return "#ffaa00"
            case "completed": return "#00ff41"
            case "failed": return "#ff4444"
            case "skipped": return "#aa44aa"
            default: return "#666666"
        }
    }
    
    border.width: itemData && itemData.status === "processing" ? 2 : 1
    
    Behavior on color { PropertyAnimation { duration: 300 } }
    Behavior on border.color { PropertyAnimation { duration: 300 } }
    
    // Processing pulse effect
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        border.color: "#ffaa00"
        border.width: 3
        visible: itemData && itemData.status === "processing"
        opacity: 0
        
        SequentialAnimation on opacity {
            running: visible
            loops: Animation.Infinite
            PropertyAnimation { to: 0.6; duration: 800 }
            PropertyAnimation { to: 0; duration: 800 }
        }
    }
    
    Row {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 10
        
        // Status indicator
        Rectangle {
            width: 8
            height: 8
            radius: 4
            anchors.verticalCenter: parent.verticalCenter
            color: parent.parent.border.color
            
            SequentialAnimation on opacity {
                running: itemData && itemData.status === "processing"
                loops: Animation.Infinite
                PropertyAnimation { to: 0.3; duration: 500 }
                PropertyAnimation { to: 1.0; duration: 500 }
            }
        }
        
        // File info
        Column {
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - 100
            spacing: 2
            
            Text {
                text: itemData ? itemData.fileName || "Unknown File" : "No Data"
                font.family: "Courier New"
                font.pixelSize: 11
                font.bold: true
                color: parent.parent.parent.border.color
                elide: Text.ElideRight
                width: parent.width
            }
            
            Row {
                spacing: 15
                
                Text {
                    text: itemData ? "SIZE: " + (itemData.fileSize || "Unknown") : ""
                    font.family: "Courier New"
                    font.pixelSize: 9
                    color: "#666666"
                }
                
                Text {
                    text: itemData ? "STATUS: " + (itemData.status || "pending").toUpperCase() : ""
                    font.family: "Courier New"
                    font.pixelSize: 9
                    color: parent.parent.parent.parent.border.color
                }
                
                Text {
                    text: itemData && itemData.processingTime ? "TIME: " + itemData.processingTime + "s" : ""
                    font.family: "Courier New"
                    font.pixelSize: 9
                    color: "#666666"
                    visible: itemData && itemData.status === "completed"
                }
            }
        }
        
        // Progress bar for active item
        Rectangle {
            width: 60
            height: 6
            anchors.verticalCenter: parent.verticalCenter
            color: "#001100"
            border.color: "#00ff41"
            border.width: 1
            visible: itemData && itemData.status === "processing"
            
            Rectangle {
                width: parent.width * (itemData && itemData.progress ? itemData.progress : 0)
                height: parent.height - 2
                x: 1
                y: 1
                color: "#00ff41"
                opacity: 0.8
                
                Behavior on width {
                    PropertyAnimation { duration: 200 }
                }
            }
        }
        
        // Remove button
        Rectangle {
            width: 20
            height: 20
            anchors.verticalCenter: parent.verticalCenter
            color: "transparent"
            border.color: "#ff4444"
            border.width: 1
            visible: itemData && (itemData.status === "pending" || itemData.status === "failed")
            
            Text {
                anchors.centerIn: parent
                text: "×"
                font.family: "Courier New"
                font.pixelSize: 14
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
                    removeRequested(itemIndex)
                }
            }
        }
    }
    
    // Error message overlay
    Rectangle {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: 15
        color: "#440000"
        border.color: "#ff4444"
        border.width: 1
        visible: itemData && itemData.status === "failed" && itemData.errorMessage
        
        Text {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 5
            text: itemData && itemData.errorMessage ? "ERROR: " + itemData.errorMessage : ""
            font.family: "Courier New"
            font.pixelSize: 8
            color: "#ff4444"
            elide: Text.ElideRight
            width: parent.width - 10
        }
    }
}