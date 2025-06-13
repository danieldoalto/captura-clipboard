#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from theme_manager import ThemeManager
from ui_helper import UIHelper

class AppThemeAdapter:
    """
    Adaptador para integrar o gerenciador de temas com a aplicação principal.
    Esta classe serve como uma ponte entre o ThemeManager e o app.py,
    evitando sobrecarregar o arquivo principal com código adicional.
    """
    
    def __init__(self, config_path: str = "config.yml", logger=None):
        """
        Inicializa o adaptador de tema.
        
        Args:
            config_path: Caminho para o arquivo de configuração
            logger: Logger para mensagens de log
        """
        self.logger = logger
        
        # Inicializa o gerenciador de temas
        self.theme_manager = ThemeManager(config_path=config_path, logger=logger)
        
        # Inicializa o helper de UI
        self.ui_helper = UIHelper(theme_manager=self.theme_manager, logger=logger)
        
        if self.logger:
            self.logger.info(f"Tema atual: {self.theme_manager.current_theme}")
    
    def apply_theme_to_app(self, app_instance):
        """
        Aplica o tema à instância da aplicação.
        
        Args:
            app_instance: Instância da aplicação principal
        """
        self.ui_helper.apply_app_theme(app_instance)
        
    def get_ui_helper(self):
        """
        Retorna a instância do helper de UI para uso nos componentes.
        
        Returns:
            UIHelper: Instância do helper de UI
        """
        return self.ui_helper
    
    def get_theme_manager(self):
        """
        Retorna a instância do gerenciador de temas.
        
        Returns:
            ThemeManager: Instância do gerenciador de temas
        """
        return self.theme_manager
        
    def set_theme(self, theme_name):
        """
        Define o tema atual.
        
        Args:
            theme_name: Nome do tema ('default', 'dark')
            
        Returns:
            bool: True se o tema foi alterado com sucesso, False caso contrário
        """
        success = self.theme_manager.set_theme(theme_name)
        if success:
            # Atualiza o arquivo de configuração
            self.theme_manager.config['ui']['theme'] = theme_name
            self.theme_manager.save_config()
        return success
