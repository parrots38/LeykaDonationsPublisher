import logging.config
import sqlite3


log = logging.getLogger("main.Database.Data")


class SQLite:
    OFFSETS_TABLE = "publisher_offsets"
    CHANNELS_TABLE = "publisher_channels"
    MESSAGE_TABLE = "publisher_message"
    TABLES_NAMES = {OFFSETS_TABLE, CHANNELS_TABLE, MESSAGE_TABLE}
    TABLES_CREATE = {
        OFFSETS_TABLE: [
            f"CREATE TABLE {OFFSETS_TABLE} (name TEXT, value INTEGER);",
            f"INSERT INTO {OFFSETS_TABLE} VALUES ('telegram', 0);",
            f"INSERT INTO {OFFSETS_TABLE} VALUES ('leyka', 0);"
        ],
        CHANNELS_TABLE: [f"CREATE TABLE {CHANNELS_TABLE} (name TEXT)"],
        MESSAGE_TABLE: [
            f"CREATE TABLE {MESSAGE_TABLE} (field TEXT, value TEXT);",
            f"INSERT INTO {MESSAGE_TABLE} VALUES ('header', 'Hi! It is a header. Change me plz.');",
            f"INSERT INTO {MESSAGE_TABLE} VALUES ('footer', 'There is a footer. Change me plz.');"
        ]
    }

    def __init__(self, db_name):
        self._telegram_updates_offset = 0
        self._leyka_updates_offset = 0
        self._db_name = db_name

        log.debug("Connecting to SQLite database [%s].", self._db_name)
        try:
            self._connect = sqlite3.connect(self._db_name)
            self._cursor = self._connect.cursor()
        except sqlite3.Error as err:
            log.error("Error when connecting to SQLite database [%s]:\n%s", self._db_name, err)

        self._create_tables(self._check_tables())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        log.debug("Closing connect to SQLite database [%s].", self._db_name)
        self._cursor.close()
        self._connect.close()

    def _execute_query(self, query, params=None):
        """ Execute query by params.

        :param query: str, query.
        :param params: tuple, tuple of values for query.
        :return: None
        """

        if params:
            str_params = ", ".join(str(p) for p in params)
            log.debug("Executing query [%s] with params [%s].", query, str_params)
            try:
                self._cursor.execute(query, params)
            except sqlite3.Error as err:
                log.error("Error when executing query [%s] with params [%s]:\n%s", query, str_params, err)
                raise
        else:
            log.debug("Executing query [%s].", query)
            try:
                self._cursor.execute(query)
            except sqlite3.Error as err:
                log.error("Error when executing query [%s]:\n%s", query, err)
                raise

    def _check_tables(self):
        """ Check, that tables from TABLES_NAMES exist.

        :return: set, not exist tables.
        """
        self._cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables_list = self._cursor.fetchall()
        tables_set = {result[0] for result in tables_list}
        not_exist_tables = SQLite.TABLES_NAMES - tables_set
        if not_exist_tables:
            log.warning("Not exist tables [%s].", ", ".join(not_exist_tables))
        return not_exist_tables

    def _create_tables(self, tables):
        """ Create tables from tables list.

        :param tables: list, list of tables names for create.
        :return: None
        """
        if tables:
            log.info("Creating tables: [%s].", ", ".join(tables))
            for table in tables:
                for query in SQLite.TABLES_CREATE[table]:
                    self._execute_query(query)
            self._connect.commit()

    def set_channel_id(self, uid):
        uid = str(uid)
        if uid not in self.get_channel_ids():
            log.info("Setting channel id = [%s].", uid)
            self._execute_query(f"INSERT INTO {SQLite.CHANNELS_TABLE} VALUES (?)", (uid, ))
            self._connect.commit()
        else:
            log.info("Channel id = [%s] is already in the DB.", uid)

    def remove_channel_id(self, uid):
        log.info("Removing channel id = [%s].", str(uid))
        self._execute_query(f"DELETE FROM {SQLite.CHANNELS_TABLE} WHERE name = ?", (uid, ))
        self._connect.commit()

    def get_channel_ids(self):
        """ Return list of strings - channels names."""
        self._execute_query(f"SELECT name FROM {SQLite.CHANNELS_TABLE}")
        channels_list = self._cursor.fetchall()
        channels = [str(tup[0]) for tup in channels_list]
        log.debug("Returned channels: [%s]", ", ".join(channels))
        return channels

    def _set_updates_offset(self, name, offset):
        log.info("Setting %s updates offset to [%i].", name, offset)
        self._execute_query(f"UPDATE {SQLite.OFFSETS_TABLE} SET value = ? WHERE name = ?", (offset, name))
        self._connect.commit()

    def set_telegram_updates_offset(self, offset):
        self._set_updates_offset("telegram", offset)

    def set_leyka_updates_offset(self, offset):
        self._set_updates_offset("leyka", offset)

    def _get_updates_offset(self, name):
        """ Return int - name update's offset."""
        self._execute_query(f"SELECT MAX(value) FROM {SQLite.OFFSETS_TABLE} WHERE name = ?", (name, ))
        values_list = self._cursor.fetchall()
        offset = int(values_list[0][0])
        log.debug("Returned %s updates offset = [%i]", name, offset)
        return offset

    def get_telegram_updates_offset(self):
        return self._get_updates_offset("telegram")

    def get_leyka_updates_offset(self):
        return self._get_updates_offset("leyka")

    def _get_message_field(self, field):
        self._execute_query(f"SELECT value FROM {SQLite.MESSAGE_TABLE} WHERE field = ?", (field, ))
        values_list = self._cursor.fetchall()
        value = values_list[0][0]
        log.debug("Returned message's %s = [%s]", field, value)
        return value

    def get_header(self):
        return self._get_message_field("header")

    def get_footer(self):
        return self._get_message_field("footer")

    def _set_message_field(self, field, value):
        log.info("Setting message's %s to [%s].", field, value)
        self._execute_query(f"UPDATE {SQLite.MESSAGE_TABLE} SET value = ? WHERE field = ?", (value, field))
        self._connect.commit()

    def set_header(self, value):
        self._set_message_field("header", value)

    def set_footer(self, value):
        self._set_message_field("footer", value)
