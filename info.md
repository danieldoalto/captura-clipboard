# Project Analysis: Captura Clipboard

## 1. Core Purpose

The "Captura Clipboard" application is a Windows utility developed in Python. Its primary function is to automatically capture images from the system clipboard. It provides users with tools to manage these captured images (view thumbnails, reorder, select/deselect) and subsequently save them either individually or as a batch. An option to save selected images into a single ZIP archive is also available.

## 2. Key Technologies and Libraries

* **Python:** The fundamental programming language used for the entire application.
* **CustomTkinter:** A Python UI library based on Tkinter, used for creating the graphical user interface (GUI). It allows for modern-looking and themeable interfaces.
* **Pillow (PIL Fork):** A powerful image processing library used for:
  * Grabbing images from the clipboard (`ImageGrab.grabclipboard()`)
  * General image manipulation tasks.
  * Creating thumbnails.
  * Saving images in various formats (e.g., PNG, JPEG).
* **PyYAML:** A library for parsing YAML files, used here to read and process the `config.yml` configuration file.
* **Standard Python Libraries:**
  * `threading`: For running the clipboard monitoring process in a background thread to keep the UI responsive.
  * `os`: For interacting with the operating system (e.g., file paths, directory creation).
  * `uuid`: For generating unique identifiers for captured images.
  * `json`: For reading and writing user-specific settings (e.g., `user_settings.json`).
  * `zipfile`: For creating ZIP archives of images.
  * `subprocess`: Used as a fallback mechanism for clearing the clipboard on Windows.
  * `glob`: For finding files matching a pattern (used in `clean_temp_files`).
  * `time`: Used in the clipboard monitor loop.
  * `io`: Used in conjunction with image data.
  * `platform`: To detect the operating system (used in `clear_clipboard`).

## 3. Application Entry Point and Main Flow

* **`main.py`:**
  * This script acts as the initial entry point for the application.
  * Its primary responsibilities are to ensure the application is running from the correct working directory and to instantiate and launch the main application class (`ClipboardImageApp`).
* **`app.py` (contains `ClipboardImageApp` class):**
  * This is the central class and represents the main application window and logic.
  * **Initialization:**
    * Loads application-wide configurations from `config.yml`.
    * Sets up the logging system.
    * Initializes core components: `ThemeManager`, `AppThemeAdapter`, `ImageManager`, and `ClipboardMonitor`.
    * Clears any pre-existing temporary image files and the system clipboard on startup.
  * **UI Management:**
    * Constructs and manages all UI elements using CustomTkinter (buttons, labels, input fields, image preview area, status bar).
  * **Coordination:**
    * Acts as the orchestrator between user interactions, the `ClipboardMonitor` (for receiving new images), the `ImageManager` (for storing and processing images), and various dialog windows.
  * **Event Handling:**
    * Manages user actions (e.g., button clicks) and application lifecycle events (e.g., window close).

## 4. Core Modules/Components and Their Responsibilities

### 4.1. `clipboard_monitor.py` (`ClipboardMonitor` class)

* **Purpose:** Monitors the system clipboard for new image content.
* **Threading:** Operates in a separate background thread to prevent the main UI from freezing.
* **Detection:**
  * Periodically checks the clipboard using `PIL.ImageGrab.grabclipboard()`.
  * Calculates a hash of the image data (`_image_hash`) to compare against the previously detected image, ensuring only genuinely new images are processed.
* **Callback:** When a new, unique image is detected, it invokes a callback function (specifically, `on_image_captured` in the `ClipboardImageApp` class).
* **Clipboard Clearing:** Includes a `clear_clipboard` method that attempts to empty the clipboard, primarily using `win32clipboard` (if `pywin32` is available) or falling back to a `subprocess` call to `cmd.exe /c "echo off | clip"` on Windows.
* **Configuration:** The monitoring interval (`check_interval_ms`) is configurable via `config.yml`.

### 4.2. `image_manager.py` (`ImageManager` class)

* **Purpose:** Manages the lifecycle of all captured images.
* **Storage:**
  * When an image is added (`add_image`):
    * Assigns a unique UUID to the image.
    * Saves the image as a temporary file (e.g., in a `temp_images` subdirectory, format typically PNG).
    * Stores metadata (the PIL Image object itself, timestamp, selection status, file path, original dimensions) in an internal dictionary, keyed by the image ID.
* **Image Access & Retrieval:**
  * `get_image(image_id)`: Retrieves a PIL Image object.
  * `get_all_image_ids()`: Returns a list of all stored image IDs.
  * `get_selected_image_ids()`: Returns IDs of images marked as selected.
  * `get_image_path(image_id)`: Returns the path to the temporary file of an image.
  * `get_image_metadata(image_id)`: Returns the stored metadata for an image.
* **Image Manipulation:**
  * `create_thumbnail(image)`: Generates a smaller version of an image for display in lists or grids. Thumbnail size is configurable.
  * `resize_for_preview(image)`: Resizes an image to fit a preview area while maintaining aspect ratio. Preview dimensions are configurable.
* **Saving Images (`save_images` method):**
  * Handles saving selected images to a user-specified directory.
  * Supports custom file prefixes and sequential numbering for saved files.
  * Offers an option to create a single ZIP archive containing all selected images.
  * Remembers the last used save directory (persisted in `user_settings.json`) for user convenience.
* **Deletion & Cleanup:**
  * `delete_images_by_ids(image_ids)`: Removes specified images from management and deletes their temporary files.
  * `clear_images()`: Removes all stored images and their temporary files (e.g., when exiting without saving).
  * `clean_temp_files()`: A utility to remove all files from the `temp_images` directory, typically run on application startup.
* **Configuration:** Default save directory, prefix, image format, and thumbnail/preview sizes are loaded from `config.yml`.

### 4.3. UI and Theming Components

* **`theme_manager.py` (`ThemeManager` class):**
  * Responsible for loading and managing UI theme definitions (e.g., light, dark, custom themes).
  * Themes are defined in detail within `config.yml`, specifying colors, fonts, and styles for various UI components.
* **`app_theme_adapter.py` (`AppThemeAdapter` class):**
  * Acts as an adapter or bridge between the `ThemeManager` and the CustomTkinter application.
  * Applies the theme settings (retrieved from `ThemeManager`) to the main application window and its widgets.
* **`ui_helper.py` (Utility functions/class):**
  * Provides helper functions or a class to consistently apply styling (based on the current theme) to common UI elements (frames, buttons, labels, etc.).
  * Promotes a uniform look and feel across the application and reduces redundant styling code.

### 4.4. Dialog Windows (Separate `.py` files for each)

* **`image_selection_dialog.py` (`ImageSelectionDialog` class):**
  * Presents a dialog where users can view thumbnails of all captured images.
  * Allows users to select or deselect images for saving.
  * Supports reordering of images (likely via drag-and-drop functionality).
  * Users can initiate the image saving process from this dialog.
* **`image_viewer_dialog.py` (`ImageViewerDialog` class):**
  * A simpler dialog used to display a single selected image in a larger, more detailed view.
* **`floating_capture_window.py` (`FloatingCaptureWindow` class):**
  * A small, non-modal (floating) window that likely appears briefly when a new image is captured.
  * Provides immediate visual feedback to the user about a successful capture, possibly showing a small preview or capture count.
* **`help_dialog.py` (`HelpDialog` class):**
  * Displays help information and usage instructions to the user.
  * The content for this dialog is likely loaded from an external `help.md` Markdown file.

### 4.5. Configuration System

* **`config.yml`:**
  * The central configuration file for the application, written in YAML format.
  * Stores a wide range of settings:
    * **Application settings:** Window title, default dimensions.
    * **Image settings:** Default save format (e.g., PNG), thumbnail size, preview pane dimensions.
    * **File settings:** Default save directory, default filename prefix.
    * **Monitor settings:** Clipboard check interval (in milliseconds).
    * **Logging settings:** Log level, log file path.
    * **Theme definitions:** Detailed color palettes, font specifications, and styling rules for various UI components for different themes (e.g., 'default'/'light', 'dark').
* **`user_settings.json`:**
  * Stores user-specific preferences that need to persist across application sessions.
  * A key example is the `last_save_directory`, allowing the application to remember where the user last saved images.

### 4.6. Logging System

* **`logger.py` (Setup script/module):**
  * Configures the Python `logging` module for the application.
  * Allows different parts of the application to record events, informational messages, warnings, and errors.
  * Log output is typically directed to a file (e.g., `clipboard_capture.log`) and/or the console, aiding in debugging and tracking application behavior.

## 5. Simplified Data Flow (Image Capture to Save)

1. **Detection:** `ClipboardMonitor` (running in a background thread) detects a new image on the system clipboard.
2. **Callback:** `ClipboardMonitor` invokes the `on_image_captured` method in `ClipboardImageApp`, passing the raw PIL Image object.
3. **Processing & Storage:** `ClipboardImageApp` forwards the image to `ImageManager.add_image`.
4. **Temp Save:** `ImageManager` saves the image to a temporary file in the `temp_images` directory, assigns it a unique ID, and stores its metadata (including the PIL object) in memory.
5. **UI Update:** `ClipboardImageApp` updates its UI to reflect the new capture (e.g., increments image count, updates the preview panel with the new image).
6. **User Interaction (Image Selection):**
    * The user opens the `ImageSelectionDialog` (launched from `ClipboardImageApp`).
    * Inside the dialog, the user reviews thumbnails, selects/deselects images, and potentially reorders them.
7. **Initiate Save:** The user triggers the save operation (e.g., by clicking a "Save" button in `ImageSelectionDialog` or the main `ClipboardImageApp` window).
8. **Save Execution:**
    * `ClipboardImageApp` (or `ImageSelectionDialog` via `ClipboardImageApp`) calls `ImageManager.save_images`.
    * This method is provided with the list of selected image IDs (and their order), the desired filename prefix, the target save directory, and whether to create a ZIP archive.
9. **Final Save:** `ImageManager` iterates through the selected images, copies their temporary files to the final destination directory with appropriate names (prefix + sequential number), and creates a ZIP file if requested.

## 6. Key Design Principles Observed

* **Modularity:** The application is well-organized into distinct Python files (modules), each encapsulating a specific set of functionalities (e.g., `app.py` for main UI, `clipboard_monitor.py` for clipboard interaction, `image_manager.py` for data handling).
* **Separation of Concerns (SoC):** There's a clear distinction between UI logic (handled by `app.py` and various dialog classes) and the underlying business/core logic (e.g., image capture in `clipboard_monitor.py`, image data management in `image_manager.py`).
* **Asynchronous Operations:** The use of `threading` for clipboard monitoring ensures that the UI remains responsive and doesn't freeze while waiting for clipboard events.
* **Centralized Configuration:** `config.yml` serves as a single source of truth for most application settings, allowing for easier customization of behavior and appearance without direct code modification.
* **Object-Oriented Design (OOD):** The application extensively uses classes (e.g., `ClipboardImageApp`, `ClipboardMonitor`, `ImageManager`, various dialog classes) to encapsulate data and related behaviors, promoting code reusability and maintainability.
* **User Experience Focus:** Features like theme management, remembering the last save directory, and providing clear feedback (e.g., floating capture window) indicate a consideration for user experience.

This architectural structure provides a robust and maintainable foundation for the "Captura Clipboard" application.
