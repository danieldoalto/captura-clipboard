import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from image_viewer_dialog import ImageViewerDialog # Import ImageViewerDialog
from typing import Dict, List, Callable # Assuming List and Callable might be used in full class
import os
import shutil

# Placeholder for ImageManager import, will be resolved when ImageManager is moved
# from image_manager import ImageManager 
# For now, to avoid error if image_manager.py doesn't exist yet, we can't import it.
# This will be an issue if ImageManager is used directly as a type hint without 'from __future__ import annotations'
# or stringified type hints if ImageManager is not yet defined.
# Let's assume ImageManager will be available in the global scope or imported from app for now,
# and we'll fix this when refactoring app.py's imports.

class ImageSelectionDialog(ctk.CTkToplevel):
    """
    Modal dialog for selecting images to save.
    """
    
    def __init__(self, parent, image_manager, *args, **kwargs): # image_manager: ImageManager
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
        # Clear existing thumbnails and frames
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.thumbnails.clear()
        self.row_frames.clear()
        
        self.original_order = self.image_manager.get_all_image_ids()
        self.current_order = list(self.original_order) # Make a copy
        
        image_ids = self.image_manager.get_all_image_ids()
        if not image_ids:
            ctk.CTkLabel(self.scroll_frame, text="Nenhuma imagem capturada.").pack(pady=20)
            return

        # Determine number of columns based on window width (responsive)
        # Max thumbnail width + padding
        thumbnail_size_val = self.image_manager.image_config.get('thumbnail_size', 128) # Default to 128 if not found
        thumb_max_width = thumbnail_size_val + 20 
        num_cols = max(1, self.scroll_frame.winfo_width() // thumb_max_width)
        
        current_row_frame = None
        
        for idx, image_id in enumerate(self.current_order):
            img_data = self.image_manager.get_image_metadata(image_id)
            if not img_data or 'path' not in img_data or not img_data['path']:
                self.logger.warning(f"Invalid or missing metadata/path for image_id: {image_id}. Data: {img_data}")
                continue
            
            # Additional check to ensure the path actually exists before trying to open
            if not os.path.exists(img_data['path']):
                self.logger.warning(f"Image path does not exist for image_id: {image_id}. Path: {img_data['path']}")
                continue
            
            if idx % num_cols == 0:
                current_row_frame = ctk.CTkFrame(self.scroll_frame)
                current_row_frame.pack(fill="x", expand=True)
                self.row_frames.append(current_row_frame)
            
            thumb_frame = ctk.CTkFrame(current_row_frame, border_width=1, border_color="gray")
            thumb_frame.pack(side="left", padx=5, pady=5, anchor="n")
            
            # Store image_id with the frame for drag and drop
            thumb_frame.image_id = image_id 

            # Thumbnail image
            img = Image.open(img_data['path'])
            img.thumbnail((thumbnail_size_val, thumbnail_size_val))
            photo = ImageTk.PhotoImage(img)
            
            img_label = ctk.CTkLabel(thumb_frame, image=photo, text="")
            img_label.image = photo # Keep a reference
            img_label.pack()
            
            # Checkbox for selection
            var = tk.BooleanVar(value=img_data.get('selected', True))
            cb = ctk.CTkCheckBox(thumb_frame, text=f"{idx+1}.jpg", variable=var, 
                                 command=lambda i_id=image_id, v=var: self.image_manager.set_image_selected(i_id, v.get()))
            cb.pack(pady=(0,5))
            
            self.thumbnails[image_id] = {
                'frame': thumb_frame, 
                'label': img_label, 
                'var': var, 
                'cb': cb,
                'original_path': img_data['path']
            }
            
            # Bind drag and drop events to the thumbnail frame
            thumb_frame.bind("<ButtonPress-1>", lambda event, i_id=image_id: self.on_drag_start(event, i_id))
            thumb_frame.bind("<B1-Motion>", self.on_drag_motion)
            thumb_frame.bind("<ButtonRelease-1>", self.on_drag_release)
            thumb_frame.bind("<Double-Button-1>", lambda event, i_id=image_id: self.show_image_preview(i_id))
            img_label.bind("<Double-Button-1>", lambda event, i_id=image_id: self.show_image_preview(i_id)) # Bind to label too for better UX

        # Update scrollregion after adding all thumbnails
        self.scroll_frame.update_idletasks()
        self.update_apply_button_state()

    def on_drag_start(self, event, image_id: str):
        self.logger.debug(f"Drag start on image_id: {image_id} at ({event.x_root}, {event.y_root})")
        self.logger.debug(f"Drag start: {image_id}")
        widget = self.thumbnails[image_id]['frame']
        self.drag_source = widget
        self.drag_source.lift()
        # Record initial mouse position relative to widget
        self.drag_source.start_x = event.x_root - widget.winfo_x()
        self.drag_source.start_y = event.y_root - widget.winfo_y()
        # Highlight source
        self.drag_source.configure(border_color="blue", border_width=2)

    def on_drag_motion(self, event):
        # self.logger.debug(f"Drag motion to ({event.x_root}, {event.y_root})") # Can be very verbose
        if not self.drag_source:
            return

        x = event.x_root - self.drag_source.start_x
        y = event.y_root - self.drag_source.start_y
        self.drag_source.place(x=x, y=y, anchor="nw")

        # Determine drop target
        self.logger.debug(f"Original current_order before potential drop: {self.current_order}")
        self.drop_target = None
        for image_id, data in self.thumbnails.items():
            target_widget = data['frame']
            if target_widget == self.drag_source: 
                continue
            
            x1, y1 = target_widget.winfo_rootx(), target_widget.winfo_rooty()
            x2, y2 = x1 + target_widget.winfo_width(), y1 + target_widget.winfo_height()
            
            if x1 < event.x_root < x2 and y1 < event.y_root < y2:
                self.drop_target = target_widget
                self.logger.debug(f"Drop target identified: {self.drop_target}")
                break
            # Highlight potential drop target
            target_widget.configure(border_color="green", border_width=2)
        else:
            # Reset highlight if not target
            target_widget.configure(border_color="gray", border_width=1)

    def on_drag_release(self, event):
        self.logger.debug(f"Drag release at ({event.x_root}, {event.y_root})")
        if not self.drag_source:
            self.logger.debug("Drag release with no drag_source.")
            return

        self.logger.debug(f"Drag release. Source widget image_id: {self.drag_source.image_id}, Drop target widget image_id: {self.drop_target.image_id if self.drop_target else 'None'}")
        self.drag_source.configure(border_color="gray", border_width=1) # Reset source highlight

        self.logger.debug(f"Attempting reorder. Drag source ID: {self.drag_source.image_id}, Drop target ID: {self.drop_target.image_id if self.drop_target else 'None'}")
        if self.drop_target and self.drop_target.image_id != self.drag_source.image_id:
            source_id = self.drag_source.image_id
            target_id = self.drop_target.image_id
            
            try:
                s_idx = self.current_order.index(source_id)
                t_idx = self.current_order.index(target_id)
                
                self.current_order.pop(s_idx)
                self.current_order.insert(t_idx, source_id)
                
                self.has_unsaved_changes = True
                self.logger.debug(f"Reordered. New current_order: {self.current_order}")
                self.load_thumbnails() # Reload to reflect new order
            except ValueError:
                self.logger.error(f"Error reordering: ID not found in current_order. Source: {source_id}, Target: {target_id}, Order: {self.current_order}")
                self.load_thumbnails() # Reload to reset
        else:
            self.logger.debug("No valid drop or dropped on itself. Reverting.")
            self.load_thumbnails() # No valid drop or dropped on itself, revert

        # Reset drag state
        self.logger.debug("Resetting drag state.")
        self.drag_source = None
        self.drop_target = None # Ensure drop_target is reset
        self.update_apply_button_state()

    def show_image_preview(self, image_id: str):
        self.logger.info(f"Request to preview image: {image_id}")
        image_path = self.image_manager.get_image_path(image_id)
        if image_path and os.path.exists(image_path):
            filename_display = os.path.basename(image_path)
            preview_dialog = ImageViewerDialog(parent=self,
                                               image_path=image_path,
                                               image_id=image_id,
                                               filename=filename_display)
            # Modality is handled by ImageViewerDialog itself
        else:
            self.logger.warning(f"Could not show preview for {image_id}. Path: {image_path}")
            messagebox.showwarning("Pré-visualização Indisponível",
                                   f"Não foi possível carregar a imagem para pré-visualização.", parent=self)

    def update_apply_button_state(self):
        if self.has_unsaved_changes:
            self.apply_button.configure(state="normal")
        else:
            self.apply_button.configure(state="disabled")

    def apply_changes(self):
        self.logger.info("Applying changes to image order.")
        self.original_order = self.current_order.copy()
        self.has_unsaved_changes = False
        self.load_thumbnails() # Reload with new order and reset selection states
        messagebox.showinfo("Ordem Aplicada", "A nova ordem das imagens foi aplicada.", parent=self)

    def on_save(self):
        selected_images = self.image_manager.get_selected_images()
        if not selected_images:
            messagebox.showwarning("Nenhuma Imagem", "Nenhuma imagem selecionada para salvar.", parent=self)
            return

        save_path = filedialog.askdirectory(parent=self)
        if not save_path:
            return

        prefix = self.prefix_entry.get()
        create_zip = self.create_zip_var.get()
        
        try:
            saved_files = self.image_manager.save_selected_images(save_path, prefix, create_zip)
            if saved_files:
                messagebox.showinfo("Imagens Salvas", f"{len(saved_files)} imagem(ns) salva(s) em {save_path}", parent=self)
                self.images_saved = True
                # Clear selected images from manager after saving
                self.image_manager.delete_images([img_id for img_id, data in selected_images.items()])
                self.on_close() # Close dialog after saving
            else:
                messagebox.showerror("Erro ao Salvar", "Nenhuma imagem foi salva. Verifique os logs.", parent=self)
        except Exception as e:
            self.logger.error(f"Error saving images: {e}")
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro: {e}", parent=self)

    def on_close(self):
        if self.has_unsaved_changes:
            if messagebox.askyesno("Alterações Não Aplicadas", 
                                   "Existem alterações na ordem das imagens que não foram aplicadas. Deseja descartá-las e fechar?",
                                   parent=self):
                self.destroy()
            else:
                return # Don't close
        else:
            self.destroy()

    def was_saved(self) -> bool:
        return self.images_saved
