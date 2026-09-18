import os
import shutil
from datetime import datetime

def perform_automated_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    if os.path.exists("edupredict.db"):
        shutil.copy("edupredict.db", f"{backup_dir}/edupredict.db")
        print(f"[BACKUP] Copied edupredict.db -> {backup_dir}/edupredict.db")
        
    if os.path.exists("data"):
        shutil.copytree("data", f"{backup_dir}/data", dirs_exist_ok=True)
        print(f"[BACKUP] Copied data/ -> {backup_dir}/data")
        
    if os.path.exists("models"):
        shutil.copytree("models", f"{backup_dir}/models", dirs_exist_ok=True)
        print(f"[BACKUP] Copied models/ -> {backup_dir}/models")
        
    print(f"[SUCCESS] Backup saved to {backup_dir}")

if __name__ == "__main__":
    perform_automated_backup()
