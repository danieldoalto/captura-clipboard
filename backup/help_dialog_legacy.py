import customtkinter as ctk
from customtkinter import CTkFont
import re

class HelpDialog(ctk.CTkToplevel):
    """
    Legacy version of HelpDialog — uses CTkTextbox with manual Markdown parsing.
    Retained for reference; new implementation converts Markdown to HTML.
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.title("Ajuda (Legacy)")
        self.geometry("700x550")
        self.transient(parent)
        self.grab_set()
        self.focus_set()

        default_font_family = "Arial"
        default_font_size = 12

        textbox = ctk.CTkTextbox(self, wrap="word", corner_radius=0,
                                 font=CTkFont(family=default_font_family, size=default_font_size))
        textbox.pack(expand=True, fill="both", padx=10, pady=10)

        try:
            with open("help.md", "r", encoding="utf-8") as f:
                help_text = f.read()
        except FileNotFoundError:
            help_text = "Arquivo de ajuda (help.md) não encontrado."

        textbox.insert("1.0", help_text)
        textbox.configure(state="disabled")

        close_button = ctk.CTkButton(self, text="Fechar", command=self.destroy)
        close_button.pack(pady=10)
