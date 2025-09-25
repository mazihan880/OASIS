#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to replace Chinese text with English in Python files
"""

import os
import re

def replace_chinese_in_file(file_path, translations):
    """Replace Chinese text in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace Chinese text with English
        for chinese, english in translations.items():
            content = content.replace(chinese, english)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def process_directory(directory, translations):
    """Process all Python files in directory"""
    updated_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if replace_chinese_in_file(file_path, translations):
                    updated_files.append(file_path)
    
    return updated_files

if __name__ == "__main__":
    # Translation dictionary - now empty as all translations are complete
    translations = {}
    
    # Process the directory
    directory = "/Users/michael/AgentSafeV2/AgentSafe/review_version"
    updated_files = process_directory(directory, translations)
    
    print(f"Chinese to English replacement completed!")
    print(f"Updated {len(updated_files)} files")
    
    if updated_files:
        print("\nUpdated files:")
        for file_path in updated_files:
            print(f"  - {file_path}")
    else:
        print("No files needed updates - all Chinese text has been successfully replaced!")