import json
import logging
import os
from pathlib import Path
from platform import system
from plyer import storagepath

class SettingsData:
    def __init__(self):
        if system() == "Android":
            base_dir = Path(storagepath.get_files_dir())
            self.settings_file = base_dir / "data" / "settings.json"
        else:
            self.settings_file = Path(__file__).parent.parent.parent / "data" / "settings.json"
        
        # Default settings
        self.default_settings = {
            "schedule_notifications": True,
            "expiry_days": 1,
            "theme": "light",
            "group_id": None,
            "last_update": None
        }

    def ensure_settings_directory(self):
        """Ensure the settings directory exists and is accessible"""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            # Test write access
            test_file = self.settings_file.parent / ".test_write"
            test_file.touch()
            test_file.unlink()
            return True
        except Exception as e:
            logging.error(f"Failed to create or access settings directory: {e}")
            return False

    def load_settings(self, app):
        """Load settings from file with fallback to defaults"""
        app.settings = self.default_settings.copy()
        
        if not self.ensure_settings_directory():
            logging.warning("Using default settings due to directory access issues")
            return

        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    loaded_settings = json.load(f)
                    # Update defaults with loaded values
                    app.settings.update(loaded_settings)
                logging.info("Settings loaded successfully")
            except json.JSONDecodeError as e:
                logging.error(f"Corrupted settings file: {e}")
                # Backup corrupted file
                if self.settings_file.exists():
                    backup_file = self.settings_file.with_suffix('.json.bak')
                    try:
                        self.settings_file.rename(backup_file)
                        logging.info(f"Corrupted settings backed up to {backup_file}")
                    except Exception as e:
                        logging.error(f"Failed to backup corrupted settings: {e}")
            except Exception as e:
                logging.error(f"Error loading settings: {e}")
        else:
            logging.info("Settings file does not exist, using defaults")

    def save_settings(self, app):
        """Save settings to file with proper error handling"""
        if not self.ensure_settings_directory():
            logging.error("Cannot save settings due to directory access issues")
            return False

        try:
            # Create temporary file
            temp_file = self.settings_file.with_suffix('.tmp')
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(app.settings, f, ensure_ascii=False, indent=4)

            # Verify the written data
            with open(temp_file, "r", encoding="utf-8") as f:
                json.load(f)  # This will raise an exception if the file is corrupted

            # Atomic replace
            if system() == "Windows":
                # Windows needs special handling for atomic file replacement
                if self.settings_file.exists():
                    self.settings_file.unlink()
                temp_file.rename(self.settings_file)
            else:
                # Unix-like systems support atomic rename
                temp_file.replace(self.settings_file)

            # Set proper permissions
            try:
                os.chmod(self.settings_file, 0o600)
            except Exception as e:
                logging.warning(f"Failed to set file permissions: {e}")

            logging.info("Settings saved successfully")
            return True

        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception as e:
                    logging.error(f"Failed to clean up temporary file: {e}")
            return False