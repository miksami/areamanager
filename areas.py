import db

def get_area(aid):
    sql = "SELECT a.uid uid, a.name name, a.description description, u.username author FROM areas a, users u WHERE a.id = ? AND a.uid = u.id"
    query = db.query(sql, [aid])
    return query[0] if query else None