import re
import os
from pelican import signals

def fix_image_paths_in_output_files(generator):
    """Fix image paths in output HTML files after generation"""
    output_path = generator.settings['OUTPUT_PATH']
    
    # Process all HTML files in the output directory
    for root, dirs, files in os.walk(output_path):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                
                try:
                    # Read the HTML file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Fix image paths like src="image.jpg" -> src="/imgs/image.jpg"
                    # Made case-insensitive to match JPG, PNG, etc.
                    new_content = re.sub(
                        r'src="(?!https?:|/|\.{1,2}/|imgs/)([\w\-]+\.(png|jpe?g|gif|webp|svg))"',
                        r'src="/imgs/\1"',
                        content,
                        flags=re.IGNORECASE
                    )
                    
                    # Write back if changed
                    if new_content != content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

def fix_image_paths_writer_finalized(generator, writer):
    """Fix image paths when writer is finalized"""
    fix_image_paths_in_output_files(generator)

def register():
    # Register for multiple signals to ensure it works in all modes
    signals.finalized.connect(fix_image_paths_in_output_files)
    signals.article_writer_finalized.connect(fix_image_paths_writer_finalized)
    signals.page_writer_finalized.connect(fix_image_paths_writer_finalized)
