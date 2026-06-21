from app.utils.stock_service import StockService

def schedule_stock_checks(app):
    # Remove existing job if it exists
    if app.scheduler.get_job('stock_check_daily_at_noon'):
        app.scheduler.remove_job('stock_check_daily_at_noon')
    
    # Added a new job to run daily at 12 PM (noon)
    app.scheduler.add_job(
        id='stock_check_daily_at_noon',
        func=StockService.check_stock_levels,
        args=[app],
        trigger='cron',
        hour=12,  # (12 PM)
        minute=0,
        second=0,
        replace_existing=True
    )
    print("\n⏰ Scheduled stock check to run daily at noon (12 PM)\n")