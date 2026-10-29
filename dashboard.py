"""Privacy-preserving digital forensic filtering dashboard.
Run: python3 -m streamlit run dashboard.py
"""
from pathlib import Path
from datetime import datetime
import time
import mimetypes
import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parent
DEFAULT_EVIDENCE = Path.home()
LABELS = {
    1: {'title': 'Single Keyword', 'subtitle': 'Single-condition keyword matching', 'types': 'pdf', 'keywords': 'Jack or University or USA'},
    2: {'title': 'Boolean Conditions', 'subtitle': 'Multiple concepts with AND / OR', 'types': 'pdf or docx or txt or doc', 'keywords': 'Weapon or Linux and Windows'},
    3: {'title': 'OCR & Multi-format', 'subtitle': 'Text extraction and image OCR', 'types': 'jpeg or png or pdf or docx or txt or doc', 'keywords': 'Email or Microsoft or March or 0x1a2b3c'},
    4: {'title': 'Disk Image', 'subtitle': 'Disk image and recovered-file analysis', 'types': 'jpg or png or pdf or docx or txt or doc', 'keywords': 'rhino or Orleans or FTP or USB'},
}

# Transparent 1x1 favicon: the browser tab shows no visible icon.
from io import BytesIO
from PIL import Image
_favicon = BytesIO()
Image.new('RGBA', (1, 1), (0, 0, 0, 0)).save(_favicon, format='PNG')
st.set_page_config(page_title='Digital Forensic Filtering', page_icon=_favicon.getvalue(), layout='wide', initial_sidebar_state='expanded')
st.markdown('''
<style>
:root {--ink:#17243b; --muted:#64748b; --line:#e3e9f1; --navy:#203d66;}
.stApp {background:#f7f9fc;color:var(--ink)}
.block-container {max-width:1320px;padding-top:2rem;padding-bottom:4rem}
[data-testid="stSidebar"] {background:#14243a}
[data-testid="stSidebar"] * {color:#f0f5fc !important}
[data-testid="stSidebar"] [data-testid="stRadio"] label {padding:.45rem .1rem}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {color:#b6c4d7 !important}
[data-testid="stSidebar"] hr {border-color:#35475f}
h1,h2,h3 {color:#17243b;letter-spacing:-.035em}
h1 {font-size:2rem !important;font-weight:750 !important}
h3 {font-size:1.14rem !important}
[data-testid="stMetric"] {background:white;border:1px solid var(--line);border-radius:13px;padding:18px 20px;box-shadow:0 3px 14px rgba(23,36,59,.025)}
[data-testid="stMetricLabel"] {color:#64748b}
[data-testid="stMetricValue"] {color:#17243b;font-weight:750}
[data-testid="stVerticalBlockBorderWrapper"] {border-color:#e3e9f1 !important}
[data-testid="stDataFrame"] {border-radius:12px;overflow:hidden}
.stButton>button[kind="primary"] {background:#244b79;border:1px solid #244b79;border-radius:9px;font-weight:650;padding:.55rem 1.4rem}
.stButton>button[kind="primary"]:hover {background:#173b64;border-color:#173b64}
.stTextInput input,.stTextArea textarea {background:white;border-radius:9px}
.kicker {font-size:.73rem;font-weight:800;letter-spacing:.12em;color:#4c719b;text-transform:uppercase;margin-bottom:.35rem}
.subhead {color:#63758b;font-size:.95rem;margin-top:-.5rem;margin-bottom:1.4rem}
.panel-title {font-weight:750;font-size:1.08rem;margin:0 0 .4rem}
.muted-note {color:#65758a;font-size:.86rem}
.stage {display:inline-block;background:#eaf0f8;border:1px solid #d7e1ee;color:#2c527e;padding:.3rem .65rem;border-radius:7px;font-size:.79rem;font-weight:700}
/* Fix Streamlit top spacing */
[data-testid="stMainBlockContainer"] {
    padding-top: 3rem !important;
    padding-bottom: 3rem !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stSidebar"] .stButton > button {width:100%;min-height:3rem;justify-content:flex-start;text-align:left;border-radius:10px;padding:.65rem 1rem;background:transparent;border:1px solid transparent;box-shadow:none}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {background:#e7f0ff !important;border-color:#e7f0ff !important}
[data-testid="stSidebar"] .stButton > button[kind="primary"] p {color:#173d70 !important;font-weight:750}
[data-testid="stSidebar"] .stButton > button[kind="secondary"] p {color:#e3ebf6 !important}
[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {background:#263b55;border-color:#334d6c}
.sidebar-brand {font-size:1.2rem;font-weight:800;color:#fff;margin:0}
.sidebar-subtitle {font-size:.72rem;color:#9aafc8;margin:.25rem 0 1.6rem}
.sidebar-section {font-size:.72rem;font-weight:800;letter-spacing:.08em;color:#9aafc8;margin:1.5rem 0 .6rem}
.sidebar-module {font-size:.84rem;font-weight:650;color:#e3ebf6;padding:.5rem .15rem}
.sidebar-module span {display:block;font-size:.73rem;font-weight:400;color:#a3b4ca;margin-top:.2rem}
.sidebar-notice {background:#20364f;border:1px solid #314b69;border-radius:10px;padding:.85rem;font-size:.78rem;color:#d8e3f2;line-height:1.55;margin-top:1.5rem}
.sidebar-notice strong {display:block;color:#fff;margin-bottom:.25rem}

/* Compact evidence download buttons only; sidebar navigation is unaffected. */
[data-testid="stDownloadButton"] button {
    min-height: 2rem !important;
    padding: .22rem .65rem !important;
    font-size: .8rem !important;
    border-radius: 6px !important;
}
</style>
''', unsafe_allow_html=True)

if 'config_runs' not in st.session_state:
    st.session_state.config_runs = {}
if 'question_run' not in st.session_state:
    st.session_state.question_run = None

if 'active_page' not in st.session_state:
    st.session_state.active_page = 'Overview'

with st.sidebar:
    st.markdown('<div class="sidebar-brand">FORENSIC FILTER</div><div class="sidebar-subtitle">LOCAL INVESTIGATION WORKSPACE</div>', unsafe_allow_html=True)
    for name in ('Overview', 'Configuration-Based', 'Question-Based'):
        if st.button(name, key=f'nav_{name}', type='primary' if st.session_state.active_page == name else 'secondary', use_container_width=True):
            st.session_state.active_page = name
            st.rerun()
    st.markdown('<div class="sidebar-section">SYSTEM MODULES</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-module">Configuration-Based<span>Labels 1–4 · Keywords · OCR</span></div><div class="sidebar-module">Question-Based<span>Local Qwen · Evidence filtering</span></div><div class="sidebar-notice"><strong>Local execution</strong>Evidence files remain on this computer.</div>', unsafe_allow_html=True)

page = st.session_state.active_page

def heading(kicker, title, subtitle):
    st.markdown(f'<div class="kicker">{kicker}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="subhead">{subtitle}</div>', unsafe_allow_html=True)


def metrics(total, matches):
    count = len(matches)
    a,b,c = st.columns(3, gap='medium')
    a.metric('FILES EXAMINED', f'{total:,}' if total is not None else '—')
    b.metric('MATCHED EVIDENCE', f'{count:,}')
    c.metric('NOT MATCHED', f'{max(0,total-count):,}' if total is not None else '—')


def results_table(matches, source_dirs=None, widget_key='results'):
    """List only matched evidence and allow downloading the original files."""
    if not matches:
        st.info('No matching files were returned for these conditions.')
        return

    source_dirs = [Path(p).expanduser() for p in (source_dirs or [])]
    paths = [Path(str(p)).expanduser() for p in matches]
    st.caption(f'{len(paths)} matched file(s) · Download the relevant evidence below.')

    for index, candidate in enumerate(paths):
        possible = [candidate]
        if not candidate.is_absolute():
            possible += [directory / candidate for directory in source_dirs]
            possible += [directory / candidate.name for directory in source_dirs]
            possible.append(BASE / candidate)
        file_path = next((p for p in possible if p.is_file()), None)

        name_col, download_col = st.columns([4, 1], gap='medium', vertical_alignment='center')
        with name_col:
            st.write(candidate.name)
        with download_col:
            if file_path is None:
                st.caption('File unavailable')
            else:
                with file_path.open('rb') as evidence_file:
                    st.download_button(
                        label='⬇ Download',
                        data=evidence_file,
                        file_name=file_path.name,
                        mime=mimetypes.guess_type(file_path.name)[0] or 'application/octet-stream',
                        key=f'{widget_key}_download_{index}',
                        use_container_width=False,
                    )


if page == 'Overview':
    heading('INVESTIGATION WORKSPACE', 'Digital Forensic Filtering', 'Privacy-aware evidence selection using configuration rules and local question interpretation.')
    st.markdown('#### Choose an analysis workflow')
    left,right = st.columns(2, gap='large')
    with left:
        with st.container(border=True):
            st.markdown('### 01 · Configuration-Based')
            st.write('Run four experimental labels using file types, keyword conditions, OCR, and disk-image processing.')
            st.markdown('<span class="stage">Labels 1–4</span>', unsafe_allow_html=True)
            st.caption('Select Configuration-Based in the sidebar to run an experiment.')
    with right:
        with st.container(border=True):
            st.markdown('### 02 · Question-Based')
            st.write('Ask an investigative question and use local Qwen models to interpret and filter recovered evidence.')
            st.markdown('<span class="stage">Local LLM + Vision</span>', unsafe_allow_html=True)
            st.caption('Select Question-Based in the sidebar to submit a question.')
    st.markdown('#### Local environment')
    modules = [('Configuration engine', BASE/'test_0507.py'), ('Disk-image engine', BASE/'test_0807.py'), ('Question interpreter', BASE/'llm_forensic_filter.py'), ('Recovered evidence', BASE/'carve_out')]
    with st.container(border=True):
        for name, path in modules:
            col1,col2 = st.columns([3,1])
            col1.write(name)
            col2.write('● Available' if path.exists() else '○ Not found')
    st.caption('This dashboard shows live results only after you run a test. It does not use fabricated summary statistics.')

elif page == 'Configuration-Based':
    heading('RULE-DRIVEN INVESTIGATION', 'Configuration-Based Filtering', 'Select a label, confirm the local evidence path, and execute its original filtering logic.')
    label = st.selectbox('Experiment', [1,2,3,4], format_func=lambda n: f'Label {n}  ·  {LABELS[n]["title"]}')
    cfg = LABELS[label]
    st.markdown(f'**Label {label} — {cfg["subtitle"]}**')
    with st.container(border=True):
        st.markdown('<div class="panel-title">01 · Evidence source</div>', unsafe_allow_html=True)
        if label < 4:
            location = st.text_input('Directory containing evidence files', value=str(DEFAULT_EVIDENCE), key=f'location_{label}', help='Use the full macOS path. Only files directly inside this folder are scanned.')
        else:
            location = st.text_input('Disk image (.dd)', value=str(BASE/'sample.dd'), key='disk_location')
            recovery = st.text_input('Recovered files folder', value=str(BASE/'carve_out'), key='recovery_location')
        source = Path(location).expanduser()
        if source.exists():
            st.caption('✓ Evidence source found on this computer')
        else:
            st.warning('The evidence path does not exist. Check the directory name before running.')
    with st.container(border=True):
        st.markdown('<div class="panel-title">02 · Filtering criteria</div>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        types_line = c1.text_input('File types (separated by "or")', value=cfg['types'], key=f'types_{label}')
        keywords = c2.text_input('Keyword expression', value=cfg['keywords'], key=f'keywords_{label}')
        st.caption('Keywords follow the original scripts’ AND / OR matching behavior.')
    if st.button('▶  Run Label Test', type='primary', use_container_width=False):
        types = [s.strip().lower().lstrip('.') for s in types_line.lower().split(' or ') if s.strip()]
        if not types or not keywords.strip():
            st.error('Enter at least one file type and a keyword expression.')
        elif label < 4 and not source.is_dir():
            st.error(f'Cannot find directory: {source}')
        elif label == 4 and not source.is_file():
            st.error(f'Cannot find disk image: {source}')
        else:
            try:
                start = time.monotonic()
                if label < 4:
                    from test_0507 import process_directory
                    candidates = [p for p in source.iterdir() if p.is_file() and p.suffix.lower().lstrip('.') in types]
                    with st.spinner('Scanning the selected evidence directory…'):
                        matches = process_directory(str(source), types, keywords)
                    total = len(candidates)
                else:
                    from test_0807 import process_dd_image, process_recovered_fragments
                    recovered = Path(recovery).expanduser()
                    with st.spinner('Examining the disk image and recovered evidence…'):
                        matches = process_dd_image(str(source), types, keywords)
                        if not matches and recovered.is_dir():
                            matches = process_recovered_fragments(str(recovered), types, keywords)
                    total = None
                st.session_state.config_runs[label] = {'total':total, 'matches':matches, 'elapsed':time.monotonic()-start, 'at':datetime.now().strftime('%H:%M:%S'), 'path':str(source)}
                st.success('Filtering completed.')
            except Exception as exc:
                st.error(f'Test failed: {exc}')
    run = st.session_state.config_runs.get(label)
    if run:
        st.markdown('### 03 · Filtering results')
        st.caption(f'Last run at {run["at"]} · {run["elapsed"]:.1f} seconds · {run["path"]}')
        metrics(run['total'], run['matches'])
        st.markdown('#### Matched evidence')
        results_table(run['matches'], source_dirs=[run['path'], BASE / 'carve_out', BASE / 'Recovery'], widget_key=f'config_{label}')
        with st.expander('Interpretation and limitations'):
            st.write('The original Label 1–3 code scans only files directly inside the chosen folder. Its exception handling can silently skip extraction failures. Counts reflect eligible file extensions, not necessarily successfully extracted files.')
            if label == 4:
                st.write('Label 4 candidate counts are not measured. The original recovered-file scanning routine does not enforce the supplied file type list and can produce binary-text false positives.')

else:
    heading('LLM-ASSISTED INVESTIGATION', 'Question-Based Filtering', 'Ask a case-related question, interpret it locally, and inspect the matched evidence.')
    with st.container(border=True):
        st.markdown('<div class="panel-title">01 · Investigation question</div>', unsafe_allow_html=True)
        question = st.text_area('Question', placeholder='Which recovered files contain information related to removable USB storage?', height=125, label_visibility='collapsed')
        recovery = st.text_input('Recovered evidence directory', value=str(BASE/'carve_out'), key='question_recovery')
        st.caption('Runs local Qwen interpretation and the existing recovered-file filtering pipeline. Vision analysis can take additional time.')
        run_question = st.button('▶  Run Question Filter', type='primary')
    if run_question:
        target = Path(recovery).expanduser()
        if not question.strip():
            st.warning('Enter an investigation question first.')
        elif not target.is_dir():
            st.error(f'Recovered evidence folder not found: {target}')
        else:
            try:
                from llm_forensic_filter import interpret_question, process_recovered_candidates
                start = time.monotonic()
                with st.status('Running local forensic filtering…', expanded=True) as status:
                    st.write('Step 1 / 2 · Interpreting the investigation question with the local language model…')
                    keyword_line, keywords, logic = interpret_question(question)
                    st.write(f'Interpretation ready · {logic} · {keyword_line}')
                    st.write('Step 2 / 2 · Examining recovered files. Image analysis may take longer…')
                    matches, total = process_recovered_candidates(str(target), keyword_line, keywords, logic, question)
                    status.update(label='Analysis complete', state='complete', expanded=False)
                st.session_state.question_run = {'question':question, 'recovery_path':str(target), 'keywords':keywords, 'logic':logic, 'expression':keyword_line, 'matches':matches, 'total':total, 'elapsed':time.monotonic()-start, 'at':datetime.now().strftime('%H:%M:%S')}
                st.success('Question-based filtering completed.')
            except Exception as exc:
                st.error(f'Question-based filtering failed: {exc}')
                st.info('Check that Ollama is running and the configured Qwen models are available.')
    run = st.session_state.question_run
    if run:
        st.markdown('### 02 · Investigation results')
        st.caption(f'Last run at {run["at"]} · {run["elapsed"]:.1f} seconds · Question: {run["question"]}')
        metrics(run['total'], run['matches'])
        st.markdown('#### Matched evidence')
        results_table(run['matches'], source_dirs=[run.get('recovery_path', recovery), BASE / 'carve_out'], widget_key='question')
        with st.expander('View LLM interpretation', expanded=False):
            st.write('**Keyword expression:**', run['expression'])
            st.write('**Keywords:**', run['keywords'])
            st.write('**Logic:**', run['logic'])
        st.caption('The reported candidate total comes from the existing question-based filtering function. Verify whether metadata files such as audit.txt are included before using these counts in the final report.')
