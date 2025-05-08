import schedule
import time
import os
import logging
from datetime import datetime
from utils.cron.fetch_latest_data import fetch_odds
from utils.data_cleaner import process_historical

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/pipeline.log'),
        logging.StreamHandler()
    ]
)

def job_wrapper(job_func, job_name):
    """Decorator for error handling and logging"""
    def wrapped():
        try:
            start_time = datetime.now()
            logging.info(f"Starting {job_name}...")
            job_func()
            duration = (datetime.now() - start_time).total_seconds()
            logging.info(f"Completed {job_name} in {duration:.2f}s")
        except Exception as e:
            logging.error(f"Failed {job_name}: {str(e)}")
    return wrapped

# Define jobs with proper decoration
@job_wrapper("fetch live updates") # type: ignore
def daily_update():
    """Full data refresh"""
    fetch_odds()
    process_historical()
    
    # Backup data with folder check
    if not os.path.exists("data/backups"):
        os.makedirs("data/backups")
    os.system("cp data/processed/clean_matches.csv data/backups/clean_matches_$(date +%Y%m%d).csv")

@job_wrapper("weekly model training") # type: ignore
def weekly_retrain():
    """Model retraining"""
    logging.info("Starting model retraining...")
    os.system("python train_model.py >> data/training.log 2>&1")
    logging.info("Model retraining completed")

@job_wrapper("live odds refresh") # type: ignore
def live_odds_update():
    """Lightweight odds refresh"""
    odds_data = fetch_odds()
    if odds_data:
        logging.info("Live odds fetched successfully")
    else:
        logging.warning("No live odds data returned")
@job_wrapper("clean backup") # type: ignore
def cleanup_old_files():
    """Remove files older than 30 days"""
    deleted_files = os.popen("find data/backups -type f -mtime +30 -delete -print").read()
    if deleted_files:
        logging.info(f"Deleted files: \n{deleted_files}")
    else:
        logging.info("No files to delete.")

if __name__ == "__main__":
    # Create decorated job functions with names
    decorated_daily_update = job_wrapper(daily_update, "Daily Data Update")
    decorated_weekly_retrain = job_wrapper(weekly_retrain, "Weekly Model Retraining")
    decorated_live_odds_update = job_wrapper(live_odds_update, "Live Odds Refresh")
    decorated_cleanup = job_wrapper(cleanup_old_files, "Cleanup Old Files")

    # Schedule jobs
    schedule.every().day.at("09:00").do(decorated_daily_update)
    schedule.every(6).hours.do(decorated_live_odds_update)
    schedule.every().monday.at("03:00").do(decorated_weekly_retrain)
    schedule.every().sunday.at("04:00").do(decorated_cleanup)

    logging.info("🚀 Pipeline scheduler started")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logging.info("🛑 Pipeline stopped by user")
