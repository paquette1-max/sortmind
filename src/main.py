"""
Main entry point for SortMind - AI-powered document organization.
"""
import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import after path setup
try:
    from core.config import AppConfig
    from core.logging_config import setup_logging
    from ui.app_controller import AppController
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current path: {Path(__file__).parent}")
    sys.exit(1)


def main():
    """Main application entry point."""
    
    # Load configuration
    config_path = Path(__file__).parent.parent / "config.yaml"
    try:
        config = AppConfig.from_yaml(config_path) if config_path.exists() else AppConfig()
    except Exception as e:
        print(f"Failed to load config: {e}")
        config = AppConfig()
    
    # Setup logging
    try:
        setup_logging(config)
    except Exception as e:
        print(f"Failed to setup logging: {e}")
        # Continue with basic logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting SortMind application")
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("SortMind")
    app.setApplicationVersion("1.0.0")
    
    # Load and apply dark theme stylesheet (Vesper UI Specialist)
    try:
        qss_path = Path(__file__).parent / "ui" / "dark_theme.qss"
        if qss_path.exists():
            with open(qss_path, "r") as f:
                app.setStyleSheet(f.read())
            logger.info("Dark theme loaded from Vesper UI Specialist")
        else:
            logger.warning(f"Dark theme not found at {qss_path}")
    except Exception as e:
        logger.warning(f"Failed to load dark theme: {e}")
    
    # Create and run main window
    try:
        controller = AppController(config)
        controller.run()
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
