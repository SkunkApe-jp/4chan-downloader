import os
import json
from pathlib import Path
import html

def generate_gallery(download_root, title="4chan Downloads"):
    """Generate HTML gallery for 4chan downloads"""
    
    root = Path(download_root)
    if not root.exists():
        raise Exception(f"Download directory not found: {root}")
    
    images_data = []
    
    # Supported extensions
    exts = ('.jpg', '.jpeg', '.png', '.gif', '.webm', '.mp4', '.pdf')
    
    # Find all images recursively
    for img_path in root.rglob("*"):
        if img_path.suffix.lower() in exts:
            # Look for matching json
            json_path = img_path.with_suffix(".json")
            metadata = {}
            if json_path.exists():
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        if metadata is None:
                            metadata = {}
                except:
                    pass
            
            # Use relative path
            try:
                rel_path = img_path.relative_to(root)
            except ValueError:
                rel_path = img_path.name
            
            # Build tags from metadata
            tags = []
            if metadata.get('board'):
                tags.append(metadata['board'])
            if metadata.get('extension'):
                tags.append(metadata['extension'])
            if metadata.get('thread_subject'):
                # Add thread subject as tag (first 3 words)
                subject_words = metadata['thread_subject'].split()[:3]
                if subject_words:
                    tags.append(' '.join(subject_words))
            if metadata.get('poster_name'):
                tags.append(metadata['poster_name'])
            
            images_data.append({
                'path': str(rel_path).replace("\\", "/"),
                'filename': str(metadata.get('id') or img_path.name),
                'original_filename': str(metadata.get('original_filename') or ''),
                'board': str(metadata.get('board') or 'Unknown'),
                'thread_subject': str(metadata.get('thread_subject') or ''),
                'file_size': str(metadata.get('file_size') or ''),
                'dimensions': str(metadata.get('dimensions') or ''),
                'timestamp': str(metadata.get('timestamp') or ''),
                'poster_name': str(metadata.get('poster_name') or ''),
                'post_number': str(metadata.get('post_number') or ''),
                'extension': str(metadata.get('extension') or img_path.suffix[1:]),
                'tags': tags
            })
    
    # Collect all unique tags
    all_tags = set()
    for img in images_data:
        for tag in img['tags']:
            all_tags.add(tag)
    sorted_tags = sorted(list(all_tags))
    
    # Helper functions
    def esc_attr(val):
        return html.escape(str(val))
    
    def json_attr(val):
        return html.escape(json.dumps(val))
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{esc_attr(title)}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #09090b;
            --card-bg: #18181b;
            --accent: #10b981;
            --accent-glow: rgba(16, 185, 129, 0.5);
            --text-main: #f4f4f5;
            --text-muted: #a1a1aa;
            --border: #27272a;
            --glass: rgba(24, 24, 27, 0.8);
        }}

        * {{ box-sizing: border-box; }}
        
        body {{
            background-color: var(--bg);
            color: var(--text-main);
            font-family: 'Outfit', sans-serif;
            margin: 0;
            padding: 0;
            min-height: 100vh;
        }}

        header {{
            padding: 60px 20px 40px;
            text-align: center;
            background: radial-gradient(circle at top, #1e1e2e 0%, transparent 70%);
        }}

        h1 {{
            font-size: 3rem;
            font-weight: 700;
            margin: 0;
            background: linear-gradient(to bottom, #ffffff, #a1a1aa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.05em;
        }}

        .stats {{
            margin-top: 15px;
            font-size: 1rem;
            color: var(--text-muted);
            font-weight: 300;
        }}

        #count {{
            color: var(--text-main);
            font-weight: 600;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 40px 60px;
        }}

        .controls {{
            position: sticky;
            top: 20px;
            z-index: 100;
            background: var(--glass);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}

        .search-wrapper {{
            position: relative;
            margin-bottom: 20px;
        }}

        .search-box {{
            width: 100%;
            background: #09090b;
            border: 1px solid var(--border);
            padding: 16px 20px;
            border-radius: 12px;
            color: white;
            font-size: 1.1rem;
            transition: all 0.3s ease;
            outline: none;
        }}

        .search-box:focus {{
            border-color: var(--accent);
            box-shadow: 0 0 0 4px var(--accent-glow);
        }}

        .tag-cloud {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            max-height: 120px;
            overflow-y: auto;
            padding-right: 10px;
        }}

        .tag-cloud::-webkit-scrollbar {{ width: 4px; }}
        .tag-cloud::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 10px; }}

        .tag-pill {{
            background: #27272a;
            border: 1px solid transparent;
            padding: 6px 14px;
            border-radius: 99px;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            color: var(--text-muted);
            user-select: none;
        }}

        .tag-pill:hover {{
            background: #3f3f46;
            color: var(--text-main);
        }}

        .tag-pill.active {{
            background: var(--accent);
            color: white;
            box-shadow: 0 4px 12px var(--accent-glow);
        }}

        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 30px;
        }}

        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
        }}

        .card:hover {{
            transform: translate-Y(-8px);
            border-color: #3f3f46;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        }}

        .img-container {{
            width: 100%;
            aspect-ratio: 16/10;
            overflow: hidden;
            cursor: zoom-in;
            background: #09090b;
        }}

        .card img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.6s ease;
        }}

        .card:hover img {{
            transform: scale(1.05);
        }}

        .card-body {{
            padding: 20px;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}

        .card-board {{
            font-weight: 700;
            color: var(--accent);
            font-size: 0.9rem;
            text-transform: uppercase;
        }}

        .dimensions {{
            font-size: 0.8rem;
            color: var(--text-muted);
            background: #27272a;
            padding: 2px 8px;
            border-radius: 4px;
        }}

        .filename {{
            font-size: 0.85rem;
            color: var(--text-main);
            margin-bottom: 8px;
            word-break: break-all;
        }}

        .original-name {{
            font-size: 0.75rem;
            color: var(--text-muted);
            font-style: italic;
            margin-bottom: 12px;
        }}

        .meta-row {{
            display: flex;
            gap: 15px;
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-bottom: 15px;
            flex-wrap: wrap;
        }}

        .meta-item b {{
            color: var(--text-main);
            font-weight: 500;
        }}

        .card-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: auto;
        }}

        .mini-tag {{
            font-size: 0.75rem;
            color: var(--text-muted);
            background: rgba(255,255,255,0.03);
            padding: 3px 8px;
            border-radius: 6px;
            border: 1px solid var(--border);
        }}

        .modal {{
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(9, 9, 11, 0.98);
            z-index: 1000;
            justify-content: center;
            align-items: center;
            padding: 40px;
            cursor: zoom-out;
            animation: fadeIn 0.3s ease;
        }}

        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}

        .modal img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            border-radius: 8px;
            box-shadow: 0 30px 60px rgba(0,0,0,0.8);
        }}

        [hidden] {{ display: none !important; }}
    </style>
</head>
<body>
    <header>
        <h1>{esc_attr(title)}</h1>
        <div class="stats">4chan Download Collection &bull; <span id="count">{len(images_data)}</span> Images</div>
    </header>

    <div class="container">
        <section class="controls">
            <div class="search-wrapper">
                <input type="text" class="search-box" id="search" placeholder="Search filenames, boards, subjects...">
            </div>
            <div class="tag-cloud" id="tagCloud">
                {"".join([f'<span class="tag-pill" data-tag="{esc_attr(t)}">{esc_attr(t)}</span>' for t in sorted_tags])}
            </div>
        </section>

        <main class="gallery" id="gallery">
            {"".join([f'''
            <div class="card" 
                 data-tags='{json_attr(img["tags"])}' 
                 data-filename="{esc_attr(img["filename"])}" 
                 data-board="{esc_attr(img["board"])}"
                 data-all="{esc_attr(img["filename"])} {esc_attr(img["board"])} {esc_attr(img["thread_subject"])} {esc_attr(img["poster_name"])} {" ".join(img["tags"])}">
                
                <div class="img-container" onclick="openModal('{esc_attr(img["path"])}')">
                    <img src="{esc_attr(img["path"])}" loading="lazy" alt="{esc_attr(img["filename"])}">
                </div>
                
                <div class="card-body">
                    <div class="card-header">
                        <span class="card-board">/{esc_attr(img["board"])}/</span>
                        <span class="dimensions">{esc_attr(img["dimensions"])}</span>
                    </div>
                    
                    <div class="filename">{esc_attr(img["filename"])}</div>
                    <div class="original-name">{esc_attr(img["original_filename"][:50] + "..." if len(img["original_filename"]) > 50 else img["original_filename"])}</div>
                    
                    <div class="meta-row">
                        <span class="meta-item"><b>{esc_attr(img["file_size"])}</b></span>
                        <span class="meta-item">No.{esc_attr(img["post_number"])}</span>
                        <span class="meta-item">{esc_attr(img["poster_name"])}</span>
                    </div>
                    
                    <div class="card-tags">
                        {" ".join([f'<span class="mini-tag">{esc_attr(tag)}</span>' for tag in img["tags"][:6]])}
                        {f'<span class="mini-tag">+{len(img["tags"])-6}</span>' if len(img["tags"]) > 6 else ''}
                    </div>
                </div>
            </div>
            ''' for img in images_data])}
        </main>
    </div>

    <div class="modal" id="modal" onclick="closeModal()">
        <img id="modalImg" src="">
    </div>

    <script>
        const cards = Array.from(document.querySelectorAll('.card'));
        const searchInput = document.getElementById('search');
        const countSpan = document.getElementById('count');
        const tagPills = document.querySelectorAll('.tag-pill');
        let activeTags = new Set();

        function filter() {{
            const query = searchInput.value.toLowerCase().trim();
            let visibleCount = 0;

            cards.forEach(card => {{
                const terms = card.dataset.all.toLowerCase();
                let cardTags = [];
                try {{
                    cardTags = JSON.parse(card.dataset.tags);
                }} catch(e) {{
                    console.error("Failed to parse tags for card", card.dataset.filename);
                }}
                
                const matchesSearch = !query || terms.includes(query);
                const matchesTags = activeTags.size === 0 || Array.from(activeTags).every(t => cardTags.includes(t));

                if (matchesSearch && matchesTags) {{
                    card.removeAttribute('hidden');
                    visibleCount++;
                }} else {{
                    card.setAttribute('hidden', '');
                }}
            }});
            countSpan.textContent = visibleCount;
        }}

        tagPills.forEach(pill => {{
            pill.addEventListener('click', () => {{
                const tag = pill.dataset.tag;
                if (activeTags.has(tag)) {{
                    activeTags.delete(tag);
                    pill.classList.remove('active');
                }} else {{
                    activeTags.add(tag);
                    pill.classList.add('active');
                }}
                filter();
            }});
        }});

        searchInput.addEventListener('input', filter);

        function openModal(src) {{
            const modal = document.getElementById('modal');
            const modalImg = document.getElementById('modalImg');
            modalImg.src = src;
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }}

        function closeModal() {{
            document.getElementById('modal').style.display = 'none';
            document.body.style.overflow = 'auto';
        }}

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') closeModal();
        }});
    </script>
</body>
</html>
"""
    
    output_path = root / "gallery.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    return str(output_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
        title = sys.argv[2] if len(sys.argv) > 2 else "4chan Downloads"
        result = generate_gallery(path, title)
        print(f"Gallery generated: {result}")
    else:
        print("Usage: python gallery_generator.py <download_path> [title]")
