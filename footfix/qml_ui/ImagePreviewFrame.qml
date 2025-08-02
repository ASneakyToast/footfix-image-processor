import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: previewFrame
    width: 350
    height: 400
    
    property string imagePath: ""
    property string imageInfo: "No image loaded"
    property bool hasImage: imagePath !== ""
    property string accentColor: "#00ff41"
    
    Rectangle {
        anchors.fill: parent
        color: "#000a00"
        border.color: accentColor
        border.width: 2
        opacity: 0.9
    }
    
    // Frame title
    Text {
        id: frameTitle
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: 8
        text: "IMAGE PREVIEW"
        font.family: "Courier New"
        font.pixelSize: 12
        font.bold: true
        color: accentColor
        style: Text.Outline
        styleColor: "#003311"
    }
    
    // Retro-futuristic frame decoration
    Canvas {
        anchors.fill: parent
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.strokeStyle = accentColor + "44"
            ctx.lineWidth = 1
            
            // Corner brackets
            var bracketSize = 20
            
            // Top left bracket
            ctx.beginPath()
            ctx.moveTo(bracketSize, 5)
            ctx.lineTo(5, 5)
            ctx.lineTo(5, bracketSize)
            ctx.stroke()
            
            // Top right bracket
            ctx.beginPath()
            ctx.moveTo(width - bracketSize, 5)
            ctx.lineTo(width - 5, 5)
            ctx.lineTo(width - 5, bracketSize)
            ctx.stroke()
            
            // Bottom left bracket
            ctx.beginPath()
            ctx.moveTo(bracketSize, height - 5)
            ctx.lineTo(5, height - 5)
            ctx.lineTo(5, height - bracketSize)
            ctx.stroke()
            
            // Bottom right bracket
            ctx.beginPath()
            ctx.moveTo(width - bracketSize, height - 5)
            ctx.lineTo(width - 5, height - 5)
            ctx.lineTo(width - 5, height - bracketSize)
            ctx.stroke()
            
            // Center crosshairs
            if (!hasImage) {
                ctx.strokeStyle = accentColor + "22"
                ctx.setLineDash([3, 3])
                
                // Horizontal crosshair
                ctx.beginPath()
                ctx.moveTo(width/2 - 30, height/2)
                ctx.lineTo(width/2 + 30, height/2)
                ctx.stroke()
                
                // Vertical crosshair
                ctx.beginPath()
                ctx.moveTo(width/2, height/2 - 30)
                ctx.lineTo(width/2, height/2 + 30)
                ctx.stroke()
            }
        }
    }
    
    // Image display area
    Rectangle {
        id: imageArea
        anchors.top: frameTitle.bottom
        anchors.topMargin: 15
        anchors.bottom: infoArea.top
        anchors.bottomMargin: 10
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 15
        color: "#000a00"
        border.color: accentColor + "66"
        border.width: 1
        
        Image {
            id: previewImage
            anchors.fill: parent
            anchors.margins: 2
            source: imagePath ? "file://" + imagePath : ""
            fillMode: Image.PreserveAspectFit
            visible: hasImage
            
            // Scanning effect on image load
            Rectangle {
                id: imageScanLine
                width: parent.width
                height: 2
                color: accentColor
                opacity: 0.8
                visible: false
                
                SequentialAnimation {
                    id: scanAnimation
                    PropertyAnimation {
                        target: imageScanLine
                        property: "y"
                        from: 0
                        to: imageArea.height
                        duration: 1500
                    }
                    PropertyAnimation {
                        target: imageScanLine
                        property: "visible"
                        to: false
                        duration: 1
                    }
                }
                
                Connections {
                    target: previewImage
                    function onStatusChanged() {
                        if (previewImage.status === Image.Ready) {
                            imageScanLine.visible = true
                            scanAnimation.start()
                        }
                    }
                }
            }
        }
        
        // Placeholder when no image
        Column {
            anchors.centerIn: parent
            visible: !hasImage
            spacing: 10
            
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "NO IMAGE LOADED"
                font.family: "Courier New"
                font.pixelSize: 14
                font.bold: true
                color: accentColor + "66"
            }
            
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "AWAITING INPUT..."
                font.family: "Courier New"
                font.pixelSize: 10
                color: accentColor + "44"
                
                SequentialAnimation on opacity {
                    running: !hasImage
                    loops: Animation.Infinite
                    PropertyAnimation { to: 0.3; duration: 1000 }
                    PropertyAnimation { to: 1.0; duration: 1000 }
                }
            }
        }
    }
    
    // Info display area
    Rectangle {
        id: infoArea
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        height: 60
        color: "#000a00"
        border.color: accentColor + "44"
        border.width: 1
        
        ScrollView {
            anchors.fill: parent
            anchors.margins: 5
            
            TextArea {
                text: imageInfo
                font.family: "Courier New"
                font.pixelSize: 9
                color: accentColor + "cc"
                readOnly: true
                selectByMouse: false
                wrapMode: TextArea.Wrap
                background: Rectangle {
                    color: "transparent"
                }
            }
        }
    }
    
    // Status LED indicators
    Row {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.topMargin: 8
        anchors.rightMargin: 15
        spacing: 8
        
        // Power LED
        Rectangle {
            width: 8
            height: 8
            radius: 4
            color: "#00ff41"
            
            SequentialAnimation on opacity {
                loops: Animation.Infinite
                PropertyAnimation { to: 0.3; duration: 2000 }
                PropertyAnimation { to: 1.0; duration: 2000 }
            }
        }
        
        // Data LED
        Rectangle {
            width: 8
            height: 8
            radius: 4
            color: hasImage ? "#00ff41" : "#004411"
            
            SequentialAnimation on opacity {
                running: hasImage
                loops: Animation.Infinite
                PropertyAnimation { to: 0.5; duration: 500 }
                PropertyAnimation { to: 1.0; duration: 500 }
            }
        }
        
        // Activity LED
        Rectangle {
            width: 8
            height: 8
            radius: 4
            color: "#ff4444"
            opacity: 0.3
        }
    }
}