#!/usr/bin/env python3
"""
Yardi PowerBI Web Dashboard Setup Script
Automated setup and initialization
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_data_directory():
    """Check if Yardi data directory exists"""
    data_path = Path("../Data/Yardi_Tables")
    
    if not data_path.exists():
        print(f"❌ Data directory not found: {data_path}")
        print("   Please ensure Yardi CSV files are in the correct location")
        return False
    
    csv_files = list(data_path.glob("*.csv"))
    if len(csv_files) == 0:
        print(f"❌ No CSV files found in: {data_path}")
        return False
    
    total_size = sum(f.stat().st_size for f in csv_files) / 1024 / 1024
    print(f"✅ Found {len(csv_files)} CSV files ({total_size:.1f}MB)")
    return True

def initialize_database():
    """Initialize the DuckDB database"""
    print("🗄️ Initializing database...")
    try:
        # Change to database directory and run init script
        os.chdir("database")
        result = subprocess.run([sys.executable, "init_db.py"], 
                               capture_output=True, text=True, timeout=300)
        os.chdir("..")
        
        if result.returncode == 0:
            print("✅ Database initialized successfully")
            return True
        else:
            print(f"❌ Database initialization failed:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Database initialization timed out (>5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

def create_directories():
    """Create required directories"""
    directories = ["logs", "static", "database"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Directories created")

def test_dashboard():
    """Test that the dashboard can start"""
    print("🧪 Testing dashboard startup...")
    try:
        # Try to import main modules
        import streamlit
        import duckdb
        import pandas
        import plotly
        
        print("✅ Core modules imported successfully")
        
        # Try to connect to database
        db_path = Path("database/yardi.duckdb")
        if db_path.exists():
            conn = duckdb.connect(str(db_path), read_only=True)
            tables = conn.execute("SHOW TABLES").fetchall()
            conn.close()
            print(f"✅ Database accessible with {len(tables)} tables")
            return True
        else:
            print("❌ Database file not found")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")
        return False

def main():
    """Main setup routine"""
    print("🏢 Yardi PowerBI Web Dashboard Setup")
    print("=" * 50)
    
    success = True
    
    # Step 1: Check Python version
    if not check_python_version():
        success = False
    
    # Step 2: Create directories
    create_directories()
    
    # Step 3: Install dependencies
    if success and not install_dependencies():
        success = False
    
    # Step 4: Check data directory
    if success and not check_data_directory():
        success = False
    
    # Step 5: Initialize database
    if success and not initialize_database():
        success = False
    
    # Step 6: Test dashboard
    if success and not test_dashboard():
        success = False
    
    print("=" * 50)
    
    if success:
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run the dashboard: streamlit run app.py")
        print("2. Open browser to: http://localhost:8501")
        print("3. Explore your Yardi data!")
        
        # Ask if user wants to start dashboard now
        start_now = input("\nStart dashboard now? (y/n): ").lower().strip()
        if start_now in ['y', 'yes']:
            print("Starting dashboard...")
            try:
                subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
            except KeyboardInterrupt:
                print("\nDashboard stopped")
    else:
        print("❌ Setup failed. Please check the errors above and try again.")
        print("\nCommon solutions:")
        print("- Ensure Python 3.8+ is installed")
        print("- Check that CSV data is in ../Data/Yardi_Tables/")
        print("- Try: pip install --upgrade pip setuptools")
        sys.exit(1)

if __name__ == "__main__":
    main()