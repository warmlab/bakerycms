from sqlalchemy import text, bindparam
from sqlalchemy import Integer, String

def clear_product_notchecked(session, table_name, product_id, param, values):
    if values:
        sql = 'DELETE FROM {0} WHERE product_id=:product_id AND {1} NOT IN (:values)'.format(table_name, param)
        t = text(sql, bindparams=[bindparam('product_id', type_=Integer, required=True),
                                 bindparam('values', type_=String, required=True)])
        session.execute(t, {"product_id": product_id, "values": values})
