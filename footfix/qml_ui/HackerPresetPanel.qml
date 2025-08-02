import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: presetPanel
    width: 800
    height: 400
    
    property string selectedPreset: "editorial_web"
    property var presetData: {
        "editorial_web": {
            "name": "EDITORIAL_WEB",
            "description": "MAX 2560×1440 | 0.5-1MB TARGET",
            "specs": "HIGH RESOLUTION | WEB OPTIMIZED",
            "color": "#00ff41",
            "threat_level": "LOW",
            "status": "OPTIMAL"
        },
        "email": {
            "name": "EMAIL_COMPRESS",
            "description": "MAX 600PX WIDTH | <100KB",
            "specs": "COMPRESSION HEAVY | FAST TRANSFER",
            "color": "#ffaa00",
            "threat_level": "MEDIUM",
            "status": "COMPRESSED"
        },
        "instagram_story": {
            "name": "INSTA_STORY",
            "description": "1080×1920 | 9:16 RATIO",
            "specs": "EXACT DIMENSIONS | MOBILE",
            "color": "#ff4444",
            "threat_level": "HIGH",
            "status": "CROPPED"
        },
        "instagram_feed_portrait": {
            "name": "INSTA_FEED",
            "description": "1080×1350 | 4:5 RATIO",
            "specs": "PORTRAIT MODE | SOCIAL",
            "color": "#4444ff",
            "threat_level": "HIGH",
            "status": "CROPPED"
        }
    }
    
    signal presetSelected(string presetId)
    
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        border.color: "#00ff41"
        border.width: 2
        opacity: 0.8
    }
    
    Text {
        id: panelTitle
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: 10
        text: "PROCESSING PROTOCOLS"
        font.family: "Courier New"
        font.pixelSize: 16
        font.bold: true
        color: "#00ff41"
        style: Text.Outline
        styleColor: "#004422"
    }
    
    // Preset selection grid - irregular layout
    Item {
        id: presetGrid
        anchors.top: panelTitle.bottom
        anchors.topMargin: 30
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 20
        
        // Editorial Web - Top left hexagon
        HackerPresetButton {
            id: editorialButton
            x: 50
            y: 20
            width: 280
            height: 120
            presetId: "editorial_web"
            presetName: presetData.editorial_web.name
            description: presetData.editorial_web.description
            specs: presetData.editorial_web.specs
            accentColor: presetData.editorial_web.color
            threatLevel: presetData.editorial_web.threat_level
            status: presetData.editorial_web.status
            selected: selectedPreset === "editorial_web"
            shape: "hexagon"
            
            onClicked: {
                selectedPreset = "editorial_web"
                presetSelected("editorial_web")
            }
        }
        
        // Email - Top right diamond
        HackerPresetButton {
            id: emailButton
            x: 420
            y: 40
            width: 250
            height: 100
            presetId: "email"
            presetName: presetData.email.name
            description: presetData.email.description
            specs: presetData.email.specs
            accentColor: presetData.email.color
            threatLevel: presetData.email.threat_level
            status: presetData.email.status
            selected: selectedPreset === "email"
            shape: "diamond"
            
            onClicked: {
                selectedPreset = "email"
                presetSelected("email")
            }
        }
        
        // Instagram Story - Bottom left rectangle
        HackerPresetButton {
            id: storyButton
            x: 30
            y: 200
            width: 300
            height: 110
            presetId: "instagram_story"
            presetName: presetData.instagram_story.name
            description: presetData.instagram_story.description
            specs: presetData.instagram_story.specs
            accentColor: presetData.instagram_story.color
            threatLevel: presetData.instagram_story.threat_level
            status: presetData.instagram_story.status
            selected: selectedPreset === "instagram_story"
            shape: "rectangle"
            
            onClicked: {
                selectedPreset = "instagram_story"
                presetSelected("instagram_story")
            }
        }
        
        // Instagram Feed - Bottom right octagon
        HackerPresetButton {
            id: feedButton
            x: 450
            y: 220
            width: 280
            height: 100
            presetId: "instagram_feed_portrait"
            presetName: presetData.instagram_feed_portrait.name
            description: presetData.instagram_feed_portrait.description
            specs: presetData.instagram_feed_portrait.specs
            accentColor: presetData.instagram_feed_portrait.color
            threatLevel: presetData.instagram_feed_portrait.threat_level
            status: presetData.instagram_feed_portrait.status
            selected: selectedPreset === "instagram_feed_portrait"
            shape: "octagon"
            
            onClicked: {
                selectedPreset = "instagram_feed_portrait"
                presetSelected("instagram_feed_portrait")
            }
        }
        
        // Connection lines between presets (circuit-like)
        Canvas {
            anchors.fill: parent
            
            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                ctx.strokeStyle = "#004422"
                ctx.lineWidth = 1
                ctx.setLineDash([5, 5])
                
                // Connect editorial to email
                ctx.beginPath()
                ctx.moveTo(editorialButton.x + editorialButton.width, editorialButton.y + editorialButton.height/2)
                ctx.lineTo(emailButton.x, emailButton.y + emailButton.height/2)
                ctx.stroke()
                
                // Connect email to feed
                ctx.beginPath()
                ctx.moveTo(emailButton.x + emailButton.width/2, emailButton.y + emailButton.height)
                ctx.lineTo(feedButton.x + feedButton.width/2, feedButton.y)
                ctx.stroke()
                
                // Connect story to feed
                ctx.beginPath()
                ctx.moveTo(storyButton.x + storyButton.width, storyButton.y + storyButton.height/2)
                ctx.lineTo(feedButton.x, feedButton.y + feedButton.height/2)
                ctx.stroke()
                
                // Connect editorial to story
                ctx.beginPath()
                ctx.moveTo(editorialButton.x + editorialButton.width/2, editorialButton.y + editorialButton.height)
                ctx.lineTo(storyButton.x + storyButton.width/2, storyButton.y)
                ctx.stroke()
            }
        }
    }
}