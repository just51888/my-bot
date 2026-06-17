# -*- coding: utf-8 -*-
import os
import logging
import urllib.parse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ======================== 配置区 ========================
TOKEN = "8714935528:AAHTLZA03i41aIMP5vWwovSBklJxy81z05k"
ADMIN_ID = 7505521498

SOURCE_MAP = {
    "wx": "微信",
    "pyq": "朋友圈",
    "gzh": "公众号",
    "bd": "百度",
    "dy": "抖音",
    "kangle": "95-96康乐会所部长",
    "jinyuwan": "94金御湾会所部长",
    "songbai": "94松白会所部长",
}

WELCOME_TEXT = "欢迎！发送消息即可联系客服。"
MSG_SENT = "您的消息已发送给客服，请耐心等待回复。"
REPLY_TEMPLATE = "客服回复：{message}"
SOURCE_NOTIFY = "🔔 新用户来源：\n用户ID: {user_id}\n用户名: @{username}\n来源: {source}"
# =======================================================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 存储用户消息 ID 与用户 ID 的映射
user_message_map = {}

# 存储用户 ID 与最新消息 ID 的映射（用于 /reply 命令）
user_latest_msg = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or "无用户名"
    raw_param = context.args[0] if context.args else None
    if raw_param:
        try:
            param = urllib.parse.unquote(raw_param)
        except:
            param = raw_param
    else:
        param = None
    if param and param in SOURCE_MAP:
        source = SOURCE_MAP[param]
        reply = f"欢迎！你来自：{source}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=SOURCE_NOTIFY.format(user_id=user_id, username=username, source=source))
    elif param:
        reply = f"欢迎！你来自：{param}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=SOURCE_NOTIFY.format(user_id=user_id, username=username, source=param))
    else:
        reply = WELCOME_TEXT
    await update.message.reply_text(reply)


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or "无用户名"
    text = update.message.text
    if user_id == ADMIN_ID:
        return
    try:
        sent = await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 用户 @{username} (ID: {user_id}) 说：\n{text}"
        )
        user_message_map[sent.message_id] = user_id
        user_latest_msg[user_id] = sent.message_id  # 记录最新消息ID
        logger.info(f"✅ 已记录映射: 消息ID {sent.message_id} -> 用户 {user_id}")
        await update.message.reply_text(MSG_SENT)
    except Exception as e:
        logger.error(f"转发失败: {e}")
        await update.message.reply_text("发送失败，请稍后再试。")


async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = update.effective_user.id
    if user_id != ADMIN_ID or not message.reply_to_message:
        return
    original_msg_id = message.reply_to_message.message_id
    target_user_id = user_message_map.get(original_msg_id)
    logger.info(f"🔍 查找映射: 消息ID {original_msg_id} -> 目标用户 {target_user_id}")
    if not target_user_id:
        await message.reply_text("无法找到对应的用户，可能消息已过期。")
        return
    try:
        reply_text = REPLY_TEMPLATE.format(message=message.text)
        await context.bot.send_message(chat_id=target_user_id, text=reply_text)
        await message.reply_text("✅ 回复已发送给用户。")
        del user_message_map[original_msg_id]
        logger.info(f"✅ 回复已发送给用户 {target_user_id}")
    except Exception as e:
        logger.error(f"回复用户失败: {e}")
        await message.reply_text("回复发送失败。")


async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理员命令：/reply 用户ID 回复内容"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("只有管理员可以使用此命令。")
        return
    if len(context.args) < 2:
        await update.message.reply_text("用法：/reply 用户ID 回复内容\n例如：/reply 123456789 你好")
        return
    target_user_id = int(context.args[0])
    reply_text = " ".join(context.args[1:])
    try:
        await context.bot.send_message(chat_id=target_user_id, text=REPLY_TEMPLATE.format(message=reply_text))
        await update.message.reply_text(f"✅ 已回复给用户 {target_user_id}")
    except Exception as e:
        logger.error(f"回复用户失败: {e}")
        await update.message.reply_text(f"回复失败：{e}")


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", reply_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, handle_admin_reply))
    logger.info("机器人已启动，按 Ctrl+C 停止")
    app.run_polling()


if __name__ == "__main__":
    main()
