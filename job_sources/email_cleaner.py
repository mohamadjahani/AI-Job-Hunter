import unicodedata
from bs4 import BeautifulSoup


def clean_email_text(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(" ", strip=True)

    unwanted_chars = {
        "\u034f",  # Combining Grapheme Joiner
        "\u00ad",  # Soft Hyphen
        "\u200b",  # Zero Width Space
        "\u200c",  # Zero Width Non-Joiner
        "\u200d",  # Zero Width Joiner
        "\ufeff",  # Byte Order Mark
    }

    cleaned_chars = []

    for char in text:
        category = unicodedata.category(char)

        if char in unwanted_chars:
            continue

        if category == "Cf":
            continue

        if category.startswith("Z"):
            cleaned_chars.append(" ")
        else:
            cleaned_chars.append(char)

    text = "".join(cleaned_chars)
    text = " ".join(text.split())

    return text
