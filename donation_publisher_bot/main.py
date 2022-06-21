import yaml
import logging
import time

import Utils
from Database import Data, Donations
from PublisherBot import Bot


logging.config.dictConfig(Utils.get_config("logging.yaml"))
log = logging.getLogger("main")


def main(open_names):
    config = Utils.get_config("config.yaml")
    bot_config = config["bot"]
    db_donations_config = config["database"]["donations"]
    db_data_config = config["database"]["data"]

    with Donations.MySqlConnection(db_donations_config) as db_donations_client:
        with Data.SQLite(db_data_config["db_name"]) as db_data_client:
            bot = Bot(bot_config["token"], bot_config["name"], bot_config["admin_id"], db_data_client, open_names)
            tg_offset = db_data_client.get_telegram_updates_offset()
            updates = bot.get_updates(tg_offset)
            if updates:
                bot.handle_updates(updates)

            ids = db_data_client.get_channel_ids()
            if ids:
                donations_offset = db_data_client.get_leyka_updates_offset()
                donations = db_donations_client.get_donations_updates(donations_offset)
                if donations:
                    message = bot.get_news(donations)
                    wrong_ids = bot.send_message(ids, message)
                    for uid in wrong_ids:
                        db_data_client.remove_channel_id(uid)

                    db_data_client.set_leyka_updates_offset(db_donations_client.get_offset())


if __name__ == "__main__":
    args = Utils.get_args()
    if args.loop:
        while True:
            main(args.open_names)
            time.sleep(args.sleep * 60)
    else:
        main(args.open_names)

