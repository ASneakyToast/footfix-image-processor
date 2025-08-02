import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: batchStats
    
    property var queueData: []
    property bool isProcessing: false
    property int completedItems: 0
    property int failedItems: 0
    
    Rectangle {
        anchors.fill: parent
        color: "#0a0000"
        border.color: "#ff4444"
        border.width: 2
        opacity: 0.95
    }
    
    Column {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10
        
        // Stats header
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "BATCH STATISTICS"
            font.family: "Courier New"
            font.pixelSize: 12
            font.bold: true
            color: "#ff4444"
            style: Text.Outline
            styleColor: "#220000"
        }
        
        // Processing status display
        Rectangle {
            width: parent.width
            height: 80
            color: "#110000"
            border.color: "#ff4444"
            border.width: 1
            
            Column {
                anchors.centerIn: parent
                spacing: 8
                
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: isProcessing ? "PROCESSING ACTIVE" : "PROCESSING IDLE"
                    font.family: "Courier New"
                    font.pixelSize: 11
                    font.bold: true
                    color: isProcessing ? "#ffaa00" : "#ff4444"
                }
                
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 12
                    
                    Column {
                        spacing: 2
                        
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: "TOTAL"
                            font.family: "Courier New"
                            font.pixelSize: 8
                            color: "#666666"
                        }
                        
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: queueData.length.toString()
                            font.family: "Courier New"
                            font.pixelSize: 14
                            font.bold: true
                            color: "#ff4444"
                        }
                    }
                    
                    Column {
                        spacing: 2
                        
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: "DONE"
                            font.family: "Courier New"
                            font.pixelSize: 8
                            color: "#666666"
                        }
                        
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: completedItems.toString()
                            font.family: "Courier New"
                            font.pixelSize: 14
                            font.bold: true
                            color: "#00ff41"
                        }
                    }
                    
                    Column {
                        spacing: 2
                        
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: "FAIL"
                            font.family: "Courier New"
                            font.pixelSize: 8
                            color: "#666666"
                        }
                        
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: failedItems.toString()
                            font.family: "Courier New"
                            font.pixelSize: 14
                            font.bold: true
                            color: "#ff4444"
                        }
                    }
                }
            }
        }
        
        // Progress visualization
        Rectangle {
            width: parent.width
            height: 60
            color: "#110000"
            border.color: "#ff4444"
            border.width: 1
            
            Column {
                anchors.centerIn: parent
                spacing: 8
                width: parent.width - 20
                
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "PROGRESS VISUALIZATION"
                    font.family: "Courier New"
                    font.pixelSize: 9
                    color: "#666666"
                }
                
                // Progress bar
                Rectangle {
                    width: parent.width
                    height: 15
                    color: "#220000"
                    border.color: "#ff4444"
                    border.width: 1
                    
                    Rectangle {
                        width: parent.width * (queueData.length > 0 ? completedItems / queueData.length : 0)
                        height: parent.height - 2
                        x: 1
                        y: 1
                        color: "#00ff41"
                        opacity: 0.8
                        
                        Behavior on width {
                            PropertyAnimation { duration: 500 }
                        }
                    }
                    
                    Rectangle {
                        width: parent.width * (queueData.length > 0 ? failedItems / queueData.length : 0)
                        height: parent.height - 2
                        x: (parent.width * (queueData.length > 0 ? completedItems / queueData.length : 0)) + 1
                        y: 1
                        color: "#ff4444"
                        opacity: 0.8
                        
                        Behavior on width {
                            PropertyAnimation { duration: 500 }
                        }
                    }
                }
                
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: queueData.length > 0 ? Math.round(((completedItems + failedItems) / queueData.length) * 100) + "%" : "0%"
                    font.family: "Courier New"
                    font.pixelSize: 10
                    font.bold: true
                    color: "#ff4444"
                }
            }
        }
        
        // Performance metrics
        Rectangle {
            width: parent.width
            height: 100
            color: "#110000"
            border.color: "#ff4444"
            border.width: 1
            
            Column {
                anchors.centerIn: parent
                spacing: 6
                width: parent.width - 20
                
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "PERFORMANCE METRICS"
                    font.family: "Courier New"
                    font.pixelSize: 9
                    color: "#666666"
                }
                
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 15
                    
                    Column {
                        spacing: 2
                        
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: "SUCCESS RATE"
                            font.family: "Courier New"
                            font.pixelSize: 8
                            color: "#666666"
                        }
                        
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: {
                                var total = completedItems + failedItems
                                if (total === 0) return "N/A"
                                return Math.round((completedItems / total) * 100) + "%"
                            }
                            font.family: "Courier New"
                            font.pixelSize: 12
                            font.bold: true
                            color: "#00ff41"
                        }
                    }
                    
                    Column {
                        spacing: 2
                        
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: "REMAINING"
                            font.family: "Courier New"
                            font.pixelSize: 8
                            color: "#666666"
                        }
                        
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: Math.max(0, queueData.length - completedItems - failedItems).toString()
                            font.family: "Courier New"
                            font.pixelSize: 12
                            font.bold: true
                            color: "#ffaa00"
                        }
                    }
                }
                
                // CPU/Memory style indicators (simulated)
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 10
                    
                    Column {
                        spacing: 2
                        
                        Text {
                            text: "CPU"
                            font.family: "Courier New"
                            font.pixelSize: 8
                            color: "#666666"
                        }
                        
                        Rectangle {
                            width: 40
                            height: 8
                            color: "#220000"
                            border.color: "#666666"
                            border.width: 1
                            
                            Rectangle {
                                width: parent.width * (isProcessing ? 0.7 : 0.1)
                                height: parent.height - 2
                                x: 1
                                y: 1
                                color: isProcessing ? "#ffaa00" : "#444444"
                                
                                Behavior on width {
                                    PropertyAnimation { duration: 300 }
                                }
                            }
                        }
                    }
                    
                    Column {
                        spacing: 2
                        
                        Text {
                            text: "MEM"
                            font.family: "Courier New"
                            font.pixelSize: 8
                            color: "#666666"
                        }
                        
                        Rectangle {
                            width: 40
                            height: 8
                            color: "#220000"
                            border.color: "#666666"
                            border.width: 1
                            
                            Rectangle {
                                width: parent.width * (isProcessing ? 0.5 : 0.2)
                                height: parent.height - 2
                                x: 1
                                y: 1
                                color: isProcessing ? "#00ff41" : "#444444"
                                
                                Behavior on width {
                                    PropertyAnimation { duration: 300 }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        // Real-time activity monitor
        Rectangle {
            width: parent.width
            height: parent.height - 270  // Fill remaining space
            color: "#110000"
            border.color: "#ff4444"
            border.width: 1
            
            Column {
                anchors.fill: parent
                anchors.margins: 5
                spacing: 5
                
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "ACTIVITY MONITOR"
                    font.family: "Courier New"
                    font.pixelSize: 9
                    color: "#666666"
                }
                
                // Simulated activity graph
                Rectangle {
                    width: parent.width
                    height: parent.height - 20
                    color: "#000000"
                    
                    Canvas {
                        anchors.fill: parent
                        
                        onPaint: {
                            var ctx = getContext("2d")
                            ctx.reset()
                            
                            // Draw grid
                            ctx.strokeStyle = "#333333"
                            ctx.lineWidth = 1
                            
                            // Vertical lines
                            for (var x = 0; x < width; x += 20) {
                                ctx.beginPath()
                                ctx.moveTo(x, 0)
                                ctx.lineTo(x, height)
                                ctx.stroke()
                            }
                            
                            // Horizontal lines
                            for (var y = 0; y < height; y += 15) {
                                ctx.beginPath()
                                ctx.moveTo(0, y)
                                ctx.lineTo(width, y)
                                ctx.stroke()
                            }
                            
                            // Draw activity line (simulated)
                            if (isProcessing) {
                                ctx.strokeStyle = "#ff4444"
                                ctx.lineWidth = 2
                                ctx.beginPath()
                                
                                for (var i = 0; i < width; i += 5) {
                                    var activity = Math.sin(i * 0.1) * 0.3 + 0.5
                                    var y = height - (activity * height)
                                    if (i === 0) ctx.moveTo(i, y)
                                    else ctx.lineTo(i, y)
                                }
                                ctx.stroke()
                            }
                        }
                        
                        Timer {
                            interval: 1000
                            running: isProcessing
                            repeat: true
                            onTriggered: parent.requestPaint()
                        }
                    }
                }
            }
        }
    }
}