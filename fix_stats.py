#!/usr/bin/env python3
"""
Fix Stats File - Ensure proper structure
"""

import json
import os

STATS_FILE = 'stats.json'

def fix_stats():
    """Fix or create proper stats file"""
    default_stats = {
        'total_sent': 0,
        'last_run': None,
        'groups': {}
    }
    
    try:
        # Try to load existing stats
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            
            # Ensure all required keys exist
            for key, value in default_stats.items():
                if key not in stats:
                    stats[key] = value
                    print(f"✅ Added missing key: {key}")
            
            print("📊 Current stats:")
            print(f"   Total sent: {stats.get('total_sent', 0)}")
            print(f"   Groups tracked: {len(stats.get('groups', {}))}")
            
        else:
            stats = default_stats
            print("📊 Creating new stats file")
        
        # Save corrected stats
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=4)
        
        print("✅ Stats file fixed/created successfully!")
        
    except Exception as e:
        print(f"❌ Error fixing stats: {e}")
        # Create default stats as fallback
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_stats, f, indent=4)
        print("✅ Created default stats file as fallback")

if __name__ == "__main__":
    fix_stats()
