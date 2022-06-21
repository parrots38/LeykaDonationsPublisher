import logging.config

import mysql.connector


log = logging.getLogger("main.Database.Donations")


class MySqlConnection:
    GET_DONATIONS_UPDATES = """
    SELECT p.id, p.post_modified, p.post_title, p.post_status, pm3.meta_value as 'donor_name', pm4.meta_value as 'donor_email', CONCAT(pm1.meta_value, ' ', pm2.meta_value) AS 'amount'
    FROM tqogx_posts p, tqogx_postmeta pm1, tqogx_postmeta pm2, tqogx_postmeta pm3, tqogx_postmeta pm4
    WHERE p.id > %s AND p.post_type = 'leyka_donation' AND
    p.id = pm1.post_id AND p.id = pm2.post_id AND p.id = pm3.post_id AND p.id = pm4.post_id AND
    pm1.meta_key = 'leyka_donation_amount' AND pm2.meta_key = 'leyka_donation_currency' AND pm3.meta_key = 'leyka_donor_name' AND pm4.meta_key = 'leyka_donor_email'
    ORDER BY ID DESC
    """

    def __init__(self, config):
        """
        :param config: dict of config data: user, password, host, database, raise_on_warnings.
        """
        self._config = config
        self._offset = 0

        log.debug("Connecting to MySql database [%s].", self._config["database"])
        self._connect = mysql.connector.connect(**self._config)
        self._cursor = self._connect.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        log.debug("Closing connect to MySql database [%s].", self._config["database"])
        self._cursor.close()
        self._connect.close()

    def get_offset(self):
        return self._offset

    def get_donations_updates(self, offset):
        """ Return donations updates.

        :param offset: int.
        :return: list of strings.
        """

        log.info("Selecting donations updates from MySQL DB with offset [%i]:\n%s.", offset, MySqlConnection.GET_DONATIONS_UPDATES)
        result = None
        try:
            self._cursor.execute(MySqlConnection.GET_DONATIONS_UPDATES, (str(offset), ))
            result = self._cursor.fetchall()
            log.info("Selected [%i] results.", len(result))
            log.debug("Selected results:%s", "\n".join(str(t) for t in result))
        except mysql.connector.errors.Error as err:
            log.error("Error when selecting donations updates:\n%s", err)
        if result:
            self._offset = int(result[0][0])  # SQL query must to order by desc
            return result
