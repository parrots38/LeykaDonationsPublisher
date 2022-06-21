import time
from datetime import datetime
import re
import logging.config

import telegram.error
import telegram

import Utils


log = logging.getLogger("main.PublisherBot")


class Bot:
    RUN_COMMAND = r"\s*?/run\s*?(-[0-9]+|@\w+)\s*"  # "/run -1234567890" or "/run @abcdef124gh"
    ADMIN_COMMAND = r"\s*?/(header|footer|run)\s*(?=\w|@)(.*)(?<=\w)"  # /run or /footer or /header
    PRIVATE_MESSAGE = r"^[0-9]+$"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    FUNNY_BALLS = ["Умный Лосяш", "Трудолюбивый Копатыч", "Задорный Крош", "Изобретательный Пин", "Мудрый Кар-Карыч",
                   "Мечтающий Ежик", "Философствующий Бараш"]

    def __init__(self, token, name, admin_id, db_client, open_names):
        self._bot = telegram.Bot(token)
        self._name = name
        self._admin_id = admin_id
        self._db_client = db_client
        self._open_names = open_names

    def send_message(self, ids, message):
        """ Send message by id or all listeners.

        :param ids: list of strings, list of ids or channel names;
        :param message: string, message to send;
        :return: None
        """

        wrong_ids = []
        for uid in ids:
            log.info("Bot's sending message [%s] to [%s].", message, str(uid))
            try:
                self._bot.send_message(uid, message)
            except telegram.error.TelegramError as exc:
                log.warning(exc)
                wrong_ids.append(uid)

        return wrong_ids

    def get_updates(self, offset):
        """ Get only message updates.
        :param offset: int, updates offset;
        :return: list of telegram.Update.
        """

        all_updates = []
        old_offset = offset
        while len(all_updates) < 1000:
            updates = self._bot.get_updates(offset=offset, timeout=0, allowed_updates=["message"])
            if not updates:
                break
            offset = updates[-1].update_id + 1
            all_updates += updates

        log.info("Bot got [%i] updates.", len(all_updates))
        if offset != old_offset:
            self._db_client.set_telegram_updates_offset(offset)
        return all_updates

    def handle_updates(self, updates):
        """ Handle updates.
        If update is "left_chat_member", delete group ID from DB.
        If update is "group_chat_created" or "supergroup_chat_created", insert group ID to DB.
        If update is "new_chat_members", insert group ID to DB.
        If update is "text", valid message and insert sent ID to DB.

        :param updates: list of updates, list of telegram.Update.
        :return: None.
        """

        def _get_info_message():
            return f'{self._db_client.get_header()}\nЯк Яков пожертовал 100 rub\n...\n{self._db_client.get_footer()}'

        for update in updates:
            message = update.message
            if message:
                sender_id = str(message.chat.id)
                if message.group_chat_created or message.supergroup_chat_created:
                    log.info("Handling update: new group with id = [%s].", sender_id)
                    self._db_client.set_channel_id(sender_id)
                elif message.new_chat_members:
                    for new_member in message.new_chat_members:
                        if new_member.is_bot and str(new_member.username) == self._name:
                            log.info("Handling update: added in group with id = [%s].", sender_id)
                            self._db_client.set_channel_id(sender_id)
                elif message.text and re.match(Bot.PRIVATE_MESSAGE, sender_id):
                    log.info("Handling update: new message = [%s].", message.text)
                    if sender_id == str(self._admin_id):
                        match = re.match(Bot.ADMIN_COMMAND, message.text, re.IGNORECASE | re.DOTALL)
                        if match.group(1) == "header":
                            header = match.group(2)
                            log.info("Adding header [%s] to DB.", header)
                            self._db_client.set_header(header)
                            self.send_message([sender_id],
                                              f"Header added. Info message is looking like:\n{_get_info_message()}")
                            return
                        elif match.group(1) == "footer":
                            footer = match.group(2)
                            log.info("Adding footer [%s] to DB.", footer)
                            self._db_client.set_footer(footer)
                            self.send_message([sender_id],
                                              f"Footer added. Info message is looking like:\n{_get_info_message()}")
                            return
                        elif match.group(1) == "run":
                            pass

                    match = re.match(Bot.RUN_COMMAND, message.text, re.IGNORECASE)
                    if not match:
                        self.send_message([sender_id], "Not valid command. Please, write: /run @channel_name.")
                    else:
                        channel = match.group(1)
                        log.info("Adding channel [%s] to mailing list.", channel)
                        self._db_client.set_channel_id(channel)
                        self.send_message([sender_id], f"Channel {channel} added to publishing list.")

    def get_news(self, donations):
        """ Return a message to send to users from the donation information.

        :param donations: list of tuples, [(id, date, title, status, donor_name, amount), (...), ...].
        :return: str.
        """

        def get_true_donations(raw_donations):
            true_donations = []
            last_time = 0
            last_name = last_amount = last_email = ""
            for uid, date, title, status, donor_name, donor_email, amount in raw_donations:
                current_time = time.mktime(date.timetuple())
                # if a user couldn't pay the first time or duplicate
                if (current_time - last_time) < 10 * 60:
                    if donor_name == last_name and amount == last_amount and donor_email == last_email:
                        log.debug("Skip donation: user = [%s], amount = [%s].", donor_name, amount)
                        continue
                last_time = current_time
                last_name = donor_name
                last_email = donor_email
                last_amount = amount
                true_donations.append((uid, date, title, status, donor_name, donor_email, amount))
            log.debug("Got [%i] donations, selected [%i] donations.", len(raw_donations), len(true_donations))
            return true_donations

        donations = get_true_donations(donations)
        header = self._db_client.get_header()
        footer = self._db_client.get_footer()
        message = header + "\n"

        titles_set = {donation[2] for donation in donations}
        for title in titles_set:
            message += f'Назначение - "{title}":\n'
            for uid, date, _title, status, donor_name, donor_email, amount in donations:
                if title == _title:
                    if not self._open_names:
                        donor_name = "Некий " + random.choice(self.FUNNY_BALLS)
                    donation_info_message = f'- "{donor_name}" пожертвовал {amount}\n'
                    if len(message) + len(footer) + len(donation_info_message) < 4096:
                        message += donation_info_message
        message += footer

        return message


