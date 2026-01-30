class Database:
    def __init__(self, settings):
        self.settings = settings
        print(f"[Database] Using: {self.settings.DATABASE_URL}")
    
    def save_results(self, results):
        print(f"[Database] Saving {len(results)} query results")
        # TODO: Реальная логика сохранения в SQLite
        import datetime
        session_id = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"[Database] Created session: {session_id}")
        return session_id