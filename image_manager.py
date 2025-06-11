import os
import uuid
import zipfile
from datetime import datetime
from typing import Dict, List, Optional
from PIL import Image
import yaml


class ImageManager:
    """
    Manages captured images, including storage, saving, and exporting.
    """
    
    def __init__(self, config_path='config.yml'):
        """
        Initialize the image manager.
        
        Args:
            config_path (str): Path to the configuration file
        """
        # Load configuration
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        self.image_config = config.get('image', {})
        self.file_config = config.get('file', {})
        
        # Default save directory
        default_dir = self.file_config.get('default_save_directory', '')
        if not default_dir:
            # Use Documents folder if not specified
            default_dir = os.path.join(os.path.expanduser('~'), 'Documents')
        
        self.default_save_directory = default_dir
        self.default_prefix = self.file_config.get('default_prefix', 'captura')
        self.default_format = self.image_config.get('default_format', 'png')
        
        # Dictionary to store captured images
        # {id: {'image': PIL.Image, 'timestamp': datetime, 'selected': bool, 'path': str}}
        self.images: Dict[str, Dict] = {}
        self.logger = None  # Will be set externally
        
        # Ensure temp directory exists
        self.temp_dir = os.path.join(os.getcwd(), 'temp_images')
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def set_logger(self, logger):
        """Set the logger for this component"""
        self.logger = logger
    
    def add_image(self, image: Image.Image) -> str:
        """
        Add a new image to the manager.
        
        Args:
            image: PIL Image object
        
        Returns:
            str: ID of the added image
        """
        image_id = str(uuid.uuid4())
        
        # Save image to temporary file
        temp_path = os.path.join(self.temp_dir, f"{image_id}.{self.default_format}")
        
        try:
            image.save(temp_path)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving temporary image: {e}")
        
        self.images[image_id] = {
            'image': image,
            'timestamp': datetime.now(),
            'selected': True,  # Default to selected
            'path': temp_path,
            'width': image.width,
            'height': image.height
        }
        
        if self.logger:
            self.logger.info(f"Added new image with ID: {image_id}")
        
        return image_id
    
    def get_image(self, image_id: str) -> Optional[Image.Image]:
        """
        Get an image by its ID.
        
        Args:
            image_id: The ID of the image
        
        Returns:
            Optional[Image.Image]: The image or None if not found
        """
        if image_id in self.images:
            return self.images[image_id]['image']
        return None
    
    def get_all_image_ids(self) -> List[str]:
        """
        Get all image IDs.
        
        Returns:
            List[str]: List of all image IDs
        """
        return list(self.images.keys())
    
    def set_image_selected(self, image_id: str, selected: bool):
        """
        Set whether an image is selected or not.
        
        Args:
            image_id: The ID of the image
            selected: Whether the image is selected
        """
        if image_id in self.images:
            self.images[image_id]['selected'] = selected
    
    def get_selected_image_ids(self) -> List[str]:
        """
        Get IDs of all selected images.
        
        Returns:
            List[str]: List of selected image IDs
        """
        return [
            image_id for image_id, data in self.images.items()
            if data['selected']
        ]
    
    def get_image_path(self, image_id: str) -> Optional[str]:
        """
        Get the file path of an image.
        
        Args:
            image_id: The ID of the image
            
        Returns:
            Optional[str]: Path to the image file or None if not found
        """
        if image_id in self.images and 'path' in self.images[image_id]:
            return self.images[image_id]['path']
        return None
        
    def get_image_metadata(self, image_id: str) -> Dict:
        """
        Get metadata for an image.
        
        Args:
            image_id: The ID of the image
            
        Returns:
            Dict: Dictionary with image metadata
        """
        if image_id in self.images:
            img_data = self.images[image_id]
            return {
                'width': img_data.get('width', 0),
                'height': img_data.get('height', 0),
                'timestamp': img_data.get('timestamp', datetime.now())
            }
        return {'width': 0, 'height': 0, 'timestamp': datetime.now()}
    
    def get_thumbnail(self, image_id: str) -> Optional[Image.Image]:
        """
        Get a thumbnail of an image.
        
        Args:
            image_id: The ID of the image
            
        Returns:
            Optional[Image.Image]: Thumbnail image or None if not found
        """
        if image_id in self.images and 'image' in self.images[image_id]:
            return self.create_thumbnail(self.images[image_id]['image'])
        return None
        
    def clear_images(self):
        """Clear all stored images"""
        # Remove temporary files
        for image_id, data in self.images.items():
            if 'path' in data and os.path.exists(data['path']):
                try:
                    os.remove(data['path'])
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error removing temporary file: {e}")
                        
        self.images.clear()
        if self.logger:
            self.logger.info("Cleared all images")
    
    def save_images(self, prefix: str, directory: str, create_zip: bool = False) -> List[str]:
        """
        Save all selected images to disk.
        
        Args:
            prefix: File name prefix
            directory: Directory to save images to
            create_zip: Whether to also create a ZIP archive
        
        Returns:
            List[str]: List of saved file paths
        """
        if not prefix:
            prefix = self.default_prefix
            
        if not directory:
            directory = self.default_save_directory
            
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        saved_files = []
        selected_ids = self.get_selected_image_ids()
        
        # Save individual images
        for idx, image_id in enumerate(selected_ids):
            image_data = self.images[image_id]
            image = image_data['image']
            
            # Create filename with sequential numbering
            filename = f"{prefix}_{idx+1}.{self.default_format}"
            filepath = os.path.join(directory, filename)
            
            try:
                image.save(filepath)
                saved_files.append(filepath)
                if self.logger:
                    self.logger.info(f"Saved image to {filepath}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error saving image {filename}: {e}")
        
        # Create ZIP archive if requested
        if create_zip and saved_files:
            try:
                zip_path = os.path.join(directory, f"{prefix}_images.zip")
                with zipfile.ZipFile(zip_path, 'w') as zip_file:
                    for file in saved_files:
                        zip_file.write(file, os.path.basename(file))
                
                saved_files.append(zip_path)
                if self.logger:
                    self.logger.info(f"Created ZIP archive at {zip_path}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error creating ZIP archive: {e}")
        
        return saved_files
    
    def resize_for_preview(self, image: Image.Image) -> Image.Image:
        """
        Resize an image for preview while maintaining aspect ratio.
        
        Args:
            image: The image to resize
        
        Returns:
            Image.Image: Resized image
        """
        max_width = self.image_config.get('max_preview_width', 400)
        max_height = self.image_config.get('max_preview_height', 300)
        
        width, height = image.size
        
        # Calculate aspect ratio
        aspect = width / height
        
        # Determine new dimensions
        if width > max_width or height > max_height:
            if aspect > 1:  # Wider than tall
                new_width = min(width, max_width)
                new_height = int(new_width / aspect)
            else:  # Taller than wide
                new_height = min(height, max_height)
                new_width = int(new_height * aspect)
                
            return image.resize((new_width, new_height), Image.LANCZOS)
        
        return image
    
    def create_thumbnail(self, image: Image.Image) -> Image.Image:
        """
        Create a thumbnail of an image.
        
        Args:
            image: The image to create a thumbnail from
        
        Returns:
            Image.Image: Thumbnail image
        """
        size = self.image_config.get('thumbnail_size', 100)
        thumbnail = image.copy()
        thumbnail.thumbnail((size, size), Image.LANCZOS)
        return thumbnail
