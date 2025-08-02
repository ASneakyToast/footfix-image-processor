import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: terminalPane
    
    property int terminalId: 0
    property string terminalName: "TERMINAL"
    property var logs: []
    property string accentColor: "#00ff41"
    
    color: "#000000"
    
    ScrollView {
        anchors.fill: parent
        anchors.margins: 5
        
        ScrollBar.vertical.policy: ScrollBar.AlwaysOn
        ScrollBar.vertical.width: 8
        
        TextArea {
            id: terminalContent
            text: logs.join('\n')
            font.family: "Courier New"
            font.pixelSize: 10
            color: accentColor
            readOnly: true
            selectByMouse: true
            wrapMode: TextArea.Wrap
            
            background: Rectangle {
                color: "transparent"
            }
            
            // Auto-scroll to bottom when new content is added
            onTextChanged: {
                cursorPosition = length
            }
        }
    }
    
    // Terminal prompt at bottom
    Rectangle {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: 20
        color: "#001100"
        border.color: accentColor
        border.width: 1
        
        Row {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 5
            spacing: 5
            
            Text {
                text: terminalName + "@footfix:~$"
                font.family: "Courier New"
                font.pixelSize: 9
                color: accentColor
            }
            
            Rectangle {
                width: 6
                height: 12
                color: accentColor
                
                SequentialAnimation on opacity {
                    loops: Animation.Infinite
                    PropertyAnimation { to: 0; duration: 500 }
                    PropertyAnimation { to: 1; duration: 500 }
                }
            }
        }
        
        // Terminal connection status
        Row {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.rightMargin: 5
            spacing: 3
            
            Rectangle {
                width: 3
                height: 3
                radius: 1.5
                color: logs.length > 0 ? accentColor : "#333333"
            }
            
            Text {
                text: "CONNECTED"
                font.family: "Courier New"
                font.pixelSize: 7
                color: logs.length > 0 ? accentColor : "#333333"
            }
        }
    }
    
    // Matrix background effect
    Repeater {
        model: 8
        
        Text {
            x: Math.random() * terminalPane.width
            y: Math.random() * terminalPane.height
            text: String.fromCharCode(0x30A0 + Math.random() * 96)
            color: accentColor
            font.family: "Courier New"
            font.pixelSize: 8
            opacity: 0.05
            
            PropertyAnimation on y {
                from: -20
                to: terminalPane.height + 20
                duration: 15000 + Math.random() * 10000
                running: true
                loops: Animation.Infinite
            }
            
            PropertyAnimation on opacity {
                from: 0.01
                to: 0.1
                duration: 3000 + Math.random() * 2000
                running: true
                loops: Animation.Infinite
            }
        }
    }
}