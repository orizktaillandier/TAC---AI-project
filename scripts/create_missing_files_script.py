#!/usr/bin/env python3
"""
Script to create the missing UI pages and schema files for the Automotive Ticket Classifier.
Run this from your project root directory.
"""
import os
import json
from pathlib import Path

def create_directory_structure():
    """Create the required directory structure."""
    directories = [
        "ui/pages",
        "data/schema"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Create __init__.py files for Python packages
    init_files = [
        "ui/pages/__init__.py"
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
        print(f"✅ Created: {init_file}")

def create_files():
    """Create all the missing files."""
    
    # Files that should be created (these are the artifacts above)
    files_to_create = [
        "ui/pages/classifier.py",
        "ui/pages/management.py", 
        "ui/pages/analytics.py",
        "ui/pages/settings.py",
        "data/schema/classification.json",
        "data/schema/ticket.json",
        "data/schema/api_response.json"
    ]
    
    existing_files = []
    missing_files = []
    
    for file_path in files_to_create:
        if Path(file_path).exists():
            existing_files.append(file_path)
        else:
            missing_files.append(file_path)
    
    if existing_files:
        print("\n📄 Files that already exist:")
        for file_path in existing_files:
            print(f"   {file_path}")
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} files:")
        for file_path in missing_files:
            print(f"   {file_path}")
        
        print("\n🛠️  To create these files, copy the content from the artifacts shown above.")
        print("   Each artifact shows the filename and complete content to copy.")
    else:
        print("\n✅ All required files exist!")
    
    return missing_files

def verify_imports():
    """Verify that the import structure will work."""
    print("\n🔍 Verifying import structure...")
    
    required_files = [
        "ui/pages/__init__.py",
        "ui/pages/classifier.py",
        "ui/pages/management.py",
        "ui/pages/analytics.py", 
        "ui/pages/settings.py"
    ]
    
    all_exist = all(Path(f).exists() for f in required_files)
    
    if all_exist:
        print("✅ All UI page files exist - imports should work")
    else:
        print("❌ Some UI page files missing - imports will fail")
        
    return all_exist

def create_placeholder_files():
    """Create placeholder files with basic structure."""
    placeholders = {
        "ui/pages/__init__.py": '"""\nUI pages package.\n"""\n',
        
        "ui/pages/classifier.py": '''"""
Classifier page for the Streamlit UI.
"""
import streamlit as st

def render_classifier_page(api_client):
    """Render the classifier page."""
    st.title("🎯 Ticket Classifier")
    st.info("This page will contain the ticket classification interface.")
    # TODO: Implement classification interface
''',
        
        "ui/pages/management.py": '''"""
Ticket management page for the Streamlit UI.
"""
import streamlit as st

def render_management_page(api_client):
    """Render the ticket management page."""
    st.title("📋 Ticket Management")
    st.info("This page will contain batch processing and ticket search.")
    # TODO: Implement management interface
''',
        
        "ui/pages/analytics.py": '''"""
Analytics page for the Streamlit UI.
"""
import streamlit as st

def render_analytics_page(api_client):
    """Render the analytics page."""
    st.title("📊 Analytics")
    st.info("This page will contain performance metrics and charts.")
    # TODO: Implement analytics interface
''',
        
        "ui/pages/settings.py": '''"""
Settings page for the Streamlit UI.
"""
import streamlit as st

def render_settings_page(api_client):
    """Render the settings page."""
    st.title("⚙️ Settings")
    st.info("This page will contain configuration options.")
    # TODO: Implement settings interface
''',
        
        "data/schema/classification.json": json.dumps({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Classification Schema",
            "type": "object",
            "properties": {
                "contact": {"type": "string"},
                "dealer_name": {"type": "string"},
                "dealer_id": {"type": "string"},
                "rep": {"type": "string"},
                "category": {"type": "string"},
                "sub_category": {"type": "string"},
                "syndicator": {"type": "string"},
                "inventory_type": {"type": "string"}
            }
        }, indent=2),
        
        "data/schema/ticket.json": json.dumps({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Ticket Schema",
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "subject": {"type": "string"},
                "description": {"type": "string"}
            }
        }, indent=2),
        
        "data/schema/api_response.json": json.dumps({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "API Response Schema",
            "type": "object"
        }, indent=2)
    }
    
    created_count = 0
    
    for file_path, content in placeholders.items():
        if not Path(file_path).exists():
            # Create parent directories
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Created placeholder: {file_path}")
            created_count += 1
        else:
            print(f"⏩ Skipped existing: {file_path}")
    
    return created_count

def main():
    """Main function."""
    print("🚀 Setting up missing files for Automotive Ticket Classifier")
    print("=" * 60)
    
    # Create directory structure
    create_directory_structure()
    
    # Check what files are missing
    missing_files = create_files()
    
    if missing_files:
        print(f"\n🤔 Would you like to create placeholder files for the {len(missing_files)} missing files?")
        print("   (You can then replace them with the full content from the artifacts)")
        
        response = input("\nCreate placeholders? (y/n): ").lower().strip()
        
        if response in ['y', 'yes']:
            created = create_placeholder_files()
            print(f"\n✅ Created {created} placeholder files")
            print("\n📝 Next steps:")
            print("   1. Replace placeholder content with full implementations from artifacts")
            print("   2. Test the UI by running: streamlit run ui/main.py")
            print("   3. Verify all pages load correctly")
        else:
            print("\n📋 To create the files manually:")
            print("   1. Copy content from each artifact above")
            print("   2. Save to the corresponding file path")
            print("   3. Ensure proper directory structure")
    
    # Verify imports will work
    verify_imports()
    
    print("\n🎯 Setup complete!")

if __name__ == "__main__":
    main()
