import os
import uuid
import zipfile
import json
import glob
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
        
        # Arquivo para armazenar o último diretório de salvamento
        self.settings_file = os.path.join(os.getcwd(), 'user_settings.json')
        
        # Carregar último diretório de salvamento, se existir
        self._load_last_save_directory()
    
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
    
    def save_images(self, prefix: str, directory: str, create_zip: bool = False, custom_order: List[str] = None) -> List[str]:
        """
        Save all selected images to disk.
        
        Args:
            prefix: File name prefix
            directory: Directory to save images to
            create_zip: Whether to also create a ZIP archive
            custom_order: Optional custom ordering of image IDs
        
        Returns:
            List[str]: List of saved file paths
        """
        if not prefix:
            prefix = self.default_prefix
            
        if not directory:
            directory = self.default_save_directory
            
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Salvar o diretório escolhido para uso futuro
        self._save_last_directory(directory)
        
        saved_files = []
        selected_ids = self.get_selected_image_ids()
        
        # If custom order is provided, use it (but only for items that are selected)
        if custom_order:
            # Filter to include only selected images in the specified order
            ordered_selected_ids = [img_id for img_id in custom_order if img_id in selected_ids]
            # Add any selected images that might not be in the custom order (though this shouldn't happen)
            for img_id in selected_ids:
                if img_id not in ordered_selected_ids:
                    ordered_selected_ids.append(img_id)
            selected_ids = ordered_selected_ids
        
        if create_zip:
            try:
                zip_path = os.path.join(directory, f"{prefix}_images.zip")
                with zipfile.ZipFile(zip_path, 'w') as zip_file:
                    for idx, image_id in enumerate(selected_ids):
                        image_data = self.images[image_id]
                        image = image_data['image']
                        
                        # Criar nome de arquivo com numeração sequencial no formato nn_prefix.ext
                        # Usar zfill(2) para garantir que o número tenha 2 dígitos (com zero à esquerda se necessário)
                        seq_number = str(idx+1).zfill(2)
                        filename = f"{seq_number}_{prefix}.{self.default_format}"
                        
                        try:
                            image.save(os.path.join(self.temp_dir, filename))
                            zip_file.write(os.path.join(self.temp_dir, filename), filename)
                            os.remove(os.path.join(self.temp_dir, filename))
                            if self.logger:
                                self.logger.info(f"Saved image to ZIP archive: {filename}")
                        except Exception as e:
                            if self.logger:
                                self.logger.error(f"Error saving image {filename} to ZIP archive: {e}")
                
                saved_files.append(zip_path)
                if self.logger:
                    self.logger.info(f"Created ZIP archive at {zip_path}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error creating ZIP archive: {e}")
        else:
            # Save individual images
            for idx, image_id in enumerate(selected_ids):
                image_data = self.images[image_id]
                image = image_data['image']
                
                # Criar nome de arquivo com numeração sequencial no formato nn_prefix.ext
                # Usar zfill(2) para garantir que o número tenha 2 dígitos (com zero à esquerda se necessário)
                seq_number = str(idx+1).zfill(2)
                filename = f"{seq_number}_{prefix}.{self.default_format}"
                filepath = os.path.join(directory, filename)
                
                try:
                    image.save(filepath)
                    saved_files.append(filepath)
                    if self.logger:
                        self.logger.info(f"Saved image to {filepath}")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error saving image {filename}: {e}")
        
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
    
    def _save_last_directory(self, directory: str):
        """
        Salva o último diretório usado para ser reutilizado na próxima execução
        
        Args:
            directory: Caminho do diretório a ser salvo
        """
        try:
            settings = {}
            
            # Carregar configurações existentes, se houver
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    try:
                        settings = json.load(f)
                    except json.JSONDecodeError:
                        # Se o arquivo estiver corrompido, iniciar com um dicionário vazio
                        settings = {}
            
            # Atualizar último diretório
            settings['last_save_directory'] = directory
            self.default_save_directory = directory
            
            # Salvar configurações
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
                
            if self.logger:
                self.logger.info(f"Last save directory saved: {directory}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving last directory: {e}")
    
    def _load_last_save_directory(self):
        """
        Carrega o último diretório de salvamento usado
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    
                last_dir = settings.get('last_save_directory')
                if last_dir and os.path.exists(last_dir):
                    self.default_save_directory = last_dir
                    
                    if self.logger:
                        self.logger.info(f"Loaded last save directory: {last_dir}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading last save directory: {e}")
    
    def clean_temp_files(self):
        """
        Remove todos os arquivos temporários da pasta temp_images
        """
        try:
            # Lista todos os arquivos no diretório temporário
            temp_files = glob.glob(os.path.join(self.temp_dir, f"*.{self.default_format}"))
            
            # Remove cada arquivo
            for file_path in temp_files:
                try:
                    os.remove(file_path)
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error removing temporary file: {file_path} - {e}")
            
            if self.logger:
                self.logger.info(f"Cleaned {len(temp_files)} temporary image files")
                
            return len(temp_files)  # Retorna o número de arquivos removidos
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error cleaning temp files: {e}")
            return 0
