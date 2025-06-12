import customtkinter as ctk
from customtkinter import CTkFont
import re

class HelpDialog(ctk.CTkToplevel):
    """
    Modal dialog for displaying help information from help.md.
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.title("Ajuda")
        self.geometry("700x550")
        self.transient(parent)
        self.grab_set()
        self.focus_set()

        default_font_family = "Arial"
        default_font_size = 12

        textbox = ctk.CTkTextbox(self, wrap="word", corner_radius=0, font=CTkFont(family=default_font_family, size=default_font_size))
        textbox.pack(expand=True, fill="both", padx=10, pady=10)

        try:
            with open("help.md", "r", encoding="utf-8") as f:
                help_text = f.read()
        except FileNotFoundError:
            help_text = "Arquivo de ajuda (help.md) n\u00e3o encontrado."
        
        textbox.tag_config("h1", spacing3=15, spacing1=5, underline=True)
        textbox.tag_config("h2", spacing3=12, spacing1=4, underline=True)
        textbox.tag_config("h3", spacing3=10, spacing1=3, underline=True)
        textbox.tag_config("list_item", lmargin1=20, lmargin2=20, spacing1=2)

        inline_pattern = re.compile(r"(\*\*(.*?)\*\*)|(\*+(.*?)\*+)|(_+(.*?)_+)")

        for line in help_text.splitlines():
            stripped_line = line.strip()
            
            line_level_tags = []
            text_to_process = line 

            if stripped_line.startswith("### "):
                text_to_process = stripped_line[4:]
                line_level_tags.append("h3")
            elif stripped_line.startswith("## "):
                text_to_process = stripped_line[3:]
                line_level_tags.append("h2")
            elif stripped_line.startswith("# "):
                text_to_process = stripped_line[2:]
                line_level_tags.append("h1")
            elif stripped_line.startswith(tuple([prefix + " " for prefix in "*-+"])):
                text_to_process = stripped_line[2:]
                line_level_tags.append("list_item")
            
            segments = []
            last_match_end = 0
            for match in inline_pattern.finditer(text_to_process):
                match_start, match_end = match.span()

                if match_start > last_match_end:
                    segments.append((text_to_process[last_match_end:match_start], []))
                
                inline_segment_text = ""
                inline_segment_tags = []

                if match.group(1): # Bold: **text**
                    inline_segment_text = match.group(2)
                    # No specific visual tag for bold, styling handled by markdown interpretation if any
                elif match.group(3): # Italic: *text*
                    inline_segment_text = match.group(4)
                    # No specific visual tag for italic
                elif match.group(5): # Italic: _text_
                    inline_segment_text = match.group(6)
                    # No specific visual tag for italic
                
                # Use the content from the regex group directly
                # If specific styling for bold/italic is desired beyond what CTkTextbox supports by default for tags,
                # it would require more complex handling or different widgets.
                # For now, we just pass the text.
                current_text_segment_for_match = match.group(2) or match.group(4) or match.group(6) or text_to_process[match_start:match_end]
                segments.append((current_text_segment_for_match, inline_segment_tags)) # inline_segment_tags is empty for now
                last_match_end = match_end
            
            if last_match_end < len(text_to_process):
                segments.append((text_to_process[last_match_end:], []))
            
            if not segments and text_to_process:
                 segments.append((text_to_process, []))

            for text_segment, specific_inline_tags in segments:
                current_segment_tags = tuple(line_level_tags + specific_inline_tags) # specific_inline_tags is currently always empty
                if text_segment: 
                    textbox.insert("insert", text_segment, current_segment_tags)
            
            textbox.insert("insert", "\n")

        textbox.configure(state="disabled")
        close_button = ctk.CTkButton(self, text="Fechar", command=self.destroy)
        close_button.pack(pady=10)
