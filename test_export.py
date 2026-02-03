from data_export import export_daily_news
import os

# Export in all formats
formats = ['json', 'csv', 'xml', 'parquet']
for fmt in formats:
    try:
        filename = export_daily_news(fmt, 'exports')
        print(f'Exported {fmt}: {filename}')
    except Exception as e:
        print(f'Error exporting {fmt}: {e}')
