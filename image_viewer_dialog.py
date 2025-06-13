import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
from typing import Optional
from ui_helper import UIHelper
import os # Necessário para os.path e os.path.getsize

class ImageViewerDialog(ctk.CTkToplevel):
    """
    Dialog for viewing images in larger size
    """
    
    def __init__(self, parent, image_path: str, image_id: str, filename: str=None, ui_helper: Optional[UIHelper] = None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        # Store reference to parent and ID
        self.parent = parent
        self.image_id = image_id
        self.filename = filename
        
        # Usar o UIHelper do parent ou criar um novo se não for fornecido
        self.ui_helper = ui_helper or (parent.ui_helper if hasattr(parent, 'ui_helper') else None)
        self.theme_manager = self.ui_helper.theme_manager if self.ui_helper else None
        
        # Set title and make resizable
        self.title("Visualizar Imagem")
        self.minsize(400, 300)
        self.resizable(True, True)
        
        # Load image
        self.image = Image.open(image_path)
        
        # Calculate window size - garantir espaço suficiente para a imagem
        screen_width = self.winfo_screenwidth() * 0.9  # Use 90% of screen width max
        screen_height = self.winfo_screenheight() * 0.8  # Use 80% of screen height max
        
        # Adicionar espaço para decorações de janela, barras de rolagem e informações
        padding_width = 60   # Espaço horizontal para bordas e padding
        padding_height = 150  # Espaço vertical para bordas, informações e botões
        
        # Calcular tamanho da janela para acomodar a imagem completa
        window_width = min(self.image.width + padding_width, screen_width)
        window_height = min(self.image.height + padding_height, screen_height)
        
        # Se a imagem for maior que o espaço disponível na tela, usar o máximo possível
        # mas manter barras de rolagem
        if window_width >= screen_width or window_height >= screen_height:
            window_width = min(window_width, screen_width)
            window_height = min(window_height, screen_height)
        
        # Garantir tamanho mínimo razoável
        window_width = max(window_width, 500)  # Mínimo de 500px de largura
        window_height = max(window_height, 400)  # Mínimo de 400px de altura
        
        # Calcular o tamanho disponível para exibição da imagem
        display_width = window_width - padding_width
        display_height = window_height - padding_height
        
        # Position window centered
        x = (self.winfo_screenwidth() - window_width) // 2
        y = (self.winfo_screenheight() - window_height) // 2
        self.geometry(f"{int(window_width)}x{int(window_height)}+{x}+{y}")
        
        # Setup UI
        self.setup_ui(display_width, display_height)
        
        # # Make dialog modal (commented out to allow multiple windows)
        # self.transient(parent)
        # self.grab_set()
        self.focus_set() # Keep focus on the new window
    
    def setup_ui(self, display_width, display_height):
        """Setup image viewer UI"""
        # Obter configurações de padding do tema
        padding_small = self.ui_helper.get_padding("small") if self.ui_helper else 5
        padding_med = self.ui_helper.get_padding("medium") if self.ui_helper else 10
        padding_large = self.ui_helper.get_padding("large") if self.ui_helper else 20
        
        # Container frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=padding_med, pady=padding_med)
        
        # Aplicar estilo ao frame principal se possível
        if self.ui_helper:
            self.ui_helper.style_frame(main_frame)
            
        # Create a scrollable frame for the image
        # Usar orientação "both" para permitir rolagem horizontal e vertical se necessário
        scroll_frame = ctk.CTkFrame(main_frame)
        scroll_frame.pack(fill="both", expand=True, padx=padding_small, pady=padding_small)
        
        if self.ui_helper:
            self.ui_helper.style_frame(scroll_frame)
        
        # Verificar se a imagem é maior que o espaço disponível
        if self.image.width > display_width or self.image.height > display_height:
            # Calcular a proporção para redimensionar mantendo a proporção original
            img_ratio = min(display_width/self.image.width, display_height/self.image.height)
            display_size = (int(self.image.width * img_ratio), int(self.image.height * img_ratio))
            display_img = self.image.resize(display_size, Image.LANCZOS)
            
            # Adicionar informação sobre escala
            scale_percent = int(img_ratio * 100)
            self.scaled_display = True
            self.scale_percent = scale_percent
        else:
            # Usar a imagem original se couber no espaço disponível
            display_img = self.image
            self.scaled_display = False
        
        # Converter para PhotoImage para exibição
        self.photo_image = ImageTk.PhotoImage(display_img)
        
        # Determine canvas size (no extra white areas)
        canvas_w = min(display_img.width, display_width)
        canvas_h = min(display_img.height, display_height)

        # Create canvas with same bg as frame to avoid white stripe
        try:
            bg_color = self.theme_manager.get_color("background") if self.theme_manager else self.cget("bg")
        except AttributeError:
            # Fallback: use appearance mode default colors
            mode = ctk.get_appearance_mode()
            bg_color = "#121212" if mode == "Dark" else "#FFFFFF"
        self.canvas = tk.Canvas(scroll_frame,
                                width=canvas_w,
                                height=canvas_h,
                                highlightthickness=0,
                                background=bg_color)
        self.canvas.pack(fill="both", expand=True)

        # Center image inside canvas and store the item ID
        self.image_on_canvas = self.canvas.create_image(canvas_w//2, canvas_h//2, anchor="center", image=self.photo_image)

        # Update scrollregion to match image size in case it's larger
        self.canvas.config(scrollregion=(0, 0, display_img.width, display_img.height))

        # Bind resize event to recenter the image
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        
        # Informações da imagem e botão de fechar
        bottom_frame = ctk.CTkFrame(main_frame)
        bottom_frame.pack(fill="x", pady=(10, 0))
        if self.ui_helper:
            self.ui_helper.style_frame(bottom_frame) # Estilizar o frame de rodapé
        
        # Frame para informações em múltiplas linhas à esquerda
        info_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="y", padx=padding_small, pady=padding_small)
        
        # Exibir dimensões da imagem
        size_text = f"Tamanho: {self.image.width}x{self.image.height} pixels"
        size_label = ctk.CTkLabel(info_frame, text=size_text)
        size_label.pack(anchor="w")
        if self.ui_helper:
            self.ui_helper.style_label(size_label, "small")

        # Exibir formato e tamanho em KB
        # Acessar image_manager através do parent (ImageSelectionDialog)
        image_manager = self.parent.image_manager 
        file_path = os.path.join(image_manager.temp_dir,
                               f"{self.image_id}.{image_manager.default_format}")
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / 1024
            format_text = f"Formato: {image_manager.default_format.upper()}, Tamanho: {file_size:.1f} KB"
            format_label = ctk.CTkLabel(info_frame, text=format_text)
            format_label.pack(anchor="w")
            if self.ui_helper:
                self.ui_helper.style_label(format_label, "small")
        
        # Exibir informação de escala se a imagem foi redimensionada
        if hasattr(self, 'scaled_display') and self.scaled_display:
            scale_text = f"Exibindo em {self.scale_percent}% do tamanho original"
            scale_label = ctk.CTkLabel(info_frame, text=scale_text) # font=("Roboto", 12, "italic") - CTkLabel não suporta 'italic' diretamente na font tuple
            scale_label.pack(anchor="w")
            if self.ui_helper:
                self.ui_helper.style_label(scale_label, "small") # Pode-se criar uma variante de estilo para itálico se necessário
        
        # Exibir nome do arquivo (se fornecido)
        if self.filename:
            filename_text = f"Nome do arquivo: {self.filename}"
            filename_label = ctk.CTkLabel(info_frame, text=filename_text)
            filename_label.pack(anchor="w")
            if self.ui_helper:
                self.ui_helper.style_label(filename_label, "small")
        
        close_button = ctk.CTkButton(bottom_frame, text="Fechar", command=self.destroy, width=80)
        close_button.pack(side="right", padx=10, pady=5)
        
        # Aplicar estilo ao botão se possível
        if self.ui_helper:
            self.ui_helper.style_button(close_button, "secondary")

        # Bind Escape key to close window
        self.bind("<Escape>", lambda e: self.destroy())

    def _on_canvas_resize(self, event):
        """Recenter the image when the canvas is resized."""
        # Get current canvas size
        canvas_w = event.width
        canvas_h = event.height
        
        # Move the image to the new center
        self.canvas.coords(self.image_on_canvas, canvas_w // 2, canvas_h // 2)
