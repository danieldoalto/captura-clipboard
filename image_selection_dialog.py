import customtkinter as ctk
import tkinter as tk
import time
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from image_viewer_dialog import ImageViewerDialog # Import ImageViewerDialog
from typing import Dict, List, Callable, Optional # Assuming List and Callable might be used in full class
from ui_helper import UIHelper
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
    
    def __init__(self, parent, image_manager: 'ImageManager', ui_helper: Optional[UIHelper] = None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.parent = parent
        self.image_manager = image_manager
        self.logger = parent.logger
        
        # Usar o UIHelper do parent ou criar um novo se não for fornecido
        self.ui_helper = ui_helper or (parent.ui_helper if hasattr(parent, 'ui_helper') else None)
        self.theme_manager = self.ui_helper.theme_manager if self.ui_helper else None
        self.images_saved = False  # Track if images were saved
        self.has_unsaved_changes = False
        self.original_order = list(self.image_manager.get_all_image_ids()) # Initial order
        self.current_order = []  # Current order after drag and drop
        self.drag_source = None  # Current thumbnail being dragged
        self.drop_target = None  # Where the thumbnail will be dropped
        self.active_drop_target_widget = None # Widget atualmente destacado como alvo
        self.drag_start_time = 0
        self.drag_item_id = None
        self._drag_after_id = None
        
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
        self.update_idletasks() # Garante que os widgets tenham suas dimensões calculadas
        self.load_thumbnails()
    
    def setup_ui(self):
        """Set up the dialog UI"""
        # Obter configurações de padding do tema
        padding_small = self.ui_helper.get_padding("small") if self.ui_helper else 5
        padding_med = self.ui_helper.get_padding("medium") if self.ui_helper else 10
        padding_large = self.ui_helper.get_padding("large") if self.ui_helper else 20
        
        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=padding_med, pady=padding_med)
        
        # Aplicar estilo ao frame principal
        if self.ui_helper:
            self.ui_helper.style_frame(self.main_frame)
        
        # Header with instructions
        header_label = ctk.CTkLabel(self.main_frame, text="Selecione as imagens para salvar:")
        header_label.pack(anchor="w", padx=padding_small, pady=padding_small)
        
        # Aplicar estilo ao título
        if self.ui_helper:
            self.ui_helper.style_label(header_label, "header")
        
        # Checkbox for select all
        self.select_all_var = tk.BooleanVar(value=True)
        select_all_cb = ctk.CTkCheckBox(self.main_frame, text="Selecionar Tudo", 
                                      variable=self.select_all_var,
                                      command=self.toggle_select_all)
        select_all_cb.pack(anchor="w", padx=padding_small, pady=padding_small)
        
        # Aplicar estilo ao checkbox
        if self.ui_helper:
            self.ui_helper.style_checkbox(select_all_cb)
        
        # Create scrollable frame for thumbnails - usar orientação vertical
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame, orientation="vertical")
        self.scroll_frame.pack(fill="both", expand=True, padx=padding_small, pady=padding_small)
        
        # Aplicar estilo ao frame de rolagem
        if self.ui_helper:
            # Usar estilo de frame secundário para o frame de rolagem
            self.ui_helper.style_scrollable_frame(self.scroll_frame)
        
        # Prefix entry frame
        prefix_frame = ctk.CTkFrame(self.main_frame)
        prefix_frame.pack(fill="x", pady=(padding_med, 0))
        
        # Aplicar estilo ao frame de prefixo
        if self.ui_helper:
            self.ui_helper.style_frame(prefix_frame)
        
        prefix_label = ctk.CTkLabel(prefix_frame, text="Prefixo:")
        prefix_label.pack(side="left", padx=padding_small)
        
        # Aplicar estilo ao label
        if self.ui_helper:
            self.ui_helper.style_label(prefix_label)
        
        self.prefix_entry = ctk.CTkEntry(prefix_frame, width=200)
        self.prefix_entry.pack(side="left", padx=padding_small)
        self.prefix_entry.insert(0, self.parent.prefix_entry.get())
        
        # Aplicar estilo ao campo de entrada
        if self.ui_helper:
            self.ui_helper.style_entry(self.prefix_entry)
        
        # Create zip checkbox
        self.create_zip_var = tk.BooleanVar(value=True)
        self.create_zip_checkbox = ctk.CTkCheckBox(prefix_frame, 
                                           text="Criar arquivo ZIP", 
                                           variable=self.create_zip_var)
        self.create_zip_checkbox.pack(side="left", padx=(padding_large, padding_small))
        
        # Aplicar estilo ao checkbox
        if self.ui_helper:
            self.ui_helper.style_checkbox(self.create_zip_checkbox)
        
        # Bottom button frame
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Add buttons
        self.cancel_button = ctk.CTkButton(button_frame, text="Voltar", command=self.on_close)
        self.cancel_button.pack(side="right", padx=5)
        if self.ui_helper:
            self.ui_helper.style_button(self.cancel_button)
            self.cancel_button.configure(fg_color=self.theme_manager.get("button.secondary.background") if self.theme_manager else "#6c757d")
        
        self.save_button = ctk.CTkButton(button_frame, text="Salvar Selecionadas", command=self.on_save)
        self.save_button.pack(side="right", padx=5)
        if self.ui_helper:
            self.ui_helper.style_button(self.save_button)
            self.save_button.configure(fg_color=self.theme_manager.get("button.success.background") if self.theme_manager else "#28a745")

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
        if self.ui_helper:
            self.ui_helper.style_button(self.apply_button) # Apply base style
        
        # Dictionary to store thumbnail data
        self.thumbnails: Dict[str, Dict] = {}
    
    def _get_cell_from_widget(self, widget):
        """Helper function to determine the parent cell of a widget"""
        if not widget:
            return None
        
        # Check if widget is directly in our thumbnails
        for image_id, thumbnail in self.thumbnails.items():
            if widget == thumbnail['frame']:
                return thumbnail['frame']
        
        # Check for thumbnail label
        for image_id, thumbnail in self.thumbnails.items():
            if widget == thumbnail['label']:
                return thumbnail['frame']
        
        # If not found directly, try to find the parent that might be a thumbnail frame
        parent = widget.master
        if parent and parent != self and parent != self.scroll_frame:
            return self._get_cell_from_widget(parent)
            
        return None
    
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
        
        image_ids = self.image_manager.get_all_image_ids()
        if not image_ids:
            ctk.CTkLabel(self.scroll_frame, text="Nenhuma imagem capturada.").pack(pady=20)
            return

        # Initialize ordering if needed (respects prior drag-and-drop if not applied)
        if not self.current_order or set(self.current_order) != set(image_ids):
            # If images were added/removed externally or first load, reset current_order from original_order (or manager's state)
            self.current_order = list(self.original_order)
            if set(self.current_order) != set(image_ids): # Further sync if manager changed significantly
                self.current_order = image_ids.copy()
                self.original_order = image_ids.copy() # Reset original if completely out of sync

        # Determine number of columns based on window width
        thumbnail_size_val = self.image_manager.image_config.get('thumbnail_size', 128)
        num_cols = 3 # Fixo em 3 colunas
        
        current_row_frame = None
        
        for idx, image_id in enumerate(self.current_order):
            img_data = self.image_manager.get_image_metadata(image_id)
            if not img_data or 'path' not in img_data or not os.path.exists(img_data['path']):
                self.logger.warning(f"Skipping thumbnail for missing image_id: {image_id}")
                continue
            
            if idx % num_cols == 0:
                current_row_frame = ctk.CTkFrame(self.scroll_frame)
                current_row_frame.pack(fill="x", expand=True, pady=(5 if idx > 0 else 0))
                self.row_frames.append(current_row_frame)
            
            cell_frame = ctk.CTkFrame(current_row_frame, fg_color="transparent")
            cell_frame.pack(side="left", fill="x", expand=True, padx=2, pady=2)

            thumb_frame = ctk.CTkFrame(cell_frame, border_width=1)
            thumb_frame.pack(anchor="n", padx=3, pady=3)
            thumb_frame.image_id = image_id

            img = Image.open(img_data['path'])
            img.thumbnail((thumbnail_size_val, thumbnail_size_val))
            photo = ImageTk.PhotoImage(img)
            
            img_label = ctk.CTkLabel(thumb_frame, image=photo, text="")
            img_label.image = photo
            img_label.pack(side="top", fill="both", expand=True)
            
            var = tk.BooleanVar(value=img_data.get('selected', True))
            filename_display_text = f"{idx+1}.{self.image_manager.default_format}"
            cb = ctk.CTkCheckBox(thumb_frame, text=filename_display_text, variable=var,
                                 command=lambda i_id=image_id, v=var: self.image_manager.set_image_selected(i_id, v.get()))
            cb.pack(side="bottom", pady=(2,5))
            
            self.thumbnails[image_id] = {
                'frame': thumb_frame, 
                'label': img_label, 
                'var': var, 
                'cb': cb,
                'original_path': img_data['path']
            }
            
            if self.ui_helper:
                self.ui_helper.style_checkbox(cb)
                self.ui_helper.style_frame(thumb_frame, style="thumbnail")
            
            # Bind events to both the frame and the label to ensure dragging works everywhere
            for widget in [thumb_frame, img_label]:
                widget.bind("<ButtonPress-1>", lambda e, img_id=image_id: self.on_drag_start(e, img_id))
                widget.bind("<B1-Motion>", self.on_drag_motion)
                widget.bind("<ButtonRelease-1>", self.on_drag_release)
                widget.bind("<Double-Button-1>", lambda e, i_id=image_id: self.show_image_preview(i_id))

        # Update scrollregion after adding all thumbnails
        self.scroll_frame.update_idletasks()
        self.update_apply_button_state()

    def on_drag_start(self, event, image_id: str):
        # Schedule a function to start the drag after a delay.
        # This allows double-clicks to be processed without interference.
        self.drag_item_id = image_id
        self._drag_after_id = self.after(200, lambda: self._start_drag(image_id))

    def _start_drag(self, image_id: str):
        """Helper to begin the drag operation after a delay."""
        # Ensure the drag operation is still valid
        if self.drag_item_id == image_id:
            self.drag_source = self.thumbnails[image_id]['frame']
            self.logger.info(f"Drag officially started for item: {image_id}")
            if self.ui_helper:
                self.ui_helper.highlight_widget(self.drag_source, "drag_source")
            # Mark that drag has started; prevent quick-release cancellation
            self._drag_after_id = None

    def on_drag_motion(self, event):
        if not self.drag_source:
            return
        
        self.logger.debug(f"Drag motion at ({event.x_root}, {event.y_root})")
        
        # Scroll the scroll_frame if near the edges
        scroll_y = self.scroll_frame.winfo_rooty()
        scroll_height = self.scroll_frame.winfo_height()
        mouse_y = event.y_root
        threshold = 50  # pixels from edge to trigger scroll
        scroll_speed_factor = 0.05  # Adjust scroll speed
        
        if mouse_y < scroll_y + threshold:
            # Scroll up
            current_yview = self.scroll_frame._parent_canvas.yview()
            target_y = max(0, current_yview[0] - scroll_speed_factor)
            self.scroll_frame._parent_canvas.yview_moveto(target_y)
        elif mouse_y > scroll_y + scroll_height - threshold:
            # Scroll down
            current_yview = self.scroll_frame._parent_canvas.yview()
            target_y = min(1.0, current_yview[1] + scroll_speed_factor)
            self.scroll_frame._parent_canvas.yview_moveto(target_y)
        
        # Find target row frame based on mouse Y position
        target_row_frame = None
        for row_frame in [child for child in self.scroll_frame.winfo_children() if isinstance(child, ctk.CTkFrame)]:
            # Convert to root coordinates to match event.y_root
            row_top = row_frame.winfo_rooty()
            row_bottom = row_top + row_frame.winfo_height()
            if row_top <= mouse_y < row_bottom:
                target_row_frame = row_frame
                break
        
        if target_row_frame:
            # Encontrar a célula de destino dentro da linha
            target_cell = self._get_cell_from_widget(target_row_frame.winfo_containing(event.x_root, event.y_root))
            if target_cell and self.active_drop_target_widget is not target_cell:
                # Remove highlight from previous drop target
                if self.active_drop_target_widget and self.ui_helper:
                    self.ui_helper.remove_highlight(self.active_drop_target_widget)
                
                # Set and style the new active_drop_target_widget
                self.active_drop_target_widget = target_cell
                if self.ui_helper:
                    self.ui_helper.highlight_widget(self.active_drop_target_widget, "drop_target")
                self.drop_target = target_cell  # Store the widget itself
        else:
            # Mouse is not over any valid target
            if self.active_drop_target_widget and self.ui_helper:
                self.ui_helper.remove_highlight(self.active_drop_target_widget)
            self.active_drop_target_widget = None
            self.drop_target = None

    def on_drag_release(self, event):
        # If the mouse is released before the drag delay has passed, cancel the drag.
        if self._drag_after_id:
            self.after_cancel(self._drag_after_id)
            self._drag_after_id = None
            self.logger.debug("Drag cancelled due to quick release.")
            return
        
        self.logger.debug(f"Drag release at ({event.x_root}, {event.y_root})")
        
        source_widget_id_log = "None"
        reordered_successfully = False
        if self.drag_source:
            source_widget_id = self.drag_source.image_id
            
            # Reset source highlight
            if self.drag_source.winfo_exists():
                if self.ui_helper:
                    self.ui_helper.remove_highlight(self.drag_source)
                source_widget_id_log = source_widget_id
            
            # If we have a valid drop target, reorder the images
            if self.drop_target and hasattr(self.drop_target, 'image_id'):
                target_id = self.drop_target.image_id
                if source_widget_id != target_id:
                    self.logger.debug(f"Reordering from {source_widget_id} to {target_id}")
                    
                    # Get current positions
                    source_idx = self.current_order.index(source_widget_id)
                    target_idx = self.current_order.index(target_id)
                    
                    # Perform reordering in current_order list
                    self.current_order.remove(source_widget_id)
                    
                    # If target is now at the end (because source was before it), adjust
                    if target_idx >= len(self.current_order):
                        self.current_order.append(source_widget_id)
                    else:
                        self.current_order.insert(target_idx, source_widget_id)
                    
                    # Mark that we have unsaved changes
                    self.has_unsaved_changes = True
                    reordered_successfully = True
                    self.logger.debug(f"Reordered: {self.current_order}")
                else:
                    self.logger.debug("Source and target are the same, not reordering.")
            else:
                self.logger.debug("No valid drop target found.")
        else:
            self.logger.debug("Drag release with no drag_source.")

        self.logger.debug(f"Drag release: Reordered successfully: {reordered_successfully}")
        # Reset drag state
        self.logger.debug("Resetting drag state.")
        self.drag_source = None
        self.drop_target = None
        self.active_drop_target_widget = None
        
        # Reload thumbnails to reflect any changes or reset positions
        # This will also call update_apply_button_state() at its end.
        if reordered_successfully:
            self.load_thumbnails()
        else:
            self.update_apply_button_state()

    def show_image_preview(self, image_id: str):
        self.logger.info(f"Request to preview image: {image_id}")
        image_path = self.image_manager.get_image_path(image_id)
        if image_path and os.path.exists(image_path):
            # Build filename as it will be saved (NN_prefix.ext) instead of raw UUID
            try:
                idx_in_order = self.current_order.index(image_id)
            except ValueError:
                idx_in_order = 0  # Fallback if not found for some reason
            seq_number = str(idx_in_order + 1).zfill(2)
            prefix = self.prefix_entry.get().strip() or self.image_manager.default_prefix
            filename_display = f"{seq_number}_{prefix}.{self.image_manager.default_format}"
            preview_dialog = ImageViewerDialog(parent=self,
                                               image_path=image_path,
                                               image_id=image_id,
                                               filename=filename_display,
                                               ui_helper=self.ui_helper)
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
        selected_ids = self.image_manager.get_selected_image_ids()
        if not selected_ids:
            messagebox.showwarning("Nenhuma Imagem", "Nenhuma imagem selecionada para salvar.", parent=self)
            return

        save_path = filedialog.askdirectory(parent=self, initialdir=self.image_manager.default_save_directory)
        if not save_path:
            return

        prefix = self.prefix_entry.get().strip() or self.image_manager.default_prefix
        create_zip = self.create_zip_var.get()
        
        try:
            # Use current_order for saving to maintain the displayed numbering
            saved_files = self.image_manager.save_images(prefix, save_path, create_zip, custom_order=self.current_order)
            
            if saved_files:
                if create_zip:
                    zip_path = saved_files[0]
                    msg = f"Arquivo ZIP salvo com sucesso em:\n{zip_path}"
                else:
                    count = len(saved_files)
                    msg = f"{count} imagens salvas com sucesso em:\n{save_path}"
                messagebox.showinfo("Imagens Salvas", msg, parent=self)
                self.images_saved = True
                
                # Ask user if they want to clear the saved images from the application
                if messagebox.askyesno("Limpar Imagens Salvas", 
                                       "Deseja remover as imagens salvas da lista de captura atual?", 
                                       parent=self):
                    # Only delete images that were part of the "selected_ids" list for this save operation
                    self.image_manager.delete_images_by_ids(selected_ids)
                    self.has_unsaved_changes = False # Reset as images are gone
                    self.original_order = list(self.image_manager.get_all_image_ids()) # Update original order
                    self.load_thumbnails() # Refresh the view
                    
                    # If all images are cleared, update main app state
                    if not self.image_manager.get_all_image_ids():
                        self.parent.save_button.configure(state="disabled")
                        self.parent.has_unsaved_images = False
                        self.on_close() # Close if no images left
            else:
                messagebox.showerror("Erro ao Salvar", "Nenhuma imagem foi salva. Verifique as permissões ou logs.", parent=self)
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
