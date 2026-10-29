"""
This filters file in a specified directory based on file types
and keyword conditions provided in a configuration file

It supports:
- Multiple file formats (TXT, PDF, DOCX, PNG, JPEG)
- Logical keyword matching (AND, OR conditions)
- OCR for extracting text from image files
"""

import os
import sys
import re
from io import BytesIO # 메모리에 있는 데이터를 "파일처럼" 만들어주는 도구

from pypdf import PdfReader
from docx import Document
import pytesseract
from PIL import Image
import pytsk3

def read_config(config_file):
    """
    Read the configuration file and extracts:
    - target directory (location)
    - file types to filter
    - keyword conditions
    """
    location = ""
    file_type_line = ""
    keyword_line = ""

    with open(config_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()

            if key == "location":
                location = value
            elif key == "filetype":
                file_type_line = value
            elif key == "contain" or key == "keywords":
                keyword_line = value

    return location, file_type_line, keyword_line


def parse_file_types(file_type_line):
    """
    Convert the file type string from the configuration into list of file extensions
    Processes inputs and normalise them (trimming spaces and converting to lowercase) 
    to enable consistent file comparison during filtering
    """
    return [t.strip().lower() for t in file_type_line.split(" or ") if t.strip()]


def extract_text_pdf(file_path):
    """
    Extract text from a PDF file stored in a normal directory.
    """
    text = ""
    reader = PdfReader(file_path)

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text.lower() + "\n"

    return text


def extract_text_pdf_bytes(file_bytes):
    """
    Extract text from a PDF file loaded from a disk image.
    """
    text = ""
    reader = PdfReader(BytesIO(file_bytes))

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text.lower() + "\n"

    return text


def extract_text_txt(file_path):
    """
    Extract text from a TXT file stored in a normal directory.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().lower()


def extract_text_txt_bytes(file_bytes):
    """
    Extract text from a TXT tile loaded from a disk image.
    """
    return file_bytes.decode("utf-8", errors="ignore").lower()


def extract_text_docx(file_path):
    """
    Extract text from a DOCX file stored in a normal directory.
    """
    text = ""
    doc = Document(file_path)

    for para in doc.paragraphs:
        text += para.text.lower() + "\n"

    return text


def extract_text_docx_bytes(file_bytes):
    """
    Extract text from a DOCX file loaded from a disk image.
    """
    text = ""
    doc = Document(BytesIO(file_bytes))

    for para in doc.paragraphs:
        text += para.text.lower() + "\n"
    
    return text


def extract_text_image(file_path):
    """
    Extract text from image file stored in a normal directory.
    """
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image)
    return text.lower()


def extract_text_image_bytes(file_bytes):
    """
    Extract text from an image file loaded from a disk image using OCR.
    """
    image = Image.open(BytesIO(file_bytes))
    text = pytesseract.image_to_string(image)
    return text.lower()


def extract_text(file_path, extension):
    """
    Extract text from supported file types stored in a normal directory.
    """
    if extension == "pdf":
        return extract_text_pdf(file_path)

    elif extension == "txt":
        return extract_text_txt(file_path)

    elif extension == "docx":
        return extract_text_docx(file_path)

    elif extension in ["jpg", "jpeg", "png"]:
        return extract_text_image(file_path)

    elif extension == "doc":
        return None

    return None


def extract_text_from_bytes(file_bytes, extension):
    """
    Extract text from supported file types loaded directly from a disk image.
    """
    if extension == "pdf":
        return extract_text_pdf_bytes(file_bytes)

    elif extension == "txt":
        return extract_text_txt_bytes(file_bytes)

    elif extension == "docx":
        return extract_text_docx_bytes(file_bytes)

    elif extension in ["jpg", "jpeg", "png"]:
        return extract_text_image_bytes(file_bytes)

    elif extension == "doc":
        return None

    return None


def contains_keyword(text, word):
    """
    Checks whether a given keyword exists in the text as a complete word
    Uses regular expressions to avoid partial matches that keywords are matched accurately
    (e.g., "usa" will not be match "usage") - fixed issue!
    """
    if word.isalpha():
        pattern = r"\b" + re.escape(word) + r"\b"
        return re.search(pattern, text) is not None
    
    return word in text


def keyword_match(text, keyword_line):
    """
    Support both Label1, Label2, Lable3, and Label4 logic.

    Examples:
    - Label1: Jack or University or USA
    - Label2: Weapon or Linux and Windows
    - Label3: Email or Microsoft or March or 0x1a2b3c
    - Label4: rhino or Orleans or FTP or USB
    """
    keyword_line = keyword_line.lower()
    text = text.lower()

    or_parts = [part.strip() for part in keyword_line.split(" or ") if part.strip()]

    for part in or_parts:
        if "and" in part:
            and_parts = [p.strip() for p in part.split(" and ") if p.strip()]
            if all(contains_keyword(text,word) for word in and_parts):
                return True
        else:
            if contains_keyword(text,part):
                return True

    return False


def process_directory(location, file_types, keyword_line):
    """
    Process files from a normal directory.
    """
    matched_files = []

    for file in os.listdir(location):
        file_path = os.path.join(location, file)

        if not os.path.isfile(file_path):
            continue

        for ext in file_types:
            if file.lower().endswith("." + ext):
                try:
                    text = extract_text(file_path, ext)

                    if text is None:
                        break

                    if keyword_match(text, keyword_line):
                        matched_files.append(file)

                except Exception:
                    pass

                break

    return matched_files


def process_recovered_fragments(recovery_path, keyword_line):
    """
    Process recovered fragment files from PhotoRec.
    """
    matched_files = []

    for file in os.listdir(recovery_path):
        file_path = os.path.join(recovery_path, file)

        if not os.path.isfile(file_path):
            continue

        try:
            with open(file_path, "rb") as f:
                data = f.read().lower()

            text = data.decode("utf-8", errors="ignore")

            if keyword_match(text, keyword_line):
                matched_files.append(file)

        except Exception:
            pass
    return matched_files


def process_dd_image(dd_path, file_types, keyword_line):
    """
    Process files directly from a disk image (.dd)

    Opens the disk image, reads file from the root directory,
    extracts text from supported file types, and applies the same 
    keyword filtering logic used for normal directories.
    """
    matched_files = []

    img = pytsk3.Img_Info(dd_path)
    fs = pytsk3.FS_Info(img)
    root_dir = fs.open_dir(path="/")

    for entry in root_dir:
        try:
            name = entry.info.name.name.decode("utf-8", errors="ignore")
        except Exception:
            continue

        if name in [".", ".."]:
            continue

        meta = entry.info.meta
        if meta is None:
            continue

        if meta.type != pytsk3.TSK_FS_META_TYPE_REG:
            continue

        for ext in file_types:
            if name.lower().endswith("." + ext):
                try:
                    file_obj = fs.open_meta(inode=meta.addr)
                    file_size = meta.size
                    file_bytes = file_obj.read_random(0, file_size)

                    text = extract_text_from_bytes(file_bytes, ext)

                    if text is None:
                        break

                    if keyword_match(text, keyword_line):
                        matched_files.append(name)

                except Exception:
                    pass

                break
            
    return matched_files


def main():
    """
    Controls the overall workflow:
    - reads configuration
    - determine whether the location is a directory or a disk image
    - extracts text
    - applies filtering
    - outputs matching files
    """
    if len(sys.argv) != 2:
        print("Usage: python3 test.py <config_file>")
        sys.exit()

    config_file = sys.argv[1]

    if not os.path.isfile(config_file):
        print("Config file not found:", config_file)
        sys.exit()

    location, file_type_line, keyword_line = read_config(config_file)

    if not location or not file_type_line or not keyword_line:
        print("Config file must contain Location, FileType, and Contain/Keywords.")
        sys.exit()

    file_types = parse_file_types(file_type_line)

    if location.lower().endswith(".dd"):
        if not os.path.isfile(location):
            print("Invalid disk image:", location)
            sys.exit()

        matched_files = process_dd_image(location, file_types, keyword_line)

        if not matched_files:
            recovery_path = os.path.expanduser(
                "~/Desktop/🇦🇺 2026-1/CYBR7901/Python/Recovery/recup_dir.1"
            )
            
            if os.path.isdir(recovery_path):
                print("No active matching files found.")

                matched_files = process_recovered_fragments(
                    recovery_path,
                    keyword_line
                )

            else:
                print("Recovery folder not found:", recovery_path)

    else:
        if not os.path.isdir(location):
            print("Invalid directory:", location)
            sys.exit()
        
        matched_files = process_directory(location, file_types, keyword_line)

    if matched_files:
        print(f"Following matching file(s) found in {location}:")
        for file in matched_files:
            print(file)
    else:
        print(f"No matching file(s) found in {location}.")


if __name__ == "__main__":
    main()