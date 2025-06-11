import logging
import logging.handlers
import os
import yaml


def setup_logger(config_path='config.yml'):
    """
    Configure and setup the application logger based on configuration from config.yml
    
    Args:
        config_path (str): Path to the configuration file
    
    Returns:
        logging.Logger: Configured logger instance
    """
    try:
        # Load configuration
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        log_config = config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('file', 'clipboard_capture.log')
        max_size = log_config.get('max_file_size_mb', 10) * 1024 * 1024  # Convert to bytes
        backup_count = log_config.get('backup_count', 3)
        
        # Create logger
        logger = logging.getLogger('clipboard_capture')
        logger.setLevel(log_level)
        
        # Configure file handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_size, backupCount=backup_count
        )
        
        # Set formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        # Also add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        logger.info("Logger initialized successfully")
        return logger
        
    except Exception as e:
        # Set up a basic logger if configuration fails
        print(f"Error setting up logger: {e}. Using default configuration.")
        
        basic_logger = logging.getLogger('clipboard_capture')
        basic_logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        basic_logger.addHandler(handler)
        
        # Try to add a file handler too
        try:
            file_handler = logging.FileHandler('clipboard_capture.log')
            file_handler.setFormatter(formatter)
            basic_logger.addHandler(file_handler)
        except:
            pass
            
        return basic_logger
