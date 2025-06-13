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

        # Determine HTML content (or fallback message)
        html_content = self._load_markdown_as_html()

        # Choose widget: HTMLScrolledText if available, otherwise CTkTextbox fallback
        if HTMLScrolledText is not None:
            viewer = HTMLScrolledText(
                self,
                html=html_content,
                width=680,
                height=480,
                background=self.cget("bg")  # match current CTk theme background
            )
            viewer.pack(expand=True, fill="both", padx=10, pady=10)
        else:
            # Fallback: plain text display
            textbox = ctk.CTkTextbox(self, wrap="word", corner_radius=0,
                                     font=CTkFont(family="Arial", size=12))
            textbox.pack(expand=True, fill="both", padx=10, pady=10)
            textbox.insert("1.0", "tkhtmlview não instalado.\n\n" + self._load_markdown_raw())
            textbox.configure(state="disabled")

        close_button = ctk.CTkButton(self, text="Fechar", command=self.destroy)
        close_button.pack(pady=10)

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

    def _load_markdown_as_html(self) -> str:
        """Converts help.md to HTML using markdown library if available."""
        raw_md = self._load_markdown_raw()
        if markdown is None:
            return f"<pre>{raw_md}</pre>"  # simple fallback
        return markdown.markdown(raw_md, extensions=["fenced_code", "tables"])
