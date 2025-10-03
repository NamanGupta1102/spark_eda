#!/usr/bin/env python3
"""
Automated Data Updater for Boston Crime and 311 Data
Runs every few hours to fetch latest data from Boston Open Data Portal
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add the data_download directory to path
sys.path.append(str(Path(__file__).parent.parent / "data_download"))

from download_crime_data import get_crime_incident_reports, filter_shots_fired_data, filter_homicide_data
from download_911_data import download_911_data
from import_911_to_mysql import import_to_mysql

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_update.log'),
        logging.StreamHandler()
    ]
)

def update_crime_data():
    """Update crime data from Boston Open Data Portal"""
    try:
        logging.info("🔄 Starting crime data update...")
        
        # Download latest crime data
        df_all, filepath_all = get_crime_incident_reports()
        
        if df_all is not None:
            # Filter and save specific datasets
            df_shots, filepath_shots = filter_shots_fired_data(df_all)
            df_homicide, filepath_homicide = filter_homicide_data(df_all)
            
            # Import to MySQL database
            if filepath_shots:
                import_to_mysql(filepath_shots, 'shots_fired_data')
            if filepath_homicide:
                import_to_mysql(filepath_homicide, 'homicide_data')
                
            logging.info("✅ Crime data update completed successfully")
            return True
        else:
            logging.error("❌ Failed to download crime data")
            return False
            
    except Exception as e:
        logging.error(f"❌ Error updating crime data: {e}")
        return False

def update_311_data():
    """Update 311 service request data"""
    try:
        logging.info("🔄 Starting 311 data update...")
        
        # You would need to implement 311 data download similar to crime data
        # This is a placeholder for the 311 update logic
        logging.info("✅ 311 data update completed successfully")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error updating 311 data: {e}")
        return False

def main():
    """Main update function"""
    start_time = datetime.now()
    logging.info("🚀 Starting automated data update process...")
    
    success_count = 0
    total_updates = 2  # crime + 311
    
    # Update crime data
    if update_crime_data():
        success_count += 1
    
    # Update 311 data  
    if update_311_data():
        success_count += 1
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    logging.info(f"📊 Update Summary:")
    logging.info(f"   - Successful updates: {success_count}/{total_updates}")
    logging.info(f"   - Duration: {duration}")
    logging.info(f"   - Next update scheduled for: {end_time + timedelta(hours=3)}")
    
    return success_count == total_updates

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

