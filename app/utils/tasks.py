from app.utils.stock_service import StockService

def schedule_stock_checks(app):
    # Remove existing job if it exists
    if app.scheduler.get_job('stock_check_daily_at_midnight'):
        app.scheduler.remove_job('stock_check_daily_at_midnight')
    
    # Add new job with proper context handling
    app.scheduler.add_job(
        id='stock_check_daily_at_midnight',
        func=StockService.check_stock_levels,
        args=[app],
        trigger='cron',
        hour=0,  # 0 means midnight (12 AM)
        minute=0,
        second=0,
        replace_existing=True
    )
    print("\n⏰ Scheduled stock check to run daily at midnight (12 AM)\n")