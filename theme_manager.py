#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import yaml
import logging
import re
from typing import Any, Dict, Optional, Union

class ThemeManager:
    """
    Gerenciador de temas e configurações visuais da aplicação.
    Centraliza o acesso às cores, fontes e outras propriedades visuais a partir do config.yml.
    """
    
    def __init__(self, config_path: str = "config.yml", logger: Optional[logging.Logger] = None):
        """
        Inicializa o gerenciador de temas.
        
        Args:
            config_path: Caminho para o arquivo de configuração (default: config.yml)
            logger: Logger opcional para mensagens de depuração
        """
        self.config_path = config_path
        self.logger = logger
        self.config = {}
        self.current_theme = "default"
        self._load_config()
    
    def _load_config(self) -> None:
        """Carrega o arquivo de configuração."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
                
                # Verifica se a seção de UI existe
                if 'ui' not in self.config:
                    self._init_default_ui_config()
                
                # Configura o tema atual
                if 'ui' in self.config and 'theme' in self.config['ui']:
                    self.current_theme = self.config['ui']['theme']
                    
                if self.logger:
                    self.logger.info(f"Tema carregado: {self.current_theme}")
            else:
                if self.logger:
                    self.logger.warning(f"Arquivo de configuração não encontrado: {self.config_path}")
                self._init_default_ui_config()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao carregar configurações: {e}")
            self._init_default_ui_config()
    
    def _init_default_ui_config(self) -> None:
        """Inicializa a configuração padrão de UI se não existir."""
        if 'ui' not in self.config:
            self.config['ui'] = {
                'theme': 'default',
                'themes': {
                    'default': self._get_default_theme(),
                    'dark': self._get_dark_theme()
                }
            }
    
    def _get_default_theme(self) -> Dict[str, Any]:
        """Retorna o tema padrão (claro)."""
        return {
            'colors': {
                'primary': '#3B8ED0',
                'secondary': '#6C757D',
                'success': '#28A745',
                'danger': '#DC3545',
                'warning': '#FFC107',
                'info': '#17A2B8',
                'background': '#F0F2F5',
                'text': '#212529',
            },
            'button': {
                'background': '{colors.primary}',
                'hover_background': '#3071A9',
                'text_color': '#FFFFFF',
                'border_width': 0,
                'corner_radius': 8,
            },
            'input': {
                'background': '#FFFFFF',
                'text_color': '{colors.text}',
                'border_color': '#CED4DA',
                'border_width': 1,
                'corner_radius': 6,
            },
            'dialog': {
                'background': '#FFFFFF',
                'border_color': '#DDDDDD',
                'border_width': 1,
                'corner_radius': 10,
                'shadow': True,
            },
            'thumbnail': {
                'border_color': '#DDDDDD',
                'border_width': 1,
                'corner_radius': 4,
                'selected_border_color': '{colors.primary}',
                'selected_border_width': 2,
            },
            'fonts': {
                'default_family': 'Roboto',
                'default_size': 12,
                'header_size': 16,
                'small_size': 10,
            },
            'spacing': {
                'padding_small': 5,
                'padding_medium': 10,
                'padding_large': 20,
                'margin_small': 5,
                'margin_medium': 10,
                'margin_large': 20,
            }
        }
    
    def _get_dark_theme(self) -> Dict[str, Any]:
        """Retorna o tema escuro."""
        return {
            'colors': {
                'primary': '#007BFF',
                'secondary': '#6C757D',
                'success': '#28A745',
                'danger': '#DC3545',
                'warning': '#FFC107',
                'info': '#17A2B8',
                'background': '#121212',
                'text': '#FFFFFF',
            },
            'button': {
                'background': '{colors.primary}',
                'hover_background': '#0069D9',
                'text_color': '#FFFFFF',
                'border_width': 0,
                'corner_radius': 8,
            },
            'input': {
                'background': '#2D2D2D',
                'text_color': '{colors.text}',
                'border_color': '#444444',
                'border_width': 1,
                'corner_radius': 6,
            },
            'dialog': {
                'background': '#1E1E1E',
                'border_color': '#333333',
                'border_width': 1,
                'corner_radius': 10,
                'shadow': True,
            },
            'thumbnail': {
                'border_color': '#333333',
                'border_width': 1,
                'corner_radius': 4,
                'selected_border_color': '{colors.primary}',
                'selected_border_width': 2,
            },
            'fonts': {
                'default_family': 'Roboto',
                'default_size': 12,
                'header_size': 16,
                'small_size': 10,
            },
            'spacing': {
                'padding_small': 5,
                'padding_medium': 10,
                'padding_large': 20,
                'margin_small': 5,
                'margin_medium': 10,
                'margin_large': 20,
            }
        }
    
    def get(self, key_path: str, default_value: Any = None) -> Any:
        """
        Obtém o valor de uma configuração do tema atual usando caminho separado por pontos.
        
        Args:
            key_path: Caminho para a configuração (ex: "button.background")
            default_value: Valor padrão caso a configuração não seja encontrada
            
        Returns:
            O valor da configuração ou o valor padrão
        """
        try:
            # Começa na raiz do tema atual
            if 'ui' not in self.config or 'themes' not in self.config['ui'] or self.current_theme not in self.config['ui']['themes']:
                if self.logger:
                    self.logger.warning(f"Tema não encontrado: {self.current_theme}")
                return default_value
            
            # Usa o tema atual como base
            theme_config = self.config['ui']['themes'][self.current_theme]
            
            # Separa o caminho em partes
            path_parts = key_path.split('.')
            
            # Navega pela estrutura de configuração
            value = theme_config
            for part in path_parts:
                if part not in value:
                    return default_value
                value = value[part]
            
            # Processa referências no formato {colors.primary}
            if isinstance(value, str):
                return self._resolve_references(value)
            
            return value
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao obter configuração '{key_path}': {e}")
            return default_value
    
    def _resolve_references(self, value: str) -> Union[str, Any]:
        """
        Resolve referências a outras configurações no formato {caminho.para.config}.
        
        Args:
            value: Valor que pode conter referências
            
        Returns:
            Valor com referências resolvidas
        """
        # Padrão para identificar referências: {algo.como.isto}
        ref_pattern = r'\{([a-zA-Z0-9_.]+)\}'
        
        # Se o valor é exatamente uma referência, retorna o valor referenciado
        if value.startswith('{') and value.endswith('}') and value.count('{') == 1:
            ref_path = value[1:-1]  # Remove { }
            return self.get(ref_path, value)  # Se não encontrar, mantém a string original
        
        # Se o valor contém referências misturadas com texto, substitui cada referência
        def replace_ref(match):
            ref_path = match.group(1)
            ref_value = self.get(ref_path, match.group(0))
            return str(ref_value)
        
        return re.sub(ref_pattern, replace_ref, value)
    
    def set_theme(self, theme_name: str) -> bool:
        """
        Define o tema atual.
        
        Args:
            theme_name: Nome do tema
            
        Returns:
            True se o tema existe e foi configurado, False caso contrário
        """
        if theme_name in self.config['ui']['themes']:
            self.current_theme = theme_name
            if self.logger:
                self.logger.info(f"Tema alterado para: {theme_name}")
            return True
        
        if self.logger:
            self.logger.warning(f"Tema não encontrado: {theme_name}")
        return False
    
    def save_config(self) -> bool:
        """
        Salva as configurações no arquivo.
        
        Returns:
            True se as configurações foram salvas com sucesso, False caso contrário
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            
            if self.logger:
                self.logger.info(f"Configurações salvas em: {self.config_path}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao salvar configurações: {e}")
            return False
    
    def update_config(self, config_changes: Dict[str, Any]) -> None:
        """
        Atualiza as configurações com as alterações especificadas.
        
        Args:
            config_changes: Dicionário com alterações nas configurações
        """
        def update_dict(original, updates):
            for key, value in updates.items():
                if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                    update_dict(original[key], value)
                else:
                    original[key] = value
        
        update_dict(self.config, config_changes)
