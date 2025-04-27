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

# Configuraci��n del bot
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

# L��mite de tamaￄ1�70ￄ1�79o de video (en bytes)
max_video_size = 5 * 1024 * 1024 * 1024  # 1GB por defecto

# Configuraci��n de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Inicializaci��n del bot
app = Client("ffmpeg_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, workdir="/app/session")

# Funci��n para verificar si el usuario es un administrador supremo
def is_super_admin(user_id):
    return user_id in SUPER_ADMINS

# Funci��n para verificar si el usuario es un administrador
def is_admin(user_id):
    return user_id in ADMINS or user_id in SUPER_ADMINS

# Funci��n para verificar si el usuario es autorizado
def is_authorized(user_id):
    return user_id in AUTHORIZED_USERS or user_id in ADMINS or user_id in SUPER_ADMINS

# Funci��n para verificar si el grupo es autorizado
def is_authorized_group(chat_id):
    if chat_id in AUTHORIZED_GROUPS:
        return True
    logger.info(f"ￄ1�77ￄ1�74ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�73ￄ1�73ￄ1�72 {chat_id} ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�78ￄ1�73ￄ1�77ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�73ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�77ￄ1�74.")
    return False

# Funci��n para guardar los datos en un archivo JSON
def save_data():
    data = {
        'authorized_users': AUTHORIZED_USERS,
        'authorized_groups': AUTHORIZED_GROUPS,
        'admins': ADMINS
    }
    with open('data.json', 'w') as f:
        json.dump(data, f)

# Funci��n para cargar los datos desde un archivo JSON
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

# Funci��n para formatear el tiempo en HH:MM:SS
def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

# Funci��n para comprimir el video
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
    stdout, stderr = await process.communicate()  # Por si tiene error en la compresi��n
    if process.returncode != 0:
        logger.error(f"ￄ1�76ￄ1�70ￄ1�71ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�73ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72: {stderr.decode()}ￄ1�76ￄ1�70ￄ1�71ￄ1�75")
    return process.returncode
    
# Comando de bienvenida
@app.on_message(filters.command("start") & (filters.private | filters.group))
async def start(client: Client, message: Message):
    if is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        await message.reply_text(
            "ￄ1�79ￄ1�70 Bienvenido a Compresor Video use /help para mas ayuda ￄ1�79ￄ1�72"
        )
    else:
        await message.reply_text(
            "ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�77ￄ1�74\n\nￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�79ￄ1�71", url="https://t.me/Sasuke286")]
            ])
        )

# Comando de ayuda
@app.on_message(filters.command("help") & (filters.private | filters.group))
async def help(client: Client, message: Message):
    if is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        help_text = """
        **ￄ1�70ￄ1�76ￄ1�73ￄ1�74ￄ1�73ￄ1�72ￄ1�73ￄ1�70ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�76 ￄ1�73ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�76ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�70ￄ1�76:**

        **ￄ1�79ￄ1�74ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76 ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�79ￄ1�74:**
        - **/start**: Muestra un mensaje de bienvenida.
        - **/help**: Muestra esta lista de comandos.
        - **/calidad**: Cambia la calidad de compresi��n del video. Uso: `/calidad resolution=740x480 crf=32 audio_bitrate=60k fps=28 preset=ultrafast codec=libx265`
        - **/id**: Obtiene el ID de un usuario. Uso: `/id @username` (Solo Administradores)

        **ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�77ￄ1�76ￄ1�71ￄ1�75ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76 ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�70ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�77ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�77ￄ1�76ￄ1�71ￄ1�75:**
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
        - **/max**: Establece el l��mite de tamaￄ1�70ￄ1�79o para los videos. Uso: `/max [tamaￄ1�70ￄ1�79o en MB o GB]`

        **ￄ1�73ￄ1�74ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�78ￄ1�73ￄ1�71 ￄ1�73ￄ1�73ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�77ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�70ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�78ￄ1�79ￄ1�76:**
        - resolution: 740x480
        - crf: 32
        - audio_bitrate: 60k
        - fps: 28
        - preset: ultrafast
        - codec: libx265

        **ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72 ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�79ￄ1�73ￄ1�72ￄ1�73ￄ1�77ￄ1�79ￄ1�78:**
        - Env��a un video y el bot lo comprimir�� con la calidad actual.
        """
        await message.reply_text(help_text)
    else:
        await message.reply_text(
            "ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�77ￄ1�74\n\nￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�79ￄ1�71", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para listar administradores
@app.on_message(filters.command("listadmins") & (filters.private | filters.group))
async def list_admins(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        if ADMINS:
            admin_list = "\n".join(map(str, ADMINS))
            await message.reply_text(f"ￄ1�73ￄ1�73ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�77 ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�70ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�76 ￄ1�79ￄ1�75:\n{admin_list}")
        else:
            await message.reply_text("ￄ1�78ￄ1�77ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�70ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�78ￄ1�77.")
    else:
        await message.reply_text(
            "ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�77ￄ1�74\n\nￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�79ￄ1�71", url="https://t.me/Sasuke286")]
            ])
        )


@app.on_message(filters.command("calidad") & (filters.private | filters.group))
async def set_calidad(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        global current_calidad
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72: /calidad resolution=740x480 crf=32 audio_bitrate=60k fps=28 preset=ultrafast codec=libx265")
            return

        user_quality = current_calidad.get(message.from_user.id, DEFAULT_QUALITY.copy())
        for arg in args:
            try:
                key, value = arg.split('=')
                if key in user_quality:
                    user_quality[key] = value
                else:
                    await message.reply_text(f"ￄ1�78ￄ1�77ￄ1�73ￄ1�77ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�70ￄ1�77ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�77ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�70ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�72: {key}ￄ1�78ￄ1�77")
                    return
            except ValueError:
                await message.reply_text(f"ￄ1�78ￄ1�77ￄ1�73ￄ1�76ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�73ￄ1�73ￄ1�76ￄ1�73ￄ1�77ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�70ￄ1�77ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�77ￄ1�73ￄ1�75ￄ1�73ￄ1�72: {arg}ￄ1�78ￄ1�77")
                return

        current_calidad[message.from_user.id] = user_quality
        await message.reply_text(f"ￄ1�76ￄ1�70ￄ1�71ￄ1�75ￄ1�73ￄ1�74ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�78ￄ1�73ￄ1�71 ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�77ￄ1�73ￄ1�78ￄ1�73ￄ1�78ￄ1�73ￄ1�79: {current_calidad[message.from_user.id]}ￄ1�76ￄ1�70ￄ1�71ￄ1�75")
    else:
        await message.reply_text(
            "ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�77ￄ1�74\n\nￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�79ￄ1�71", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para agregar un usuario autorizado
@app.on_message(filters.command("add") & (filters.private | filters.group))
async def add_user(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72: /add user_id")
            return

        for user_id in args:
            try:
                user_id = int(user_id)
                if user_id not in AUTHORIZED_USERS:
                    AUTHORIZED_USERS.append(user_id)
                    save_data()
                    await message.reply_text(f"ￄ1�77ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�72 {user_id} ￄ1�73ￄ1�78ￄ1�73ￄ1�74ￄ1�73ￄ1�74 ￄ1�73ￄ1�78 ￄ1�73ￄ1�79ￄ1�73ￄ1�78 ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�77ￄ1�73ￄ1�78ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�77ￄ1�73.")
                else:
                    await message.reply_text(f"ￄ1�76ￄ1�70ￄ1�71ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�72 {user_id} ￄ1�73ￄ1�72ￄ1�73ￄ1�78 ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�77ￄ1�73ￄ1�78 ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�79ￄ1�73ￄ1�78 ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�77ￄ1�73ￄ1�78ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�76ￄ1�70ￄ1�71ￄ1�75.")
            except ValueError:
                await message.reply_text(f"ￄ1�78ￄ1�77ￄ1�73ￄ1�70ￄ1�73ￄ1�75 ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�78: {user_id}ￄ1�78ￄ1�77")
    else:
        await message.reply_text(
            "ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�77ￄ1�74\n\nￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�79ￄ1�71", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para quitar un usuario autorizado
@app.on_message(filters.command("ban") & (filters.private | filters.group))
async def ban_user(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72: /ban user_id")
            return

        for user_id in args:
            try:
                user_id = int(user_id)
                if user_id in AUTHORIZED_USERS:
                    AUTHORIZED_USERS.remove(user_id)
                    save_data()
                    await message.reply_text(f"ￄ1�77ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�72 {user_id} ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�79ￄ1�73ￄ1�78 ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�77ￄ1�73ￄ1�78ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�77ￄ1�73.")
                else:
                    await message.reply_text(f"ￄ1�76ￄ1�70ￄ1�71ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�72 {user_id} ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�77ￄ1�73ￄ1�78 ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�79ￄ1�73ￄ1�78 ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�77ￄ1�73ￄ1�78ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�76ￄ1�70ￄ1�71ￄ1�75.")
            except ValueError:
                await message.reply_text(f"ￄ1�78ￄ1�77ￄ1�73ￄ1�70ￄ1�73ￄ1�75 ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�78: {user_id}ￄ1�78ￄ1�77")
    else:
        await message.reply_text(
            "ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�77ￄ1�74\n\nￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�79ￄ1�71", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para listar usuarios autorizados
@app.on_message(filters.command("listusers") & (filters.private | filters.group))
async def list_users(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        if AUTHORIZED_USERS:
            user_list = "\n".join(map(str, AUTHORIZED_USERS))
            await message.reply_text(f"ￄ1�73ￄ1�73ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�77 ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�79ￄ1�70:\n{user_list}")
        else:
            await message.reply_text("ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�76 ￄ1�73ￄ1�78ￄ1�73ￄ1�78ￄ1�73ￄ1�77ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�73ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�77ￄ1�74.")
    else:
        await message.reply_text(
            "ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�77ￄ1�74\n\nￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�79ￄ1�71", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para agregar un grupo autorizado
@app.on_message(filters.command("grup") & (filters.private | filters.group))
async def add_group(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72: /grup group_id")
            return

        for group_id in args:
            try:
                group_id = int(group_id)
                if group_id not in AUTHORIZED_GROUPS:
                    AUTHORIZED_GROUPS.append(group_id)
                    save_data()
                    await message.reply_text(f"ￄ1�77ￄ1�73ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�73ￄ1�73ￄ1�72 {group_id} ￄ1�73ￄ1�78ￄ1�73ￄ1�74ￄ1�73ￄ1�74 ￄ1�73ￄ1�78 ￄ1�73ￄ1�79ￄ1�73ￄ1�78 ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�77 ￄ1�73ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�73ￄ1�77ￄ1�73")
                else:
                    await message.reply_text(f"ￄ1�76ￄ1�70ￄ1�71ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�73ￄ1�73ￄ1�72 {group_id} ￄ1�73ￄ1�72ￄ1�73ￄ1�78 ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�77ￄ1�73ￄ1�78 ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�79ￄ1�73ￄ1�78 ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�77 ￄ1�73ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�73ￄ1�76ￄ1�70ￄ1�71ￄ1�75.")
            except ValueError:
                await message.reply_text(f"ￄ1�78ￄ1�77ￄ1�73ￄ1�70ￄ1�73ￄ1�75 ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�78: {group_id}ￄ1�78ￄ1�77")
    else:
        await message.reply_text(
            "ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�77ￄ1�74\n\nￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�79ￄ1�71", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para quitar un grupo autorizado
@app.on_message(filters.command("bangrup") & (filters.private | filters.group))
async def ban_group(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72: /bangrup group_id")
            return

        for group_id in args:
            try:
                group_id = int(group_id)
                if group_id in AUTHORIZED_GROUPS:
                    AUTHORIZED_GROUPS.remove(group_id)
                    save_data()
                    await message.reply_text(f"ￄ1�77ￄ1�73ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�73ￄ1�73ￄ1�72 {group_id} ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�79ￄ1�73ￄ1�78 ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�77 ￄ1�73ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�73ￄ1�77ￄ1�73.")
                else:
                    await message.reply_text(f"ￄ1�76ￄ1�70ￄ1�71ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�73ￄ1�73ￄ1�72 {group_id} ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�77ￄ1�73ￄ1�78 ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�79ￄ1�73ￄ1�78 ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�77 ￄ1�73ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�73ￄ1�76ￄ1�70ￄ1�71ￄ1�75.")
            except ValueError:
                await message.reply_text(f"ￄ1�78ￄ1�77ￄ1�73ￄ1�70ￄ1�73ￄ1�75 ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�78: {group_id}ￄ1�78ￄ1�77")
    else:
        await message.reply_text(
            "ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�77ￄ1�74\n\nￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�79ￄ1�71", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para listar grupos autorizados
@app.on_message(filters.command("listgrup") & (filters.private | filters.group))
async def list_groups(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        if AUTHORIZED_GROUPS:
            group_list = "\n".join(map(str, AUTHORIZED_GROUPS))
            await message.reply_text(f"ￄ1�73ￄ1�73ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�77 ￄ1�73ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�73 ￄ1�79ￄ1�79:\n{group_list}")
        else:
            await message.reply_text("ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�72 ￄ1�73ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76 ￄ1�73ￄ1�78ￄ1�73ￄ1�78ￄ1�73ￄ1�77ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�73ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�77ￄ1�74.")
    else:
        await message.reply_text(
            "ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�77ￄ1�74\n\nￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�79ￄ1�71", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para agregar un administrador
@app.on_message(filters.command("add_admins") & filters.private)
async def add_admin(client: Client, message: Message):
    if is_super_admin(message.from_user.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72: /add_admins user_id")
            return

        for user_id in args:
            try:
                user_id = int(user_id)
                if user_id not in ADMINS and user_id not in SUPER_ADMINS:
                    ADMINS.append(user_id)
                    save_data()
                    await message.reply_text(f"ￄ1�77ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�72 {user_id} ￄ1�73ￄ1�78ￄ1�73ￄ1�74ￄ1�73ￄ1�74 ￄ1�73ￄ1�78 ￄ1�73ￄ1�79ￄ1�73ￄ1�78 ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�77 ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�70ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�76ￄ1�77ￄ1�73.")
                else:
                    await message.reply_text(f"ￄ1�76ￄ1�70ￄ1�71ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�72 {user_id} ￄ1�73ￄ1�72ￄ1�73ￄ1�78 ￄ1�73ￄ1�72ￄ1�73ￄ1�76 ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�70ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�76ￄ1�70ￄ1�71ￄ1�75.")
            except ValueError:
                await message.reply_text(f"ￄ1�78ￄ1�77ￄ1�73ￄ1�70ￄ1�73ￄ1�75 ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�78: {user_id}ￄ1�78ￄ1�77")
    else:
        await message.reply_text(
            "ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�77ￄ1�74\n\nￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�79ￄ1�71", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para quitar un administrador
@app.on_message(filters.command("ban_admins") & filters.private)
async def ban_admin(client: Client, message: Message):
    if is_super_admin(message.from_user.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72: /ban_admins user_id")
            return

        for user_id in args:
            try:
                user_id = int(user_id)
                if user_id in ADMINS and user_id not in SUPER_ADMINS:
                    ADMINS.remove(user_id)
                    save_data()
                    await message.reply_text(f"ￄ1�77ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�72 {user_id} ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�79ￄ1�73ￄ1�78 ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�77 ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�70ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�76ￄ1�77ￄ1�73.")
                else:
                    await message.reply_text(f"ￄ1�76ￄ1�70ￄ1�71ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�72 {user_id} ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�72ￄ1�73ￄ1�76 ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�70ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�76ￄ1�70ￄ1�71ￄ1�75.")
            except ValueError:
                await message.reply_text(f"ￄ1�78ￄ1�77ￄ1�73ￄ1�70ￄ1�73ￄ1�75 ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�78: {user_id}ￄ1�78ￄ1�77")
    else:
        await message.reply_text(
            "ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�77ￄ1�74\n\nￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�79ￄ1�71", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para obtener el ID de un usuario
@app.on_message(filters.command("id") & (filters.private | filters.group))
async def get_id(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        if len(message.command) == 1:
            await message.reply_text(f"ￄ1�73ￄ1�71ￄ1�73ￄ1�78 ￄ1�73ￄ1�70ￄ1�73ￄ1�75: {message.from_user.id}")
        else:
            username = message.command[1]
            user = await client.get_users(username)
            await message.reply_text(f"ￄ1�73ￄ1�70ￄ1�73ￄ1�75 ￄ1�73ￄ1�71ￄ1�73ￄ1�72 @{user.username}: {user.id}")
    else:
        await message.reply_text(
            "ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�77ￄ1�74\n\nￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�79ￄ1�71", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para Enviar un Mensaje a Todos los Usuarios y Grupos Autorizados
@app.on_message(filters.command("info") & filters.private)
async def send_info(client: Client, message: Message):
    if is_admin(message.from_user.id):
        args = message.text.split(None, 1)
        if len(args) == 1:
            await message.reply_text("ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72: /info [mensaje]")
            return

        info_message = args[1]

        # Enviar mensaje a todos los usuarios autorizados
        for user_id in AUTHORIZED_USERS:
            try:
                await client.send_message(user_id, info_message)
            except Exception as e:
                logger.error(f"ￄ1�78ￄ1�77ￄ1�73ￄ1�76ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�73ￄ1�78ￄ1�73ￄ1�79 ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�77ￄ1�73ￄ1�72 ￄ1�73ￄ1�78 ￄ1�73ￄ1�78ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�72 {user_id}: {e}ￄ1�78ￄ1�77")

        # Enviar mensaje a todos los grupos autorizados
        for group_id in AUTHORIZED_GROUPS:
            try:
                await client.send_message(group_id, info_message)
            except Exception as e:
                logger.error(f"ￄ1�78ￄ1�77ￄ1�73ￄ1�76ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�73ￄ1�78ￄ1�73ￄ1�79 ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�77ￄ1�73ￄ1�72 ￄ1�73ￄ1�78 ￄ1�73ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�73ￄ1�73ￄ1�72 {group_id}: {e}ￄ1�78ￄ1�77")

        await message.reply_text("ￄ1�77ￄ1�73ￄ1�73ￄ1�74ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�77ￄ1�73ￄ1�72 ￄ1�73ￄ1�74ￄ1�73ￄ1�79ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�79 ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�70ￄ1�73ￄ1�77ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�77ￄ1�73ￄ1�72ￄ1�77ￄ1�73.")
    else:
        await message.reply_text(
            "ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�77ￄ1�74\n\nￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�79ￄ1�71", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para cambiar el l��mite de tamaￄ1�70ￄ1�79o de video
@app.on_message(filters.command("max") & filters.private)
async def set_max_size(client: Client, message: Message):
    if is_admin(message.from_user.id):
        args = message.text.split(None, 1)
        if len(args) == 1:
            await message.reply_text("ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72: /max [tamaￄ1�70ￄ1�79o en MB o GB]")
            return

        size = args[1].upper()
        if size.endswith("GB"):
            try:
                size_gb = int(size[:-2])
                max_video_size = size_gb * 1024 * 1024 * 1024
            except ValueError:
                await message.reply_text("ￄ1�77ￄ1�74ￄ1�73ￄ1�76ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�73ￄ1�78ￄ1�73ￄ1�76ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�78 ￄ1�73ￄ1�70ￄ1�73ￄ1�76ￄ1�73ￄ1�73ￄ1�73ￄ1�75ￄ1�73ￄ1�78 ￄ1�73ￄ1�72 ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�73ￄ1�73ￄ1�78ￄ1�73ￄ1�72ￄ1�73ￄ1�76 'GB'ￄ1�77ￄ1�74")
                return
        elif size.endswith("MB"):
            try:
                size_mb = int(size[:-2])
                max_video_size = size_mb * 1024 * 1024
            except ValueError:
                await message.reply_text("ￄ1�77ￄ1�74ￄ1�73ￄ1�76ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�73ￄ1�78ￄ1�73ￄ1�76ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�78 ￄ1�73ￄ1�70ￄ1�73ￄ1�76ￄ1�73ￄ1�73ￄ1�73ￄ1�75ￄ1�73ￄ1�78 ￄ1�73ￄ1�72 ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�73ￄ1�73ￄ1�78ￄ1�73ￄ1�72ￄ1�73ￄ1�76 'MB'ￄ1�77ￄ1�74")
                return
        else:
            await message.reply_text("ￄ1�77ￄ1�74ￄ1�73ￄ1�76ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�73ￄ1�78ￄ1�73ￄ1�76ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�78 ￄ1�73ￄ1�70ￄ1�73ￄ1�76ￄ1�73ￄ1�73ￄ1�73ￄ1�75ￄ1�73ￄ1�78 ￄ1�73ￄ1�72 ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�73ￄ1�73ￄ1�78ￄ1�73ￄ1�72ￄ1�73ￄ1�76 'MB' ￄ1�73ￄ1�72 'GB'ￄ1�77ￄ1�74")
            return

        await message.reply_text(f"ￄ1�77ￄ1�73ￄ1�73ￄ1�73ￄ1�73ￄ1�76ￄ1�73ￄ1�70ￄ1�73ￄ1�76ￄ1�73ￄ1�77ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�78 {size}ￄ1�77ￄ1�73.")
    else:
        await message.reply_text(
            "ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�77ￄ1�74\n\nￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�79ￄ1�71", url="https://t.me/Sasuke286")]
            ])
        )

# Manejador de videos
@app.on_message(filters.video & (filters.private | filters.group))
async def handle_video(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        await message.reply_text("ￄ1�79ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�70ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�74ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�72ￄ1�79ￄ1�73")

        # Extraer el nombre del archivo original
        file_name = message.video.file_name
        if not file_name:
            file_name = f"{message.video.file_id}.mkv"  # Usar el file_id como nombre por defecto si no hay nombre
        else:
             # Cambiar la extensi��n del archivo a .mkv
             base_name, _ = os.path.splitext(file_name)
             file_name = f"{base_name}.mkv"

        # Descargar el video
        input_file = f"downloads/{file_name}"
        os.makedirs("downloads", exist_ok=True)
        try:
            await message.download(file_name=input_file)
        except Exception as e:
            logger.error(f"ￄ1�78ￄ1�77ￄ1�73ￄ1�76ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�73ￄ1�78ￄ1�73ￄ1�79 ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�70ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�74ￄ1�73ￄ1�78ￄ1�73ￄ1�75 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�72: {e}ￄ1�78ￄ1�77")
            await message.reply_text("ￄ1�78ￄ1�77ￄ1�73ￄ1�76ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�73ￄ1�78ￄ1�73ￄ1�79 ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�70ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�74ￄ1�73ￄ1�78ￄ1�73ￄ1�75 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�72ￄ1�78ￄ1�77.")
            return

        # Obtener el tamaￄ1�70ￄ1�79o del video original
        original_size = os.path.getsize(input_file)

        # Verificar si el video excede el l��mite de tamaￄ1�70ￄ1�79o
        if original_size > max_video_size:
            await message.reply_text(f"ￄ1�77ￄ1�74ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�77ￄ1�73ￄ1�72 ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�72 ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�70ￄ1�73ￄ1�76ￄ1�73ￄ1�77ￄ1�73ￄ1�72 ￄ1�73ￄ1�71ￄ1�73ￄ1�72 {max_video_size / (1024 * 1024 * 1024):.2f}ￄ1�73ￄ1�74ￄ1�73ￄ1�73ￄ1�77ￄ1�74")
            os.remove(input_file)
            return

        # Comprimir el video
        output_file = f"compressed/{file_name}"
        os.makedirs("compressed", exist_ok=True)
        start_time = time.time()
        await message.reply_text("ￄ1�73ￄ1�74ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�75ￄ1�73ￄ1�77ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�72ￄ1�79ￄ1�73")
        returncode = await compress_video(input_file, output_file, message.from_user.id)
        end_time = time.time()

        if returncode != 0:
            await message.reply_text("ￄ1�78ￄ1�77ￄ1�73ￄ1�76ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�73ￄ1�78ￄ1�73ￄ1�79 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�79ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�77ￄ1�73ￄ1�76ￄ1�73ￄ1�75ￄ1�78ￄ1�77.")
        else:
            # Obtener el tamaￄ1�70ￄ1�79o del video procesado
            processed_size = os.path.getsize(output_file)
            processing_time = end_time - start_time
            video_duration = message.video.duration

            # Formatear los tiempos
            processing_time_formatted = format_time(processing_time)
            video_duration_formatted = format_time(video_duration)

            # Crear la descripci��n
            description = f"""
            ￄ1�77ￄ1�70ￄ1�72ￄ1�72 ￄ1�73ￄ1�79ￄ1�73ￄ1�77ￄ1�73ￄ1�74ￄ1�73ￄ1�72ￄ1�73ￄ1�74ￄ1�73ￄ1�78ￄ1�73ￄ1�74 ￄ1�73ￄ1�79ￄ1�73ￄ1�74ￄ1�73ￄ1�77ￄ1�73ￄ1�72ￄ1�73ￄ1�78ￄ1�73ￄ1�73ￄ1�73ￄ1�70ￄ1�73ￄ1�73ￄ1�73ￄ1�74 ￄ1�73ￄ1�72ￄ1�73ￄ1�74ￄ1�73ￄ1�77ￄ1�73ￄ1�77ￄ1�73ￄ1�74ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�74ￄ1�73ￄ1�73ￄ1�73ￄ1�79ￄ1�73ￄ1�74 ￄ1�72ￄ1�73ￄ1�77ￄ1�71\n
��ￄ1�70ￄ1�73�� ￄ1�73ￄ1�77ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72 ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�74ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�78ￄ1�73ￄ1�79: {original_size / (1024 * 1024):.2f} MB
��ￄ1�70ￄ1�78�� ￄ1�73ￄ1�77ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72: {processed_size / (1024 * 1024):.2f} MB
ￄ1�77ￄ1�75 ￄ1�73ￄ1�71ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�70ￄ1�73ￄ1�73ￄ1�73ￄ1�72 ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�77ￄ1�73ￄ1�72: {processing_time_formatted}
ￄ1�71ￄ1�73 ￄ1�73ￄ1�71ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�70ￄ1�73ￄ1�73ￄ1�73ￄ1�72 ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�72: {video_duration_formatted}
ￄ1�77ￄ1�78 ￄ1�70ￄ1�73ￄ1�73ￄ1�78ￄ1�73ￄ1�78ￄ1�73ￄ1�72 ￄ1�73ￄ1�79ￄ1�73ￄ1�72 ￄ1�73ￄ1�71ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�73ￄ1�73ￄ1�75ￄ1�73ￄ1�78ￄ1�73ￄ1�77ￄ1�73ￄ1�72ￄ1�73ￄ1�76!ￄ1�77ￄ1�71
            """
            # Subir el video comprimido
            try:
                await client.send_video(message.chat.id, output_file, caption=description)
            except Exception as e:
                logger.error(f"ￄ1�78ￄ1�77ￄ1�73ￄ1�76ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�73ￄ1�78ￄ1�73ￄ1�79 ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�75 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�72: {e}ￄ1�78ￄ1�77")
                await message.reply_text("ￄ1�78ￄ1�77ￄ1�73ￄ1�76ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�73ￄ1�78ￄ1�73ￄ1�79 ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�75 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�73ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�72ￄ1�78ￄ1�77.")
            finally:
                os.remove(input_file)
                os.remove(output_file)
    else:
        await message.reply_text(
            "ￄ1�77ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�72 ￄ1�73ￄ1�78ￄ1�73ￄ1�70ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�77ￄ1�74\n\nￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72 ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�71 ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75 ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�79ￄ1�71", url="https://t.me/Sasuke286")]
            ])
        )
        
# Comando para mostrar informaci��n del bot
@app.on_message(filters.command("about") & (filters.private | filters.group))
async def about(client: Client, message: Message):
    bot_version = "ￄ1�73ￄ1�73.3"
    bot_creator = "@Sasuke286"
    bot_creation_date = "14/11/24"

    about_text = f"ￄ1�70ￄ1�76 **ￄ1�73ￄ1�72ￄ1�73ￄ1�70ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�70ￄ1�73ￄ1�78 ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�79 ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�77:**\n\n" \
                 f" - ￄ1�79ￄ1�76ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�71: {bot_version}\n" \
                 f" - ￄ1�79ￄ1�78ￄ1�76ￄ1�79ￄ1�79ￄ1�71ￄ1�73ￄ1�74ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�75: {bot_creator}\n" \
                 f" - ￄ1�79ￄ1�71ￄ1�73ￄ1�77ￄ1�73ￄ1�72ￄ1�73ￄ1�70ￄ1�73ￄ1�75ￄ1�73ￄ1�78 ￄ1�73ￄ1�71ￄ1�73ￄ1�72 ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�76ￄ1�73ￄ1�78ￄ1�73ￄ1�75ￄ1�73ￄ1�75ￄ1�73ￄ1�72ￄ1�73ￄ1�79ￄ1�73ￄ1�79ￄ1�73ￄ1�72: {bot_creation_date}\n" \
                 f" - ￄ1�79ￄ1�76ￄ1�73ￄ1�77ￄ1�73ￄ1�78ￄ1�73ￄ1�71ￄ1�73ￄ1�70ￄ1�73ￄ1�76ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�76: ￄ1�73ￄ1�74ￄ1�73ￄ1�72ￄ1�73ￄ1�71ￄ1�73ￄ1�79ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�77ￄ1�73ￄ1�76ￄ1�73ￄ1�75 ￄ1�73ￄ1�79ￄ1�73ￄ1�76ￄ1�73ￄ1�71ￄ1�73ￄ1�72ￄ1�73ￄ1�72ￄ1�73ￄ1�76.\n\n" \
                 f"ￄ1�70ￄ1�73ￄ1�73ￄ1�76ￄ1�73ￄ1�76ￄ1�73ￄ1�73ￄ1�73ￄ1�72ￄ1�73ￄ1�75ￄ1�73ￄ1�72 ￄ1�73ￄ1�77ￄ1�73ￄ1�72 ￄ1�73ￄ1�74ￄ1�73ￄ1�78ￄ1�73ￄ1�76ￄ1�73ￄ1�77ￄ1�73ￄ1�72! ￄ1�70ￄ1�77"

    await message.reply_text(about_text)

# Servidor web para el health check
flask_app = Flask(__name__)

@flask_app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

# Funci��n para iniciar Gradio
def start_gradio():
    gr.Interface(fn=lambda: "Bot de compresi��n de videos en ejecuci��n", inputs=[], outputs="text").launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    import threading
    gradio_thread = threading.Thread(target=start_gradio)
    gradio_thread.daemon = True
    gradio_thread.start()

    # Iniciar el bot
    app.run()

    # Iniciar el servidor web
    flask_app.run(host='0.0.0.0', port=8000)
