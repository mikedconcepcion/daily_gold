import os
import markdown
from jinja2 import Environment, FileSystemLoader
import shutil
import glob
import re

def extract_section(content, header_regex):
    """
    Extracts a section starting with a header matching the regex
    until the next header of the same level or higher.
    """
    lines = content.split('\n')
    in_section = False
    section_content = []
    
    for line in lines:
        if re.match(header_regex, line):
            in_section = True
            continue # Skip the header itself if we just want content, or keep it.
                     # For sidebar, we might want to strip the header and use our own.
            
        if in_section:
            # Check if we hit the next header
            if re.match(r'^#{1,3}\s', line):
                break
            section_content.append(line)
            
    return "\n".join(section_content).strip()

def parse_fear_meter(content):
    """Extracts Fear Factor Score and ASCII."""
    # Look for the Fear Factor section
    # Regex for the ASCII meter
    ascii_match = re.search(r'FEAR \[.*\] GREED', content)
    ascii_art = ""
    if ascii_match:
        # Grab the line and maybe the next few lines (triangle arrow and score)
        start = ascii_match.start()
        # Find the next double newline or end of section
        end_match = re.search(r'\n\s*\n', content[start:])
        if end_match:
            ascii_art = content[start:start+end_match.start()]
        else:
            ascii_art = content[start:]
            
    # Extract Score
    score_match = re.search(r'Score:\s*(\d+/10)', content)
    score_label_match = re.search(r'Score:\s*\d+/10\s*—\s*(.*)', content)
    
    score = score_match.group(1) if score_match else "?/10"
    label = score_label_match.group(1).strip() if score_label_match else ""
    
    return {
        "ascii": ascii_art,
        "score": score,
        "label": label
    }

def parse_tally(content):
    """Extracts the Scorecard/Tally table."""
    # Look for Scorecard section
    match = re.search(r'##.*Scorecard[\s\S]*?(?=##|$)', content, re.IGNORECASE)
    if match:
        section = match.group(0)
        # Extract the table part
        table_match = re.search(r'\|.*\|[\s\S]*?(\n\n|$)', section)
        if table_match:
            # Convert markdown table to HTML via markdown lib
            return markdown.markdown(table_match.group(0), extensions=['tables'])
    return None

def build_site():
    # Setup paths
    content_dir = "content/reports"
    output_dir = "public"
    template_dir = "templates"
    static_dir = "static"

    # Clean output directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    # Copy static assets
    shutil.copytree(static_dir, os.path.join(output_dir, "static"))
    
    # Copy root PWA files (manifest & service worker) if they exist
    if os.path.exists(os.path.join(static_dir, "service-worker.js")):
         shutil.copy(os.path.join(static_dir, "service-worker.js"), os.path.join(output_dir, "service-worker.js"))
    
    if os.path.exists(os.path.join(static_dir, "manifest.json")):
         shutil.copy(os.path.join(static_dir, "manifest.json"), os.path.join(output_dir, "manifest.json"))
         
    # Create Favicon from Logo (Fix 404)
    if os.path.exists(os.path.join(static_dir, "images", "logo.png")):
         shutil.copy(os.path.join(static_dir, "images", "logo.png"), os.path.join(output_dir, "favicon.ico"))

    # Setup Jinja2
    env = Environment(loader=FileSystemLoader(template_dir))
    post_template = env.get_template("post.html")
    index_template = env.get_template("index.html")
    
    # Process Posts
    posts = []
    for filepath in glob.glob(os.path.join(content_dir, "*.md")):
        with open(filepath, "r", encoding="utf-8") as f:
            raw_content = f.read()
            
        # Parse Frontmatter
        frontmatter = {}
        content_body = raw_content
        if raw_content.startswith("---"):
            parts = raw_content.split("---", 2)
            if len(parts) >= 3:
                fm_lines = parts[1].strip().split("\n")
                for line in fm_lines:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        frontmatter[key.strip()] = value.strip().strip('"')
                content_body = parts[2].strip()
        
        # Extract Sidebar Data
        fear_data = parse_fear_meter(content_body)
        tally_html = parse_tally(content_body)
        
        # Remove Fear Factor section from main content
        content_body_clean = re.sub(r'##.*Fear Factor.*[\s\S]*?(?=##)', '', content_body, flags=re.IGNORECASE)
        # Fallback if last section
        if "Fear Factor" in content_body and "##" not in content_body.split("Fear Factor")[1]:
             content_body_clean = re.sub(r'##.*Fear Factor.*[\s\S]*', '', content_body, flags=re.IGNORECASE)

        # Remove Scorecard section from main content if extracted
        if tally_html:
            content_body_clean = re.sub(r'##.*Scorecard[\s\S]*?(?=##)', '', content_body_clean, flags=re.IGNORECASE)
            # Fallback if it's the last section (unlikely for Scorecard but possible)
            if "Scorecard" in content_body_clean:
                 # Check if it's at the end or stuck
                 pass
        
        # Convert Fear Score to Percentage for the Bar
        fear_percent = 50 # Default
        if fear_data['score'] != "?/10":
            try:
                num = int(fear_data['score'].split('/')[0])
                fear_percent = num * 10
            except:
                pass

        # Try to parse Zone Map for better visuals
        # This regex looks for lines like "4,355-4,360 ... Description" inside the Zone Map section
        # We can extract the map content first
        zone_map_html = ""
        zone_section = re.search(r'## Liquidity & Zone Map([\s\S]*?)(?=##|$)', content_body, re.IGNORECASE)
        if zone_section:
            raw_map = zone_section.group(1)
            # Find lines with prices and descriptions
            # Example: 4,355-4,360 ░░░░░░ Buy-stop Liquidity
            # Regex: (PriceRange) (Visuals) (Description)
            # We want to maybe just highlight the price and description
            
            # Let's simple format it to a custom HTML structure
            # We can use regex to wrap lines in divs
            
            lines = raw_map.strip().split('\n')
            formatted_lines = []
            for line in lines:
                line = line.strip()
                if not line or "══" in line or "ZONE MAP" in line:
                    continue
                
                # Highlight Prices (digits, comma, dash)
                # pattern: start of line, digits
                # Check if line starts with price
                price_match = re.match(r'^([0-9,]+(?:-[0-9,]+)?)', line)
                if price_match:
                    price = price_match.group(1)
                    rest = line[len(price):].strip()
                    # Remove visual bars like ░ or ▓ if possible, or keep them but styled
                    # Let's try to identify the type based on text
                    row_class = "zone-neutral"
                    
                    # Detection Logic
                    if "Current Price" in rest:
                        row_class = "zone-current"
                    elif "Liquidity" in rest or "Stops" in rest:
                         row_class = "zone-liquidity"
                         if "Buy-stop" in rest or "High" in rest:
                             row_class += " zone-liquidity-top"
                         else:
                             row_class += " zone-liquidity-bottom"
                    elif "Sell" in rest or "Resistance" in rest or "Target" in rest:
                        row_class = "zone-resistance"
                    elif "Buy" in rest or "Support" in rest:
                        row_class = "zone-support"
                    
                    # Clean rest of visual noise
                    desc = re.sub(r'[░▓●]+', '', rest).strip()
                    desc = re.sub(r'Wait for.*', '', desc).strip() # specific cleanup
                    
                    formatted_lines.append(f'<div class="zone-row {row_class}"><span class="zone-price">{price}</span><span class="zone-desc">{desc}</span></div>')
                else:
                     # Maybe a box wrapper line or empty
                     pass
            
            if formatted_lines:
                zone_map_html = f'<div class="visual-zone-map">{"".join(formatted_lines)}</div>'
                
                # Replace the ASCII map in content_body_clean with our HTML
                # We search for the header and the following code block
                # Regex: ## Liquidity & Zone Map\n\n    ASCII...
                # We can replace the whole section content.
                
                # First, locate the section in content_body_clean
                # Note: content_body_clean might have other sections removed already
                
                # Replace the specific code block if possible, or the whole section body
                pattern = r'(## Liquidity & Zone Map\s*\n)(?:    |```|   ).*?(?=\n##|\Z)'
                # This regex is tricky for indented blocks.
                
                # Alternative: Just replace "## Liquidity & Zone Map" with "## Liquidity & Zone Map\n" + zone_map_html
                # and REMOVE the ascii block.
                
                # Let's try to remove the ASCII block first.
                # It usually starts with indentation or backticks.
                
                # Robust approach: 
                # 1. Remove the existing ASCII block from content_body_clean to avoid it rendering.
                # 2. Append/Insert the zone_map_html after the header.
                
                # Find header
                header_match = re.search(r'## Liquidity & Zone Map', content_body_clean, re.IGNORECASE)
                if header_match:
                    # Remove everything until next header (or end of string)
                    start_idx = header_match.end()
                    end_match = re.search(r'\n##', content_body_clean[start_idx:])
                    end_idx = start_idx + end_match.start() if end_match else len(content_body_clean)
                    
                    # Construct new content: Header + New HTML + Rest
                    # We keep the header, insert our HTML, then the next section starts
                    
                    new_section_content = f"\n\n{zone_map_html}\n\n"
                    
                    content_body_clean = content_body_clean[:start_idx] + new_section_content + content_body_clean[end_idx:]

        # Convert Markdown to HTML
        html_content = markdown.markdown(content_body_clean, extensions=['extra', 'tables', 'fenced_code'])
        
        # Generate TLDR Snippet
        # Strategy: Prioritize "Momentum View" quote for enticing/minimal TLDR.
        # Fallback to "Recap" if not found.
        snippet = ""
        
        # 1. Try Momentum View Quote
        quote_match = re.search(r'## Momentum View\s*\n\s*>\s*"?([\s\S]*?)"?\s*(?=\n|$)', content_body)
        if quote_match:
            snippet = quote_match.group(1).replace('\n', ' ').strip()
        else:
            # 2. Try "Recap:" text
            recap_match = re.search(r'\*\*Recap:\*\*\s*([\s\S]*?)(?=\n##|$)', content_body)
            if recap_match:
                 snippet = recap_match.group(1).strip()
            else:
                # 3. Fallback: First paragraph after "Overnight Recap"
                clean_text = re.sub(r'<[^>]+>', '', html_content)
                sentences = clean_text.split('.')
                if len(sentences) > 0:
                    snippet = sentences[0].strip() + "."

        # Clean Markdown characters (bold, italics)
        snippet = re.sub(r'\*\*|__|\*|_', '', snippet)
        
        # Truncate if too long (keep it enticing and short)
        if len(snippet) > 140:
            # Try to cut at last space
            snippet = snippet[:137]
            last_space = snippet.rfind(' ')
            if last_space > 0:
                snippet = snippet[:last_space]
            snippet += "..."
            
        # Clean Title (Aggressive)
        clean_title = frontmatter.get("title", "Untitled")
        # Just use the session name if available, it's the most intuitive title "London Session"
        if frontmatter.get("session"):
            clean_title = frontmatter.get("session")
        elif "Report -" in clean_title:
             clean_title = clean_title.split("Report -")[0].strip()

        post_data = {
            "title": clean_title,
            "original_title": frontmatter.get("title", "Untitled"),
            "date": frontmatter.get("date", "Unknown Date"),
            "session": frontmatter.get("session", ""),
            "content": html_content,
            "filename": os.path.basename(filepath).replace(".md", ".html"),
            "snippet": snippet,
            "fear_factor": True if fear_data['score'] != "?/10" else False,
            "fear_score": fear_data['score'],
            "fear_label": fear_data['label'],
            "fear_percent": fear_percent
        }
        
        posts.append(post_data)
        
        # Render Post Page
        rendered_post = post_template.render(post=post_data, title=post_data["title"])
        post_path = os.path.join(output_dir, post_data["filename"])
        with open(post_path, "w", encoding="utf-8") as f:
            f.write(rendered_post)
            
        print(f"Generated {post_path}")

    # Sort posts by date/filename reverse
    posts.sort(key=lambda x: x["filename"], reverse=True)

    # Render Index Page
    rendered_index = index_template.render(posts=posts, title="Daily Gold Reports")
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(rendered_index)
        
    print("Site build complete.")

if __name__ == "__main__":
    build_site()
