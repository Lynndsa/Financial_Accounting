import os
import time
import logging
import threading
from datetime import datetime
from database.db import get_connection

# НАСТРОЙКА ЛОГЕРА
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(BASE_DIR, 'backups.log')

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

def clear_old_backups(backup_dir):
    """Удаление файлов бэкапов, которые старше 7 дней"""
    try:
        now = time.time()
        max_age_seconds = 7 * 24 * 60 * 60 
        
        if os.path.exists(backup_dir):
            for filename in os.listdir(backup_dir):
                file_path = os.path.join(backup_dir, filename)
                
                if os.path.isfile(file_path) and filename.endswith('.sql'):
                    file_modified_time = os.path.getmtime(file_path)
                    if (now - file_modified_time) > max_age_seconds:
                        os.remove(file_path)
                        # Пишем в лог-файл об удалении
                        logging.info(f"Ротация: удален старый бэкап {filename}")
    except Exception as e:
        logging.error(f"Ошибка при очистке старых бэкапов: {e}")

def create_sql_file():
    """Сборка полного дампа БД (структура, данные, триггеры, процедуры)"""
    backup_path = ""
    try:
        logging.info("Инициализация процесса резервного копирования.") # Лог старта
        
        conn = get_connection()
        cursor = conn.cursor()
        
        DB_NAME = conn.db.decode('utf-8') if isinstance(conn.db, bytes) else conn.db
        
        BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
            
        clear_old_backups(BACKUP_DIR)
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backup_{DB_NAME}_{timestamp}.sql"
        backup_path = os.path.join(BACKUP_DIR, filename)
        
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(f"-- Полный бэкап создан: {datetime.now()}\n\n")
            f.write("SET FOREIGN_KEY_CHECKS = 0;\n")
            f.write("SET UNIQUE_CHECKS = 0;\n")
            f.write("SET @OLD_SQL_MODE = @@SQL_MODE, SQL_MODE = '';\n\n")
            
            # 1. Выгрузка таблиц и их содержимого
            cursor.execute("SHOW TABLES")
            tables_data = cursor.fetchall()
            tables = [list(row.values())[0] for row in tables_data]
            
            for table in tables:
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                create_table_stmt = cursor.fetchone()
                create_sql = create_table_stmt.get('Create Table') or create_table_stmt.get('Create View')
                
                f.write(f"DROP TABLE IF EXISTS `{table}`;\n{create_sql};\n\n")
                
                cursor.execute(f"SELECT * FROM `{table}`")
                rows = cursor.fetchall()
                
                if rows:
                    for row in rows:
                        columns = ", ".join([f"`{k}`" for k in row.keys()])
                        values = []
                        for val in row.values():
                            if val is None:
                                values.append("NULL")
                            elif isinstance(val, (int, float)):
                                values.append(str(val))
                            elif isinstance(val, datetime):
                                values.append(f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'")
                            else:
                                values.append(f"'{str(val).replace("'", "''")}'")
                                
                        f.write(f"INSERT INTO `{table}` ({columns}) VALUES ({', '.join(values)});\n")
                    f.write("\n")
            
            # 2. Выгрузка триггеров
            cursor.execute(f"SELECT TRIGGER_NAME FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = '{DB_NAME}'")
            triggers_data = cursor.fetchall()
            if triggers_data:
                f.write("DELIMITER //\n\n")
                for trig in triggers_data:
                    trigger_name = list(trig.values())[0]
                    cursor.execute(f"SHOW CREATE TRIGGER `{trigger_name}`")
                    trig_stmt = cursor.fetchone()
                    trig_sql = trig_stmt.get('SQL Original Statement') or trig_stmt.get('sql_original_statement')
                    if trig_sql:
                        f.write(f"DROP TRIGGER IF EXISTS `{trigger_name}`//\n{trig_sql}//\n\n")
                f.write("DELIMITER ;\n\n")
            
            # 3. Парсинг хранимых процедур
            cursor.execute(f"SHOW PROCEDURE STATUS WHERE Db = '{DB_NAME}'")
            procedures_data = cursor.fetchall()
            if procedures_data:
                f.write("DELIMITER //\n\n")
                for proc in procedures_data:
                    proc_name = proc.get('Name') or proc.get('name')
                    cursor.execute(f"SHOW CREATE PROCEDURE `{proc_name}`")
                    proc_stmt = cursor.fetchone()
                    proc_sql = proc_stmt.get('Create Procedure') or proc_stmt.get('create procedure')
                    if proc_sql:
                        f.write(f"DROP PROCEDURE IF EXISTS `{proc_name}`//\n{proc_sql}//\n\n")
                f.write("DELIMITER ;\n\n")

            f.write("SET FOREIGN_KEY_CHECKS = 1;\n")
            f.write("SET UNIQUE_CHECKS = 1;\n")
            f.write("SET SQL_MODE = @OLD_SQL_MODE;\n")
            
        # Запись об успехе в лог и вывод одной строки в консоль
        logging.info(f"Успешно сформирован бэкап: {filename}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Сформирован бэкап: {filename}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        # При критической ошибке пишем всё в лог
        logging.error(f"Критическая ошибка модуля бэкапов: {e}", exc_info=True)
        print(f"Ошибка бэкапа: {e}")
        if backup_path and os.path.exists(backup_path):
            os.remove(backup_path)

def backup_loop_24h():
    """Фоновый таймер повтора раз в сутки"""
    while True:
        create_sql_file()
        time.sleep(86400)

def start_auto_backups():
    """Асинхронный запуск процесса в отдельном потоке"""
    t = threading.Thread(target=backup_loop_24h, daemon=True)
    t.start()

if __name__ == "__main__":
    try:
        create_sql_file()
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        pass