import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk

class ImageViewerDialog(ctk.CTkToplevel):
    """
    Dialog for viewing images in larger size
    """
    
    def __init__(self, parent, image_path: str, image_id: str, filename: str=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        # Store reference to parent and ID
        self.parent = parent
        self.image_id = image_id
        self.filename = filename
        
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
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        self.focus_set()
    
    def setup_ui(self, display_width, display_height):
        """Setup image viewer UI"""
        # Container frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create a scrollable frame for the image
        # Usar orientação "both" para permitir rolagem horizontal e vertical se necessário
        scroll_frame = ctk.CTkScrollableFrame(main_frame, orientation="vertical")
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
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
        
        # Criar um canvas para exibir a imagem com rolagem se necessário
        self.canvas = tk.Canvas(scroll_frame, 
                               width=min(display_img.width, display_width),
                               height=min(display_img.height, display_height),
                               highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Exibir a imagem no canvas
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo_image)
        
        # Configurar o canvas para rolagem
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
        # Informações da imagem e botão de fechar
        bottom_frame = ctk.CTkFrame(main_frame)
        bottom_frame.pack(fill="x", pady=(10, 0))
        
        # Frame para in
        # (O restante do código da classe continua aqui, 
        # mas foi truncado na visualização anterior.
        # É importante copiar a classe INTEIRA)
        # ... (restante do método setup_ui e da classe ImageViewerDialog)
        # Adicionando o restante do código que faltava na visualização:
        info_text = f"ID: {self.image_id} | Nome: {self.filename if self.filename else 'N/A'}"
        if self.scaled_display:
            info_text += f" | Exibindo em {self.scale_percent}% do tamanho original"
        
        info_label = ctk.CTkLabel(bottom_frame, text=info_text)
        info_label.pack(side="left", padx=10)
        
        close_button = ctk.CTkButton(bottom_frame, text="Fechar", command=self.destroy, width=80)
        close_button.pack(side="right", padx=10, pady=5)

        # Bind Escape key to close window
        self.bind("<Escape>", lambda e: self.destroy())
