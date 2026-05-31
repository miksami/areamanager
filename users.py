import db

def get_user(uid):
    sql = "SELECT username FROM users WHERE id = ?"
    query = db.query(sql, [uid])
    return query[0] if query else None