# Digital Forensic Filtering Dashboard

This is a local Streamlit prototype for privacy-aware digital forensic evidence filtering. It provides Configuration-Based Filtering (Labels 1–4) and Question-Based Filtering using local Qwen models.

## 1. Requirements

- Python 3 (a recent compatible version; package compatibility, especially `pytsk3`, may vary by operating system and Python version)
- An internet connection for initial dependency/model installation
- **Tesseract OCR** installed as a separate system program for image text extraction
- **Ollama** installed and running for Question-Based Filtering
- Evidence files provided separately; no evidence is included in this package

The project was developed for a local macOS environment. Other operating systems may require adjustments, especially for `pytsk3` and system dependencies.

## 2. Files

Keep the following files in the same folder:

```text
Digital_Forensic_Filtering/
├── dashboard.py
├── test_0507.py
├── test_0807.py
├── llm_forensic_filter.py
├── requirements.txt
├── README.md
├── sample.dd          # optional: provide separately for Label 4
└── carve_out/         # optional: provide separately for recovered-file / question tests
```

**Important:** The original Python files are provided under the module filenames expected by `dashboard.py`. Do not rename these modules without also changing their imports.

## 3. Install dependencies

Open Terminal and navigate to the project folder:

```bash
cd /path/to/Digital_Forensic_Filtering
```

Optionally create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the Python packages:

```bash
python3 -m pip install -r requirements.txt
```

On macOS, install Tesseract OCR separately (if Homebrew is available):

```bash
brew install tesseract
```

On other systems, install Tesseract through the system's package manager and ensure the `tesseract` executable is on PATH. Installing `pytesseract` alone does not install the Tesseract executable.

**Note:** `pytsk3` is a native forensic library and may require compatible Python/build tools; if its installation fails, consult its platform-specific installation instructions. Both configuration modules import `pytsk3` at module load time, even when not scanning a disk image.

## 4. Start the dashboard

```bash
python3 -m streamlit run dashboard.py
```

The browser should open automatically. Otherwise visit **http://localhost:8501**. Stop the server with **Ctrl+C** in Terminal.

## 5. Configuration-Based Filtering

1. Select **Configuration-Based** from the sidebar.
2. Select Label 1, 2, 3 or 4.
3. For Labels 1–3, enter the **absolute path** of a local folder containing test evidence. These labels scan files directly inside the selected folder, not subfolders.
4. For Label 4, enter the path to a local `.dd` disk image and optionally the path to a directory of previously recovered files (for example, `carve_out/`).
5. Set the file extensions and keyword expression, then select **Run Label Test**.
6. Review the results and download available matched files.

**Limitations:** Label 4's direct disk-image scan depends on the image having a readable filesystem. The dashboard can fall back to scanning an existing recovered-files folder, but it does **not** automatically run Foremost or carve files from an image. The recovered-files routine does not strictly enforce the selected file extensions. A file found inside the disk image may not be downloadable unless the corresponding file also exists at a resolvable local path.

## 6. Question-Based Filtering

Install Ollama separately from https://ollama.com and ensure its service is running. Download the model tags configured in `llm_forensic_filter.py`:

```bash
ollama pull qwen3:4b-instruct
ollama pull qwen2.5vl:3b
```

Check that the model names are available locally using `ollama list`. If a model tag is unavailable, an equivalent model cannot simply be substituted without changing the corresponding model constant in the Python script and validating its behavior.

1. Ensure Ollama is running and the models are available.
2. In the dashboard, choose **Question-Based**.
3. Enter the absolute path to the local recovered-evidence folder (for example, `carve_out/`).
4. Enter an investigative question and select **Run Question Filter**.
5. Review the matched evidence and expand **View LLM interpretation** for the extracted criteria.

The question-based workflow may be slow, especially for image analysis, and requires sufficient local memory and processing capacity.

## 7. Important notes

- This package contains **code only**, not sample evidence, a disk image, or recovered files. Provide test data separately and update the paths shown in the dashboard to match the receiving computer.
- The dashboard runs **locally**; it is not a hosted website. The machine running it performs the filtering.
- Only use synthetic, authorised or appropriately de-identified evidence when sharing this prototype.
- The dashboard does not provide an evidence upload widget: evidence must already be present on the computer running the app.
- This README documents setup based on code inspection; installation and end-to-end execution have **not** been validated on the recipient's computer.
