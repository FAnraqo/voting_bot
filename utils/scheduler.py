from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from config import VOTING_END_TIME
from handlers.end_voting import notify_results
from datetime import datetime

scheduler = AsyncIOScheduler()

async def setup_scheduler(app):
    end_time = datetime.strptime(VOTING_END_TIME, '%Y-%m-%d %H:%M:%S')
    scheduler.add_job(notify_results, DateTrigger(run_date=end_time), args=[app])
    scheduler.start()
