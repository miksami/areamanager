import sqlite3
from flask import g

def get_connection():
    con = sqlite3.connect("database.db")
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con

def execute(sql, params=[]):
    try:
        con = get_connection()
        result = con.execute(sql, params)
        con.commit()
        g.last_insert_id = result.lastrowid
        con.close()
    except Exception as e:
        con.close() # if an exception occurs while modifying tables, they will stay locked. we catch this exception, close the connection, and re-raise the exception
        raise e

def last_insert_id():
    return g.last_insert_id    
    
def query(sql, params=[]):
    try:
        con = get_connection()
        result = con.execute(sql, params).fetchall()
    except Exception as e:
        con.close()
        raise e
    con.close()
    return result
