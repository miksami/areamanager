import db

def get_item(iid):
    sql = "SELECT i.aid aid, i.uid uid, i.name name, u.username author FROM items i, users u WHERE i.id = ? AND i.uid = u.id"
    query = db.query(sql, [iid])
    return query[0] if query else None