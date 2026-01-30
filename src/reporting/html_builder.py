class HTMLBuilder:
    def __init__(self, settings):
        self.settings = settings
        print(f"[Reporter] Reports will go to: {self.settings.REPORTS_DIR}")
    
    def generate_daily_report(self, session_id):
        print(f"[Reporter] Generating HTML report for session: {session_id}")
        # TODO: Реальная генерация HTML таблицы
        import datetime
        report_file = self.settings.REPORTS_DIR / f"report_{session_id}.html"
        
        html_content = f"""
        <html>
        <head><title>SEO Report {session_id}</title></head>
        <body>
            <h1>SEO Report</h1>
            <p>Session: {session_id}</p>
            <p>Generated: {datetime.datetime.now()}</p>
            <table border="1">
                <tr><th>Query</th><th>Position</th><th>URL</th></tr>
                <tr><td colspan="3">Report will be here</td></tr>
            </table>
        </body>
        </html>
        """
        
        report_file.write_text(html_content)
        print(f"[Reporter] Report saved to: {report_file}")
        return str(report_file)