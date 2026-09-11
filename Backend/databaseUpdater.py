"""
handles updating the database
"""

import sqlite3

class databaseUpdater:
    def __init__(self):
        self.connection = sqlite3.connect("../stocks.db")

x = databaseUpdater()
