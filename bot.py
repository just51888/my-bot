# -*- coding: utf-8 -*-
import os
import logging
import urllib.parse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ======================== 配置区（你可以任意修改） ========================
TOKEN = "8714935528:AAHTLZA03i41aIMP5vWwovSBklJxy81z05k"  # 你的机器人 Token
ADMIN_ID = 7505521498  # 你的 Telegram 用户 ID

# 链接追踪映射表（用户点击 ?start=xxx 时，机器人回复对应的中文）
SOURCE_MAP = {
    "wx": "微信",
    "pyq": "朋友圈",
    "gzh": "公众号",
    "bd": "百度",
    "dy": "抖音",
    "kangle": "95-96康乐会所部长",
    "jinyuwan": "94金御湾会所部长",
    "songbai": "94松白会所部长",
    # 你可以继续添加更多
}

# 欢迎消息（用户点击 /start 不带参数时回复）
WELCOME_TEXT = "欢迎！发送消息即可联系客服。"

# 用户消息发送成功提示
MSG_SENT = "您的消息已发送给客服，请耐心等待回复。"

# 管理员回复格式
REPLY_TEMPLATE = "客服回复：{message}"

# 管理员收到新用户来源的通知格式
SOURCE_NOTIFY = "🔔 新用户来源：\n用户ID: {user_id}\n用户名: @{username}\n来源: {source}"
# =======================================================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 存储用户消息 ID 与用户 ID 的映射（用于管理员回复时找到目标用户）
user_message_map = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令，支持 Deep Linking 参数"""
    user = update.effective_user
    user_id = user.id
    username = user.username or "无用户名"

    # 获取参数
    raw_param = context.args[0] if context.args else None
    if raw_param:
        try:
            param = urllib.parse.unquote(raw_param)
        except:
            param = raw_param
    else:
        param = None

    # 判断是否在映射表中
    if param and param in SOURCE_MAP:
        source = SOURCE_MAP[param]
        reply = f"欢迎！你来自：{source}"
        # 通知管理员
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=SOURCE_NOTIFY.format(user_id=user_id, username=username, source=source)
        )
    elif param:
        # 有参数但不在映射表中，直接显示参数
        reply = f"欢迎！你来自：{param}"
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=SOURCE_NOTIFY.format(user_id=user_id, username=username, source=param)
        )
    else:
        reply = WELCOME_TEXT

    await update.message.reply_text(reply)


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理普通用户消息（非命令），转发给管理员"""
    user = update.effective_user
    user_id = user.id
    username = user.username or "无用户名"
    text = update.message.text

    # 不处理管理员自己发的消息（避免死循环）
    if user_id == ADMIN_ID:
        return

    # 转发给管理员
    try:
        sent = await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 用户 @{username} (ID: {user_id}) 说：\n{text}"
        )
        # 记录消息映射，以便管理员回复时找到目标用户
        user_message_map[sent.message_id] = user_id
        logger.info(f"✅ 已记录映射: 消息ID {sent.message_id} -> 用户 {user_id}")
        # 回复用户表示已收到
        await update.message.reply_text(MSG_SENT)
    except Exception as e:
        logger.error(f"转发失败: {e}")
        await update.message.reply_text("发送失败，请稍后再试。")


async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理管理员对转发消息的回复，转发给原始用户"""
    message = update.message
    user_id = update.effective_user.id

    # 必须是管理员且回复的是转发的消息
    if user_id != ADMIN_ID:
        return
    if not message.reply_to_message:
        return

    # 查找原始用户 ID
    original_msg_id = message.reply_to_message.message_id
    target_user_id = user_message_map.get(original_msg_id)

    logger.info(f"🔍 查找映射: 消息ID {original_msg_id} -> 目标用户 {target_user_id}")

    if not target_user_id:
        await message.reply_text("无法找到对应的用户，可能消息已过期。")
        return

    # 转发回复给用户
    try:
        reply_text = REPLY_TEMPLATE.format(message=message.text)
        await context.bot.send_message(
            chat_id=target_user_id,
            text=reply_text
        )
        await message.reply_text("✅ 回复已发送给用户。")
        # 删除映射，避免重复
        del user_message_map[original_msg_id]
        logger.info(f"✅ 回复已发送给用户 {target_user_id}")
    except Exception as e:
        logger.error(f"回复用户失败: {e}")
        await message.reply_text("回复发送失败。")


def main():
    app = Application.builder().token(TOKEN).build()

    # 命令处理器
    app.add_handler(CommandHandler("start", start))

    # 用户消息处理器（只处理文本，不处理命令）
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))

    # 管理员回复处理器（通过 MessageHandler 捕获所有消息，内部判断是否管理员回复）
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, handle_admin_reply))

    logger.info("机器人已启动，按 Ctrl+C 停止")
    app.run_polling()


if __name__ == "__main__":
    main()
