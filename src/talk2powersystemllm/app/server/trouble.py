import markdown

from .config import settings


def get_trouble_html():
    with open(settings.trouble_md_path, "r", encoding="utf-8") as trouble_md_file:
        trouble_md_text = trouble_md_file.read()
        return markdown.markdown(trouble_md_text, extensions=["toc", "fenced_code"], extension_configs={
            "toc": {
                "title": "Table of Contents"
            }
        })
