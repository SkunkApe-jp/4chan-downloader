#!/usr/bin/env python3
"""
Build script to create executable for 4chan Downloader
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

def build_exe():
    """Build the 4chan downloader as a standalone executable"""
    
    print("Building 4chan Downloader executable...")
    
    # Clean up previous builds
    build_dirs = ['build', 'dist']
    for d in build_dirs:
        if os.path.exists(d):
            print(f"Cleaning up {d}/...")
            shutil.rmtree(d)
    
    # Find PyInstaller path
    pyinstaller_path = shutil.which('pyinstaller')
    if not pyinstaller_path:
        # Try common installation paths
        home = os.path.expanduser('~')
        pyinstaller_path = os.path.join(home, 'AppData', 'Local', 'Python', 'pythoncore-3.14-64', 'Scripts', 'pyinstaller.exe')
        if not os.path.exists(pyinstaller_path):
            print("PyInstaller not found. Please install it with: pip install pyinstaller")
            return False
    
    # PyInstaller command
    cmd = [
        pyinstaller_path,
        '--onefile',           # Single executable file
        '--windowed',          # GUI application (no console)
        '--name', 'FourChanDownloader',
        '--icon', '4chin.ico',
        '--add-data', 'fourchan_downloader.py;.',
        '--add-data', 'gallery_generator.py;.',
        '--clean',
        '--noconfirm',
        'gui.py'
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error building executable:\n{result.stderr}")
        return False
    
    print("Build successful!")
    print(f"Executable location: {Path('dist/FourChanDownloader.exe').absolute()}")
    return True

if __name__ == "__main__":
    # Check if pyinstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
    
    build_exe()
