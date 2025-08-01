"""
System notifications for FootFix.
Provides cross-platform notification support with macOS native notifications.
"""

import logging
import platform
from pathlib import Path

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages system notifications for the application."""
    
    def __init__(self):
        self.system = platform.system()
        self.enabled = True
        self.sound_enabled = True
        
    def show_notification(self, title: str, message: str, subtitle: str = None):
        """
        Show a system notification.
        
        Args:
            title: Notification title
            message: Main notification message
            subtitle: Optional subtitle (macOS only)
        """
        if not self.enabled:
            return
            
        if self.system == "Darwin":  # macOS
            self._show_macos_notification(title, message, subtitle)
        else:
            # For other platforms, we could use plyer or other libraries
            logger.info(f"Notification: {title} - {message}")
            
    def _show_macos_notification(self, title: str, message: str, subtitle: str = None):
        """Show a native macOS notification using osascript."""
        try:
            import subprocess
            
            # Build the AppleScript command
            script_parts = [
                'display notification',
                f'"{message}"',
                'with title',
                f'"{title}"'
            ]
            
            if subtitle:
                script_parts.extend(['subtitle', f'"{subtitle}"'])
                
            if self.sound_enabled:
                script_parts.extend(['sound name', '"default"'])
                
            script = ' '.join(script_parts)
            
            # Execute the AppleScript
            subprocess.run(
                ['osascript', '-e', script],
                check=True,
                capture_output=True
            )
            
        except Exception as e:
            logger.error(f"Failed to show macOS notification: {e}")
            
    def play_sound(self, sound_name: str = "default"):
        """
        Play a system sound.
        
        Args:
            sound_name: Name of the sound to play
        """
        if not self.sound_enabled:
            return
            
        if self.system == "Darwin":  # macOS
            self._play_macos_sound(sound_name)
            
    def _play_macos_sound(self, sound_name: str):
        """Play a system sound on macOS."""
        try:
            import subprocess
            
            if sound_name == "default":
                # Use the default notification sound
                subprocess.run(
                    ['afplay', '/System/Library/Sounds/Glass.aiff'],
                    check=True,
                    capture_output=True
                )
            elif sound_name == "success":
                # Use a positive sound
                subprocess.run(
                    ['afplay', '/System/Library/Sounds/Hero.aiff'],
                    check=True,
                    capture_output=True
                )
            elif sound_name == "error":
                # Use an error sound
                subprocess.run(
                    ['afplay', '/System/Library/Sounds/Basso.aiff'],
                    check=True,
                    capture_output=True
                )
                
        except Exception as e:
            logger.debug(f"Failed to play sound: {e}")
            
    def show_batch_completion(self, successful: int, failed: int, elapsed_time: float):
        """
        Show a notification for batch processing completion.
        
        Args:
            successful: Number of successfully processed images
            failed: Number of failed images
            elapsed_time: Total processing time in seconds
        """
        # Format elapsed time
        if elapsed_time < 60:
            time_str = f"{elapsed_time:.1f} seconds"
        else:
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_str = f"{minutes}m {seconds}s"
            
        # Build notification
        if failed == 0:
            title = "Batch Processing Complete"
            message = f"Successfully processed {successful} image{'s' if successful != 1 else ''} in {time_str}"
            sound = "success"
        else:
            title = "Batch Processing Complete with Errors"
            message = f"Processed {successful} image{'s' if successful != 1 else ''}, {failed} failed"
            sound = "error"
            
        self.show_notification(title, message, subtitle="FootFix")
        
        # Play appropriate sound
        if self.sound_enabled:
            self.play_sound(sound)
            
    def show_single_completion(self, filename: str, success: bool = True):
        """
        Show a notification for single image processing completion.
        
        Args:
            filename: Name of the processed file
            success: Whether processing was successful
        """
        if success:
            title = "Image Processed"
            message = f"{filename} has been processed successfully"
            sound = "default"
        else:
            title = "Processing Failed"
            message = f"Failed to process {filename}"
            sound = "error"
            
        self.show_notification(title, message, subtitle="FootFix")
        
        if self.sound_enabled:
            self.play_sound(sound)
            
    def set_enabled(self, enabled: bool):
        """Enable or disable notifications."""
        self.enabled = enabled
        
    def set_sound_enabled(self, enabled: bool):
        """Enable or disable notification sounds."""
        self.sound_enabled = enabled