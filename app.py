import os
import threading
import yaml
import customtkinter as ctk
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Dict, List, Optional, Callable

from logger import setup_logger
from clipboard_monitor import ClipboardMonitor
from image_manager import ImageManager


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
        
        # Frame para informações em múltiplas linhas
        info_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="y", padx=5, pady=5)
        
        # Exibir dimensões da imagem
        size_text = f"Tamanho: {self.image.width}x{self.image.height} pixels"
        ctk.CTkLabel(info_frame, text=size_text, font=("Roboto", 12)).pack(anchor="w")
        
        # Exibir formato e tamanho em KB
        file_path = os.path.join(self.parent.image_manager.temp_dir, 
                               f"{self.image_id}.{self.parent.image_manager.default_format}")
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / 1024
            format_text = f"Formato: {self.parent.image_manager.default_format.upper()}, Tamanho: {file_size:.1f} KB"
            ctk.CTkLabel(info_frame, text=format_text, font=("Roboto", 12)).pack(anchor="w")
        
        # Exibir informação de escala se a imagem foi redimensionada
        if hasattr(self, 'scaled_display') and self.scaled_display:
            scale_text = f"Exibindo em {self.scale_percent}% do tamanho original"
            ctk.CTkLabel(info_frame, text=scale_text, font=("Roboto", 12, "italic")).pack(anchor="w")
        
        # Exibir nome do arquivo (se fornecido)
        if self.filename:
            filename_text = f"Nome do arquivo: {self.filename}"
            ctk.CTkLabel(info_frame, text=filename_text, font=("Roboto", 12)).pack(anchor="w")
        
        # Botão de fechar
        close_btn = ctk.CTkButton(
            bottom_frame, 
            text="Fechar", 
            command=self.destroy,
            width=100,
            font=("Roboto", 12, "bold")
        )
        close_btn.pack(side="right", padx=10, pady=5)


class FloatingCaptureWindow(ctk.CTkToplevel):
    """
    Floating mini-window that shows capture progress and provides a stop button.
    Appears when capturing is active, while main window is minimized.
    """
    
    def __init__(self, parent, stop_callback: Callable, border_color="#32CD32", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.parent = parent
        self.stop_callback = stop_callback
        self.logger = parent.logger
        self.border_color = border_color  # Cor da borda (verde por padrão)
        self.border_width = 2  # Largura da borda em pixels
        
        # Configure window
        self.title("Capturando")  # Title still set for taskbar
        self.geometry("300x80")  # Small window size
        self.resizable(False, False)  # Fixed size
        self.attributes("-topmost", True)  # Always on top
        self.overrideredirect(True)  # Remove window decoration (title bar)
        
        # Center the window on screen
        self.center_window()
        
        # Since we have no title bar to close the window,
        # bind an escape key handler as an alternative
        self.bind("<Escape>", lambda e: self.stop_callback())
        
        # Variables for window dragging
        self.drag_data = {"x": 0, "y": 0, "dragging": False}
        
        # Setup UI
        self.setup_ui()
        
        # Initialize capture count
        self.capture_count = 0
        self.last_image_size = "N/A"
    
    def center_window(self):
        """Center window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_ui(self):
        """Setup the mini-window UI"""
        # Primeiro frame para a borda colorida
        border_frame = ctk.CTkFrame(self, fg_color=self.border_color)
        border_frame.pack(fill="both", expand=True)
        
        # Main container com padding menor para mostrar a borda
        self.main_frame = ctk.CTkFrame(border_frame, corner_radius=10, fg_color="#202060", border_width=self.border_width, border_color=self.border_color)  # Debug: Dark blue
        self.main_frame.pack(fill="both", expand=True, padx=self.border_width, pady=self.border_width)
        
        # Make the entire window draggable
        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<ButtonRelease-1>", self.stop_drag)
        self.bind("<B1-Motion>", self.on_drag)
        
        # Info frame (top)
        self.content_frame = ctk.CTkFrame(self.main_frame, corner_radius=8, fg_color="#303070")  # Debug: Slightly lighter blue
        info_frame = self.content_frame # Use self.content_frame for subsequent packing
        info_frame.pack(fill="x", pady=(0, 5))
        
        # Capture count
        self.count_label = ctk.CTkLabel(info_frame, text="Capturas: 0")
        self.count_label.pack(side="left")
        
        # Image size
        self.size_label = ctk.CTkLabel(info_frame, text="Tamanho: N/A")
        self.size_label.pack(side="right")
        
        # Button frame (bottom)
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x", pady=(5, 0))
        
        # Stop button
        self.finish_button = ctk.CTkButton(
            button_frame, 
            text="Pausar Captura", 
            command=self.stop_callback,
            fg_color="#dc3545",
            hover_color="#c82333",
            corner_radius=5,
            height=30
        )
        self.finish_button.pack(fill="x")
    
    def start_drag(self, event):
        """Start window dragging operation"""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.drag_data["dragging"] = True
    
    def stop_drag(self, event):
        """Stop window dragging operation"""
        self.drag_data["dragging"] = False
    
    def on_drag(self, event):
        """Move window during drag operation"""
        if self.drag_data["dragging"]:
            # Calculate the distance moved
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            
            # Move window by this offset
            new_x = self.winfo_x() + dx
            new_y = self.winfo_y() + dy
            self.geometry(f"+{new_x}+{new_y}")
    
    def update_capture_info(self, count: int, image_width: int = None, image_height: int = None):
        """Update capture count and image size information"""
        self.capture_count = count
        self.count_label.configure(text=f"Capturas: {count}")
        
        if image_width is not None and image_height is not None:
            self.last_image_size = f"{image_width}x{image_height}"
            self.size_label.configure(text=f"Tamanho: {self.last_image_size}")


# End of FloatingCaptureWindow class


class ImageSelectionDialog(ctk.CTkToplevel):
    """
    Modal dialog for selecting images to save.
    """
    
    def __init__(self, parent, image_manager: ImageManager, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.parent = parent
        self.image_manager = image_manager
        self.logger = parent.logger
        self.images_saved = False  # Track if images were saved
        self.has_unsaved_changes = False  # Track if order has changed but not applied
        self.original_order = []  # Original order of images
        self.current_order = []  # Current order after drag and drop
        self.drag_source = None  # Current thumbnail being dragged
        self.drop_target = None  # Where the thumbnail will be dropped
        
        # Configure window
        self.title("Selecionar Imagens")
        self.minsize(600, 400)
        self.resizable(True, True)
        self.geometry("800x600")
        window_width = 800
        window_height = 600
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.grab_set()  # Make modal
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Armazenar referências a todos os widgets importantes
        self.thumbnails = {}
        self.row_frames = []
        
        # Initialize UI
        self.setup_ui()
        self.load_thumbnails()
    
    def setup_ui(self):
        """Set up the dialog UI"""
        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header with instructions
        header_label = ctk.CTkLabel(self.main_frame, text="Selecione as imagens para salvar:", 
                                 font=("Roboto", 14, "bold"))
        header_label.pack(anchor="w", padx=5, pady=5)
        
        # Checkbox for select all
        self.select_all_var = tk.BooleanVar(value=True)
        select_all_cb = ctk.CTkCheckBox(self.main_frame, text="Selecionar Tudo", 
                                      variable=self.select_all_var,
                                      command=self.toggle_select_all)
        select_all_cb.pack(anchor="w", padx=5, pady=5)
        
        # Create scrollable frame for thumbnails - usar orientação vertical
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame, orientation="vertical")
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Prefix entry frame
        prefix_frame = ctk.CTkFrame(self.main_frame)
        prefix_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkLabel(prefix_frame, text="Prefixo:").pack(side="left", padx=5)
        
        self.prefix_entry = ctk.CTkEntry(prefix_frame, width=200)
        self.prefix_entry.pack(side="left", padx=5)
        self.prefix_entry.insert(0, self.parent.prefix_entry.get())
        
        # Bottom button frame
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Add ZIP checkbox
        self.create_zip_var = tk.BooleanVar(value=False)
        self.create_zip_checkbox = ctk.CTkCheckBox(button_frame, text="Criar arquivo ZIP", 
                                variable=self.create_zip_var)
        self.create_zip_checkbox.pack(side="left", padx=5)
        
        # Add buttons
        self.cancel_button = ctk.CTkButton(button_frame, text="Voltar", command=self.on_close)
        self.cancel_button.pack(side="right", padx=5)
        
        self.save_button = ctk.CTkButton(button_frame, text="Salvar Selecionadas", command=self.on_save)
        self.save_button.pack(side="right", padx=5)
        
        # Add apply changes button
        self.apply_button = ctk.CTkButton(
            button_frame, 
            text="Aplicar Alterações", 
            command=self.apply_changes,
            state="disabled",
            fg_color="#17a2b8",
            hover_color="#138496"
        )
        self.apply_button.pack(side="right", padx=5)
        
        # Dictionary to store thumbnail data
        self.thumbnails: Dict[str, Dict] = {}
    
    def toggle_select_all(self):
        """Toggle selection state of all images"""
        select_all = self.select_all_var.get()
        
        # Update checkboxes
        for thumb_data in self.thumbnails.values():
            thumb_data['var'].set(select_all)
        
        # Update image manager selection
        for image_id in self.thumbnails:
            self.image_manager.set_image_selected(image_id, select_all)
    
    def load_thumbnails(self):
        """Load and display image thumbnails"""
        # Clear existing thumbnails if any
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        # Clear the thumbnails dictionary to avoid stale references
        self.thumbnails = {}
        
        # Get all images from manager
        image_ids = self.image_manager.get_all_image_ids()
        if not image_ids:
            ctk.CTkLabel(self.scroll_frame, text="Nenhuma imagem capturada", 
                      font=("Roboto", 16)).pack(pady=50)
            return
            
        # Initialize ordering if needed
        if not self.original_order:
            self.original_order = image_ids.copy()
        
        # Initialize or update current_order if needed
        if not self.current_order or set(self.current_order) != set(image_ids):
            # If images were added or removed, reset the current order
            self.current_order = image_ids.copy()
        
        # Criar um container principal para organizar as miniaturas em grade
        main_container = ctk.CTkFrame(self.scroll_frame)
        main_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configurar parâmetros das miniaturas
        thumbnail_size = self.image_manager.image_config.get("thumbnail_size", 100)
        padding = 10
        max_columns = 3  # Máximo de 3 miniaturas por linha
        
        # Armazenar referências para garantir que não sejam coletadas pelo garbage collector
        self.thumbnails_container = main_container


        # Criar frames para cada linha de miniaturas
        current_row = None
        current_col = 0
        
        # Use current_order instead of image_ids to respect the custom ordering
        for idx, image_id in enumerate(self.current_order):
            try:
                # Criar nova linha se necessário
                if current_col == 0 or current_col >= max_columns:
                    current_row = ctk.CTkFrame(main_container)
                    current_row.pack(fill="x", expand=False, pady=(0, padding))
                    current_col = 0
                
                # Tentar carregar a imagem do arquivo
                image_path = self.image_manager.get_image_path(image_id)
                if not image_path or not os.path.exists(image_path):
                    continue
                    
                # Carregar a imagem do arquivo
                original_image = Image.open(image_path)
                if not original_image:
                    continue
                
                thumbnail = self.image_manager.create_thumbnail(original_image)
                
                # Calcular largura para cada miniatura (distribuir igualmente em 3 colunas)
                thumb_width = (main_container.winfo_width() // max_columns) - (padding * 2)
                if thumb_width < thumbnail_size + 40:  # Garantir largura mínima
                    thumb_width = thumbnail_size + 40
                
                # Altura fixa para cada miniatura
                thumb_height = thumbnail_size + 90  # Espaço para info e imagem
                
                # Criar frame para cada miniatura
                thumb_frame = ctk.CTkFrame(current_row, width=thumb_width, height=thumb_height)
                thumb_frame.pack(side="left", padx=padding, pady=padding, fill="both", expand=True)
                thumb_frame.pack_propagate(False)  # Manter tamanho fixo
                
                # Store image_id as attribute for drag and drop identification
                thumb_frame.image_id = image_id
                
                # Get image metadata
                image_info = self.image_manager.get_image_metadata(image_id)
                size_info = f"{image_info['width']}x{image_info['height']}"
                file_number = idx + 1
                # Format with leading zero for numbers < 10
                seq_number = str(file_number).zfill(2)
                prefix = self.prefix_entry.get().strip() or self.image_manager.default_prefix
                filename = f"{seq_number}_{prefix}.{self.image_manager.default_format}"
                
                # Adicionar informações ACIMA da miniatura
                info_frame = ctk.CTkFrame(thumb_frame, fg_color="transparent")
                info_frame.pack(fill="x", padx=5, pady=(5, 0))

                # Bind drag events to info_frame as well to improve UX
                # The image_id captured here corresponds to the thumbnail this info_frame belongs to.
                info_frame.bind("<ButtonPress-1>", lambda event, id=image_id: self.start_drag(event, id))
                info_frame.bind("<B1-Motion>", lambda event, id=image_id: self.perform_drag_motion(event, id))
                info_frame.bind("<ButtonRelease-1>", lambda event, id=image_id: self.end_drag(event, id))
                
                # Checkbox para seleção
                check_var = tk.BooleanVar(value=True)
                check = ctk.CTkCheckBox(info_frame, text="", variable=check_var, 
                                     command=lambda id=image_id, var=check_var: self.on_thumbnail_select(id, var))
                check.pack(side="left", padx=2)
                
                # Número do arquivo
                file_label = ctk.CTkLabel(info_frame, text=f"#{file_number}", 
                                       font=("Roboto", 10, "bold"))
                file_label.pack(side="left", padx=2)
                
                # Tamanho da imagem
                size_label = ctk.CTkLabel(info_frame, text=f"{size_info}", 
                                      font=("Roboto", 10))
                size_label.pack(side="right", padx=2)
                
                # Create PhotoImage from thumbnail
                thumbnail_tk = ImageTk.PhotoImage(thumbnail)
                
                # Create label for thumbnail
                label = ctk.CTkLabel(thumb_frame, text="", image=thumbnail_tk)
                label.image = thumbnail_tk  # Keep reference to prevent garbage collection
                label.pack(padx=5, pady=5, expand=True, fill="both")
                
                # Criar uma função específica para este ID de imagem para o clique duplo
                def on_double_click_closure(img_id=image_id):
                    def handler(event):
                        self.on_thumbnail_double_click(img_id)
                    return handler
                
                # Set up double-click event for thumbnail usando a closure
                label.bind("<Double-Button-1>", on_double_click_closure())
                
                # Setup drag and drop events for reordering
                # Using lambdas with default arguments to capture the current image_id
                thumb_frame.bind("<ButtonPress-1>", lambda event, id=image_id: self.start_drag(event, id))
                thumb_frame.bind("<B1-Motion>", lambda event, id=image_id: self.perform_drag_motion(event, id))
                thumb_frame.bind("<ButtonRelease-1>", lambda event, id=image_id: self.end_drag(event, id))
                
                # Also bind drag events to the image label to ensure good UX
                label.bind("<ButtonPress-1>", lambda event, id=image_id: self.start_drag(event, id))
                label.bind("<B1-Motion>", lambda event, id=image_id: self.perform_drag_motion(event, id))
                label.bind("<ButtonRelease-1>", lambda event, id=image_id: self.end_drag(event, id))
                
                # Adicionar tooltip com info completa ao passar o mouse
                tooltip_text = f"Tamanho: {size_info}\nArquivo: {filename}\nClique e arraste para reordenar"
                label.tooltip_text = tooltip_text
                
                # Store reference to all important objects to prevent garbage collection
                self.thumbnails[image_id] = {
                    'var': check_var,
                    'frame': thumb_frame,
                    'label': label,
                    'image': thumbnail_tk,
                    'size_label': size_label,
                    'file_label': file_label,
                    'check': check,
                    'info_frame': info_frame
                }
                
                # Avançar para a próxima coluna
                current_col += 1
                
            except Exception as e:
                self.logger.error(f"Erro ao carregar miniatura para imagem {image_id}: {e}")
    
    def on_thumbnail_select(self, image_id: str, var: tk.BooleanVar):
        """Handle individual thumbnail selection"""
        is_selected = var.get()
        self.image_manager.set_image_selected(image_id, is_selected)
        
        # Update select all checkbox if needed
        if not is_selected and self.select_all_var.get():
            self.select_all_var.set(False)
            
    def on_thumbnail_double_click(self, image_id: str):
        """Handle double-click on thumbnail to open image viewer"""
        try:
            # Get image path and metadata from image manager
            image_path = self.image_manager.get_image_path(image_id)
            if not image_path or not os.path.exists(image_path):
                self.logger.error(f"Arquivo de imagem não encontrado: {image_path}")
                messagebox.showerror("Erro", "Arquivo de imagem não encontrado.")
                return
            
            # Get the filename that would be used when saving
            image_ids = list(self.thumbnails.keys())
            try:
                image_index = image_ids.index(image_id) + 1
            except ValueError:
                # Fallback se o ID não estiver na lista (não deveria acontecer)
                image_index = 1
            
            # Format with leading zero for numbers < 10
            prefix = self.prefix_entry.get().strip() or self.image_manager.default_prefix
            filename = f"{image_index:02d}_{prefix}.{self.image_manager.default_format}"
                
            # Open image viewer dialog with additional info
            self.logger.info(f"Opening image viewer for image {image_id}, path: {image_path}")
            viewer = ImageViewerDialog(self, image_path, image_id, filename)
            
        except Exception as e:
            self.logger.error(f"Error opening image viewer: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir a imagem: {str(e)}")
    
    def on_save(self):
        """Save selected images"""
        try:
            # Get selected images
            selected_ids = self.image_manager.get_selected_image_ids()
            if not selected_ids:
                messagebox.showinfo("Nenhuma Seleção", "Nenhuma imagem selecionada para salvar.")
                return
            
            # Get save directory
            prefix = self.parent.prefix_entry.get().strip()
            directory = filedialog.askdirectory(title="Selecionar Pasta para Salvar")
            
            if not directory:
                return  # User cancelled
            
            # Get ZIP option
            create_zip = self.create_zip_var.get()
            
            # Save images with current order for proper numbering
            saved_files = self.image_manager.save_images(prefix, directory, create_zip, custom_order=self.current_order)
            
            if saved_files:
                # Show success message
                count = len(saved_files)
                msg = f"{count} imagens salvas com sucesso em:\n{directory}"
                if create_zip:
                    msg += "\nArquivo ZIP criado."
                messagebox.showinfo("Sucesso", msg)
                
                # Mark that images were saved
                self.images_saved = True
                
                # Close dialog
                self.on_close()
            else:
                messagebox.showerror("Erro", "Nenhuma imagem foi salva. Verifique as permissões da pasta.")
                
        except Exception as e:
            self.parent.logger.error(f"Error saving images: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar imagens: {str(e)}")
    
    def start_drag(self, event, image_id):
        """Start dragging a thumbnail"""
        if image_id in self.thumbnails:
            self.drag_source = image_id
            # Visual feedback - change background color of the dragged thumbnail
            self.thumbnails[image_id]['frame'].configure(fg_color="#3a7ebf")
            self.logger.debug(f"Started dragging thumbnail {image_id}")
    
    def perform_drag_motion(self, event, originating_widget_image_id):
        """Handle mouse motion during a drag operation. Identifies drop target."""
        if not self.drag_source:
            return

        # Determine the widget currently under the mouse cursor.
        # event.x and event.y are relative to the widget that received the event (originating_widget_image_id's frame/label).
        # We need to find which thumbnail frame the absolute mouse position (event.x_root, event.y_root) is over.
        mouse_x_root = event.x_root
        mouse_y_root = event.y_root

        new_potential_drop_target = None
        for image_id, data in self.thumbnails.items():
            frame = data['frame']
            if not frame.winfo_exists(): # Skip if frame somehow got destroyed
                continue

            frame_x = frame.winfo_rootx()
            frame_y = frame.winfo_rooty()
            frame_width = frame.winfo_width()
            frame_height = frame.winfo_height()

            # Check if the absolute mouse position is within this frame's bounds
            if (frame_x <= mouse_x_root < frame_x + frame_width and
                frame_y <= mouse_y_root < frame_y + frame_height):
                if image_id != self.drag_source: # Can't drop onto itself
                    new_potential_drop_target = image_id
                break # Found the frame under the mouse

        # Update drop_target and visual feedback if it has changed
        if new_potential_drop_target != self.drop_target:
            # Reset visual feedback for the old drop_target (if any)
            if self.drop_target and self.drop_target in self.thumbnails and self.thumbnails[self.drop_target]['frame'].winfo_exists():
                self.thumbnails[self.drop_target]['frame'].configure(fg_color="transparent") # Or original theme color
            
            self.drop_target = new_potential_drop_target
            self.logger.debug(f"Dragging. Potential drop target: {self.drop_target}")

            # Apply visual feedback for the new drop_target (if any)
            if self.drop_target and self.drop_target in self.thumbnails and self.thumbnails[self.drop_target]['frame'].winfo_exists():
                self.thumbnails[self.drop_target]['frame'].configure(fg_color="#2a5e8f") # Highlight color
        
    # The old on_drag_over might be removed or repurposed later if not needed.
    # For now, we keep it but it's not bound to <Enter> on draggable items anymore.
    def on_drag_over(self, event, target_image_id):
        """Handle drag over a thumbnail (currently not used by individual thumbnail <Enter> events)"""
        self.logger.debug(f"on_drag_over (not primary for DND): source={self.drag_source}, target={target_image_id}")
        # Original logic can remain here if used by other parts, or be removed if fully superseded.
        if self.drag_source and target_image_id != self.drag_source:
            # This logic is now primarily in perform_drag_motion
            pass
    
    def end_drag(self, event, _event_target_id): # _event_target_id is from the widget that received ButtonRelease
        """End dragging and reorder thumbnails if needed"""
        # Use self.drop_target, which is set by on_drag_over, as the definitive drop location.
        if self.drag_source and self.drop_target and self.drag_source != self.drop_target:
            self.logger.debug(f"Dropping {self.drag_source} onto {self.drop_target}")
            
            # Find positions in current order
            try:
                source_idx = self.current_order.index(self.drag_source)
                target_idx = self.current_order.index(self.drop_target)
                
                # Reorder the current_order list
                item = self.current_order.pop(source_idx)
                self.current_order.insert(target_idx, item)
                
                # Set unsaved changes flag
                if self.current_order != self.original_order:
                    self.has_unsaved_changes = True
                    self.apply_button.configure(state="normal")
                
                # Reload thumbnails to reflect new order
                self.load_thumbnails()
                
            except ValueError as e:
                self.logger.error(f"Error reordering thumbnails: {e}")
        
        # Reset drag state and visual feedback
        for img_id, data in self.thumbnails.items():
            data['frame'].configure(fg_color="transparent") # Or reset to original theme color if 'transparent' is problematic
        
        self.drag_source = None
        self.drop_target = None # Reset drop_target as well
        self.drop_target = None
    
    def apply_changes(self):
        """Apply the reordering changes"""
        if self.has_unsaved_changes:
            self.logger.info("Applying image reordering changes")
            # Update the original order to match the current order
            self.original_order = self.current_order.copy()
            self.has_unsaved_changes = False
            self.apply_button.configure(state="disabled")
            
            # Reload thumbnails to update file numbers
            self.load_thumbnails()
            
            messagebox.showinfo("Sucesso", "Alterações de ordenamento aplicadas com sucesso!")
            
    def on_close(self):
        """Handle dialog close"""
        # Check for unsaved changes
        if self.has_unsaved_changes:
            response = messagebox.askyesnocancel(
                "Alterações não salvas",
                "Existem alterações na ordem das imagens não aplicadas. Deseja aplicar antes de sair?",
                icon="warning"
            )
            
            if response is None:  # Cancel
                return
            elif response:  # Yes - apply changes
                self.apply_changes()
        
        self.destroy()


class ClipboardImageApp(ctk.CTk):
    """
    Main application window for clipboard image capture.
    """
    
    def __init__(self):
        super().__init__()
        
        # Load configuration
        with open('config.yml', 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Setup logger
        self.logger = setup_logger()
        
        # Create image manager
        self.image_manager = ImageManager()
        self.image_manager.set_logger(self.logger)
        
        # Limpar os arquivos temporários na inicialização
        files_cleaned = self.image_manager.clean_temp_files()
        self.logger.info(f"Cleaned {files_cleaned} temporary files on startup")
        
        # Create clipboard monitor
        self.clipboard_monitor = ClipboardMonitor(callback=self.on_image_captured)
        self.clipboard_monitor.set_logger(self.logger)
        
        # Limpar o clipboard na inicialização
        self.clipboard_monitor.clear_clipboard()
        self.logger.info("Clipboard cleared on startup")
        
        # UI attributes
        self.current_image = None
        self.current_image_tk = None
        self.monitoring = False
        self.floating_window = None
        self.capture_count = 0  # Persistente durante toda a sessão do aplicativo
        self.has_unsaved_images = False  # Controla se há imagens não salvas
        
        # Configure window
        app_config = self.config.get('application', {})
        self.title(app_config.get('title', 'Captura Clipboard'))
        self.geometry(f"{app_config.get('width', 800)}x{app_config.get('height', 600)}")
        self.minsize(600, 400)
        
        # Set appearance mode
        ctk.set_appearance_mode(app_config.get('theme', 'dark'))
        
        # Initialize UI
        self.setup_ui()
        
        # Other initialization
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.logger.info("Application started")
    
    def setup_ui(self):
        """Set up the main application UI"""
        # Main frame with padding
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create controls frame at top
        self.controls_frame = ctk.CTkFrame(self.main_frame)
        self.controls_frame.pack(fill="x", padx=10, pady=10)
        
        # Prefix input
        prefix_label = ctk.CTkLabel(self.controls_frame, text="Prefixo:")
        prefix_label.pack(side="left", padx=5)
        
        self.prefix_entry = ctk.CTkEntry(self.controls_frame, width=200)
        self.prefix_entry.insert(0, self.image_manager.default_prefix)
        self.prefix_entry.pack(side="left", padx=5)
        
        # Control buttons
        self.start_button = ctk.CTkButton(
            self.controls_frame, 
            text="Iniciar Captura", 
            command=self.start_monitoring,
            fg_color="#28a745",
            hover_color="#218838"
        )
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ctk.CTkButton(
            self.controls_frame, 
            text="Pausar Captura", 
            command=self.stop_monitoring,
            state="disabled",
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.stop_button.pack(side="left", padx=5)
        
        self.save_button = ctk.CTkButton(
            self.controls_frame, 
            text="Verificar Imagens", 
            command=self.show_save_dialog,
            state="disabled",
            fg_color="#28a745",
            hover_color="#218838"
        )
        self.save_button.pack(side="left", padx=5)
        
        self.exit_button = ctk.CTkButton(
            self.controls_frame, 
            text="Sair", 
            command=self.on_close,
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        self.exit_button.pack(side="right", padx=5)
        
        # Status label
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Status: Pronto")
        self.status_label.pack(side="left", padx=5)
        
        self.image_count_label = ctk.CTkLabel(self.status_frame, text="Imagens: 0")
        self.image_count_label.pack(side="right", padx=5)
        
        # Create image preview frame
        self.preview_frame = ctk.CTkFrame(self.main_frame)
        self.preview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.preview_label = ctk.CTkLabel(self.preview_frame, text="Nenhuma imagem capturada")
        self.preview_label.pack(fill="both", expand=True)
    
    def start_monitoring(self):
        """Start clipboard monitoring"""
        if self.monitoring:
            return
        
        # Apenas atualizar o estado, sem limpar imagens existentes
        self.monitoring = True
        
        # Resetar a visualização do preview, mas manter as imagens já capturadas
        if self.current_image is not None:
            self.preview_label.configure(text="")
        else:
            self.preview_label.configure(text="Aguardando Capturas...")
            
        # Atualizar contador com o total atual (mantendo imagens existentes)
        total_images = len(self.image_manager.get_all_image_ids())
        self.capture_count = total_images  # Manter o contador acumulado
        self.image_count_label.configure(text=f"Imagens: {total_images} (Total: {self.capture_count})")
        
        # Update button states
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.save_button.configure(state="disabled" if total_images == 0 else "normal")
        
        # Start the monitor
        self.clipboard_monitor.start()
        
        # Create floating window and minimize main window
        self.has_unsaved_images = total_images > 0
        self.floating_window = FloatingCaptureWindow(self, self.stop_monitoring, border_color="#32CD32")  # Verde claro
        self.after(100, self.iconify)  # Minimize main window after a short delay
        
    def restore(self):
        """Restore main window"""
        self.deiconify()
        
    def show_floating_window(self):
        """Show floating mini window"""
        if hasattr(self, 'floating_window') and self.floating_window is not None:
            self.floating_window.destroy()
            
        # Create floating window
        self.floating_window = FloatingCaptureWindow(self, stop_callback=self.stop_monitoring)
        
        self.logger.info("Floating capture window opened")
    
    def stop_monitoring(self):
        """Stop clipboard monitoring"""
        self.clipboard_monitor.stop()
        self.monitoring = False
        
        # Close floating window if exists
        if hasattr(self, 'floating_window') and self.floating_window is not None:
            self.floating_window.destroy()
            self.floating_window = None
            self.logger.info("Floating capture window closed")
            
        # Restore main window
        self.restore()
        
        # Update UI
        self.status_label.configure(text="Status: Monitoramento parado")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        
        self.logger.info("Stopped clipboard monitoring")
    
    def on_image_captured(self, image: Image.Image):
        """
        Callback function for when a new image is captured from clipboard
        """
        if not image:
            return
        
        try:
            # Add to image manager
            image_id = self.image_manager.add_image(image)
            
            # Increment capture count for the entire session
            self.capture_count += 1
            self.has_unsaved_images = True
            
            # Create a resized preview
            preview = self.image_manager.resize_for_preview(image)
            
            # Convert to PhotoImage for display
            self.current_image = preview
            self.current_image_tk = ImageTk.PhotoImage(preview)
            
            # Update preview in main window
            self.preview_label.configure(text="", image=self.current_image_tk)
            
            # Enable save button if this is the first image
            if len(self.image_manager.get_all_image_ids()) == 1:
                self.save_button.configure(state="normal")
            
            # Get current image count and size
            current_images = len(self.image_manager.get_all_image_ids())
            width, height = image.size
            
            # Update image count in main window - show both current batch and total session
            self.image_count_label.configure(
                text=f"Imagens: {current_images} (Total: {self.capture_count})"
            )
            
            # Update floating window if active
            if hasattr(self, 'floating_window') and self.floating_window is not None:
                self.floating_window.update_capture_info(self.capture_count, width, height)
            
            self.logger.info(f"Displayed captured image with ID: {image_id} | Size: {width}x{height}")
            
        except Exception as e:
            self.logger.error(f"Error processing captured image: {e}")
    
    def show_save_dialog(self):
        """Show the image selection dialog"""
        # Check if we have any images
        if not self.image_manager.get_all_image_ids():
            messagebox.showinfo("Nenhuma Imagem", "Nenhuma imagem capturada para verificar.")
            return
        
        # Create and show dialog
        dialog = ImageSelectionDialog(self, self.image_manager)
        self.wait_window(dialog)
        
        # After dialog is closed, check if images were saved
        if hasattr(dialog, 'images_saved') and dialog.images_saved:
            self.has_unsaved_images = False
    
    def on_close(self):
        """Handle application close"""
        try:
            # Stop monitoring if active
            if self.monitoring:
                self.stop_monitoring()
                
            # Close floating window if exists
            if hasattr(self, 'floating_window') and self.floating_window is not None:
                self.floating_window.destroy()
                self.floating_window = None
            
            # Check if there are unsaved images
            if self.has_unsaved_images and len(self.image_manager.get_all_image_ids()) > 0:
                # Ask for confirmation before closing
                result = messagebox.askyesno(
                    "Sair sem salvar", 
                    "Existem imagens capturadas que não foram salvas. Deseja sair sem salvar?"
                )
                
                if result:  # User confirmed exit without saving
                    # Remove all temporary images
                    self.image_manager.clear_images()
                    self.logger.info("Discarded unsaved images before exit")
                    self.logger.info("Application closed")
                    self.quit()
                    self.destroy()
                else:  # User cancelled exit
                    return  # Don't close the app
            else:
                # No unsaved images, just close
                self.logger.info("Application closed")
                self.quit()
                self.destroy()
                
        except Exception as e:
            self.logger.error(f"Error during application close: {e}")


if __name__ == "__main__":
    app = ClipboardImageApp()
    app.mainloop()
