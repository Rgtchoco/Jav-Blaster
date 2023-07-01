# -*- coding: UTF-8 -*-
import concurrent.futures
import math
import os
import re
import string
import typing
import random
import jvav
import asyncio
import threading
import langdetect
import lxml  # for bs4
import telebot
from pyrogram import Client
from telebot import apihelper, types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from logger import Logger
from config import BotConfig
from database import BotFileDb, BotCacheDb


# TG 地址
BASE_URL_TG = "https://t.me"
# MissAv 地址
BASE_URL_MISS_AV = "https://missav.com"
# 项目地址
PROJECT_ADDRESS = "https://github.com/akynazh/tg-jav-bot"
# 默认使用官方机器人: https://t.me/PikPak6_Bot
PIKPAK_BOT_NAME = "PikPak6_Bot"
# 联系作者
CONTACT_AUTHOR = f"{BASE_URL_TG}/jackbryant286"
# 文件存储目录位置
PATH_ROOT = f'{os.path.expanduser("~")}/.tg_jav_bot'
# 日志文件位置
PATH_LOG_FILE = f"{PATH_ROOT}/log.txt"
# 记录文件位置
PATH_RECORD_FILE = f"{PATH_ROOT}/record.json"
# my_account.session 文件位置
PATH_SESSION_FILE = f"{PATH_ROOT}/my_account"
# 配置文件位置
PATH_CONFIG_FILE = f"config.yaml"
# 正则匹配 AV
AV_PAT = re.compile(r"[a-z0-9]+[-_](?:ppv-)?[a-z0-9]+")
# 帮助消息
MSG_HELP = f"""Hey, I am Powerful an AV Fan!

/help - Need any help!
/stars - View favorite actors.
/avs - View favorite product codes.
/nice - Get a random highly rated product.
/new - Get a random latest product.
/rank - Get the DMM actress ranking.
/record - Get the favorite records file.
/star [actor name]
/av [product code]

⚠️ ᴘᴏᴡᴇʀᴇᴅ ʙʏ Jᴀᴠ Bʟᴀsᴛᴇʀ
"""
BOT_CMDS = {
    "help": "View command help",
    "stars": "View favorite actors",
    "avs": "View favorite AV codes",
    "nice": "Get a random high-rated AV",
    "new": "Get a random latest AV",
    "rank": "Get DMM actress ranking",
    "record": "Get favorite records file",
    "star": "Followed by actor's name to search for the actor",
    "av": "Followed by AV code to search for the AV",
}


if not os.path.exists(PATH_ROOT):
    os.makedirs(PATH_ROOT)
LOG = Logger(path_log_file=PATH_LOG_FILE).logger
BOT_CFG = BotConfig(PATH_CONFIG_FILE)
apihelper.proxy = BOT_CFG.proxy_json
BOT = telebot.TeleBot(BOT_CFG.tg_bot_token)
BOT_DB = BotFileDb(PATH_RECORD_FILE)
BOT_CACHE_DB = BotCacheDb(
    host=BOT_CFG.redis_host, port=BOT_CFG.redis_port, use_cache=BOT_CFG.use_cache
)
BASE_UTIL = jvav.BaseUtil(BOT_CFG.proxy_addr)
DMM_UTIL = jvav.DmmUtil(BOT_CFG.proxy_addr_dmm)
JAVBUS_UTIL = jvav.JavBusUtil(BOT_CFG.proxy_addr)
JAVLIB_UTIL = jvav.JavLibUtil(BOT_CFG.proxy_addr)
SUKEBEI_UTIL = jvav.SukebeiUtil(BOT_CFG.proxy_addr)
TRANS_UTIL = jvav.TransUtil(BOT_CFG.proxy_addr)
WIKI_UTIL = jvav.WikiUtil(BOT_CFG.proxy_addr)
AVGLE_UTIL = jvav.AvgleUtil(BOT_CFG.proxy_addr)


class BotKey:
    """callback key value."""

    KEY_GET_SAMPLE_BY_ID = "k0_0"
    KEY_GET_MORE_MAGNETS_BY_ID = "k0_1"
    KEY_SEARCH_STAR_BY_NAME = "k0_2"
    KEY_GET_TOP_STARS = "k0_3"
    KEY_WATCH_PV_BY_ID = "k1_0"
    KEY_WATCH_FV_BY_ID = "k1_1"
    KEY_GET_AV_BY_ID = "k2_0"
    KEY_RANDOM_GET_AV_BY_STAR_ID = "k2_1"
    KEY_RANDOM_GET_AV_NICE = "k2_2"
    KEY_RANDOM_GET_AV_NEW = "k2_3"
    KEY_GET_NEW_AVS_BY_STAR_NAME_ID = "k2_4"
    KEY_GET_NICE_AVS_BY_STAR_NAME = "k2_5"
    KEY_RECORD_STAR_BY_STAR_NAME_ID = "k3_0"
    KEY_RECORD_AV_BY_ID_STAR_IDS = "k3_1"
    KEY_GET_STARS_RECORD = "k3_2"
    KEY_GET_AVS_RECORD = "k3_3"
    KEY_GET_STAR_DETAIL_RECORD_BY_STAR_NAME_ID = "k3_4"
    KEY_GET_AV_DETAIL_RECORD_BY_ID = "k3_5"
    KEY_UNDO_RECORD_STAR_BY_STAR_NAME_ID = "k3_6"
    KEY_UNDO_RECORD_AV_BY_ID = "k3_7"
    KEY_DEL_AV_CACHE = "k4_1"


class BotUtils:
    """Bot Utils"""

    def __init__(self):
        pass

    def send_action_typing(self):
        """Display typing action"""
        BOT.send_chat_action(chat_id=BOT_CFG.tg_chat_id, action="typing")

    def send_msg(self, msg: str, pv=False, markup=None):
        """Send message

        :param str msg: Message text content
        :param bool pv: Whether to show preview, default is False
        :param InlineKeyboardMarkup markup: Markup, default is None
        """
        BOT.send_message(
            chat_id=BOT_CFG.tg_chat_id,
            text=msg,
            disable_web_page_preview=not pv,
            parse_mode="HTML",
            reply_markup=markup,
        )

    def send_msg_code_op(self, code: int, op: str):
        """Send message based on status code and operation description

        :param int code: Status code
        :param str op: Operation description
        """
        if code == 200:
            self.send_msg(
                f"""Executing operation: {op}
Execution result: Success ^_^"""
            )
        elif code == 404:
            self.send_msg(
                f"""Executing operation: {op}
Execution result: Not found Q_Q"""
            )
        elif code == 500:
            self.send_msg(
                f"""Executing operation: {op}
Execution result: Server error, please retry or check the logs Q_Q"""
            )
        elif code == 502:
            self.send_msg(
                f"""Executing operation: {op}
Execution result: Network request failed, please retry or check the network Q_Q"""
            )

    def send_msg_success_op(self, op: str):
        """Send message for successful operation

        :param str op: Operation description
        """
        self.send_msg(
            f"""Executing operation: {op}
Execution result: Success ^_^"""
        )

    def send_msg_fail_reason_op(self, reason: str, op: str):
        """Send message for failed operation with reason

        :param str reason: Failure reason
        :param str op: Operation description
        """
        self.send_msg(
            f"""Executing operation: {op}
Execution result: Failure, {reason} Q_Q"""
        )

    def check_success(self, code: int, op: str) -> bool:
        """Check status code to confirm if the request was successful

        :param int code: Status code
        :param str op: Operation description
        :return bool: Whether the request was successful or not
        """
        if code == 200:
            return True
        if code == 404:
            self.send_msg_code_op(code=404, op=op)
        elif code == 500:
            self.send_msg_code_op(code=500, op=op)
        elif code == 502:
            self.send_msg_code_op(code=502, op=op)
        return False

    def create_btn_by_key(self, key_type: str, obj) -> InlineKeyboardButton:
        """Create a button based on the button type

        :param str key_type: Button type
        :param any obj: Data object
        :return InlineKeyboardButton: Button object
        """
        if key_type == BotKey.KEY_GET_STAR_DETAIL_RECORD_BY_STAR_NAME_ID:
            return InlineKeyboardButton(
                text=obj["name"], callback_data=f'{obj["name"]}|{obj["id"]}:{key_type}'
            )
        elif key_type == BotKey.KEY_GET_AV_DETAIL_RECORD_BY_ID:
            return InlineKeyboardButton(text=obj, callback_data=f"{obj}:{key_type}")
        elif key_type == BotKey.KEY_SEARCH_STAR_BY_NAME:
            return InlineKeyboardButton(text=obj, callback_data=f"{obj}:{key_type}")
        elif key_type == BotKey.KEY_GET_AV_BY_ID:
            return InlineKeyboardButton(
                text=f'{obj["id"]} | {obj["rate"]}',
                callback_data=f'{obj["id"]}:{key_type}',
            )

    def send_msg_btns(
        self,
        max_btn_per_row: int,
        max_row_per_msg: int,
        key_type: str,
        title: str,
        objs: list,
        extra_btns=[],
        page_btns=[],
    ):
        """Send button message

        :param int max_btn_per_row: Maximum number of buttons per row
        :param int max_row_per_msg: Maximum number of rows per message
        :param str key_type: Button type
        :param str title: Message title
        :param list objs: Data object array
        :param list extra_btns: Additional button list, 2-dimensional array, corresponds to the actual button arrangement, default is empty
        :param list page_btns: Pagination block
        """
        # Initialize data
        markup = InlineKeyboardMarkup()
        row_count = 0
        btns = []
        # Start generating buttons and sending messages
        for obj in objs:
            btns.append(self.create_btn_by_key(key_type, obj))
            # If the number of buttons in a row reaches max_btn_per_row, add the row
            if len(btns) == max_btn_per_row:
                markup.row(*btns)
                row_count += 1
                btns = []
            # If the number of rows in the message reaches max_row_per_msg, send the message
            if row_count == max_row_per_msg:
                for extra_btn in extra_btns:
                    markup.row(*extra_btn)
                if page_btns != []:
                    markup.row(*page_btns)
                self.send_msg(msg=title, markup=markup)
                row_count = 0
                markup = InlineKeyboardMarkup()
        # If the current row's button count is not 0, add the row
        if btns != []:
            markup.row(*btns)
            row_count += 1
        # If the current row count is not 0, send the message
        if row_count != 0:
            for extra_btn in extra_btns:
                markup.row(*extra_btn)
            if page_btns != []:
                markup.row(*page_btns)
            self.send_msg(msg=title, markup=markup)

    def get_page_elements(
        self, objs: list, page: int, col: int, row: int, key_type: str
    ) -> typing.Tuple[list, list, str]:
        """Get the current page object list, pagination button list, and quantity title

        :param list objs: All objects
        :param int page: Current page
        :param int col: Number of columns per page
        :param int row: Number of rows per page
        :param str key_type: Key type
        :return tuple[list, list, str]: Current page object list, pagination button list, quantity title
        """
        # Record the total count
        record_count_total = len(objs)
        # Records per page
        record_count_per_page = col * row
        # Number of pages
        if record_count_per_page > record_count_total:
            page_count = 1
        else:
            page_count = math.ceil(record_count_total / record_count_per_page)
        # If the requested page is greater than the total number of pages, set the requested page to the last page
        if page > page_count:
            page = page_count
        # Get the current page object list
        start_idx = (page - 1) * record_count_per_page
        objs = objs[start_idx : start_idx + record_count_per_page]
        # Get the button list
        if page == 1:
            to_previous = 1
        else:
            to_previous = page - 1
        if page == page_count:
            to_next = page_count
        else:
            to_next = page + 1
        btn_to_first = InlineKeyboardButton(text="<<", callback_data=f"1:{key_type}")
        btn_to_previous = InlineKeyboardButton(
            text="<", callback_data=f"{to_previous}:{key_type}"
        )
        btn_to_current = InlineKeyboardButton(
            text=f"-{page}-", callback_data=f"{page}:{key_type}"
        )
        btn_to_next = InlineKeyboardButton(
            text=">", callback_data=f"{to_next}:{key_type}"
        )
        btn_to_last = InlineKeyboardButton(
            text=">>", callback_data=f"{page_count}:{key_type}"
        )
        # Get the quantity title
        title = f"Total: <b>{record_count_total}</b>, Total pages: <b>{page_count}</b>"
        return (
            objs,
            [btn_to_first, btn_to_previous, btn_to_current, btn_to_next, btn_to_last],
            title,
        )

    def get_stars_record(self, page=1):
        """Get actor/actress collection records.
    
        :param int page: Page number, default is the first page.
        """
        # Initialize data
        record, is_star_exists, _ = BOT_DB.check_has_record()
        if not record or not is_star_exists:
            self.send_msg_fail_reason_op(reason="No actor/actress collection records found", op="Get actor/actress collection records")
            return
        stars = record["stars"]
        stars.reverse()
        col, row = 4, 5
        objs, page_btns, title = self.get_page_elements(
            objs=stars,
            page=page,
            col=col,
            row=row,
            key_type=BotKey.KEY_GET_STARS_RECORD,
        )
        # Send button message
        self.send_msg_btns(
            max_btn_per_row=col,
            max_row_per_msg=row,
            key_type=BotKey.KEY_GET_STAR_DETAIL_RECORD_BY_STAR_NAME_ID,
            title="<b>Favorite Actors/Actresses: </b>" + title,
            objs=objs,
            page_btns=page_btns,
        )
    
    def get_star_detail_record_by_name_id(self, star_name: str, star_id: str):
        """Get more information about an actor/actress based on their name and ID.
    
        :param str star_name: Actor/actress name
        :param str star_id: Actor/actress ID
        """
        # Initialize data
        record, is_stars_exists, is_avs_exists = BOT_DB.check_has_record()
        if not record:
            self.send_msg(reason="No collection records found for this actor/actress", op=f"Get more information about actor/actress <code>{star_name}</code>")
            return
        avs = []
        star_avs = []
        cur_star_exists = False
        if is_avs_exists:
            avs = record["avs"]
            avs.reverse()
            for av in avs:
                # If the actor/actress ID is in the list of actor/actress IDs for this AV
                if star_id in av["stars"]:
                    star_avs.append(av["id"])
        if is_stars_exists:
            stars = record["stars"]
            for star in stars:
                if star["id"].lower() == star_id.lower():
                    cur_star_exists = True
        # Send button message
        extra_btn1 = InlineKeyboardButton(
            text="Random AV",
            callback_data=f"{star_name}|{star_id}:{BotKey.KEY_RANDOM_GET_AV_BY_STAR_ID}",
        )
        extra_btn2 = InlineKeyboardButton(
            text="Latest AV",
            callback_data=f"{star_name}|{star_id}:{BotKey.KEY_GET_NEW_AVS_BY_STAR_NAME_ID}",
        )
        extra_btn3 = InlineKeyboardButton(
            text="High-rated AV",
            callback_data=f"{star_name}:{BotKey.KEY_GET_NICE_AVS_BY_STAR_NAME}",
        )
        if cur_star_exists:
            extra_btn4 = InlineKeyboardButton(
                text="Remove from collection",
                callback_data=f"{star_name}|{star_id}:{BotKey.KEY_UNDO_RECORD_STAR_BY_STAR_NAME_ID}",
            )
        else:
            extra_btn4 = InlineKeyboardButton(
                text="Add to collection",
                callback_data=f"{star_name}|{star_id}:{BotKey.KEY_RECORD_STAR_BY_STAR_NAME_ID}",
            )
        title = f'<code>{star_name}</code> | <a href="{WIKI_UTIL.BASE_URL_JAPAN_WIKI}/{star_name}">Wiki</a> | <a href="{JAVBUS_UTIL.BASE_URL_SEARCH_BY_STAR_ID}/{star_id}">Javbus</a>'
        if len(star_avs) == 0:  # No collection records found for this actor/actress
            markup = InlineKeyboardMarkup()
            markup.row(extra_btn1, extra_btn2, extra_btn3, extra_btn4)
            self.send_msg(msg=title, markup=markup)
            return
        self.send_msg_btns(
            max_btn_per_row=4,
            max_row_per_msg=10,
            key_type=BotKey.KEY_GET_AV_DETAIL_RECORD_BY_ID,
            title=title,
            objs=star_avs,
            extra_btns=[[extra_btn1, extra_btn2, extra_btn3, extra_btn4]],
        )
    
    def get_avs_record(self, page=1):
        """Get AV (Adult Video) collection records.
    
        :param int page: Page number, default is the first page.
        """
        # Initialize data
        record, _, is_avs_exists = BOT_DB.check_has_record()
        if not record or not is_avs_exists:
            self.send_msg_fail_reason_op(reason="No AV collection records found", op="Get AV collection records")
            return
        avs = [av["id"] for av in record["avs"]]
        avs.reverse()
        # Send button message
        extra_btn1 = InlineKeyboardButton(
            text="Random high-rated AV",
            callback_data=f"0:{BotKey.KEY_RANDOM_GET_AV_NICE}"
        )
        extra_btn2 = InlineKeyboardButton(
            text="Random latest AV",
            callback_data=f"0:{BotKey.KEY_RANDOM_GET_AV_NEW}"
        )
        col, row = 4, 10
        objs, page_btns, title = self.get_page_elements(
            objs=avs, page=page, col=col, row=row, key_type=BotKey.KEY_GET_AVS_RECORD
        )
        self.send_msg_btns(
            max_btn_per_row=col,
            max_row_per_msg=row,
            key_type=BotKey.KEY_GET_AV_DETAIL_RECORD_BY_ID,
            title="<b>Favorite AVs: </b>" + title,
            objs=objs,
            extra_btns=[[extra_btn1, extra_btn2]],
            page_btns=page_btns,
        )

    def get_av_detail_record_by_id(self, id: str):
        """Get more information about an AV (Adult Video) based on its ID.
    
        :param str id: AV ID
        """
        record, _, is_avs_exists = BOT_DB.check_has_record()
        avs = record["avs"]
        cur_av_exists = False
        for av in avs:
            if id.lower() == av["id"].lower():
                cur_av_exists = True
        markup = InlineKeyboardMarkup()
        btn = InlineKeyboardButton(
            text="Get corresponding AV",
            callback_data=f"{id}:{BotKey.KEY_GET_AV_BY_ID}",
        )
        if cur_av_exists:
            markup.row(
                btn,
                InlineKeyboardButton(
                    text="Remove from collection",
                    callback_data=f"{id}:{BotKey.KEY_UNDO_RECORD_AV_BY_ID}",
                ),
            )
        else:
            markup.row(btn)
        self.send_msg(msg=f"<code>{id}</code>", markup=markup)
    
    def get_av_by_id(
        self,
        id: str,
        send_to_pikpak=False,
        is_nice=True,
        is_uncensored=True,
        magnet_max_count=3,
        not_send=False,
    ) -> dict:
        """Get AV (Adult Video) based on its ID.
    
        :param str id: AV ID
        :param bool send_to_pikpak: Whether to send to pikpak, default is False
        :param bool is_nice: Whether to filter for high-quality videos with subtitles, default is True
        :param bool is_uncensored: Whether to filter for uncensored videos, default is True
        :param int magnet_max_count: Maximum number of filtered magnets, default is 3
        :param not_send: Whether to not send the AV result, default is False
        :return dict: If not_send is True, return the obtained AV (if any)
        """
        # Get AV
        op_get_av_by_id = f"Search for AV with ID <code>{id}</code>"
        av = BOT_CACHE_DB.get_cache(key=id, type=BotCacheDb.TYPE_AV)
        av_score = None
        is_cache = False
        futures = {}
        if not av or not_send:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                if not not_send:
                    futures[
                        executor.submit(DMM_UTIL.get_score_by_id, id)
                    ] = 0  # Get AV score
                futures[
                    executor.submit(
                        JAVBUS_UTIL.get_av_by_id,
                        id,
                        is_nice,
                        is_uncensored,
                        magnet_max_count,
                    )
                ] = 1  # Get AV from Javbus
                futures[
                    executor.submit(
                        SUKEBEI_UTIL.get_av_by_id,
                        id,
                        is_nice,
                        is_uncensored,
                        magnet_max_count,
                    )
                ] = 2  # Get AV from Sukebei
                for future in concurrent.futures.as_completed(futures):
                    future_type = futures[future]
                    if future_type == 0:
                        _, av_score = future.result()
                    elif future_type == 1:
                        code_javbus, av_javbus = future.result()
                    elif future_type == 2:
                        code_sukebei, av_sukebei = future.result()
            if code_javbus != 200 and code_sukebei != 200:
                if code_javbus == 502 or code_sukebei == 502:
                    self.send_msg_code_op(502, op_get_av_by_id)
                else:
                    self.send_msg_code_op(404, op_get_av_by_id)
                return
            if code_javbus == 200:  # Prefer Javbus
                av = av_javbus
            elif code_sukebei == 200:
                av = av_sukebei
            av["score"] = av_score
            if not not_send:
                if len(av["magnets"]) == 0:
                    BOT_CACHE_DB.set_cache(
                        key=id, value=av, type=BotCacheDb.TYPE_AV, expire=3600 * 24 * 1
                    )
                else:
                    BOT_CACHE_DB.set_cache(key=id, value=av, type=BotCacheDb.TYPE_AV)
        else:
            av_score = av["score"]
            is_cache = True
        if not_send:
            return av
        # Extract data
        av_id = id
        av_title = av["title"]
        av_img = av["img"]
        av_date = av["date"]
        av_tags = av["tags"]
        av_stars = av["stars"]
        av_magnets = av["magnets"]
        av_url = av["url"]
        # Compose message
        msg = ""
        # Title
        if av_title != "":
            av_title_ch = TRANS_UTIL.trans(
                text=av_title, from_lang="ja", to_lang="en"
            )
            if av_title_ch:
                av_title = av_title_ch
            av_title = av_title.replace("<", "").replace(">", "")
            msg += f"""【Title】<a href="{av_url}">{av_title}</a>
"""
        # ID
        msg += f"""【ID】<code>{av_id}</code>
"""
        # Date
        if av_date != "":
            msg += f"""【Date】{av_date}
"""
        # Score
        if av_score:
            msg += f"""【Score】{av_score}
"""
        # Stars
        if av_stars != []:
            show_star_name = av_stars[0]["name"]
            show_star_id = av_stars[0]["id"]
            stars_msg = BOT_CACHE_DB.get_cache(
                key=av_id, type=BotCacheDb.TYPE_STARS_MSG
            )
            if not stars_msg:
                stars_msg = ""
                futures = {}
                more_star_msg = ""
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    for i, star in enumerate(av_stars):
                        # Exit if count is greater than 5
                        if i >= 5:
                            more_star_msg = f"""【Stars】<a href="{av_url}">View more......</a>
"""
                            break
                        # Get search name
                        name = star["name"]
                        other_name_start = name.find("(")  # Remove alias
                        if other_name_start != -1:
                            name = name[:other_name_start]
                            star["name"] = name
                        # Get Chinese Wiki from Japanese Wiki
                        futures[
                            executor.submit(
                                WIKI_UTIL.get_wiki_page_by_lang, name, "ja", "zh"
                            )
                        ] = i
                    for future in concurrent.futures.as_completed(futures):
                        future_type = futures[future]
                        wiki_json = future.result()
                        wiki = f"{WIKI_UTIL.BASE_URL_JAPAN_WIKI}/{name}"
                        name = av_stars[future_type]["name"]
                        link = f'{JAVBUS_UTIL.BASE_URL_SEARCH_BY_STAR_ID}/{av_stars[future_type]["id"]}'
                        if wiki_json and wiki_json["lang"] == "zh":
                            name_zh = wiki_json["title"]
                            wiki_zh = wiki_json["url"]
                            stars_msg += f"""【Stars】<code>{name_zh}</code> | <a href="{wiki_zh}">Wiki</a> | <a href="{link}">Javbus</a>
"""
                        else:
                            stars_msg += f"""【Stars】<code>{name}</code> | <a href="{wiki}">Wiki</a> | <a href="{link}">Javbus</a>
"""
                if more_star_msg != "":
                    stars_msg += more_star_msg
                BOT_CACHE_DB.set_cache(
                    key=av_id, value=stars_msg, type=BotCacheDb.TYPE_STARS_MSG
                )
            msg += stars_msg
        # Tags
        if av_tags != "":
            av_tags = av_tags.replace("<", "").replace(">", "")
            msg += f"""【Tags】{av_tags}

"""
        # Other
        msg += f"""【Other】<a href="{BASE_URL_TG}/{PIKPAK_BOT_NAME}">Pikpak</a> | <a href="{PROJECT_ADDRESS}">Project</a> | <a href="{CONTACT_AUTHOR}">Author</a>
"""
        # Magnet
        magnet_send_to_pikpak = ""
        for i, magnet in enumerate(av_magnets):
            if i == 0:
                magnet_send_to_pikpak = magnet["link"]
            magnet_tags = ""
            if magnet["uc"] == "1":
                magnet_tags += "Uncensored "
            if magnet["hd"] == "1":
                magnet_tags += "HD "
            if magnet["zm"] == "1":
                magnet_tags += "Subtitles "
            msg_tmp = f"""【{magnet_tags}Magnet-{string.ascii_letters[i].upper()} {magnet["size"]}】<code>{magnet["link"]}</code>
"""
            if len(msg + msg_tmp) >= 2000:
                break
            msg += msg_tmp
        # Generate callback buttons
        # First row buttons
        pv_btn = InlineKeyboardButton(
            text="Preview", callback_data=f"{av_id}:{BotKey.KEY_WATCH_PV_BY_ID}"
        )
        fv_btn = InlineKeyboardButton(
            text="Watch", callback_data=f"{av_id}:{BotKey.KEY_WATCH_FV_BY_ID}"
        )
        sample_btn = InlineKeyboardButton(
            text="Screenshot", callback_data=f"{av_id}:{BotKey.KEY_GET_SAMPLE_BY_ID}"
        )
        more_btn = InlineKeyboardButton(
            text="More Magnets", callback_data=f"{av_id}:{BotKey.KEY_GET_MORE_MAGNETS_BY_ID}"
        )
        if len(av_magnets) != 0:
            markup = InlineKeyboardMarkup().row(sample_btn, pv_btn, fv_btn, more_btn)
        else:
            markup = InlineKeyboardMarkup().row(sample_btn, pv_btn, fv_btn)
        # Second row buttons
        # Star record button
        star_record_btn = None
        if len(av_stars) == 1:
            if BOT_DB.check_star_exists_by_id(star_id=show_star_id):
                star_record_btn = InlineKeyboardButton(
                    text="Star Record",
                    callback_data=f"{show_star_name}|{show_star_id}:{BotKey.KEY_GET_STAR_DETAIL_RECORD_BY_STAR_NAME_ID}",
                )
            else:
                star_record_btn = InlineKeyboardButton(
                    text=f"Record {show_star_name}",
                    callback_data=f"{show_star_name}|{show_star_id}:{BotKey.KEY_RECORD_STAR_BY_STAR_NAME_ID}",
                )
        star_ids = ""
        for i, star in enumerate(av_stars):
            star_ids += star["id"] + "|"
            if i >= 5:
                star_ids += "...|"
                break
        if star_ids != "":
            star_ids = star_ids[: len(star_ids) - 1]
        # AV record button
        av_record_btn = None
        if BOT_DB.check_id_exists(id=av_id):
            av_record_btn = InlineKeyboardButton(
                text="AV Record",
                callback_data=f"{av_id}:{BotKey.KEY_GET_AV_DETAIL_RECORD_BY_ID}",
            )
        else:
            av_record_btn = InlineKeyboardButton(
                text=f"Record {av_id}",
                callback_data=f"{av_id}|{star_ids}:{BotKey.KEY_RECORD_AV_BY_ID_STAR_IDS}",
            )
        # Renew button
        renew_btn = None
        if is_cache:
            renew_btn = InlineKeyboardButton(
                text="Renew", callback_data=f"{av_id}:{BotKey.KEY_DEL_AV_CACHE}"
            )
        if star_record_btn and renew_btn:
            markup.row(av_record_btn, star_record_btn, renew_btn)
        elif star_record_btn:
            markup.row(av_record_btn, star_record_btn)
        elif renew_btn:
            markup.row(av_record_btn, renew_btn)
        else:
            markup.row(av_record_btn)
        # Send message
        if av_img == "":
            self.send_msg(msg=msg, markup=markup)
        else:
            try:
                BOT.send_photo(
                    chat_id=BOT_CFG.tg_chat_id,
                    photo=av_img,
                    caption=msg,
                    parse_mode="HTML",
                    reply_markup=markup,
                )
            except Exception:  # Some images may fail to send
                self.send_msg(msg=msg, markup=markup)
        # Send to pikpak
        if BOT_CFG.use_pikpak == "1" and magnet_send_to_pikpak != "" and send_to_pikpak:
            self.send_magnet_to_pikpak(magnet_send_to_pikpak, av_id)

    def send_magnet_to_pikpak(self, magnet: str, id: str):
        """Send magnet to pikpak

        :param str magnet: Magnet link
        :param str id: Corresponding AV ID
        """
        name = PIKPAK_BOT_NAME
        op_send_magnet_to_pikpak = f"Send magnet A: <code>{magnet}</code> of AV ID {id} to pikpak"
        if self.send_msg_to_pikpak(magnet):
            self.send_msg_success_op(op_send_magnet_to_pikpak)
        else:
            self.send_msg_fail_reason_op(
                reason="Please check your network or logs", op=op_send_magnet_to_pikpak
            )

    def get_sample_by_id(self, id: str):
        """Get AV screenshots by ID

        :param str id: AV ID
        """
        op_get_sample = f"Get AV screenshots for ID <code>{id}</code>"
        # Get screenshots
        samples = BOT_CACHE_DB.get_cache(key=id, type=BotCacheDb.TYPE_SAMPLE)
        if not samples:
            code, samples = JAVBUS_UTIL.get_samples_by_id(id)
            if not self.check_success(code, op_get_sample):
                return
            BOT_CACHE_DB.set_cache(key=id, value=samples, type=BotCacheDb.TYPE_SAMPLE)
        # Send image list
        samples_imp = []
        sample_error = False
        for sample in samples:
            samples_imp.append(InputMediaPhoto(sample))
            if len(samples_imp) == 10:  # Send in batches of 10 images
                try:
                    BOT.send_media_group(chat_id=BOT_CFG.tg_chat_id, media=samples_imp)
                    samples_imp = []
                except Exception:
                    sample_error = True
                    self.send_msg_fail_reason_op(reason="Failed to parse images", op=op_get_sample)
                    break
        if samples_imp != [] and not sample_error:
            try:
                BOT.send_media_group(chat_id=BOT_CFG.tg_chat_id, media=samples_imp)
            except Exception:
                self.send_msg_fail_reason_op(reason="Failed to parse images", op=op_get_sample)

    def watch_av_by_id(self, id: str, type: str):
        """Get video for AV ID

        :param str id: AV ID
        :param str type: 0 - Preview video | 1 - Full video
        """
        id = id.lower()
        if id.find("fc2") != -1 and id.find("ppv") == -1:
            id = id.replace("fc2", "fc2-ppv")
        if type == 0:
            pv = BOT_CACHE_DB.get_cache(key=id, type=BotCacheDb.TYPE_PV)
            if not pv:
                op_watch_av = f"Get preview video for AV ID <code>{id}</code>"
                futures = {}
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures[executor.submit(DMM_UTIL.get_pv_by_id, id)] = 2
                    futures[executor.submit(AVGLE_UTIL.get_pv_by_id, id)] = 1
                    for future in concurrent.futures.as_completed(futures):
                        if futures[future] == 2:
                            code_dmm, pv_dmm = future.result()
                        elif futures[future] == 1:
                            code_avgle, pv_avgle = future.result()
                if code_dmm != 200 and code_avgle != 200:
                    if code_dmm == 502 or code_avgle == 502:
                        self.send_msg_code_op(502, op_watch_av)
                    else:
                        self.send_msg_code_op(404, op_watch_av)
                    return
                from_site = ""
                pv_src = ""
                if code_dmm == 200:
                    from_site = "dmm"
                    pv_src = pv_dmm
                elif code_avgle == 200:
                    from_site = "avgle"
                    pv_src = pv_avgle
                pv_cache = {"from_site": from_site, "src": pv_src}
                BOT_CACHE_DB.set_cache(key=id, value=pv_cache, type=BotCacheDb.TYPE_PV)
            else:
                from_site = pv["from_site"]
                pv_src = pv["src"]
            if from_site == "dmm":  # Priority: DMM
                try:
                    # Get a higher-quality video URL
                    pv_src_nice = DMM_UTIL.get_nice_pv_by_src(pv_src)
                    # Send regular video with a link to a higher-quality version
                    BOT.send_video(
                        chat_id=BOT_CFG.tg_chat_id,
                        video=pv_src,
                        caption=f'Results obtained through DMM, <a href="{pv_src_nice}">watch a higher-quality version here</a>',
                        parse_mode="HTML",
                    )
                except Exception:
                    self.send_msg(
                        f'Results obtained through DMM, but failed to parse the video: <a href="{pv_src_nice}">Video URL</a> Q_Q'
                    )
            elif from_site == "avgle":
                try:
                    BOT.send_video(
                        chat_id=BOT_CFG.tg_chat_id,
                        video=pv_src,
                        caption=f'Results obtained through Avgle: <a href="{pv_src}">Video URL</a>',
                        parse_mode="HTML",
                    )
                except Exception:
                    self.send_msg(
                        f'Results obtained through Avgle, but failed to parse the video: <a href="{pv_src}">Video URL</a> Q_Q'
                    )
        elif type == 1:
            video = BOT_CACHE_DB.get_cache(key=id, type=BotCacheDb.TYPE_FV)
            if not video:
                code, video = AVGLE_UTIL.get_fv_by_id(id)
                if code != 200:
                    self.send_msg(f"MissAv video: {BASE_URL_MISS_AV}/{id}")
                    return
                BOT_CACHE_DB.set_cache(key=id, value=video, type=BotCacheDb.TYPE_FV)
            self.send_msg(
                f"""MissAv video: {BASE_URL_MISS_AV}/{id}

Avgle Video URL: {video}
"""
            )

    def search_star_by_name(self, star_name: str) -> bool:
        """Search for a star by name
    
        :param str star_name: Star name
        """
        op_search_star = f"Search for star <code>{star_name}</code>"
        star = BOT_CACHE_DB.get_cache(key=star_name, type=BotCacheDb.TYPE_STAR)
        if not star:
            star_name_origin = star_name
            star_name = self.get_star_ja_name_by_zh_name(star_name)
            code, star = JAVBUS_UTIL.check_star_exists(star_name)
            if not self.check_success(code, op_search_star):
                return
            BOT_CACHE_DB.set_cache(key=star_name, value=star, type=BotCacheDb.TYPE_STAR)
            if star_name_origin != star_name:
                BOT_CACHE_DB.set_cache(
                    key=star_name_origin,
                    value=star,
                    type=BotCacheDb.TYPE_STAR,
                )
        star_id = star["star_id"]
        star_name = star["star_name"]
        if BOT_DB.check_star_exists_by_id(star_id=star_id):
            self.get_star_detail_record_by_name_id(star_name=star_name, star_id=star_id)
            return True
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton(
                text="Random AV",
                callback_data=f"{star_name}|{star_id}:{BotKey.KEY_RANDOM_GET_AV_BY_STAR_ID}",
            ),
            InlineKeyboardButton(
                text="Latest AV",
                callback_data=f"{star_name}|{star_id}:{BotKey.KEY_GET_NEW_AVS_BY_STAR_NAME_ID}",
            ),
            InlineKeyboardButton(
                text="High-rated AV",
                callback_data=f"{star_name}:{BotKey.KEY_GET_NICE_AVS_BY_STAR_NAME}",
            ),
            InlineKeyboardButton(
                text=f"Record {star_name}",
                callback_data=f"{star_name}|{star_id}:{BotKey.KEY_RECORD_STAR_BY_STAR_NAME_ID}",
            ),
        )
        star_wiki = f"{WIKI_UTIL.BASE_URL_CHINA_WIKI}/{star_name}"
        if langdetect.detect(star_name) == "ja":
            star_wiki = f"{WIKI_UTIL.BASE_URL_JAPAN_WIKI}/{star_name}"
        self.send_msg(
            msg=f'<code>{star_name}</code> | <a href="{star_wiki}">Wiki</a> | <a href="{JAVBUS_UTIL.BASE_URL_SEARCH_BY_STAR_NAME}/{star_name}">Javbus</a>',
            markup=markup,
        )
        return True
    
    def get_top_stars(self, page=1):
        """Get top stars from DMM, 20 stars per page
    
        :param int page: Page number, default is 1
        """
        op_get_top_stars = f"Get top stars from DMM"
        stars = BOT_CACHE_DB.get_cache(key=page, type=BotCacheDb.TYPE_RANK)
    
        if not stars:
            code, stars = DMM_UTIL.get_top_stars(page)
            if not self.check_success(code, op_get_top_stars):
                return
            BOT_CACHE_DB.set_cache(key=page, value=stars, type=BotCacheDb.TYPE_RANK)
        stars_tmp = [None] * 80
        stars = stars_tmp[: ((page - 1) * 20)] + stars + stars_tmp[((page - 1) * 20) :]
        col, row = 4, 5
        objs, page_btns, title = self.get_page_elements(
            objs=stars, page=page, col=4, row=5, key_type=BotKey.KEY_GET_TOP_STARS
        )
        self.send_msg_btns(
            max_btn_per_row=col,
            max_row_per_msg=row,
            key_type=BotKey.KEY_SEARCH_STAR_BY_NAME,
            title="<b>DMM Top Stars: </b>" + title,
            objs=objs,
            page_btns=page_btns,
        )
    
    def send_msg_to_pikpak(self, msg):
        """Send a message to Pikpak bot
    
        :param _type_ msg: Message
        :return any: Returns None if failed
        """
    
        async def send():
            try:
                async with Client(
                    name=PATH_SESSION_FILE,
                    api_id=BOT_CFG.tg_api_id,
                    api_hash=BOT_CFG.tg_api_hash,
                    proxy=BOT_CFG.proxy_json_pikpak,
                ) as app:
                    return await app.send_message(PIKPAK_BOT_NAME, msg)
            except Exception as e:
                LOG.error(f"Failed to send message to pikpak: {e}")
                return None
    
        return asyncio.run(send())
    
    def get_more_magnets_by_id(self, id: str):
        """Get more magnets by ID
    
        :param id: ID
        """
        magnets = BOT_CACHE_DB.get_cache(key=id, type=BotCacheDb.TYPE_MAGNET)
        if not magnets:
            av = self.get_av_by_id(
                id=id, is_nice=False, is_uncensored=False, not_send=True
            )
            if not av:
                return
            magnets = av["magnets"]
            BOT_CACHE_DB.set_cache(key=id, value=magnets, type=BotCacheDb.TYPE_MAGNET)
        msg = ""
        for magnet in magnets:
            magnet_tags = ""
            if magnet["uc"] == "1":
                magnet_tags += "Uncensored"
            if magnet["hd"] == "1":
                magnet_tags += "HD"
            if magnet["zm"] == "1":
                magnet_tags += "Subtitles"
            star_tag = ""
            if magnet["hd"] == "1" and magnet["zm"] == "1":
                star_tag = "*"
            msg_tmp = f"""【{star_tag}{magnet_tags} Magnet {magnet["size"]}】<code>{magnet["link"]}</code>
    """
            if len(msg + msg_tmp) >= 4000:
                self.send_msg(msg)
                msg = msg_tmp
            else:
                msg += msg_tmp
        if msg != "":
            self.send_msg(msg)
    
    def get_star_new_avs_by_name_id(self, star_name: str, star_id: str):
        """Get a star's latest AVs
    
        :param str star_name: Star name
        :param str star_id: Star ID
        """
        op_get_star_new_avs = f"Get latest AVs for <code>{star_name}</code>"
        ids = BOT_CACHE_DB.get_cache(key=star_id, type=BotCacheDb.TYPE_NEW_AVS_OF_STAR)
        if not ids:
            code, ids = JAVBUS_UTIL.get_new_ids_by_star_id(star_id=star_id)
            if not self.check_success(code, op_get_star_new_avs):
                return
            BOT_CACHE_DB.set_cache(
                key=star_id, value=ids, type=BotCacheDb.TYPE_NEW_AVS_OF_STAR
            )
        title = f"<code>{star_name}</code> Latest AVs"
        btns = [
            InlineKeyboardButton(
                text=id, callback_data=f"{id}:{BotKey.KEY_GET_AV_BY_ID}"
            )
            for id in ids
        ]
        if len(btns) <= 4:
            self.send_msg(msg=title, markup=InlineKeyboardMarkup().row(*btns))
        else:
            markup = InlineKeyboardMarkup()
            markup.row(*btns[:4])
            markup.row(*btns[4:])
            self.send_msg(msg=title, markup=markup)

    def get_star_en_name_by_zh_name(self, star_name: str) -> str:
        """Get the English name based on the Chinese name
    
        :param str star_name: Chinese name
        :return str: English name (if found)
        """
        if langdetect.detect(star_name) == "ja":
            return star_name
        star_en_name = BOT_CACHE_DB.get_cache(
            key=star_name, type=BotCacheDb.TYPE_STAR_EN_NAME
        )
        if star_en_name:
            return star_en_name
        wiki_json = WIKI_UTIL.get_wiki_page_by_lang(
            topic=star_name, from_lang="zh", to_lang="en"
        )
        if wiki_json and wiki_json["lang"] == "en":
            BOT_CACHE_DB.set_cache(
                key=star_name,
                value=wiki_json["title"],
                type=BotCacheDb.TYPE_STAR_EN_NAME,
            )
            return wiki_json["title"]
        return star_name



def handle_callback(call):
    """Handle callback

    :param _type_ call
    """
    # Echo typing...
    bot_utils = BotUtils()
    bot_utils.send_action_typing()
    LOG.info(f"Handle callback: {call.data}")
    # Extract callback content
    s = call.data.rfind(":")
    content = call.data[:s]
    key_type = call.data[s + 1 :]
    # Check the key type and process
    if key_type == BotKey.KEY_WATCH_PV_BY_ID:
        bot_utils.watch_av_by_id(id=content, type=0)
    elif key_type == BotKey.KEY_WATCH_FV_BY_ID:
        bot_utils.watch_av_by_id(id=content, type=1)
    elif key_type == BotKey.KEY_GET_SAMPLE_BY_ID:
        bot_utils.get_sample_by_id(id=content)
    elif key_type == BotKey.KEY_GET_MORE_MAGNETS_BY_ID:
        bot_utils.get_more_magnets_by_id(id=content)
    elif key_type == BotKey.KEY_RANDOM_GET_AV_BY_STAR_ID:
        tmp = content.split("|")
        star_name = tmp[0]
        star_id = tmp[1]
        code, id = JAVBUS_UTIL.get_id_by_star_id(star_id=star_id)
        if bot_utils.check_success(code, f"Randomly get actor <code>{star_name}</code>'s av"):
            bot_utils.get_av_by_id(id=id)
    elif key_type == BotKey.KEY_GET_NEW_AVS_BY_STAR_NAME_ID:
        tmp = content.split("|")
        star_name = tmp[0]
        star_id = tmp[1]
        bot_utils.get_star_new_avs_by_name_id(star_name=star_name, star_id=star_id)
    elif key_type == BotKey.KEY_RECORD_STAR_BY_STAR_NAME_ID:
        s = content.find("|")
        star_name = content[:s]
        star_id = content[s + 1 :]
        if BOT_DB.record_star_by_name_id(star_name=star_name, star_id=star_id):
            bot_utils.get_star_detail_record_by_name_id(
                star_name=star_name, star_id=star_id
            )
        else:
            bot_utils.send_msg_code_op(500, f"Collect actor <code>{star_name}</code>")
    elif key_type == BotKey.KEY_RECORD_AV_BY_ID_STAR_IDS:
        res = content.split("|")
        id = res[0]
        stars = []
        if res[1] != "":
            stars = [s for s in res[1:]]
        if BOT_DB.record_id_by_id_stars(id=id, stars=stars):
            bot_utils.get_av_detail_record_by_id(id=id)
        else:
            bot_utils.send_msg_code_op(500, f"Collect code <code>{id}</code>")
    elif key_type == BotKey.KEY_GET_STARS_RECORD:
        bot_utils.get_stars_record(page=int(content))
    elif key_type == BotKey.KEY_GET_AVS_RECORD:
        bot_utils.get_avs_record(page=int(content))
    elif key_type == BotKey.KEY_GET_STAR_DETAIL_RECORD_BY_STAR_NAME_ID:
        s = content.find("|")
        bot_utils.get_star_detail_record_by_name_id(
            star_name=content[:s], star_id=content[s + 1 :]
        )
    elif key_type == BotKey.KEY_GET_AV_DETAIL_RECORD_BY_ID:
        bot_utils.get_av_detail_record_by_id(id=content)
    elif key_type == BotKey.KEY_GET_AV_BY_ID:
        bot_utils.get_av_by_id(id=content)
    elif key_type == BotKey.KEY_RANDOM_GET_AV_NICE:
        code, id = JAVLIB_UTIL.get_random_id_from_rank(0)
        if bot_utils.check_success(code, "Randomly get high-rated av"):
            bot_utils.get_av_by_id(id=id)
    elif key_type == BotKey.KEY_RANDOM_GET_AV_NEW:
        code, id = JAVLIB_UTIL.get_random_id_from_rank(1)
        if bot_utils.check_success(code, "Randomly get latest av"):
            bot_utils.get_av_by_id(id=id)
    elif key_type == BotKey.KEY_UNDO_RECORD_AV_BY_ID:
        op_undo_record_av = f"Undo collecting code <code>{content}</code>"
        if BOT_DB.undo_record_id(id=content):
            bot_utils.send_msg_success_op(op_undo_record_av)
        else:
            bot_utils.send_msg_fail_reason_op(reason="File parsing error", op=op_undo_record_av)
    elif key_type == BotKey.KEY_UNDO_RECORD_STAR_BY_STAR_NAME_ID:
        s = content.find("|")
        op_undo_record_star = f"Undo collecting actor <code>{content[:s]}</code>"
        if BOT_DB.undo_record_star_by_id(star_id=content[s + 1 :]):
            bot_utils.send_msg_success_op(op_undo_record_star)
        else:
            bot_utils.send_msg_fail_reason_op(reason="File parsing error", op=op_undo_record_star)
    elif key_type == BotKey.KEY_SEARCH_STAR_BY_NAME:
        star_name = content
        star_name_alias = ""
        idx_alias = star_name.find("（")
        if idx_alias != -1:
            star_name_alias = star_name[idx_alias + 1 : -1]
            star_name = star_name[:idx_alias]
        if not bot_utils.search_star_by_name(star_name) and star_name_alias != "":
            bot_utils.send_msg(f"Trying to search for actor {star_name}'s alias {star_name_alias}......")
            bot_utils.search_star_by_name(star_name_alias)
    elif key_type == BotKey.KEY_GET_TOP_STARS:
        bot_utils.get_top_stars(page=int(content))
    elif key_type == BotKey.KEY_GET_NICE_AVS_BY_STAR_NAME:
        star_name_ori = content
        avs = BOT_CACHE_DB.get_cache(
            key=star_name_ori, type=BotCacheDb.TYPE_NICE_AVS_OF_STAR
        )
        if not avs:
            star_name_en = bot_utils.get_star_en_name_by_zh_name(star_name_ori)
            code, avs = DMM_UTIL.get_nice_avs_by_star_name(star_name=star_name_en)
            if bot_utils.check_success(code, f"Get high-rated avs of actor {star_name_ori}"):
                avs = avs[:60]
                BOT_CACHE_DB.set_cache(
                    key=star_name_ori,
                    value=avs,
                    type=BotCacheDb.TYPE_NICE_AVS_OF_STAR,
                )
                if star_name_en != star_name_ori:
                    BOT_CACHE_DB.set_cache(
                        key=star_name_en,
                        value=avs,
                        type=BotCacheDb.TYPE_NICE_AVS_OF_STAR,
                    )
            else:
                return
        bot_utils.send_msg_btns(
            max_btn_per_row=3,
            max_row_per_msg=20,
            key_type=BotKey.KEY_GET_AV_BY_ID,
            title=f"<b>High-rated avs of actor {star_name_ori}</b>",
            objs=avs,
        )
    elif key_type == BotKey.KEY_DEL_AV_CACHE:
        BOT_CACHE_DB.remove_cache(key=content, type=BotCacheDb.TYPE_AV)
        BOT_CACHE_DB.remove_cache(key=content, type=BotCacheDb.TYPE_STARS_MSG)
        bot_utils.get_av_by_id(id=content)

def handle_message(message):
    """Handle message

    :param message: Message object
    """
    # Echo typing...
    bot_utils = BotUtils()
    bot_utils.send_action_typing()
    # Intercept requests
    chat_id = str(message.chat.id)
    if chat_id.lower() != BOT_CFG.tg_chat_id.lower():
        LOG.info(f"Intercepted request from non-target user, id: {chat_id}")
        BOT.send_message(
            chat_id=chat_id,
            text=f'This bot is for private use only. If you want to use it, please deploy it yourself: <a href="{PROJECT_ADDRESS}">Project Address</a>',
            parse_mode="HTML",
        )
        return
    bot_utils = BotUtils()
    # Get message text content
    if message.content_type != "text":
        msg = message.caption
    else:
        msg = message.text
    if not msg:
        return
    LOG.info(f'Received message: "{msg}"')
    msg = msg.lower().strip()
    msgs = msg.split(" ", 1)  # Split into two parts
    # Message command
    msg_cmd = msgs[0]
    # Message parameter
    msg_param = ""
    if len(msgs) > 1:  # Has parameter
        msg_param = msgs[1].strip()
    # Handle message
    if msg_cmd == "/help" or msg_cmd == "/start":
        bot_utils.send_msg(MSG_HELP)
    elif msg_cmd == "/nice":
        page = random.randint(1, JAVLIB_UTIL.MAX_RANK_PAGE)
        ids = BOT_CACHE_DB.get_cache(key=page, type=BotCacheDb.TYPE_JLIB_PAGE_NICE_AVS)
        if not ids:
            code, ids = JAVLIB_UTIL.get_random_ids_from_rank_by_page(
                page=page, list_type=0
            )
            if bot_utils.check_success(code, "Get random high-rated av"):
                BOT_CACHE_DB.set_cache(
                    key=page,
                    value=ids,
                    type=BotCacheDb.TYPE_JLIB_PAGE_NICE_AVS,
                )
            else:
                return
        bot_utils.get_av_by_id(id=random.choice(ids))
    elif msg_cmd == "/new":
        page = random.randint(1, JAVLIB_UTIL.MAX_RANK_PAGE)
        ids = BOT_CACHE_DB.get_cache(key=page, type=BotCacheDb.TYPE_JLIB_PAGE_NEW_AVS)
        if not ids:
            code, ids = JAVLIB_UTIL.get_random_ids_from_rank_by_page(
                page=page, list_type=1
            )
            if bot_utils.check_success(code, "Get random latest av"):
                BOT_CACHE_DB.set_cache(
                    key=page,
                    value=ids,
                    type=BotCacheDb.TYPE_JLIB_PAGE_NEW_AVS,
                )
            else:
                return
        bot_utils.get_av_by_id(id=random.choice(ids))
    elif msg_cmd == "/stars":
        bot_utils.get_stars_record()
    elif msg_cmd == "/avs":
        bot_utils.get_avs_record()
    elif msg_cmd == "/record":
        if os.path.exists(PATH_RECORD_FILE):
            BOT.send_document(
                chat_id=BOT_CFG.tg_chat_id, document=types.InputFile(PATH_RECORD_FILE)
            )
        else:
            bot_utils.send_msg_fail_reason_op(reason="No collection record yet", op="Get collection record file")
    elif msg_cmd == "/rank":
        bot_utils.get_top_stars(1)
    elif msg_cmd == "/star":
        if msg_param != "":
            bot_utils.send_msg(f"Searching for actor: <code>{msg_param}</code> ......")
            bot_utils.search_star_by_name(msg_param)
    elif msg_cmd == "/av":
        if msg_param:
            bot_utils.send_msg(f"Searching for code: <code>{msg_param}</code> ......")
            bot_utils.get_av_by_id(id=msg_param, send_to_pikpak=True)
    else:
        ids = AV_PAT.findall(msg)
        if not ids or len(ids) == 0:
            bot_utils.send_msg(
                "The message does not seem to contain valid codes. You can try searching by using '/av code'. Use the '/help' command for assistance ~"
            )
        else:
            ids = [id.lower() for id in ids]
            ids = set(ids)
            ids_msg = ", ".join(ids)
            bot_utils.send_msg(f"Detected codes: {ids_msg}, searching......")
            for i, id in enumerate(ids):
                threading.Thread(target=bot_utils.get_av_by_id, args=(id,)).start()


EXECUTOR = concurrent.futures.ThreadPoolExecutor()


@BOT.callback_query_handler(func=lambda call: True)
def my_callback_handler(call):
    """Callback handler for messages

    :param call: CallbackQuery object
    """
    EXECUTOR.submit(handle_callback, call)


@BOT.message_handler(content_types=["text", "photo", "animation", "video", "document"])
def my_message_handler(message):
    """Message handler

    :param message: Message object
    """
    EXECUTOR.submit(handle_message, message)


def pyrogram_auth():
    if BOT_CFG.use_pikpak == "1" and not os.path.exists(f"{PATH_SESSION_FILE}.session"):
        LOG.info(f"Performing pyrogram authentication......")
        try:
            BotUtils().send_msg_to_pikpak("Pyrogram authentication")
            LOG.info(f"Pyrogram authentication successful")
        except BaseException as e:
            LOG.error(f"Pyrogram authentication failed: {e}")


def main():
    pyrogram_auth()
    try:
        bot_info = BOT.get_me()
        LOG.info(f"Connected to bot: @{bot_info.username} (ID: {bot_info.id})")
    except Exception as e:
        LOG.error(f"Unable to connect to bot: {e}")
        return
    BOT.set_my_commands([types.BotCommand(cmd, BOT_CMDS[cmd]) for cmd in BOT_CMDS])
    BOT.infinity_polling()


if __name__ == "__main__":
    main()
