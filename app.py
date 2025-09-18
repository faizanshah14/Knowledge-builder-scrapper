import os
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
import json

import streamlit as st
from dotenv import load_dotenv

from scrapper.crawler import crawl_site
from scrapper.extractor import extract_markdown_items
from scrapper.indexer import build_faiss_index
from scrapper.qa_agent import answer_question, debug_index_contents


load_dotenv()

st.set_page_config(page_title="Knowledge Builder", page_icon="🍎", layout="centered")

# Output directories (define before using)
outputs_dir = Path("outputs")
outputs_dir.mkdir(exist_ok=True)
cache_dir = Path(".index_cache")
cache_dir.mkdir(exist_ok=True)


def slugify(text: str) -> str:
    safe = "".join(c.lower() if c.isalnum() else "-" for c in text)
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe.strip("-")[:80]


def index_name_for(url_str: str) -> str:
    h = hashlib.sha256(url_str.encode("utf-8")).hexdigest()[:12]
    return f"index_{h}"


def scrape_to_json(url_str: str) -> dict:
    includes = [p.strip() for p in include_patterns.split(",") if p.strip()]
    excludes = [p.strip() for p in exclude_patterns.split(",") if p.strip()]
    urls = crawl_site(url_str, max_pages=max_pages, concurrency=concurrency, include_patterns=includes, exclude_patterns=excludes)
    items = extract_markdown_items(urls)
    return {"site": url_str, "items": items}


def persist_run(url_str: str, data: dict) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    site_slug = slugify(url_str)
    run_dir = outputs_dir / site_slug
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / f"{site_slug}-{ts}.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return json_path


def ensure_index_for(json_path: Path, url_str: str) -> Path:
    name = index_name_for(url_str)
    idx_path = cache_dir / name
    if idx_path.exists() and (idx_path / "index.faiss").exists():
        return idx_path
    if idx_path.exists():
        shutil.rmtree(idx_path)
    build_faiss_index(str(json_path), str(idx_path))
    return idx_path

st.markdown("""
# 🍎 Knowledge Builder
Bring any site's technical knowledge into your knowledgebase, then ask questions with Claude.
""")

with st.sidebar:
    st.header("Settings")
    
    # Claude API Key Management
    st.subheader("🔑 Claude API Key")
    current_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if current_key:
        st.success("✅ API Key Found")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Change API Key", key="change_api_key"):
                st.session_state["show_key_input"] = True
        with col2:
            if st.button("Remove API Key", type="secondary", key="remove_api_key"):
                st.session_state["confirm_remove_key"] = True
    else:
        st.error("❌ API Key Missing")
        st.session_state["show_key_input"] = True
    
    # Confirmation dialog for removing API key
    if st.session_state.get("confirm_remove_key", False):
        st.warning("⚠️ Are you sure you want to remove the API key?")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Yes, Remove", type="primary", key="confirm_remove_key"):
                # Remove from .env file
                env_path = Path(".env")
                if env_path.exists():
                    env_content = env_path.read_text()
                    lines = env_content.split('\n')
                    lines = [line for line in lines if not line.startswith("ANTHROPIC_API_KEY")]
                    env_path.write_text('\n'.join(lines))
                # Clear from environment
                if "ANTHROPIC_API_KEY" in os.environ:
                    del os.environ["ANTHROPIC_API_KEY"]
                st.success("API Key removed successfully!")
                st.session_state["confirm_remove_key"] = False
                st.session_state["show_key_input"] = False
                st.rerun()
        with col2:
            if st.button("Cancel", key="cancel_remove_key"):
                st.session_state["confirm_remove_key"] = False
                st.rerun()
    
    if st.session_state.get("show_key_input", False):
        new_key = st.text_input("Enter Claude API Key", type="password", value=current_key)
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Save Key", key="save_api_key"):
                if new_key:
                    # Save to .env file
                    env_path = Path(".env")
                    env_content = env_path.read_text() if env_path.exists() else ""
                    if "ANTHROPIC_API_KEY" in env_content:
                        # Update existing key
                        lines = env_content.split('\n')
                        lines = [line for line in lines if not line.startswith("ANTHROPIC_API_KEY")]
                        lines.append(f"ANTHROPIC_API_KEY={new_key}")
                        env_path.write_text('\n'.join(lines))
                    else:
                        # Add new key
                        env_path.write_text(f"{env_content}\nANTHROPIC_API_KEY={new_key}\n")
                    st.success("API Key saved! Please restart the app.")
                    st.rerun()
                else:
                    st.error("Please enter a valid API key")
        with col2:
            if st.button("Cancel", key="cancel_save_key"):
                st.session_state["show_key_input"] = False
                st.rerun()
    
    st.divider()
    
    # Previous Searches
    st.subheader("📚 Previous Searches")
    if outputs_dir.exists():
        search_dirs = [d for d in outputs_dir.iterdir() if d.is_dir()]
        if search_dirs:
            search_options = ["Select a previous search..."] + [d.name for d in search_dirs]
            selected_search = st.selectbox("Load Previous Search", search_options)
            
            if selected_search != "Select a previous search...":
                search_dir = outputs_dir / selected_search
                json_files = list(search_dir.glob("*.json"))
                if json_files:
                    # Get the most recent file
                    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
                    if st.button("Load This Search", key=f"load_search_{selected_search}"):
                        st.session_state["last_json"] = str(latest_file)
                        st.session_state["last_site"] = selected_search
                        # Load the data to get item count
                        with open(latest_file, 'r') as f:
                            data = json.load(f)
                        st.session_state["last_count"] = len(data.get("items", []))
                        # Build index if it doesn't exist
                        idx = ensure_index_for(latest_file, selected_search)
                        st.session_state["active_index"] = str(idx)
                        st.success(f"Loaded {len(data.get('items', []))} items from {selected_search}")
                        st.rerun()
                    
                    # Show file info
                    st.info(f"Latest: {latest_file.name}")
                    st.info(f"Files: {len(json_files)}")
                else:
                    st.warning("No JSON files found in this search")
        else:
            st.info("No previous searches found")
    else:
        st.info("No previous searches found")
    
    st.divider()
    
    # Scraping Settings
    st.subheader("⚙️ Scraping Settings")
    max_pages = st.number_input("Max pages", min_value=10, max_value=2000, value=200, step=10)
    concurrency = st.number_input("Concurrency", min_value=4, max_value=64, value=16, step=1)
    include_patterns = st.text_input("Include patterns", value="blog,guide,learn,post")
    exclude_patterns = st.text_input("Exclude patterns", value="")
    model = st.selectbox("Claude model", [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
    ])

# Functions already defined above

# Use form for Enter key submission
with st.form("scrape_form"):
    url = st.text_input("Website or section URL", placeholder="https://interviewing.io/blog")
    
    col = st.columns([1,1,1,1])
    with col[0]:
        go = st.form_submit_button("Scrape & Index", type="primary", use_container_width=True, key="scrape_button")
    with col[1]:
        reset = st.form_submit_button("Reset Cache", use_container_width=True, key="reset_cache_button")
    with col[2]:
        show_outputs = st.form_submit_button("Open Outputs", use_container_width=True, key="show_outputs_button")
    with col[3]:
        debug_index = st.form_submit_button("Debug Index", use_container_width=True, key="debug_index_button")

if reset:
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        cache_dir.mkdir(exist_ok=True)
    st.success("Cache cleared.")

if show_outputs:
    st.info(f"Outputs folder: {outputs_dir.resolve()}")

if debug_index and st.session_state.get("active_index"):
    with st.spinner("Checking index contents..."):
        try:
            doc_count = debug_index_contents(st.session_state["active_index"])
            st.success(f"Index contains {doc_count} documents. Check the terminal for details.")
        except Exception as e:
            st.error(f"Debug failed: {e}")
elif debug_index:
    st.warning("No active index found. Please scrape a site first.")

if go:
    try:
        with st.spinner("Scraping content and building index…"):
            # if url is not a valid URL, show an error
            if not url.startswith("http"):
                st.error("Please enter a valid URL")
            else:
                data = scrape_to_json(url)
                json_path = persist_run(url, data)
                idx = ensure_index_for(json_path, url)
                st.session_state["active_index"] = str(idx)
                st.session_state["last_json"] = str(json_path)
                st.session_state["last_site"] = url
                st.session_state["last_count"] = len(data.get("items", []))
                st.success("Ready to ask questions.")
    except Exception as e:
        st.error(f"Scraping failed: {str(e)}")
        st.info("Try adjusting the include/exclude patterns or check if the website has accessible content.")
st.subheader("Ask Claude")

# Initialize session state for auto-submit
if "auto_ask" not in st.session_state:
    st.session_state["auto_ask"] = False

q = st.text_input("Question", placeholder="What are the key interview prep tips?", key="question_field")

# Check if question was just entered (for auto-submit on Enter)
if q and q != st.session_state.get("prev_question", ""):
    st.session_state["prev_question"] = q
    st.session_state["auto_ask"] = True

ask_disabled = not (st.session_state.get("active_index") and q and os.environ.get("ANTHROPIC_API_KEY"))

col1, col2 = st.columns([1, 1])
with col1:
    ask_button = st.button("Ask", disabled=ask_disabled, type="primary", use_container_width=True, key="ask_button")

# Handle both button click and auto-submit
should_ask = ask_button or (st.session_state.get("auto_ask", False) and q and not ask_disabled)

if should_ask:
    st.session_state["auto_ask"] = False  # Reset auto-ask flag
    with st.spinner("Thinking with Claude…"):
        try:
            answer = answer_question(st.session_state["active_index"], q, os.environ.get("ANTHROPIC_API_KEY"), model=model)
            st.markdown("### Answer")
            st.write(answer)
        except Exception as e:
            st.error(f"Error: {e}")


if st.session_state.get("last_json"):
    st.subheader("📊 Current Search")
    
    # Main metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Items", st.session_state.get("last_count", 0))
    with c2:
        st.metric("Site", st.session_state.get("last_site", "Unknown")[:20] + "..." if len(st.session_state.get("last_site", "")) > 20 else st.session_state.get("last_site", "Unknown"))
    with c3:
        st.metric("Status", "✅ Ready" if st.session_state.get("active_index") else "❌ No Index")
    with c4:
        st.metric("API Key", "✅ Set" if os.environ.get("ANTHROPIC_API_KEY") else "❌ Missing")
    
    st.divider()
    
    # File management
    st.subheader("📁 File Management")
    
    json_path = Path(st.session_state["last_json"])
    search_dir = json_path.parent
    
    # Show all files in this search
    all_files = list(search_dir.glob("*.json"))
    if all_files:
        st.write(f"**Files in this search ({len(all_files)}):**")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        for i, file in enumerate(sorted(all_files, key=lambda f: f.stat().st_mtime, reverse=True)):
            with col1:
                st.write(f"📄 {file.name}")
            with col2:
                file_size = file.stat().st_size
                st.write(f"{file_size:,} bytes")
            with col3:
                st.download_button(
                    "Download", 
                    data=file.read_bytes(), 
                    file_name=file.name, 
                    mime="application/json",
                    key=f"download_{i}"
                )
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Rebuild Index", use_container_width=True, key="rebuild_index_button"):
            try:
                idx = ensure_index_for(json_path, st.session_state.get("last_site", ""))
                st.session_state["active_index"] = str(idx)
                st.success("Index rebuilt successfully!")
            except Exception as e:
                st.error(f"Failed to rebuild index: {e}")
    
    with col2:
        if st.button("🗑️ Delete This Search", use_container_width=True, key="delete_search_button"):
            if st.session_state.get("confirm_delete"):
                # Delete the search directory
                import shutil
                shutil.rmtree(search_dir)
                # Clear session state
                for key in ["last_json", "last_site", "last_count", "active_index"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("Search deleted!")
                st.rerun()
            else:
                st.session_state["confirm_delete"] = True
                st.warning("Click again to confirm deletion")
    
    with col3:
        if st.button("📋 Copy Search Info", use_container_width=True, key="copy_info_button"):
            info = f"Site: {st.session_state.get('last_site')}\nItems: {st.session_state.get('last_count')}\nFiles: {len(all_files)}\nPath: {search_dir}"
            st.code(info)
            st.success("Search info copied to clipboard!")

