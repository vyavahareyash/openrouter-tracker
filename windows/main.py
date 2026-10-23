"""Main entry point for OpenRouter Tracker on Windows."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from windows.app.main_window import MainWindow
from windows.app.tray import SystemTrayManager, create_default_tray_icon
from windows.core.storage import SharedStorage
from windows.widget.desktop_widget import DesktopWidget


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenRouter Tracker (Windows)")
    parser.add_argument("--widget-only", action="store_true", help="Launch only the desktop widget and tray icon")
    parser.add_argument("--app-only", action="store_true", help="Launch only the companion application")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("OpenRouter Tracker")
    app.setOrganizationName("OpenRouter")
    app.setQuitOnLastWindowClosed(False)

    app_icon = create_default_tray_icon()
    app.setWindowIcon(app_icon)

    # Initialize components
    main_window = MainWindow()
    desktop_widget = DesktopWidget()

    # Wire up signals between components
    main_window.data_updated.connect(desktop_widget.load_data)
    main_window.theme.theme_changed.connect(desktop_widget.apply_theme)
    desktop_widget.open_companion_requested.connect(main_window.show)
    desktop_widget.open_companion_requested.connect(main_window.raise_)
    desktop_widget.open_companion_requested.connect(main_window.activateWindow)

    # Initialize system tray
    tray_manager = SystemTrayManager(main_window, desktop_widget)
    main_window.data_updated.connect(tray_manager.update_menu)
    desktop_widget.refresh_completed.connect(lambda _: tray_manager.update_menu())

    # Window visibility based on arguments
    if args.widget_only:
        desktop_widget.show()
    elif args.app_only:
        main_window.show()
    else:
        # Default: show companion app and desktop widget
        desktop_widget.show()
        # If user has no keys yet, pop open companion app so they can add their first key
        keys = SharedStorage.load_all_keys()
        if not keys or not SharedStorage.get_setting("start_minimized", False):
            main_window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
