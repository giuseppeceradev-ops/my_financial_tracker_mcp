from abc import abstractmethod
import os



class Database:
    def __init__(self, folder_path:str, db_name: str):
        self.db_dir = folder_path
        os.makedirs(self.db_dir, exist_ok=True)

        self.db_name = os.path.join(self.db_dir, db_name)
        self.init_db()

    # -------------------------
    # INIT
    # -------------------------
    @abstractmethod
    def init_db(self):
        pass