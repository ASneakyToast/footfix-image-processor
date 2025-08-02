import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: hackerCombo
    
    property var model: []
    property int currentIndex: 0
    property string currentText: model[currentIndex] || ""
    property bool isOpen: false
    
    signal activated(int index)
    
    height: 25
    
    // Find the top-level window for proper dropdown positioning
    property var topLevelWindow: {
        var item = hackerCombo
        while (item.parent) {
            item = item.parent
        }
        return item
    }
    
    // Main button
    Rectangle {
        id: mainButton
        anchors.fill: parent
        color: "#001100"
        border.color: "#44ff44"
        border.width: 1
        
        Row {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 10
            anchors.rightMargin: 25
            width: parent.width - 35
            
            Text {
                text: currentText
                font.family: "Courier New"
                font.pixelSize: 10
                color: "#44ff44"
                width: parent.width
                elide: Text.ElideRight
            }
        }
        
        // Dropdown arrow
        Text {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.rightMargin: 8
            text: isOpen ? "▲" : "▼"
            font.family: "Courier New"
            font.pixelSize: 8
            color: "#44ff44"
        }
        
        MouseArea {
            anchors.fill: parent
            onClicked: {
                isOpen = !isOpen
            }
        }
    }
    
    // Global dropdown overlay
    Loader {
        id: dropdownLoader
        active: isOpen
        
        sourceComponent: Component {
            Item {
                parent: topLevelWindow
                anchors.fill: parent
                z: 10000
                
                // Click-outside-to-close overlay
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        isOpen = false
                    }
                }
                
                // Dropdown list positioned correctly
                Rectangle {
                    id: dropdown
                    x: {
                        var globalPos = hackerCombo.mapToItem(topLevelWindow, 0, 0)
                        return globalPos.x
                    }
                    y: {
                        var globalPos = hackerCombo.mapToItem(topLevelWindow, 0, 0)
                        return globalPos.y + hackerCombo.height
                    }
                    width: hackerCombo.width
                    height: Math.min(model.length * 25, 150)
                    color: "#001100"
                    border.color: "#44ff44"
                    border.width: 1
                    
                    ListView {
                        anchors.fill: parent
                        anchors.margins: 1
                        model: hackerCombo.model
                        clip: true
                        
                        delegate: Rectangle {
                            width: ListView.view.width
                            height: 25
                            color: mouseArea.containsMouse ? "#44ff4422" : "transparent"
                            
                            Text {
                                anchors.left: parent.left
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.leftMargin: 10
                                text: modelData
                                font.family: "Courier New"
                                font.pixelSize: 10
                                color: "#44ff44"
                            }
                            
                            MouseArea {
                                id: mouseArea
                                anchors.fill: parent
                                hoverEnabled: true
                                
                                onClicked: {
                                    currentIndex = index
                                    isOpen = false
                                    activated(index)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}