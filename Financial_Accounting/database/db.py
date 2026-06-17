import pymysql


def get_connection():
    return pymysql.connect(
        host='141.8.192.31',
        user='a1279252_financy',
        password='Romashka_130',
        database='a1279252_financy',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
