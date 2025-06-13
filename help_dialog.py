import customtkinter as ctk
from customtkinter import CTkFont

# New imports for markdown rendering
try:
    from tkhtmlview import HTMLScrolledText  # lightweight HTML renderer for Tkinter
except ImportError:
    HTMLScrolledText = None  # Fallback if the package is missing

try:
    import markdown  # Convert Markdown to HTML
except ImportError:
    markdown = None


class HelpDialog(ctk.CTkToplevel):
    """Modal dialog that renders help.md as HTML inside the application."""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.title("Ajuda")
        self.geometry("700x550")
        self.transient(parent)
        self.grab_set()
        self.focus_set()

        # Color scheme based on current appearance mode
        mode = ctk.get_appearance_mode()
        if mode == "Dark":
            bg_color = "#2b2b2b"
            fg_color = "#dddddd"
        else:
            bg_color = "#ffffff"
            fg_color = "#000000"

        # Determine HTML content (or fallback message) with inline style for colors
        html_content = self._load_markdown_as_html(bg_color, fg_color)

        # Layout using grid so close button stays fixed at bottom
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        if HTMLScrolledText is not None:
            viewer = HTMLScrolledText(
                self,
                html=html_content,
                background=bg_color,
                width=680,
                height=480,
            )
            viewer.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))
        else:
            # Fallback: plain text display
            textbox = ctk.CTkTextbox(self, wrap="word", corner_radius=0,
                                     font=CTkFont(family="Arial", size=12))
            textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))
            textbox.insert("1.0", "tkhtmlview não instalado.\n\n" + self._load_markdown_raw())
            textbox.configure(state="disabled")

        close_button = ctk.CTkButton(self, text="Fechar", command=self.destroy)
        close_button.grid(row=1, column=0, pady=10)

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _load_markdown_raw(self) -> str:
        """Reads help.md and returns raw text (or default message)."""
        try:
            with open("help.md", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "Arquivo de ajuda (help.md) não encontrado."

    def _load_markdown_as_html(self, bg: str, fg: str) -> str:
        """Converts help.md to HTML and injects basic dark/light styles."""
        raw_md = self._load_markdown_raw()
        if markdown is None:
            # Simple fallback with pre tag and inline color style
            return f'<pre style="background:{bg};color:{fg};">{raw_md}</pre>'

        base_html = markdown.markdown(raw_md, extensions=["fenced_code", "tables"])
        body_style = (
            f"background-color:{bg}; color:{fg}; font-family: Arial, sans-serif; margin:10px;"
        )
        return f"<html><body style=\"{body_style}\">{base_html}</body></html>"
