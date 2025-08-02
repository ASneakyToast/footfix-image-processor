import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: multiTerminal
    
    property var terminalLogs: []
    property bool isProcessing: false
    
    function addLog(terminalId, message) {
        if (!terminalLogs[terminalId]) {
            terminalLogs[terminalId] = []
        }
        terminalLogs[terminalId].push(message)
        
        // Keep only last 50 messages per terminal
        if (terminalLogs[terminalId].length > 50) {
            terminalLogs[terminalId] = terminalLogs[terminalId].slice(-50)
        }
        
        // Trigger refresh
        terminalLogsChanged()
    }
    
    function clearTerminal(terminalId) {
        if (terminalLogs[terminalId]) {
            terminalLogs[terminalId] = []
            terminalLogsChanged()
        }
    }
    
    Rectangle {
        anchors.fill: parent
        color: "#000a00"
        border.color: "#00ff41"
        border.width: 2
        opacity: 0.95
    }
    
    // Terminal tabs header
    Rectangle {
        id: terminalHeader
        width: parent.width
        height: 30
        color: "#002200"
        border.color: "#00ff41"
        border.width: 1
        
        Row {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 10
            spacing: 2
            
            Repeater {
                model: ["MAIN", "PROC", "ERROR", "DEBUG"]
                
                Rectangle {
                    width: 60
                    height: 20
                    color: terminalTabs.currentIndex === index ? "#004400" : "transparent"
                    border.color: "#00ff41"
                    border.width: 1
                    
                    Text {
                        anchors.centerIn: parent
                        text: modelData
                        font.family: "Courier New"
                        font.pixelSize: 9
                        color: terminalTabs.currentIndex === index ? "#00ff41" : "#666666"
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            terminalTabs.currentIndex = index
                        }
                    }
                    
                    // Activity indicator
                    Rectangle {
                        width: 4
                        height: 4
                        radius: 2
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 2
                        color: {
                            if (index === 1 && isProcessing) return "#ffaa00"  // PROC
                            if (index === 2 && terminalLogs[2] && terminalLogs[2].length > 0) return "#ff4444"  // ERROR
                            return "#444444"
                        }
                        
                        SequentialAnimation on opacity {
                            running: (index === 1 && isProcessing) || (index === 2 && terminalLogs[2] && terminalLogs[2].length > 0)
                            loops: Animation.Infinite
                            PropertyAnimation { to: 0.3; duration: 800 }
                            PropertyAnimation { to: 1.0; duration: 800 }
                        }
                    }
                }
            }
        }
        
        // Terminal controls
        Row {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.rightMargin: 10
            spacing: 5
            
            Rectangle {
                width: 40
                height: 15
                color: "transparent"
                border.color: "#666666"
                border.width: 1
                
                Text {
                    anchors.centerIn: parent
                    text: "CLEAR"
                    font.family: "Courier New"
                    font.pixelSize: 8
                    color: "#666666"
                }
                
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        clearTerminal(terminalTabs.currentIndex)
                    }
                }
            }
        }
    }
    
    // Terminal content area
    SwipeView {
        id: terminalTabs
        anchors.top: terminalHeader.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        currentIndex: 0
        interactive: false
        
        // MAIN Terminal
        HackerTerminalPane {
            terminalId: 0
            terminalName: "MAIN"
            logs: terminalLogs[0] || []
            accentColor: "#00ff41"
        }
        
        // PROC Terminal
        HackerTerminalPane {
            terminalId: 1
            terminalName: "PROC"
            logs: terminalLogs[1] || []
            accentColor: "#ffaa00"
        }
        
        // ERROR Terminal
        HackerTerminalPane {
            terminalId: 2
            terminalName: "ERROR"
            logs: terminalLogs[2] || []
            accentColor: "#ff4444"
        }
        
        // DEBUG Terminal
        HackerTerminalPane {
            terminalId: 3
            terminalName: "DEBUG"
            logs: terminalLogs[3] || []
            accentColor: "#4444ff"
        }
    }
}