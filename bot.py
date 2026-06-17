# -*- coding: utf-8 -*-
import os
import logging
import re
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
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 用户 @{username} (ID: {user_id}) 说：\n{text}"
        )
        await update.message.reply_text(MSG_SENT)
        logger.info(f"✅ 用户 {user_id} 的消息已转发")
    except Exception as e:
        logger.error(f"转发失败: {e}")
        await update.message.reply_text("发送失败，请稍后再试。")


async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理管理员发送的消息，提取 @用户ID 并回复"""
    message = update.message
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    text = message.text
    if not text:
        return
    # 如果是命令，不处理
    if text.startswith('/'):
        return

    # 提取 @数字 格式的用户ID
    match = re.search(r'@(\d+)', text)
    if not match:
        await message.reply_text("请使用 @用户ID 格式回复\n例如：@8415 好的")
        return

    target_user_id = int(match.group(1))
    # 去掉 @用户ID 部分，剩下的作为回复内容
    reply_content = re.sub(r'@\d+\s*', '', text).strip()
    if not reply_content:
        await message.reply_text("请附带回复内容\n例如：@8415 好的")
        return

    try:
        await context.bot.send_message(chat_id=target_user_id, text=REPLY_TEMPLATE.format(message=reply_content))
        await message.reply_text(f"✅ 已回复给用户 {target_user_id}")
        logger.info(f"✅ 已回复给用户 {target_user_id}")
    except Exception as e:
        logger.error(f"回复用户失败: {e}")
        await message.reply_text(f"回复失败：用户可能已退出对话。")


async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_message))
    logger.info("机器人已启动，按 Ctrl+C 停止")
    app.run_polling()


if __name__ == "__main__":
    main()
    main()
    main()
