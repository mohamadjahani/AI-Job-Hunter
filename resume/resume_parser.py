from pathlib import Path
from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parent
RESUME_FILE = BASE_DIR / "Jahani_ATS_Resume.pdf"


def extract_resume_text():
    reader = PdfReader(str(RESUME_FILE))

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages)


if __name__ == "__main__":
    resume_text = extract_resume_text()

    print("Resume Characters:", len(resume_text))
    print("=" * 50)
    print(resume_text[:1500])
