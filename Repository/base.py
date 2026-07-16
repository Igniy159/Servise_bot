from sqlite3 import Connection

class Repo:
    def __init__(self, con: Connection):
        self.con = con
