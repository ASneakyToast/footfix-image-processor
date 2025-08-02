import QtQuick 2.15

Row {
    property string label: "SYS"
    property string status: "ONLINE"
    property string color: "#00ff41"
    
    spacing: 5
    
    Text {
        text: label + ":"
        font.family: "Courier New"
        font.pixelSize: 9
        color: "#666666"
        anchors.verticalCenter: parent.verticalCenter
    }
    
    Rectangle {
        width: 8
        height: 8
        radius: 4
        color: parent.color
        anchors.verticalCenter: parent.verticalCenter
        
        SequentialAnimation on opacity {
            loops: Animation.Infinite
            PropertyAnimation { to: 0.4; duration: 1500 }
            PropertyAnimation { to: 1.0; duration: 1500 }
        }
    }
    
    Text {
        text: status
        font.family: "Courier New"
        font.pixelSize: 9
        font.bold: true
        color: parent.color
        anchors.verticalCenter: parent.verticalCenter
    }
}