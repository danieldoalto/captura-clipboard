#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import customtkinter
import logging
from typing import Any, Dict, Optional
from theme_manager import ThemeManager

class UIHelper:
    """
    Classe auxiliar que fornece métodos para estilizar componentes de UI
    baseados nas configurações de tema do ThemeManager.
    """
    
    def __init__(self, theme_manager: ThemeManager, logger: Optional[logging.Logger] = None):
        """
        Inicializa o helper de UI.
        
        Args:
            theme_manager: Instância do ThemeManager para obter configurações de tema
            logger: Logger opcional para mensagens de depuração
        """
        self.theme_manager = theme_manager
        self.logger = logger
        self.original_styles = {}
    
    def style_button(self, button: customtkinter.CTkButton, variant: Optional[str] = None) -> None:
        """
        Aplica o estilo do tema atual a um botão.
        
        Args:
            button: Botão CTkButton para aplicar o estilo
            variant: Nome da variante do botão (ex: "success", "secondary")
        """
        base_path = "button"
        
        # Propriedades que podem ser específicas da variante
        default_fg_color = self.theme_manager.get(f"{base_path}.background")
        default_hover_color = self.theme_manager.get(f"{base_path}.hover_background")
        
        if variant:
            variant_base_path = f"{base_path}.{variant}"
            # Tenta obter da variante, senão do botão base
            fg_color = self.theme_manager.get(f"{variant_base_path}.background", default_fg_color)
            hover_color = self.theme_manager.get(f"{variant_base_path}.hover_background", default_hover_color)
        else:
            fg_color = default_fg_color
            hover_color = default_hover_color
            
        # Propriedades geralmente do botão base, pois variantes no config.yml atual
        # não definem text_color, corner_radius, border_width.
        text_color = self.theme_manager.get(f"{base_path}.text_color", "#FFFFFF") # Default se não encontrado
        corner_radius = self.theme_manager.get(f"{base_path}.corner_radius", 8)
        border_width = self.theme_manager.get(f"{base_path}.border_width", 0)

        button.configure(
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color,
            corner_radius=corner_radius,
            border_width=border_width
        )
    
    def style_entry(self, entry: customtkinter.CTkEntry) -> None:
        """
        Aplica o estilo do tema atual a um campo de entrada.
        
        Args:
            entry: Campo de entrada CTkEntry para aplicar o estilo
        """
        entry.configure(
            fg_color=self.theme_manager.get("input.background"),
            text_color=self.theme_manager.get("input.text_color"),
            border_color=self.theme_manager.get("input.border_color"),
            border_width=self.theme_manager.get("input.border_width", 1),
            corner_radius=self.theme_manager.get("input.corner_radius", 6)
        )
    
    def style_frame(self, frame: customtkinter.CTkFrame, style: str = "dialog") -> None:
        """
        Aplica o estilo do tema atual a um frame.
        
        Args:
            frame: Frame CTkFrame para aplicar o estilo
            style: Estilo a ser aplicado ('dialog', 'thumbnail', ou customizado)
        """
        if style == "dialog":
            frame.configure(
                fg_color=self.theme_manager.get("dialog.background"),
                border_color=self.theme_manager.get("dialog.border_color"),
                border_width=self.theme_manager.get("dialog.border_width", 1),
                corner_radius=self.theme_manager.get("dialog.corner_radius", 10)
            )
        elif style == "thumbnail":
            frame.configure(
                fg_color=self.theme_manager.get("dialog.background"),
                border_color=self.theme_manager.get("thumbnail.border_color"),
                border_width=self.theme_manager.get("thumbnail.border_width", 1),
                corner_radius=self.theme_manager.get("thumbnail.corner_radius", 4)
            )
        else:
            # Estilo customizado
            if self.logger:
                self.logger.debug(f"Aplicando estilo customizado: {style}")
    
    def style_label(self, label: customtkinter.CTkLabel, style: str = "default") -> None:
        """
        Aplica o estilo do tema atual a um label.
        
        Args:
            label: Label CTkLabel para aplicar o estilo
            style: Estilo a ser aplicado ('default', 'header', 'small')
        """
        text_color = self.theme_manager.get("colors.text")
        font_family = self.theme_manager.get("fonts.default_family")
        
        if style == "default":
            font_size = self.theme_manager.get("fonts.default_size", 12)
        elif style == "header":
            font_size = self.theme_manager.get("fonts.header_size", 16)
        elif style == "small":
            font_size = self.theme_manager.get("fonts.small_size", 10)
        else:
            font_size = self.theme_manager.get("fonts.default_size", 12)
        
        label.configure(
            text_color=text_color,
            font=(font_family, font_size)
        )
    
    def get_padding(self, size: str = "medium") -> int:
        """
        Retorna o valor de padding do tema atual.
        
        Args:
            size: Tamanho do padding ('small', 'medium', 'large')
            
        Returns:
            Valor de padding em pixels
        """
        if size == "small":
            return self.theme_manager.get("spacing.padding_small", 5)
        elif size == "medium":
            return self.theme_manager.get("spacing.padding_medium", 10)
        elif size == "large":
            return self.theme_manager.get("spacing.padding_large", 20)
        else:
            return self.theme_manager.get("spacing.padding_medium", 10)
    
    def get_margin(self, size: str = "medium") -> int:
        """
        Retorna o valor de margem do tema atual.
        
        Args:
            size: Tamanho da margem ('small', 'medium', 'large')
            
        Returns:
            Valor de margem em pixels
        """
        if size == "small":
            return self.theme_manager.get("spacing.margin_small", 5)
        elif size == "medium":
            return self.theme_manager.get("spacing.margin_medium", 10)
        elif size == "large":
            return self.theme_manager.get("spacing.margin_large", 20)
        else:
            return self.theme_manager.get("spacing.margin_medium", 10)
    
    def get_color(self, color_name: str) -> str:
        """
        Retorna a cor especificada do tema atual.
        
        Args:
            color_name: Nome da cor ('primary', 'secondary', 'success', etc.)
            
        Returns:
            Código hexadecimal da cor
        """
        return self.theme_manager.get(f"colors.{color_name}", "#000000")
    
    def apply_app_theme(self, app_instance: Any) -> None:
        """
        Aplica o tema global à instância da aplicação CustomTkinter.
        
        Args:
            app_instance: Instância da aplicação principal
        """
        # Define cores globais do customtkinter
        background_color = self.theme_manager.get("colors.background")
        is_dark = self.theme_manager.current_theme == "dark"
        
        appearance_mode = "dark" if is_dark else "light"
        customtkinter.set_appearance_mode(appearance_mode)
        
        if is_dark:
            # Tema escuro
            customtkinter.set_default_color_theme("dark-blue")
        else:
            # Tema claro
            customtkinter.set_default_color_theme("blue")
        
        # Configure janela principal se disponível
        if hasattr(app_instance, "configure"):
            try:
                app_instance.configure(fg_color=background_color)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Erro ao configurar tema da aplicação: {e}")
                    
    def style_checkbox(self, checkbox: customtkinter.CTkCheckBox) -> None:
        """
        Aplica o estilo do tema atual a um checkbox.
        
        Args:
            checkbox: Checkbox CTkCheckBox para aplicar o estilo
        """
        checkbox.configure(
            fg_color=self.theme_manager.get("checkbox.fg_color", self.theme_manager.get("colors.primary")),
            hover_color=self.theme_manager.get("checkbox.hover_color", self.theme_manager.get("colors.secondary")),
            text_color=self.theme_manager.get("checkbox.text_color", self.theme_manager.get("colors.text")),
            checkmark_color=self.theme_manager.get("checkbox.checkmark_color", "#FFFFFF"),
            corner_radius=self.theme_manager.get("checkbox.corner_radius", 6)
        )

    def style_scrollable_frame(self, frame: customtkinter.CTkScrollableFrame) -> None:
        """
        Aplica o estilo do tema atual a um CTkScrollableFrame.
        
        Args:
            frame: CTkScrollableFrame para aplicar o estilo
        """
        frame.configure(
            fg_color=self.theme_manager.get("scrollable_frame.background", self.theme_manager.get("dialog.background")),
            # Scrollable frames often don't have their own border distinct from their content or parent
            # border_color=self.theme_manager.get("scrollable_frame.border_color", self.theme_manager.get("dialog.border_color")),
            # border_width=self.theme_manager.get("scrollable_frame.border_width", 0), 
            corner_radius=self.theme_manager.get("scrollable_frame.corner_radius", self.theme_manager.get("dialog.corner_radius", 8)), # Smaller radius for inner element
            
            # Styling scrollbar elements
            scrollbar_fg_color=self.theme_manager.get("scrollable_frame.scrollbar_fg_color", self.theme_manager.get("colors.secondary")),
            scrollbar_button_color=self.theme_manager.get("scrollable_frame.scrollbar_button_color", self.theme_manager.get("colors.primary")),
            scrollbar_button_hover_color=self.theme_manager.get("scrollable_frame.scrollbar_button_hover_color", self.theme_manager.get("colors.primary_hover", "#0056b3")) # Assuming a primary_hover
        )
        # Note: CTkScrollableFrame border_width and border_color apply to the scrollbar trough, not the frame itself.
        # The frame's own border would typically be managed by a parent CTkFrame if desired.
        # For the main area of the scrollable frame, fg_color is the most relevant.
    def highlight_widget(self, widget: Any, style_key: str) -> None:
        """
        Aplica um estilo de destaque a um widget e armazena seu estilo original.

        Args:
            widget: O widget a ser destacado.
            style_key: A chave para o estilo de destaque no tema (ex: 'drop_target').
        """
        if not hasattr(widget, "configure"):
            if self.logger:
                self.logger.warning(f"Widget {widget} não tem método 'configure' para aplicar destaque.")
            return

        original_fg = None
        original_border = None

        try:
            original_fg = widget.cget("fg_color")
        except Exception:
            pass # Widget pode não ter fg_color
        
        try:
            original_border = widget.cget("border_color")
        except Exception:
            pass # Widget pode não ter border_color

        self.original_styles[widget] = {
            "fg_color": original_fg,
            "border_color": original_border
        }

        highlight_fg_color = self.theme_manager.get(f"highlight.{style_key}.background_color", original_fg) 
        highlight_border_color = self.theme_manager.get(f"highlight.{style_key}.border_color", original_border)
        
        configure_options = {}
        if highlight_fg_color is not None:
            configure_options["fg_color"] = highlight_fg_color
        if highlight_border_color is not None:
            configure_options["border_color"] = highlight_border_color
        
        if configure_options:
            widget.configure(**configure_options)
            if self.logger:
                self.logger.debug(f"Widget {widget} destacado com estilo '{style_key}'. Aplicado: {configure_options}")
        elif self.logger:
            self.logger.debug(f"Nenhuma configuração de destaque encontrada ou aplicada para o estilo '{style_key}' no widget {widget}.")

    def remove_highlight(self, widget: Any) -> None:
        """
        Remove o destaque de um widget, restaurando seu estilo original.

        Args:
            widget: O widget do qual remover o destaque.
        """
        if widget in self.original_styles:
            original_style = self.original_styles.pop(widget)
            configure_options = {}
            if original_style.get("fg_color") is not None:
                configure_options["fg_color"] = original_style["fg_color"]
            if original_style.get("border_color") is not None:
                configure_options["border_color"] = original_style["border_color"]
            
            if configure_options:
                try:
                    widget.configure(**configure_options)
                    if self.logger:
                        self.logger.debug(f"Destaque removido do widget {widget}. Restaurado: {configure_options}")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Erro ao remover destaque do widget {widget}: {e}")
            elif self.logger:
                 self.logger.debug(f"Nenhum estilo original encontrado para restaurar no widget {widget} ou widget não configurável.")
        elif self.logger:
            self.logger.warning(f"Tentativa de remover destaque de um widget {widget} que não estava na lista de estilos originais.")

    def style_selected_thumbnail(self, frame: customtkinter.CTkFrame, is_selected: bool) -> None:
        """
        Aplica o estilo para um thumbnail selecionado ou não selecionado.
        
        Args:
            frame: Frame da miniatura
            is_selected: Se a miniatura está selecionada ou não
        """
        if is_selected:
            frame.configure(
                border_color=self.theme_manager.get("thumbnail.selected_border_color"),
                border_width=self.theme_manager.get("thumbnail.selected_border_width", 2)
            )
        else:
            frame.configure(
                border_color=self.theme_manager.get("thumbnail.border_color"),
                border_width=self.theme_manager.get("thumbnail.border_width", 1)
            )
