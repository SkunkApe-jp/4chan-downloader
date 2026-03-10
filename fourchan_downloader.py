#!/usr/bin/env python3
"""
4chan Batch Downloader Core Logic
"""

import requests
import re
import time
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
from bs4 import BeautifulSoup

class FourChanScraper:
    BASE_URL = "https://boards.4chan.org"
    CDN_URL = "https://i.4cdn.org"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://boards.4chan.org/',
        })
    
    def parse_thread_url(self, url):
        """Parse thread URL to extract board and thread ID"""
        # URL format: https://boards.4chan.org/{board}/thread/{thread_id}
        # or: https://boards.4chan.org/{board}/thread/{thread_id}/{thread_name}
        parts = url.replace('https://', '').replace('http://', '').split('/')
        
        if len(parts) < 4:
            return None
        
        board = parts[1] if 'boards.4chan.org' in parts[0] else parts[0]
        thread_id = parts[3] if parts[2] == 'thread' else None
        thread_name = parts[4] if len(parts) > 4 else thread_id
        
        if not thread_id:
            return None
        
        return {
            'board': board,
            'thread_id': thread_id,
            'thread_name': thread_name,
            'url': url
        }
    
    def get_thread_info(self, url):
        """Get thread information including title"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to get thread subject
            subject_elem = soup.select_one('.subject')
            subject = subject_elem.text.strip() if subject_elem else None
            
            # Get board title
            board_title_elem = soup.select_one('.boardTitle')
            board_title = board_title_elem.text.strip() if board_title_elem else None
            
            return {
                'subject': subject,
                'board_title': board_title,
                'url': url
            }
        except Exception as e:
            return {'subject': None, 'board_title': None, 'url': url, 'error': str(e)}
    
    def scrape_thread_images(self, url):
        """Scrape all images from a thread with metadata"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all posts with files
            posts = soup.find_all("div", {"class": "post"})
            
            images = []
            for post in posts:
                # Find file container
                file_elem = post.select_one('.file')
                if not file_elem:
                    continue
                
                # Get image link
                img_link = file_elem.select_one('a.fileThumb')
                if not img_link:
                    continue
                
                # Extract href which contains the image URL
                href = img_link.get('href', '')
                if not href:
                    continue
                
                # Extract board and filename from href
                match = re.match(r'//i(?:s|)\d*\.(?:4cdn|4chan)\.org/(\w+)/(\d+\.(\w+))', href)
                if not match:
                    continue
                
                board = match.group(1)
                filename = match.group(2)
                extension = match.group(3).lower()
                
                # Get file metadata
                file_text = file_elem.select_one('.fileText')
                file_info = self._parse_file_info(file_text) if file_text else {}
                
                # Get post metadata
                post_info = post.select_one('.postInfo')
                poster_name = None
                post_number = None
                timestamp = None
                
                if post_info:
                    name_elem = post_info.select_one('.name')
                    poster_name = name_elem.text.strip() if name_elem else None
                    
                    num_elem = post_info.select_one('span[title]')
                    if num_elem:
                        post_number = num_elem.text.strip()
                        timestamp = num_elem.get('title')
                
                # Get original filename from the fileText link
                orig_filename = None
                if file_text:
                    file_link = file_text.find('a')
                    if file_link:
                        try:
                            orig_filename = file_link['title']
                        except KeyError:
                            orig_filename = file_link.text.strip()
                
                images.append({
                    'url': f"https:{href}",
                    'board': board,
                    'filename': filename,
                    'extension': extension,
                    'original_filename': orig_filename,
                    'thread_url': url,
                    'file_size': file_info.get('size'),
                    'dimensions': file_info.get('dimensions'),
                    'md5': file_info.get('md5'),
                    'poster_name': poster_name,
                    'post_number': post_number,
                    'timestamp': timestamp
                })
            
            # Sort by filename for consistent ordering
            images.sort(key=lambda x: x['filename'])
            
            return images
            
        except requests.RequestException as e:
            return {'error': str(e)}
    
    def _parse_file_info(self, file_text_elem):
        """Parse file info from fileText element"""
        info = {}
        if not file_text_elem:
            return info
        
        text = file_text_elem.get_text()
        
        # Extract file size (e.g., "(1.23 MB, ")
        size_match = re.search(r'\(([\d.]+\s*(?:B|KB|MB|GB))', text)
        if size_match:
            info['size'] = size_match.group(1)
        
        # Extract dimensions (e.g., "1920x1080")
        dim_match = re.search(r'(\d+)x(\d+)', text)
        if dim_match:
            info['dimensions'] = f"{dim_match.group(1)}x{dim_match.group(2)}"
        
        # Extract MD5 from fileThumb data-md5 attribute if available
        # (we'll look for this in the parent)
        
        return info
    
    def get_image_titles(self, url):
        """Get original filenames from thread"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text
            
            soup = BeautifulSoup(html_content, 'html.parser')
            divs = soup.find_all("div", {"class": "fileText"})
            
            titles = []
            for div in divs:
                first_child = div.find_all("a", recursive=False)
                if first_child:
                    try:
                        title = first_child[0]["title"]
                    except KeyError:
                        title = first_child[0].text
                    titles.append(title)
            
            return titles
        except Exception as e:
            return []


class FourChanDownloader:
    def __init__(self, download_root="downloads", max_workers=5, throttle=0.5):
        self.download_root = Path(download_root)
        self.download_root.mkdir(exist_ok=True, parents=True)
        self.max_workers = max_workers
        self.throttle = throttle
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        })
    
    def download_image(self, image_info, folder, use_original_name=False, original_name=None, thread_subject=None, save_metadata=True):
        """Download a single image and optionally save metadata"""
        if use_original_name and original_name:
            # Sanitize filename
            filename = self._sanitize_filename(original_name)
        else:
            filename = image_info['filename']
        
        filepath = folder / filename
        json_path = folder / f"{filepath.stem}.json"
        
        # Skip if already exists (but save metadata if missing)
        if filepath.exists():
            if save_metadata and not json_path.exists():
                metadata = self._create_metadata(image_info, filename, thread_subject)
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=4)
            return {'status': 'skipped', 'filename': filename}
        
        url = image_info['url']
        
        try:
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Save metadata
            if save_metadata:
                metadata = self._create_metadata(image_info, filename, thread_subject)
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=4)
            
            # Throttle to avoid rate limiting
            time.sleep(self.throttle)
            
            return {'status': 'success', 'filename': filename}
            
        except Exception as e:
            return {'status': 'failed', 'filename': filename, 'error': str(e)}
    
    def _create_metadata(self, image_info, saved_filename, thread_subject=None):
        """Create metadata dict for JSON export"""
        return {
            'id': saved_filename,
            'board': image_info.get('board'),
            'thread_subject': thread_subject,
            'filename_4chan': image_info.get('filename'),
            'original_filename': image_info.get('original_filename'),
            'extension': image_info.get('extension'),
            'file_size': image_info.get('file_size'),
            'dimensions': image_info.get('dimensions'),
            'poster_name': image_info.get('poster_name'),
            'post_number': image_info.get('post_number'),
            'timestamp': image_info.get('timestamp'),
            'url': image_info.get('url')
        }
    
    def _sanitize_filename(self, filename):
        """Sanitize filename for safe filesystem storage"""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename
    
    def create_thread_folder(self, board, thread_id, thread_name=None):
        """Create folder structure for thread downloads"""
        folder_name = thread_name if thread_name else thread_id
        folder = self.download_root / board / folder_name
        folder.mkdir(exist_ok=True, parents=True)
        return folder


if __name__ == "__main__":
    print("This file is now a library. Please use gui.py or run it as a module.")
