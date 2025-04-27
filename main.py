import os
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import subprocess
import time
import json 
from flask import Flask, jsonify
import gradio as gr

# Configuraci锟斤拷n del bot
API_ID = ''
API_HASH = ''
BOT_TOKEN = ''

# Lista de administradores supremos (IDs de usuario)
SUPER_ADMINS = [5702506445]  # Reemplaza con los IDs de los administradores supremos

# Lista de administradores (IDs de usuario)
ADMINS = [5702506445]  # Reemplaza con los IDs de los administradores

# Lista de usuarios autorizados (IDs de usuario)
AUTHORIZED_USERS = [5702506445]

# Lista de grupos autorizados (IDs de grupo)
AUTHORIZED_GROUPS = [-1002354746023]

# Calidad predeterminada
DEFAULT_QUALITY = {
    'resolution': '740x480',
    'crf': '32',
    'audio_bitrate': '60k',
    'fps': '28',
    'preset': 'ultrafast',
    'codec': 'libx265'
}

# Calidad actual (cambiar a un diccionario que almacene la calidad por usuario)
current_calidad = {}

# L锟斤拷mite de tama锟�0锟�9o de video (en bytes)
max_video_size = 5 * 1024 * 1024 * 1024  # 1GB por defecto

# Configuraci锟斤拷n de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Inicializaci锟斤拷n del bot
app = Client("ffmpeg_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, workdir="/app/session")

# Funci锟斤拷n para verificar si el usuario es un administrador supremo
def is_super_admin(user_id):
    return user_id in SUPER_ADMINS

# Funci锟斤拷n para verificar si el usuario es un administrador
def is_admin(user_id):
    return user_id in ADMINS or user_id in SUPER_ADMINS

# Funci锟斤拷n para verificar si el usuario es autorizado
def is_authorized(user_id):
    return user_id in AUTHORIZED_USERS or user_id in ADMINS or user_id in SUPER_ADMINS

# Funci锟斤拷n para verificar si el grupo es autorizado
def is_authorized_group(chat_id):
    if chat_id in AUTHORIZED_GROUPS:
        return True
    logger.info(f"锟�7锟�4锟�3锟�8锟�3锟�5锟�3锟�8锟�3锟�3锟�3锟�2 {chat_id} 锟�3锟�1锟�3锟�2 锟�3锟�8锟�3锟�8锟�3锟�7锟�3锟�2锟�3锟�5锟�3锟�6锟�3锟�3锟�3锟�8锟�3锟�1锟�3锟�2锟�7锟�4.")
    return False

# Funci锟斤拷n para guardar los datos en un archivo JSON
def save_data():
    data = {
        'authorized_users': AUTHORIZED_USERS,
        'authorized_groups': AUTHORIZED_GROUPS,
        'admins': ADMINS
    }
    with open('data.json', 'w') as f:
        json.dump(data, f)

# Funci锟斤拷n para cargar los datos desde un archivo JSON
def load_data():
    global AUTHORIZED_USERS, AUTHORIZED_GROUPS, ADMINS
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
            AUTHORIZED_USERS = data.get('authorized_users', [])
            AUTHORIZED_GROUPS = data.get('authorized_groups', [])
            ADMINS = data.get('admins', [])
    except FileNotFoundError:
        pass

# Cargar datos al iniciar el bot
load_data()

# Funci锟斤拷n para formatear el tiempo en HH:MM:SS
def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

# Funci锟斤拷n para comprimir el video
async def compress_video(input_file, output_file, user_id):
    # Obtener la calidad del usuario o usar la calidad predeterminada
    quality = current_calidad.get(user_id, DEFAULT_QUALITY)
    
    command = [
        'ffmpeg',
        '-i', input_file,
        '-vf', f'scale={quality["resolution"]},fps={quality["fps"]}',
        '-c:v', quality['codec'],
        '-crf', quality['crf'],
        '-preset', quality['preset'],
        '-b:a', quality['audio_bitrate'],
        '-threads', '0',  # Usar todos los hilos disponibles
        '-y', output_file
    ]
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = await process.communicate()  # Por si tiene error en la compresi锟斤拷n
    if process.returncode != 0:
        logger.error(f"锟�6锟�0锟�1锟�5锟�3锟�6锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�5 锟�3锟�2锟�3锟�1 锟�3锟�2锟�3锟�9 锟�3锟�3锟�3锟�5锟�3锟�2锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�2: {stderr.decode()}锟�6锟�0锟�1锟�5")
    return process.returncode
    
# Comando de bienvenida
@app.on_message(filters.command("start") & (filters.private | filters.group))
async def start(client: Client, message: Message):
    if is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        await message.reply_text(
            "锟�9锟�0 Bienvenido a Compresor Video use /help para mas ayuda 锟�9锟�2"
        )
    else:
        await message.reply_text(
            "锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�3锟�3锟�2锟�3锟�6锟�3锟�2锟�3锟�2 锟�3锟�8锟�3锟�0锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�2锟�7锟�4\n\n锟�3锟�9锟�3锟�8锟�3锟�9锟�3锟�9锟�3锟�2 锟�3锟�0锟�3锟�2锟�3锟�1 锟�3锟�2锟�3锟�9 锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5 锟�9锟�8锟�6锟�9锟�9锟�1", url="https://t.me/Sasuke286")]
            ])
        )

# Comando de ayuda
@app.on_message(filters.command("help") & (filters.private | filters.group))
async def help(client: Client, message: Message):
    if is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        help_text = """
        **锟�0锟�6锟�3锟�4锟�3锟�2锟�3锟�0锟�3锟�8锟�3锟�1锟�3锟�1锟�3锟�2锟�3锟�6 锟�3锟�5锟�3锟�6锟�3锟�6锟�3锟�3锟�3锟�2锟�3锟�1锟�3锟�6锟�3锟�9锟�3锟�9锟�3锟�2锟�3锟�6锟�0锟�6:**

        **锟�9锟�4锟�3锟�3锟�3锟�2锟�3锟�6 锟�3锟�1锟�3锟�2 锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�8锟�3锟�5锟�3锟�6锟�3锟�2锟�9锟�4:**
        - **/start**: Muestra un mensaje de bienvenida.
        - **/help**: Muestra esta lista de comandos.
        - **/calidad**: Cambia la calidad de compresi锟斤拷n del video. Uso: `/calidad resolution=740x480 crf=32 audio_bitrate=60k fps=28 preset=ultrafast codec=libx265`
        - **/id**: Obtiene el ID de un usuario. Uso: `/id @username` (Solo Administradores)

        **锟�9锟�8锟�6锟�9锟�7锟�6锟�1锟�5锟�3锟�3锟�3锟�2锟�3锟�6 锟�3锟�1锟�3锟�2 锟�3锟�8锟�3锟�1锟�3锟�0锟�3锟�6锟�3锟�1锟�3锟�6锟�3锟�6锟�3锟�7锟�3锟�5锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5锟�9锟�8锟�6锟�9锟�7锟�6锟�1锟�5:**
        - **/add**: Agrega un usuario autorizado. Uso: `/add user_id`
        - **/ban**: Quita un usuario autorizado. Uso: `/ban user_id`
        - **/listusers**: Lista los usuarios autorizados.
        - **/grup**: Agrega un grupo autorizado. Uso: `/grup group_id`
        - **/bangrup**: Quita un grupo autorizado. Uso: `/bangrup group_id`
        - **/listgrup**: Lista los grupos autorizados.
        - **/add_admins**: Agrega un nuevo administrador. Uso: `/add_admins user_id` (Solo Administradores Supremos)
        - **/ban_admins**: Quita un administrador. Uso: `/ban_admins user_id` (Solo Administradores Supremos)
        - **/listadmins**: Lista los administradores.
        - **/info**: Envia un mensaje a todos los usuarios y grupos autorizados. Uso: `/info [mensaje]`
        - **/max**: Establece el l锟斤拷mite de tama锟�0锟�9o para los videos. Uso: `/max [tama锟�0锟�9o en MB o GB]`

        **锟�3锟�4锟�3锟�8锟�3锟�9锟�3锟�6锟�3锟�1锟�3锟�8锟�3锟�1 锟�3锟�3锟�3锟�5锟�3锟�2锟�3锟�1锟�3锟�2锟�3锟�7锟�3锟�2锟�3锟�5锟�3锟�0锟�3锟�6锟�3锟�1锟�3锟�8锟�3锟�1锟�3锟�8锟�9锟�6:**
        - resolution: 740x480
        - crf: 32
        - audio_bitrate: 60k
        - fps: 28
        - preset: ultrafast
        - codec: libx265

        **锟�3锟�2锟�3锟�6锟�3锟�2 锟�3锟�1锟�3锟�2锟�3锟�9 锟�3锟�9锟�3锟�2锟�3锟�7锟�9锟�8:**
        - Env锟斤拷a un video y el bot lo comprimir锟斤拷 con la calidad actual.
        """
        await message.reply_text(help_text)
    else:
        await message.reply_text(
            "锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�3锟�3锟�2锟�3锟�6锟�3锟�2锟�3锟�2 锟�3锟�8锟�3锟�0锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�2锟�7锟�4\n\n锟�3锟�9锟�3锟�8锟�3锟�9锟�3锟�9锟�3锟�2 锟�3锟�0锟�3锟�2锟�3锟�1 锟�3锟�2锟�3锟�9 锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5 锟�9锟�8锟�6锟�9锟�9锟�1", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para listar administradores
@app.on_message(filters.command("listadmins") & (filters.private | filters.group))
async def list_admins(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        if ADMINS:
            admin_list = "\n".join(map(str, ADMINS))
            await message.reply_text(f"锟�3锟�3锟�3锟�6锟�3锟�6锟�3锟�7 锟�3锟�2锟�3锟�1锟�3锟�0锟�3锟�6锟�3锟�1锟�3锟�6 锟�9锟�5:\n{admin_list}")
        else:
            await message.reply_text("锟�8锟�7锟�3锟�5锟�3锟�2 锟�3锟�5锟�3锟�8锟�3锟�2 锟�3锟�8锟�3锟�1锟�3锟�0锟�3锟�6锟�3锟�1锟�8锟�7.")
    else:
        await message.reply_text(
            "锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�3锟�3锟�2锟�3锟�6锟�3锟�2锟�3锟�2 锟�3锟�8锟�3锟�0锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�2锟�7锟�4\n\n锟�3锟�9锟�3锟�8锟�3锟�9锟�3锟�9锟�3锟�2 锟�3锟�0锟�3锟�2锟�3锟�1 锟�3锟�2锟�3锟�9 锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5 锟�9锟�8锟�6锟�9锟�9锟�1", url="https://t.me/Sasuke286")]
            ])
        )


@app.on_message(filters.command("calidad") & (filters.private | filters.group))
async def set_calidad(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        global current_calidad
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("锟�3锟�2锟�3锟�6锟�3锟�2: /calidad resolution=740x480 crf=32 audio_bitrate=60k fps=28 preset=ultrafast codec=libx265")
            return

        user_quality = current_calidad.get(message.from_user.id, DEFAULT_QUALITY.copy())
        for arg in args:
            try:
                key, value = arg.split('=')
                if key in user_quality:
                    user_quality[key] = value
                else:
                    await message.reply_text(f"锟�8锟�7锟�3锟�7锟�3锟�8锟�3锟�5锟�3锟�8锟�0锟�7锟�3锟�0锟�3锟�2锟�3锟�7锟�3锟�5锟�3锟�2 锟�3锟�1锟�3锟�2锟�3锟�6锟�3锟�0锟�3锟�2锟�3锟�1锟�3锟�2锟�3锟�0锟�3锟�6锟�3锟�1锟�3锟�2: {key}锟�8锟�7")
                    return
            except ValueError:
                await message.reply_text(f"锟�8锟�7锟�3锟�6锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�5 锟�3锟�5锟�3锟�2锟�3锟�3锟�3锟�6锟�3锟�7锟�3锟�8锟�3锟�1锟�3锟�1锟�3锟�2 锟�3锟�3锟�3锟�8锟�3锟�5锟�3锟�8锟�0锟�7锟�3锟�0锟�3锟�2锟�3锟�7锟�3锟�5锟�3锟�2: {arg}锟�8锟�7")
                return

        current_calidad[message.from_user.id] = user_quality
        await message.reply_text(f"锟�6锟�0锟�1锟�5锟�3锟�4锟�3锟�8锟�3锟�9锟�3锟�6锟�3锟�1锟�3锟�8锟�3锟�1 锟�3锟�8锟�3锟�0锟�3锟�7锟�3锟�8锟�3锟�8锟�3锟�9: {current_calidad[message.from_user.id]}锟�6锟�0锟�1锟�5")
    else:
        await message.reply_text(
            "锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�3锟�3锟�2锟�3锟�6锟�3锟�2锟�3锟�2 锟�3锟�8锟�3锟�0锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�2锟�7锟�4\n\n锟�3锟�9锟�3锟�8锟�3锟�9锟�3锟�9锟�3锟�2 锟�3锟�0锟�3锟�2锟�3锟�1 锟�3锟�2锟�3锟�9 锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5 锟�9锟�8锟�6锟�9锟�9锟�1", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para agregar un usuario autorizado
@app.on_message(filters.command("add") & (filters.private | filters.group))
async def add_user(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("锟�3锟�2锟�3锟�6锟�3锟�2: /add user_id")
            return

        for user_id in args:
            try:
                user_id = int(user_id)
                if user_id not in AUTHORIZED_USERS:
                    AUTHORIZED_USERS.append(user_id)
                    save_data()
                    await message.reply_text(f"锟�7锟�3锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�8锟�3锟�5锟�3锟�6锟�3锟�2 {user_id} 锟�3锟�8锟�3锟�4锟�3锟�4 锟�3锟�8 锟�3锟�9锟�3锟�8 锟�3锟�9锟�3锟�6锟�3锟�6锟�3锟�7锟�3锟�8锟�3锟�6锟�3锟�2锟�3锟�5锟�7锟�3.")
                else:
                    await message.reply_text(f"锟�6锟�0锟�1锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�8锟�3锟�5锟�3锟�6锟�3锟�2 {user_id} 锟�3锟�2锟�3锟�8 锟�3锟�2锟�3锟�6锟�3锟�7锟�3锟�8 锟�3锟�2锟�3锟�1 锟�3锟�9锟�3锟�8 锟�3锟�9锟�3锟�6锟�3锟�6锟�3锟�7锟�3锟�8锟�3锟�6锟�3锟�2锟�3锟�5锟�6锟�0锟�1锟�5.")
            except ValueError:
                await message.reply_text(f"锟�8锟�7锟�3锟�0锟�3锟�5 锟�3锟�2锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�1锟�3锟�2锟�3锟�8: {user_id}锟�8锟�7")
    else:
        await message.reply_text(
            "锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�3锟�3锟�2锟�3锟�6锟�3锟�2锟�3锟�2 锟�3锟�8锟�3锟�0锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�2锟�7锟�4\n\n锟�3锟�9锟�3锟�8锟�3锟�9锟�3锟�9锟�3锟�2 锟�3锟�0锟�3锟�2锟�3锟�1 锟�3锟�2锟�3锟�9 锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5 锟�9锟�8锟�6锟�9锟�9锟�1", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para quitar un usuario autorizado
@app.on_message(filters.command("ban") & (filters.private | filters.group))
async def ban_user(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("锟�3锟�2锟�3锟�6锟�3锟�2: /ban user_id")
            return

        for user_id in args:
            try:
                user_id = int(user_id)
                if user_id in AUTHORIZED_USERS:
                    AUTHORIZED_USERS.remove(user_id)
                    save_data()
                    await message.reply_text(f"锟�7锟�3锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�8锟�3锟�5锟�3锟�6锟�3锟�2 {user_id} 锟�3锟�5锟�3锟�2锟�3锟�0锟�3锟�2锟�3锟�9锟�3锟�6锟�3锟�1锟�3锟�2 锟�3锟�1锟�3锟�2 锟�3锟�9锟�3锟�8 锟�3锟�9锟�3锟�6锟�3锟�6锟�3锟�7锟�3锟�8锟�3锟�6锟�3锟�2锟�3锟�5锟�7锟�3.")
                else:
                    await message.reply_text(f"锟�6锟�0锟�1锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�8锟�3锟�5锟�3锟�6锟�3锟�2 {user_id} 锟�3锟�1锟�3锟�2 锟�3锟�2锟�3锟�6锟�3锟�7锟�3锟�8 锟�3锟�2锟�3锟�1 锟�3锟�9锟�3锟�8 锟�3锟�9锟�3锟�6锟�3锟�6锟�3锟�7锟�3锟�8锟�3锟�6锟�3锟�2锟�3锟�5锟�6锟�0锟�1锟�5.")
            except ValueError:
                await message.reply_text(f"锟�8锟�7锟�3锟�0锟�3锟�5 锟�3锟�2锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�1锟�3锟�2锟�3锟�8: {user_id}锟�8锟�7")
    else:
        await message.reply_text(
            "锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�3锟�3锟�2锟�3锟�6锟�3锟�2锟�3锟�2 锟�3锟�8锟�3锟�0锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�2锟�7锟�4\n\n锟�3锟�9锟�3锟�8锟�3锟�9锟�3锟�9锟�3锟�2 锟�3锟�0锟�3锟�2锟�3锟�1 锟�3锟�2锟�3锟�9 锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5 锟�9锟�8锟�6锟�9锟�9锟�1", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para listar usuarios autorizados
@app.on_message(filters.command("listusers") & (filters.private | filters.group))
async def list_users(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        if AUTHORIZED_USERS:
            user_list = "\n".join(map(str, AUTHORIZED_USERS))
            await message.reply_text(f"锟�3锟�3锟�3锟�6锟�3锟�6锟�3锟�7 锟�3锟�2锟�3锟�6锟�3锟�2锟�3锟�5 锟�9锟�0:\n{user_list}")
        else:
            await message.reply_text("锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�5锟�3锟�8锟�3锟�2 锟�3锟�8锟�3锟�6锟�3锟�8锟�3锟�8锟�3锟�5锟�3锟�6锟�3锟�2锟�3锟�6 锟�3锟�8锟�3锟�8锟�3锟�7锟�3锟�2锟�3锟�5锟�3锟�6锟�3锟�3锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�6锟�7锟�4.")
    else:
        await message.reply_text(
            "锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�3锟�3锟�2锟�3锟�6锟�3锟�2锟�3锟�2 锟�3锟�8锟�3锟�0锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�2锟�7锟�4\n\n锟�3锟�9锟�3锟�8锟�3锟�9锟�3锟�9锟�3锟�2 锟�3锟�0锟�3锟�2锟�3锟�1 锟�3锟�2锟�3锟�9 锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5 锟�9锟�8锟�6锟�9锟�9锟�1", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para agregar un grupo autorizado
@app.on_message(filters.command("grup") & (filters.private | filters.group))
async def add_group(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("锟�3锟�2锟�3锟�6锟�3锟�2: /grup group_id")
            return

        for group_id in args:
            try:
                group_id = int(group_id)
                if group_id not in AUTHORIZED_GROUPS:
                    AUTHORIZED_GROUPS.append(group_id)
                    save_data()
                    await message.reply_text(f"锟�7锟�3锟�3锟�8锟�3锟�5锟�3锟�8锟�3锟�3锟�3锟�2 {group_id} 锟�3锟�8锟�3锟�4锟�3锟�4 锟�3锟�8 锟�3锟�9锟�3锟�8 锟�3锟�9锟�3锟�6锟�3锟�6锟�3锟�7 锟�3锟�4锟�3锟�5锟�3锟�8锟�3锟�3锟�7锟�3")
                else:
                    await message.reply_text(f"锟�6锟�0锟�1锟�5锟�3锟�8锟�3锟�5锟�3锟�8锟�3锟�3锟�3锟�2 {group_id} 锟�3锟�2锟�3锟�8 锟�3锟�2锟�3锟�6锟�3锟�7锟�3锟�8 锟�3锟�2锟�3锟�1 锟�3锟�9锟�3锟�8 锟�3锟�9锟�3锟�6锟�3锟�6锟�3锟�7 锟�3锟�4锟�3锟�5锟�3锟�8锟�3锟�3锟�6锟�0锟�1锟�5.")
            except ValueError:
                await message.reply_text(f"锟�8锟�7锟�3锟�0锟�3锟�5 锟�3锟�2锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�1锟�3锟�2锟�3锟�8: {group_id}锟�8锟�7")
    else:
        await message.reply_text(
            "锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�3锟�3锟�2锟�3锟�6锟�3锟�2锟�3锟�2 锟�3锟�8锟�3锟�0锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�2锟�7锟�4\n\n锟�3锟�9锟�3锟�8锟�3锟�9锟�3锟�9锟�3锟�2 锟�3锟�0锟�3锟�2锟�3锟�1 锟�3锟�2锟�3锟�9 锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5 锟�9锟�8锟�6锟�9锟�9锟�1", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para quitar un grupo autorizado
@app.on_message(filters.command("bangrup") & (filters.private | filters.group))
async def ban_group(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("锟�3锟�2锟�3锟�6锟�3锟�2: /bangrup group_id")
            return

        for group_id in args:
            try:
                group_id = int(group_id)
                if group_id in AUTHORIZED_GROUPS:
                    AUTHORIZED_GROUPS.remove(group_id)
                    save_data()
                    await message.reply_text(f"锟�7锟�3锟�3锟�8锟�3锟�5锟�3锟�8锟�3锟�3锟�3锟�2 {group_id} 锟�3锟�5锟�3锟�2锟�3锟�0锟�3锟�2锟�3锟�9锟�3锟�6锟�3锟�1锟�3锟�2 锟�3锟�1锟�3锟�2 锟�3锟�9锟�3锟�8 锟�3锟�9锟�3锟�6锟�3锟�6锟�3锟�7 锟�3锟�4锟�3锟�5锟�3锟�8锟�3锟�3锟�7锟�3.")
                else:
                    await message.reply_text(f"锟�6锟�0锟�1锟�5锟�3锟�8锟�3锟�5锟�3锟�8锟�3锟�3锟�3锟�2 {group_id} 锟�3锟�1锟�3锟�2 锟�3锟�2锟�3锟�6锟�3锟�7锟�3锟�8 锟�3锟�2锟�3锟�1 锟�3锟�9锟�3锟�8 锟�3锟�9锟�3锟�6锟�3锟�6锟�3锟�7 锟�3锟�4锟�3锟�5锟�3锟�8锟�3锟�3锟�6锟�0锟�1锟�5.")
            except ValueError:
                await message.reply_text(f"锟�8锟�7锟�3锟�0锟�3锟�5 锟�3锟�2锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�1锟�3锟�2锟�3锟�8: {group_id}锟�8锟�7")
    else:
        await message.reply_text(
            "锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�3锟�3锟�2锟�3锟�6锟�3锟�2锟�3锟�2 锟�3锟�8锟�3锟�0锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�2锟�7锟�4\n\n锟�3锟�9锟�3锟�8锟�3锟�9锟�3锟�9锟�3锟�2 锟�3锟�0锟�3锟�2锟�3锟�1 锟�3锟�2锟�3锟�9 锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5锟�9锟�8锟�6锟�9锟�9锟�1", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para listar grupos autorizados
@app.on_message(filters.command("listgrup") & (filters.private | filters.group))
async def list_groups(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        if AUTHORIZED_GROUPS:
            group_list = "\n".join(map(str, AUTHORIZED_GROUPS))
            await message.reply_text(f"锟�3锟�3锟�3锟�6锟�3锟�6锟�3锟�7 锟�3锟�4锟�3锟�5锟�3锟�8锟�3锟�3 锟�9锟�9:\n{group_list}")
        else:
            await message.reply_text("锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�5锟�3锟�8锟�3锟�2 锟�3锟�4锟�3锟�5锟�3锟�8锟�3锟�3锟�3锟�2锟�3锟�6 锟�3锟�8锟�3锟�8锟�3锟�7锟�3锟�2锟�3锟�5锟�3锟�6锟�3锟�3锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�6锟�7锟�4.")
    else:
        await message.reply_text(
            "锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�3锟�3锟�2锟�3锟�6锟�3锟�2锟�3锟�2 锟�3锟�8锟�3锟�0锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�2锟�7锟�4\n\n锟�3锟�9锟�3锟�8锟�3锟�9锟�3锟�9锟�3锟�2 锟�3锟�0锟�3锟�2锟�3锟�1 锟�3锟�2锟�3锟�9 锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5锟�9锟�8锟�6锟�9锟�9锟�1", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para agregar un administrador
@app.on_message(filters.command("add_admins") & filters.private)
async def add_admin(client: Client, message: Message):
    if is_super_admin(message.from_user.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("锟�3锟�2锟�3锟�6锟�3锟�2: /add_admins user_id")
            return

        for user_id in args:
            try:
                user_id = int(user_id)
                if user_id not in ADMINS and user_id not in SUPER_ADMINS:
                    ADMINS.append(user_id)
                    save_data()
                    await message.reply_text(f"锟�7锟�3锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�8锟�3锟�5锟�3锟�6锟�3锟�2 {user_id} 锟�3锟�8锟�3锟�4锟�3锟�4 锟�3锟�8 锟�3锟�9锟�3锟�8 锟�3锟�9锟�3锟�6锟�3锟�6锟�3锟�7 锟�3锟�8锟�3锟�1锟�3锟�0锟�3锟�6锟�3锟�1锟�3锟�6锟�7锟�3.")
                else:
                    await message.reply_text(f"锟�6锟�0锟�1锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�8锟�3锟�5锟�3锟�6锟�3锟�2 {user_id} 锟�3锟�2锟�3锟�8 锟�3锟�2锟�3锟�6 锟�3锟�8锟�3锟�1锟�3锟�0锟�3锟�6锟�3锟�1锟�6锟�0锟�1锟�5.")
            except ValueError:
                await message.reply_text(f"锟�8锟�7锟�3锟�0锟�3锟�5 锟�3锟�2锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�1锟�3锟�2锟�3锟�8: {user_id}锟�8锟�7")
    else:
        await message.reply_text(
            "锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�3锟�3锟�2锟�3锟�6锟�3锟�2锟�3锟�2 锟�3锟�8锟�3锟�0锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�2锟�7锟�4\n\n锟�3锟�9锟�3锟�8锟�3锟�9锟�3锟�9锟�3锟�2 锟�3锟�0锟�3锟�2锟�3锟�1 锟�3锟�2锟�3锟�9 锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5 锟�9锟�8锟�6锟�9锟�9锟�1", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para quitar un administrador
@app.on_message(filters.command("ban_admins") & filters.private)
async def ban_admin(client: Client, message: Message):
    if is_super_admin(message.from_user.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("锟�3锟�2锟�3锟�6锟�3锟�2: /ban_admins user_id")
            return

        for user_id in args:
            try:
                user_id = int(user_id)
                if user_id in ADMINS and user_id not in SUPER_ADMINS:
                    ADMINS.remove(user_id)
                    save_data()
                    await message.reply_text(f"锟�7锟�3锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�8锟�3锟�5锟�3锟�6锟�3锟�2 {user_id} 锟�3锟�5锟�3锟�2锟�3锟�0锟�3锟�2锟�3锟�9锟�3锟�6锟�3锟�1锟�3锟�2 锟�3锟�1锟�3锟�2 锟�3锟�9锟�3锟�8 锟�3锟�9锟�3锟�6锟�3锟�6锟�3锟�7 锟�3锟�8锟�3锟�1锟�3锟�0锟�3锟�6锟�3锟�1锟�3锟�6锟�7锟�3.")
                else:
                    await message.reply_text(f"锟�6锟�0锟�1锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�8锟�3锟�5锟�3锟�6锟�3锟�2 {user_id} 锟�3锟�1锟�3锟�2 锟�3锟�2锟�3锟�6 锟�3锟�8锟�3锟�1锟�3锟�0锟�3锟�6锟�3锟�1锟�6锟�0锟�1锟�5.")
            except ValueError:
                await message.reply_text(f"锟�8锟�7锟�3锟�0锟�3锟�5 锟�3锟�2锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�1锟�3锟�2锟�3锟�8: {user_id}锟�8锟�7")
    else:
        await message.reply_text(
            "锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�3锟�3锟�2锟�3锟�6锟�3锟�2锟�3锟�2 锟�3锟�8锟�3锟�0锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�2锟�7锟�4\n\n锟�3锟�9锟�3锟�8锟�3锟�9锟�3锟�9锟�3锟�2 锟�3锟�0锟�3锟�2锟�3锟�1 锟�3锟�2锟�3锟�9 锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5 锟�9锟�8锟�6锟�9锟�9锟�1", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para obtener el ID de un usuario
@app.on_message(filters.command("id") & (filters.private | filters.group))
async def get_id(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        if len(message.command) == 1:
            await message.reply_text(f"锟�3锟�1锟�3锟�8 锟�3锟�0锟�3锟�5: {message.from_user.id}")
        else:
            username = message.command[1]
            user = await client.get_users(username)
            await message.reply_text(f"锟�3锟�0锟�3锟�5 锟�3锟�1锟�3锟�2 @{user.username}: {user.id}")
    else:
        await message.reply_text(
            "锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�3锟�3锟�2锟�3锟�6锟�3锟�2锟�3锟�2 锟�3锟�8锟�3锟�0锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�2锟�7锟�4\n\n锟�3锟�9锟�3锟�8锟�3锟�9锟�3锟�9锟�3锟�2 锟�3锟�0锟�3锟�2锟�3锟�1 锟�3锟�2锟�3锟�9 锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5 锟�9锟�8锟�6锟�9锟�9锟�1", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para Enviar un Mensaje a Todos los Usuarios y Grupos Autorizados
@app.on_message(filters.command("info") & filters.private)
async def send_info(client: Client, message: Message):
    if is_admin(message.from_user.id):
        args = message.text.split(None, 1)
        if len(args) == 1:
            await message.reply_text("锟�3锟�2锟�3锟�6锟�3锟�2: /info [mensaje]")
            return

        info_message = args[1]

        # Enviar mensaje a todos los usuarios autorizados
        for user_id in AUTHORIZED_USERS:
            try:
                await client.send_message(user_id, info_message)
            except Exception as e:
                logger.error(f"锟�8锟�7锟�3锟�6锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�5 锟�3锟�8锟�3锟�9 锟�3锟�2锟�3锟�1锟�3锟�9锟�3锟�6锟�3锟�8锟�3锟�5 锟�3锟�0锟�3锟�2锟�3锟�1锟�3锟�6锟�3锟�8锟�3锟�7锟�3锟�2 锟�3锟�8 锟�3锟�8锟�3锟�6锟�3锟�8锟�3锟�8锟�3锟�5锟�3锟�6锟�3锟�2 {user_id}: {e}锟�8锟�7")

        # Enviar mensaje a todos los grupos autorizados
        for group_id in AUTHORIZED_GROUPS:
            try:
                await client.send_message(group_id, info_message)
            except Exception as e:
                logger.error(f"锟�8锟�7锟�3锟�6锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�5 锟�3锟�8锟�3锟�9 锟�3锟�2锟�3锟�1锟�3锟�9锟�3锟�6锟�3锟�8锟�3锟�5 锟�3锟�0锟�3锟�2锟�3锟�1锟�3锟�6锟�3锟�8锟�3锟�7锟�3锟�2 锟�3锟�8 锟�3锟�4锟�3锟�5锟�3锟�8锟�3锟�3锟�3锟�2 {group_id}: {e}锟�8锟�7")

        await message.reply_text("锟�7锟�3锟�3锟�4锟�3锟�2锟�3锟�1锟�3锟�6锟�3锟�8锟�3锟�7锟�3锟�2 锟�3锟�4锟�3锟�9锟�3锟�2锟�3锟�9锟�3锟�8锟�3锟�9 锟�3锟�2锟�3锟�1锟�3锟�9锟�3锟�6锟�3锟�8锟�3锟�1锟�3锟�2 锟�3锟�0锟�3锟�2锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�0锟�3锟�7锟�3锟�8锟�3锟�0锟�3锟�2锟�3锟�1锟�3锟�7锟�3锟�2锟�7锟�3.")
    else:
        await message.reply_text(
            "锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�3锟�3锟�2锟�3锟�6锟�3锟�2锟�3锟�2 锟�3锟�8锟�3锟�0锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�2锟�7锟�4\n\n锟�3锟�9锟�3锟�8锟�3锟�9锟�3锟�9锟�3锟�2 锟�3锟�0锟�3锟�2锟�3锟�1 锟�3锟�2锟�3锟�9 锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5 锟�9锟�8锟�6锟�9锟�9锟�1", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para cambiar el l锟斤拷mite de tama锟�0锟�9o de video
@app.on_message(filters.command("max") & filters.private)
async def set_max_size(client: Client, message: Message):
    if is_admin(message.from_user.id):
        args = message.text.split(None, 1)
        if len(args) == 1:
            await message.reply_text("锟�3锟�2锟�3锟�6锟�3锟�2: /max [tama锟�0锟�9o en MB o GB]")
            return

        size = args[1].upper()
        if size.endswith("GB"):
            try:
                size_gb = int(size[:-2])
                max_video_size = size_gb * 1024 * 1024 * 1024
            except ValueError:
                await message.reply_text("锟�7锟�4锟�3锟�6锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�5 锟�3锟�8锟�3锟�6锟�3锟�2 锟�3锟�8锟�3锟�1锟�3锟�8 锟�3锟�0锟�3锟�6锟�3锟�3锟�3锟�5锟�3锟�8 锟�3锟�2 锟�3锟�1锟�3锟�2锟�3锟�6锟�3锟�3锟�3锟�8锟�3锟�2锟�3锟�6 'GB'锟�7锟�4")
                return
        elif size.endswith("MB"):
            try:
                size_mb = int(size[:-2])
                max_video_size = size_mb * 1024 * 1024
            except ValueError:
                await message.reply_text("锟�7锟�4锟�3锟�6锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�5 锟�3锟�8锟�3锟�6锟�3锟�2 锟�3锟�8锟�3锟�1锟�3锟�8 锟�3锟�0锟�3锟�6锟�3锟�3锟�3锟�5锟�3锟�8 锟�3锟�2 锟�3锟�1锟�3锟�2锟�3锟�6锟�3锟�3锟�3锟�8锟�3锟�2锟�3锟�6 'MB'锟�7锟�4")
                return
        else:
            await message.reply_text("锟�7锟�4锟�3锟�6锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�5 锟�3锟�8锟�3锟�6锟�3锟�2 锟�3锟�8锟�3锟�1锟�3锟�8 锟�3锟�0锟�3锟�6锟�3锟�3锟�3锟�5锟�3锟�8 锟�3锟�2 锟�3锟�1锟�3锟�2锟�3锟�6锟�3锟�3锟�3锟�8锟�3锟�2锟�3锟�6 'MB' 锟�3锟�2 'GB'锟�7锟�4")
            return

        await message.reply_text(f"锟�7锟�3锟�3锟�3锟�3锟�6锟�3锟�0锟�3锟�6锟�3锟�7锟�3锟�2 锟�3锟�0锟�3锟�8锟�3锟�0锟�3锟�9锟�3锟�6锟�3锟�8锟�3锟�1锟�3锟�2 锟�3锟�8 {size}锟�7锟�3.")
    else:
        await message.reply_text(
            "锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�3锟�3锟�2锟�3锟�6锟�3锟�2锟�3锟�2 锟�3锟�8锟�3锟�0锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�2锟�7锟�4\n\n锟�3锟�9锟�3锟�8锟�3锟�9锟�3锟�9锟�3锟�2 锟�3锟�0锟�3锟�2锟�3锟�1 锟�3锟�2锟�3锟�9 锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5 锟�9锟�8锟�6锟�9锟�9锟�1", url="https://t.me/Sasuke286")]
            ])
        )

# Manejador de videos
@app.on_message(filters.video & (filters.private | filters.group))
async def handle_video(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        await message.reply_text("锟�9锟�2锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�0锟�3锟�8锟�3锟�5锟�3锟�4锟�3锟�8锟�3锟�1锟�3锟�1锟�3锟�2 锟�3锟�3锟�3锟�6锟�3锟�1锟�3锟�2锟�3锟�2锟�9锟�3")

        # Extraer el nombre del archivo original
        file_name = message.video.file_name
        if not file_name:
            file_name = f"{message.video.file_id}.mkv"  # Usar el file_id como nombre por defecto si no hay nombre
        else:
             # Cambiar la extensi锟斤拷n del archivo a .mkv
             base_name, _ = os.path.splitext(file_name)
             file_name = f"{base_name}.mkv"

        # Descargar el video
        input_file = f"downloads/{file_name}"
        os.makedirs("downloads", exist_ok=True)
        try:
            await message.download(file_name=input_file)
        except Exception as e:
            logger.error(f"锟�8锟�7锟�3锟�6锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�5 锟�3锟�8锟�3锟�9 锟�3锟�1锟�3锟�2锟�3锟�6锟�3锟�0锟�3锟�8锟�3锟�5锟�3锟�4锟�3锟�8锟�3锟�5 锟�3锟�2锟�3锟�9 锟�3锟�9锟�3锟�6锟�3锟�1锟�3锟�2锟�3锟�2: {e}锟�8锟�7")
            await message.reply_text("锟�8锟�7锟�3锟�6锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�5 锟�3锟�8锟�3锟�9 锟�3锟�1锟�3锟�2锟�3锟�6锟�3锟�0锟�3锟�8锟�3锟�5锟�3锟�4锟�3锟�8锟�3锟�5 锟�3锟�2锟�3锟�9 锟�3锟�9锟�3锟�6锟�3锟�1锟�3锟�2锟�3锟�2锟�8锟�7.")
            return

        # Obtener el tama锟�0锟�9o del video original
        original_size = os.path.getsize(input_file)

        # Verificar si el video excede el l锟斤拷mite de tama锟�0锟�9o
        if original_size > max_video_size:
            await message.reply_text(f"锟�7锟�4锟�3锟�6锟�3锟�6锟�3锟�7锟�3锟�2 锟�3锟�9锟�3锟�6锟�3锟�1锟�3锟�2锟�3锟�2 锟�3锟�2锟�3锟�1锟�3锟�2锟�3锟�1锟�3锟�2 锟�3锟�2锟�3锟�9 锟�3锟�9锟�3锟�6锟�3锟�0锟�3锟�6锟�3锟�7锟�3锟�2 锟�3锟�1锟�3锟�2 {max_video_size / (1024 * 1024 * 1024):.2f}锟�3锟�4锟�3锟�3锟�7锟�4")
            os.remove(input_file)
            return

        # Comprimir el video
        output_file = f"compressed/{file_name}"
        os.makedirs("compressed", exist_ok=True)
        start_time = time.time()
        await message.reply_text("锟�3锟�4锟�3锟�2锟�3锟�1锟�3锟�9锟�3锟�6锟�3锟�5锟�3锟�7锟�3锟�6锟�3锟�2锟�3锟�1锟�3锟�1锟�3锟�2 锟�3锟�3锟�3锟�6锟�3锟�1锟�3锟�2锟�3锟�2锟�9锟�3")
        returncode = await compress_video(input_file, output_file, message.from_user.id)
        end_time = time.time()

        if returncode != 0:
            await message.reply_text("锟�8锟�7锟�3锟�6锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�5 锟�3锟�8锟�3锟�9 锟�3锟�0锟�3锟�2锟�3锟�1锟�3锟�9锟�3锟�2锟�3锟�5锟�3锟�7锟�3锟�6锟�3锟�5锟�8锟�7.")
        else:
            # Obtener el tama锟�0锟�9o del video procesado
            processed_size = os.path.getsize(output_file)
            processing_time = end_time - start_time
            video_duration = message.video.duration

            # Formatear los tiempos
            processing_time_formatted = format_time(processing_time)
            video_duration_formatted = format_time(video_duration)

            # Crear la descripci锟斤拷n
            description = f"""
            锟�7锟�0锟�2锟�2 锟�3锟�9锟�3锟�7锟�3锟�4锟�3锟�2锟�3锟�4锟�3锟�8锟�3锟�4 锟�3锟�9锟�3锟�4锟�3锟�7锟�3锟�2锟�3锟�8锟�3锟�3锟�3锟�0锟�3锟�3锟�3锟�4 锟�3锟�2锟�3锟�4锟�3锟�7锟�3锟�7锟�3锟�4锟�3锟�2锟�3锟�9锟�3锟�0锟�3锟�2锟�3锟�4锟�3锟�3锟�3锟�9锟�3锟�4 锟�2锟�3锟�7锟�1\n
锟斤拷锟�0锟�3锟斤拷 锟�3锟�7锟�3锟�2锟�3锟�6锟�3锟�2 锟�3锟�2锟�3锟�5锟�3锟�6锟�3锟�4锟�3锟�6锟�3锟�1锟�3锟�8锟�3锟�9: {original_size / (1024 * 1024):.2f} MB
锟斤拷锟�0锟�8锟斤拷 锟�3锟�7锟�3锟�2锟�3锟�6锟�3锟�2 锟�3锟�3锟�3锟�5锟�3锟�2锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�1锟�3锟�2: {processed_size / (1024 * 1024):.2f} MB
锟�7锟�5 锟�3锟�1锟�3锟�6锟�3锟�2锟�3锟�0锟�3锟�3锟�3锟�2 锟�3锟�1锟�3锟�2 锟�3锟�3锟�3锟�5锟�3锟�2锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�0锟�3锟�6锟�3锟�2锟�3锟�1锟�3锟�7锟�3锟�2: {processing_time_formatted}
锟�1锟�3 锟�3锟�1锟�3锟�6锟�3锟�2锟�3锟�0锟�3锟�3锟�3锟�2 锟�3锟�1锟�3锟�2锟�3锟�9 锟�3锟�9锟�3锟�6锟�3锟�1锟�3锟�2锟�3锟�2: {video_duration_formatted}
锟�7锟�8 锟�0锟�3锟�3锟�8锟�3锟�8锟�3锟�2 锟�3锟�9锟�3锟�2 锟�3锟�1锟�3锟�6锟�3锟�6锟�3锟�3锟�3锟�5锟�3锟�8锟�3锟�7锟�3锟�2锟�3锟�6!锟�7锟�1
            """
            # Subir el video comprimido
            try:
                await client.send_video(message.chat.id, output_file, caption=description)
            except Exception as e:
                logger.error(f"锟�8锟�7锟�3锟�6锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�5 锟�3锟�8锟�3锟�9 锟�3锟�6锟�3锟�8锟�3锟�9锟�3锟�6锟�3锟�5 锟�3锟�2锟�3锟�9 锟�3锟�9锟�3锟�6锟�3锟�1锟�3锟�2锟�3锟�2: {e}锟�8锟�7")
                await message.reply_text("锟�8锟�7锟�3锟�6锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�5 锟�3锟�8锟�3锟�9 锟�3锟�6锟�3锟�8锟�3锟�9锟�3锟�6锟�3锟�5 锟�3锟�2锟�3锟�9 锟�3锟�3锟�3锟�6锟�3锟�1锟�3锟�2锟�3锟�2锟�8锟�7.")
            finally:
                os.remove(input_file)
                os.remove(output_file)
    else:
        await message.reply_text(
            "锟�7锟�4锟�3锟�5锟�3锟�2 锟�3锟�3锟�3锟�2锟�3锟�6锟�3锟�2锟�3锟�2 锟�3锟�8锟�3锟�0锟�3锟�0锟�3锟�2锟�3锟�6锟�3锟�2锟�7锟�4\n\n锟�3锟�9锟�3锟�8锟�3锟�9锟�3锟�9锟�3锟�2 锟�3锟�0锟�3锟�2锟�3锟�1 锟�3锟�2锟�3锟�9 锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5 锟�9锟�8锟�6锟�9锟�9锟�1", url="https://t.me/Sasuke286")]
            ])
        )
        
# Comando para mostrar informaci锟斤拷n del bot
@app.on_message(filters.command("about") & (filters.private | filters.group))
async def about(client: Client, message: Message):
    bot_version = "锟�3锟�3.3"
    bot_creator = "@Sasuke286"
    bot_creation_date = "14/11/24"

    about_text = f"锟�0锟�6 **锟�3锟�2锟�3锟�0锟�3锟�2锟�3锟�5锟�3锟�0锟�3锟�8 锟�3锟�1锟�3锟�2锟�3锟�9 锟�3锟�3锟�3锟�2锟�3锟�7:**\n\n" \
                 f" - 锟�9锟�6锟�3锟�3锟�3锟�2锟�3锟�5锟�3锟�6锟�3锟�6锟�3锟�2锟�3锟�1: {bot_version}\n" \
                 f" - 锟�9锟�8锟�6锟�9锟�9锟�1锟�3锟�4锟�3锟�5锟�3锟�2锟�3锟�8锟�3锟�1锟�3锟�2锟�3锟�5: {bot_creator}\n" \
                 f" - 锟�9锟�1锟�3锟�7锟�3锟�2锟�3锟�0锟�3锟�5锟�3锟�8 锟�3锟�1锟�3锟�2 锟�3锟�5锟�3锟�2锟�3锟�6锟�3锟�8锟�3锟�5锟�3锟�5锟�3锟�2锟�3锟�9锟�3锟�9锟�3锟�2: {bot_creation_date}\n" \
                 f" - 锟�9锟�6锟�3锟�7锟�3锟�8锟�3锟�1锟�3锟�0锟�3锟�6锟�3锟�2锟�3锟�1锟�3锟�2锟�3锟�6: 锟�3锟�4锟�3锟�2锟�3锟�1锟�3锟�9锟�3锟�2锟�3锟�5锟�3锟�7锟�3锟�6锟�3锟�5 锟�3锟�9锟�3锟�6锟�3锟�1锟�3锟�2锟�3锟�2锟�3锟�6.\n\n" \
                 f"锟�0锟�3锟�3锟�6锟�3锟�6锟�3锟�3锟�3锟�2锟�3锟�5锟�3锟�2 锟�3锟�7锟�3锟�2 锟�3锟�4锟�3锟�8锟�3锟�6锟�3锟�7锟�3锟�2! 锟�0锟�7"

    await message.reply_text(about_text)

# Servidor web para el health check
flask_app = Flask(__name__)

@flask_app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

# Funci锟斤拷n para iniciar Gradio
def start_gradio():
    gr.Interface(fn=lambda: "Bot de compresi锟斤拷n de videos en ejecuci锟斤拷n", inputs=[], outputs="text").launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    import threading
    gradio_thread = threading.Thread(target=start_gradio)
    gradio_thread.daemon = True
    gradio_thread.start()

    # Iniciar el bot
    app.run()

    # Iniciar el servidor web
    flask_app.run(host='0.0.0.0', port=8000)
