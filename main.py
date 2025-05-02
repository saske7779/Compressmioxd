import os
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import subprocess
import time
import json
from flask import Flask, jsonify
import gradio as gr
import datetime
import re

# Configuración del bot
API_ID = '21282861'
API_HASH = '5570ce56a170e27183b728b887f88aa0'
BOT_TOKEN = '8040530669:AAH2-RroQAT0RjDOVjE6dnTybFri61S5cb4'

# Lista de administradores supremos (IDs de usuario)
SUPER_ADMINS = [5702506445]

# Lista de administradores (IDs de usuario)
ADMINS = [5702506445]

# Lista de usuarios autorizados (IDs de usuario)
AUTHORIZED_USERS = [5702506445]

# Lista de grupos autorizados (IDs de grupo)
AUTHORIZED_GROUPS = [-1002354746023]

# Configuración de video settings
video_settings = {
    'default': {
        'resolution': '740x480',
        'crf': '32',
        'audio_bitrate': '60k',
        'fps': '28',
        'preset': 'ultrafast',
        'codec': 'libx265'
    }
}
current_calidad = {}

# Límite de tamaño de video (en bytes)
max_video_size = 5 * 1024 * 1024 * 1024

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Inicialización del bot
import os
session_dir = "/root/Compressmloxd/sessions"
os.makedirs(session_dir, exist_ok=True)

app = Client(
    "ffmpeg_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir=session_dir
)

# Función para verificar si el usuario es un administrador supremo
def is_super_admin(user_id):
    return user_id in SUPER_ADMINS

# Función para verificar si el usuario es un administrador
def is_admin(user_id):
    return user_id in ADMINS or user_id in SUPER_ADMINS

# Función para verificar si el usuario es autorizado
def is_authorized(user_id):
    return user_id in AUTHORIZED_USERS or user_id in ADMINS or user_id in SUPER_ADMINS

# Función para verificar si el grupo es autorizado
def is_authorized_group(chat_id):
    if chat_id in AUTHORIZED_GROUPS:
        return True
    logger.info(f"Grupo {chat_id} no está autorizado.")
    return False

# Función para guardar los datos en un archivo JSON
def save_data():
    data = {
        'authorized_users': AUTHORIZED_USERS,
        'authorized_groups': AUTHORIZED_GROUPS,
        'admins': ADMINS
    }
    with open('data.json', 'w') as f:
        json.dump(data, f)

# Función para cargar los datos desde un archivo JSON
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

# Función para formatear el tiempo en HH:MM:SS
def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

# Nuevas funciones de procesamiento de video
def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.{decimal_places}f} {unit}"
        size /= 1024.0
    return f"{size:.{decimal_places}f} PB"

def obtener_duracion_video(original_video_path):
    try:
        total_duration = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", original_video_path]
        )
        return float(total_duration.strip())
    except Exception as e:
        raise RuntimeError(f"Error al obtener la duración del video: {e}")

def comprimir_video(user_id, original_video_path, compressed_video_path, video_settings):
    settings = video_settings.get(user_id, video_settings['default'])
    ffmpeg_command = [
        'ffmpeg', '-y', '-i', original_video_path,
        '-s', settings['resolution'],
        '-crf', settings['crf'],
        '-b:a', settings['audio_bitrate'],
        '-r', settings['fps'],
        '-preset', settings['preset'],
        '-c:v', settings['codec'],
        compressed_video_path
    ]
    return subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE, text=True)

def calcular_progreso(output, total_duration):
    if "size=" in output and "time=" in output:
        match = re.search(r"size=\s*([\d]+).*time=([\d:.]+)", output)
        if match:
            size_kb, current_time_str = match.groups()
            size_kb = int(size_kb)
            readable_size = human_readable_size(size_kb * 1024)  # Convert KB to bytes
            current_time_parts = list(map(float, current_time_str.split(':')))
            current_time = (
                current_time_parts[0] * 3600 +
                current_time_parts[1] * 60 +
                current_time_parts[2]
            )
            percentage = (current_time / total_duration) * 100
            return readable_size, percentage, current_time
    return None, 0, 0

async def procesar_video(client, message, user_id, original_video_path):
    chat_id = message.chat.id
    compressed_video_path = f"{os.path.splitext(original_video_path)[0]}_compressed.mkv"
    # Crear mensaje de progreso con botón de cancelar
    progress_message = await client.send_message(
        chat_id=chat_id,
        text="🚀 **Iniciando proceso de compresión...**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancelar", callback_data=f"cancel_{message.id}")]
        ])
    )
    last_message_text = ""  # Para rastrear el último texto enviado y evitar MESSAGE_NOT_MODIFIED

    try:
        total_duration = obtener_duracion_video(original_video_path)
        start_time = datetime.datetime.now()
        
        process = comprimir_video(user_id, original_video_path, compressed_video_path, video_settings)
        last_update_time = datetime.datetime.now()

        # Variable para controlar si se canceló
        cancelled = False

        while True:
            # Verificar si el proceso ha terminado
            if process.poll() is not None:
                break

            # Leer la salida de ffmpeg
            output = process.stderr.readline()
            if output == '':
                continue

            # Verificar si el mensaje de progreso sigue existiendo
            try:
                await client.get_messages(chat_id, progress_message.id)
            except Exception:
                # Si el mensaje fue eliminado (cancelado), terminar el proceso
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                cancelled = True
                break

            readable_size, percentage, current_time = calcular_progreso(output, total_duration)
            if (datetime.datetime.now() - last_update_time).seconds >= 17 and percentage > 0:
                elapsed_time = datetime.datetime.now() - start_time
                estimated_total_time = (elapsed_time.total_seconds() / (percentage / 100)) if percentage > 0 else 0
                remaining_time = str(datetime.timedelta(seconds=int(estimated_total_time - elapsed_time.total_seconds())))

                # Calcular velocidad de compresión en MB/s
                if readable_size and elapsed_time.total_seconds() > 0:
                    size_str = readable_size.split()
                    size_value = float(size_str[0])
                    unit = size_str[1]
                    if unit == 'KB':
                        size_mb = size_value / 1024
                    elif unit == 'GB':
                        size_mb = size_value * 1024
                    elif unit == 'TB':
                        size_mb = size_value * 1024 * 1024
                    else:
                        size_mb = size_value  # Asumimos MB si no es otro
                    speed = size_mb / elapsed_time.total_seconds()  # MB/s
                else:
                    speed = 0

                # Crear barra de progreso
                bar_length = 13
                filled = int(bar_length * percentage / 100)
                bar = '⬢' * filled + '⬡' * (bar_length - filled)

                # Crear el nuevo texto del mensaje
                new_message_text = (
                    f"🎥 **Video Compression in Progress!**\n"
                    f"┃ {bar} {percentage:.2f}%\n"
                    f"┠ Processed: `{readable_size}`\n"
                    f"┠ Status: 🔄 Compressing | ETA: 🕒 {remaining_time}\n"
                    f"┠ Speed: ⚡ {speed:.2f} MB/s\n"
                    f"┖ Elapsed: ⏳ {str(elapsed_time).split('.')[0]}\n\n"
                    f"🚀 **Powered by Wolf Production Compress**"
                )

                # Editar el mensaje solo si el texto ha cambiado
                if new_message_text != last_message_text:
                    try:
                        await client.edit_message_text(
                            chat_id=chat_id,
                            message_id=progress_message.id,
                            text=new_message_text,
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("❌ Cancelar", callback_data=f"cancel_{message.id}")]
                            ])
                        )
                        last_message_text = new_message_text
                    except Exception as e:
                        if "MESSAGE_NOT_MODIFIED" not in str(e):
                            logger.warning(f"Error al editar mensaje de progreso: {e}")
                last_update_time = datetime.datetime.now()

        # Si se canceló, no continuar con el envío del video
        if cancelled:
            # Eliminar archivos
            for file_path in [original_video_path, compressed_video_path]:
                if os.path.exists(file_path):
                    os.remove(file_path)
            return

        # Enviar mensaje de finalización
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message.id,
            text="✅ **Proceso completado. Preparando resultados...**",
            reply_markup=None  # Remover el botón
        )

        compressed_size = os.path.getsize(compressed_video_path)
        original_size = os.path.getsize(original_video_path)
        description = (
            f"✅ **Archivo procesado correctamente ☑️**\n"
            f"📂 **Tamaño original:** {human_readable_size(original_size)}\n"
            f"📁 **Tamaño procesado:** {human_readable_size(compressed_size)}\n"
            f"⌛ **Tiempo de procesamiento:** {str(datetime.datetime.now() - start_time).split('.')[0]}\n"
            f"🎥 **Duración del video:** {str(datetime.timedelta(seconds=int(total_duration)))}\n"
            f"🎉 **¡Gracias por usar Wolf Production Compress!**"
        )

        await client.send_video(chat_id, compressed_video_path, caption=description)
        
    except Exception as e:
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message.id,
            text=f"❌ **Ocurrió un error al procesar el video:**\n{e}",
            reply_markup=None
        )
    finally:
        # Limpiar archivos solo si no se canceló explícitamente
        if not cancelled:
            for file_path in [original_video_path, compressed_video_path]:
                if os.path.exists(file_path):
                    os.remove(file_path)

# Función para descargar el video con progreso
async def download_video_with_progress(client, message, file_name, total_size):
    chat_id = message.chat.id
    input_file = f"downloads/{file_name}"
    progress_message = await client.send_message(
        chat_id=chat_id,
        text="⏳ **Iniciando descarga del video...**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancelar", callback_data=f"cancel_download_{message.id}")]
        ])
    )
    last_message_text = ""
    start_time = datetime.datetime.now()
    last_update_time = datetime.datetime.now()
    cancelled = False
    last_downloaded_size = [0]  # Usar lista para modificar en callback

    async def progress_callback(current, total):
        last_downloaded_size[0] = current
        # Verificar si el mensaje de progreso sigue existiendo
        try:
            await client.get_messages(chat_id, progress_message.id)
        except Exception:
            nonlocal cancelled
            cancelled = True
            raise Exception("Download cancelled by user")

        # Actualizar el progreso cada 17 segundos
        nonlocal last_update_time, last_message_text
        if (datetime.datetime.now() - last_update_time).seconds >= 17:
            percentage = (current / total) * 100 if total > 0 else 0
            readable_size = human_readable_size(current)
            elapsed_time = datetime.datetime.now() - start_time
            speed = (current / (1024 * 1024)) / elapsed_time.total_seconds() if elapsed_time.total_seconds() > 0 else 0
            estimated_total_time = (elapsed_time.total_seconds() / (percentage / 100)) if percentage > 0 else 0
            remaining_time = str(datetime.timedelta(seconds=int(estimated_total_time - elapsed_time.total_seconds())))

            # Crear barra de progreso
            bar_length = 13
            filled = int(bar_length * percentage / 100)
            bar = '⬢' * filled + '⬡' * (bar_length - filled)

            # Crear el nuevo texto del mensaje
            new_message_text = (
                f"📥 **Video Download in Progress!**\n"
                f"┃ {bar} {percentage:.2f}%\n"
                f"┠ Downloaded: `{readable_size}`\n"
                f"┠ Status: ⬇️ Downloading | ETA: 🕒 {remaining_time}\n"
                f"┠ Speed: ⚡ {speed:.2f} MB/s\n"
                f"┖ Elapsed: ⏳ {str(elapsed_time).split('.')[0]}\n\n"
                f"🚀 **Powered by Wolf Production Compress**"
            )

            # Editar el mensaje solo si el texto ha cambiado
            if new_message_text != last_message_text:
                try:
                    await client.edit_message_text(
                        chat_id=chat_id,
                        message_id=progress_message.id,
                        text=new_message_text,
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("❌ Cancelar", callback_data=f"cancel_download_{message.id}")]
                        ])
                    )
                    last_message_text = new_message_text
                except Exception as e:
                    if "MESSAGE_NOT_MODIFIED" not in str(e):
                        logger.warning(f"Error al editar mensaje de progreso de descarga: {e}")
            last_update_time = datetime.datetime.now()

    try:
        # Descargar el archivo con callback de progreso
        await client.download_media(message, file_name=input_file, progress=progress_callback)
        
        if cancelled:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=progress_message.id,
                text="❌ **Descarga cancelada por el usuario.**",
                reply_markup=None
            )
            if os.path.exists(input_file):
                os.remove(input_file)
            return False, input_file

        # Finalizar el mensaje de progreso
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message.id,
            text="✅ **Descarga completada. Iniciando compresión...**",
            reply_markup=None
        )
        return True, input_file

    except Exception as e:
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message.id,
            text=f"❌ **Error al descargar el video:**\n{e}",
            reply_markup=None
        )
        if os.path.exists(input_file):
            os.remove(input_file)
        return False, input_file

# Manejador para el botón de cancelar (compresión)
@app.on_callback_query(filters.regex(r"cancel_(\d+)"))
async def cancel_compression(client: Client, callback_query: CallbackQuery):
    message_id = int(callback_query.data.split("_")[1])
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    # Verificar que el usuario que cancela es autorizado
    if not (is_admin(user_id) or is_authorized(user_id) or is_authorized_group(chat_id)):
        await callback_query.answer("No tienes permiso para cancelar.", show_alert=True)
        return

    try:
        # Eliminar el mensaje de progreso
        await client.delete_messages(chat_id, callback_query.message.id)
        # Enviar mensaje de cancelación
        await client.send_message(
            chat_id=chat_id,
            text="❌ **Compresión cancelada por el usuario.**"
        )
        await callback_query.answer("Compresión cancelada.")
    except Exception as e:
        logger.error(f"Error al procesar cancelación: {e}")
        await callback_query.answer("Error al cancelar.", show_alert=True)

# Manejador para el botón de cancelar (descarga)
@app.on_callback_query(filters.regex(r"cancel_download_(\d+)"))
async def cancel_download(client: Client, callback_query: CallbackQuery):
    message_id = int(callback_query.data.split("_")[2])
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    # Verificar que el usuario que cancela es autorizado
    if not (is_admin(user_id) or is_authorized(user_id) or is_authorized_group(chat_id)):
        await callback_query.answer("No tienes permiso para cancelar.", show_alert=True)
        return

    try:
        # Eliminar el mensaje de progreso
        await client.delete_messages(chat_id, callback_query.message.id)
        # Enviar mensaje de cancelación
        await client.send_message(
            chat_id=chat_id,
            text="❌ **Descarga cancelada por el usuario.**"
        )
        await callback_query.answer("Descarga cancelada.")
    except Exception as e:
        logger.error(f"Error al procesar cancelación de descarga: {e}")
        await callback_query.answer("Error al cancelar.", show_alert=True)

# Comando de bienvenida
@app.on_message(filters.command("start") & (filters.private | filters.group))
async def start(client: Client, message: Message):
    if is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        await message.reply_text(
            "👋 Bienvenido a Wolf Production Compress use /help para más ayuda 👌"
        )
    else:
        await message.reply_text(
            "❌ No tienes permiso ❌\n\nContacta al administrador.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Admin 👑", url="https://t.me/Sasuke286")]
            ])
        )

# Comando de ayuda
@app.on_message(filters.command("help") & (filters.private | filters.group))
async def help(client: Client, message: Message):
    if is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        help_text = """
        **📌 Comandos Disponibles en Wolf Production Compress:**

        **📋 Comandos de usuario:**
        - **/start**: Muestra un mensaje de bienvenida.
        - **/help**: Muestra esta lista de comandos.
        - **/calidad**: Cambia la calidad de compresión del video. Uso: `/calidad resolution=740x480 crf=32 audio_bitrate=60k fps=28 preset=ultrafast codec=libx265`
        - **/id**: Obtiene el ID de un usuario. Uso: `/id @username` (Solo Administradores)

        **🔧 Comandos de administración:**
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
        - **/max**: Establece el límite de tamaño para los videos. Uso: `/max [tamaño en MB o GB]`

        **⚙️ Calidad por defecto:**
        - resolution: 740x480
        - crf: 32
        - audio_bitrate: 60k
        - fps: 28
        - preset: ultrafast
        - codec: libx265

        **📹 Uso del bot:**
        - Envía un video y Wolf Production Compress lo comprimirá con la calidad actual.
        """
        await message.reply_text(help_text)
    else:
        await message.reply_text(
            "❌ No tienes permiso ❌\n\nContacta al administrador.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Admin 👑", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para listar administradores
@app.on_message(filters.command("listadmins") & (filters.private | filters.group))
async def list_admins(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        if ADMINS:
            admin_list = "\n".join(map(str, ADMINS))
            await message.reply_text(f"Lista de admins:\n{admin_list}")
        else:
            await message.reply_text("No hay admins.")
    else:
        await message.reply_text(
            "❌ No tienes permiso ❌\n\nContacta al administrador.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Admin 👑", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para cambiar calidad
@app.on_message(filters.command("calidad") & (filters.private | filters.group))
async def set_calidad(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("Uso: /calidad resolution=740x480 crf=32 audio_bitrate=60k fps=28 preset=ultrafast codec=libx265")
            return

        user_quality = video_settings.get(message.from_user.id, video_settings['default'].copy())
        for arg in args:
            try:
                key, value = arg.split('=')
                if key in user_quality:
                    user_quality[key] = value
                else:
                    await message.reply_text(f"❌ Parámetro inválido: {key} ❌")
                    return
            except ValueError:
                await message.reply_text(f"❌ Formato inválido: {arg} ❌")
                return

        video_settings[message.from_user.id] = user_quality
        await message.reply_text(f"✅ Calidad actualizada: {video_settings[message.from_user.id]} ✅")
    else:
        await message.reply_text(
            "❌ No tienes permiso ❌\n\nContacta al administrador.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Admin 👑", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para agregar un usuario autorizado
@app.on_message(filters.command("add") & (filters.private | filters.group))
async def add_user(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("Uso: /add user_id")
            return

        for user_id in args:
            try:
                user_id = int(user_id)
                if user_id not in AUTHORIZED_USERS:
                    AUTHORIZED_USERS.append(user_id)
                    save_data()
                    await message.reply_text(f"✅ Usuario {user_id} añadido a la lista ✅")
                else:
                    await message.reply_text(f"ℹ️ Usuario {user_id} ya está en la lista ℹ️")
            except ValueError:
                await message.reply_text(f"❌ ID inválido: {user_id} ❌")
    else:
        await message.reply_text(
            "❌ No tienes permiso ❌\n\nContacta al administrador.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Admin 👑", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para quitar un usuario autorizado
@app.on_message(filters.command("ban") & (filters.private | filters.group))
async def ban_user(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("Uso: /ban user_id")
            return

        for user_id in args:
            try:
                user_id = int(user_id)
                if user_id in AUTHORIZED_USERS:
                    AUTHORIZED_USERS.remove(user_id)
                    save_data()
                    await message.reply_text(f"✅ Usuario {user_id} removido de la lista ✅")
                else:
                    await message.reply_text(f"ℹ️ Usuario {user_id} no está en la lista ℹ️")
            except ValueError:
                await message.reply_text(f"❌ ID inválido: {user_id} ❌")
    else:
        await message.reply_text(
            "❌ No tienes permiso ❌\n\nContacta al administrador.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Admin 👑", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para listar usuarios autorizados
@app.on_message(filters.command("listusers") & (filters.private | filters.group))
async def list_users(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        if AUTHORIZED_USERS:
            user_list = "\n".join(map(str, AUTHORIZED_USERS))
            await message.reply_text(f"Lista de usuarios:\n{user_list}")
        else:
            await message.reply_text("❌ No hay usuarios autorizados ❌")
    else:
        await message.reply_text(
            "❌ No tienes permiso ❌\n\nContacta al administrador.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Admin 👑", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para agregar un grupo autorizado
@app.on_message(filters.command("grup") & (filters.private | filters.group))
async def add_group(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("Uso: /grup group_id")
            return

        for group_id in args:
            try:
                group_id = int(group_id)
                if group_id not in AUTHORIZED_GROUPS:
                    AUTHORIZED_GROUPS.append(group_id)
                    save_data()
                    await message.reply_text(f"✅ Grupo {group_id} añadido a la lista ✅")
                else:
                    await message.reply_text(f"ℹ️ Grupo {group_id} ya está en la lista ℹ️")
            except ValueError:
                await message.reply_text(f"❌ ID inválido: {group_id} ❌")
    else:
        await message.reply_text(
            "❌ No tienes permiso ❌\n\nContacta al administrador.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Admin 👑", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para quitar un grupo autorizado
@app.on_message(filters.command("bangrup") & (filters.private | filters.group))
async def ban_group(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("Uso: /bangrup group_id")
            return

        for group_id in args:
            try:
                group_id = int(group_id)
                if group_id in AUTHORIZED_GROUPS:
                    AUTHORIZED_GROUPS.remove(group_id)
                    save_data()
                    await message.reply_text(f"✅ Grupo {group_id} removido de la lista ✅")
                else:
                    await message.reply_text(f"ℹ️ Grupo {group_id} no está en la lista ℹ️")
            except ValueError:
                await message.reply_text(f"❌ ID inválido: {group_id} ❌")
    else:
        await message.reply_text(
            "❌ No tienes permiso ❌\n\nContacta al administrador.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Admin 👑", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para listar grupos autorizados
@app.on_message(filters.command("listgrup") & (filters.private | filters.group))
async def list_groups(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        if AUTHORIZED_GROUPS:
            group_list = "\n".join(map(str, AUTHORIZED_GROUPS))
            await message.reply_text(f"Lista de grupos:\n{group_list}")
        else:
            await message.reply_text("❌ No hay grupos autorizados ❌")
    else:
        await message.reply_text(
            "❌ No tienes permiso ❌\n\nContacta al administrador.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Admin 👑", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para agregar un administrador
@app.on_message(filters.command("add_admins") & filters.private)
async def add_admin(client: Client, message: Message):
    if is_super_admin(message.from_user.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("Uso: /add_admins user_id")
            return

        for user_id in args:
            try:
                user_id = int(user_id)
                if user_id not in ADMINS and user_id not in SUPER_ADMINS:
                    ADMINS.append(user_id)
                    save_data()
                    await message.reply_text(f"✅ Usuario {user_id} añadido a la lista de admins ✅")
                else:
                    await message.reply_text(f"ℹ️ Usuario {user_id} ya es admin ℹ️")
            except ValueError:
                await message.reply_text(f"❌ ID inválido: {user_id} ❌")
    else:
        await message.reply_text(
            "❌ No tienes permiso ❌\n\nContacta al administrador.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Admin 👑", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para quitar un administrador
@app.on_message(filters.command("ban_admins") & filters.private)
async def ban_admin(client: Client, message: Message):
    if is_super_admin(message.from_user.id):
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("Uso: /ban_admins user_id")
            return

        for user_id in args:
            try:
                user_id = int(user_id)
                if user_id in ADMINS and user_id not in SUPER_ADMINS:
                    ADMINS.remove(user_id)
                    save_data()
                    await message.reply_text(f"✅ Usuario {user_id} removido de la lista de admins ✅")
                else:
                    await message.reply_text(f"ℹ️ Usuario {user_id} no es admin ℹ️")
            except ValueError:
                await message.reply_text(f"❌ ID inválido: {user_id} ❌")
    else:
        await message.reply_text(
            "❌ No tienes permiso ❌\n\nContacta al administrador.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Admin 👑", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para obtener el ID de un usuario
@app.on_message(filters.command("id") & (filters.private | filters.group))
async def get_id(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        if len(message.command) == 1:
            await message.reply_text(f"Tu ID: {message.from_user.id}")
        else:
            username = message.command[1]
            try:
                user = await client.get_users(username)
                await message.reply_text(f"ID de @{user.username}: {user.id}")
            except Exception as e:
                await message.reply_text(f"❌ Error al obtener ID: {e} ❌")
    else:
        await message.reply_text(
            "❌ No tienes permiso ❌\n\nContacta al administrador.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Admin 👑", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para enviar un mensaje a todos los usuarios y grupos autorizados
@app.on_message(filters.command("info") & filters.private)
async def send_info(client: Client, message: Message):
    if is_admin(message.from_user.id):
        args = message.text.split(None, 1)
        if len(args) == 1:
            await message.reply_text("Uso: /info [mensaje]")
            return

        info_message = args[1]

        for user_id in AUTHORIZED_USERS:
            try:
                await client.send_message(user_id, info_message)
            except Exception as e:
                logger.error(f"Error al enviar mensaje a usuario {user_id}: {e}")

        for group_id in AUTHORIZED_GROUPS:
            try:
                await client.send_message(group_id, info_message)
            except Exception as e:
                logger.error(f"Error al enviar mensaje a grupo {group_id}: {e}")

        await message.reply_text("✅ Mensaje enviado a todos los usuarios y grupos ✅")
    else:
        await message.reply_text(
            "❌ No tienes permiso ❌\n\nContacta al administrador.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Admin 👑", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para cambiar el límite de tamaño de video
@app.on_message(filters.command("max") & filters.private)
async def set_max_size(client: Client, message: Message):
    if is_admin(message.from_user.id):
        args = message.text.split(None, 1)
        if len(args) == 1:
            await message.reply_text("Uso: /max [tamaño en MB o GB]")
            return

        size = args[1].upper()
        if size.endswith("GB"):
            try:
                size_gb = float(size[:-2])
                global max_video_size
                max_video_size = int(size_gb * 1024 * 1024 * 1024)
            except ValueError:
                await message.reply_text("❌ Formato inválido, usa un número seguido de 'GB' ❌")
                return
        elif size.endswith("MB"):
            try:
                size_mb = float(size[:-2])
                max_video_size = int(size_mb * 1024 * 1024)
            except ValueError:
                await message.reply_text("❌ Formato inválido, usa un número seguido de 'MB' ❌")
                return
        else:
            await message.reply_text("❌ Formato inválido, usa 'MB' o 'GB' ❌")
            return

        await message.reply_text(f"✅ Límite actualizado a {size} ✅")
    else:
        await message.reply_text(
            "❌ No tienes permiso ❌\n\nContacta al administrador.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Admin 👑", url="https://t.me/Sasuke286")]
            ])
        )

# Manejador de videos
@app.on_message(filters.video & (filters.private | filters.group))
async def handle_video(client: Client, message: Message):
    if is_admin(message.from_user.id) or is_authorized(message.from_user.id) or is_authorized_group(message.chat.id):
        file_name = message.video.file_name
        if not file_name:
            file_name = f"{message.video.file_id}.mkv"
        else:
            base_name, _ = os.path.splitext(file_name)
            file_name = f"{base_name}.mkv"

        os.makedirs("downloads", exist_ok=True)
        total_size = message.video.file_size

        # Descargar el video con progreso
        success, input_file = await download_video_with_progress(client, message, file_name, total_size)
        if not success:
            return  # La descarga fue cancelada o falló

        original_size = os.path.getsize(input_file)
        if original_size > max_video_size:
            await client.send_message(
                chat_id=message.chat.id,
                text=f"❌ El video excede el límite de {human_readable_size(max_video_size)} ❌"
            )
            if os.path.exists(input_file):
                os.remove(input_file)
            return

        await procesar_video(client, message, message.from_user.id, input_file)
    else:
        await message.reply_text(
            "❌ No tienes permiso ❌\n\nContacta al administrador.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Admin 👑", url="https://t.me/Sasuke286")]
            ])
        )

# Comando para mostrar información del bot
@app.on_message(filters.command("about") & (filters.private | filters.group))
async def about(client: Client, message: Message):
    bot_version = "2.3"
    bot_creator = "@Sasuke286"
    bot_creation_date = "07/04/25"

    about_text = f"📌 **Acerca de 𝐖𝐨𝐥𝐟 𝐏𝐫𝐨𝐝𝐮𝐜𝐭𝐢𝐨𝐧 𝐂𝐨𝐦𝐩𝐫𝐞𝐬𝐬:**\n\n" \
                 f" - **Versión:** {bot_version}\n" \
                 f" - **Creador:** {bot_creator}\n" \
                 f" - **Fecha de creación:** {bot_creation_date}\n" \
                 f" - **Descripción:** Comprime videos.\n\n" \
                 f"¡Gracias por usar 𝐖𝐨𝐥𝐟 𝐏𝐫𝐨𝐝𝐮𝐜𝐭𝐢𝐨𝐧 𝐂𝐨𝐦𝐩𝐫𝐞𝐬𝐬! 🙌"

    await message.reply_text(about_text)

# Servidor web para el health check
flask_app = Flask(__name__)

@flask_app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

# Función para iniciar Gradio
def start_gradio():
    gr.Interface(fn=lambda: "𝐖𝐨𝐥𝐟 𝐏𝐫𝐨𝐝𝐮𝐜𝐭𝐢𝐨𝐧 𝐂𝐨𝐦𝐩𝐫𝐞𝐬𝐬 en ejecución", inputs=[], outputs="text").launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    import threading
    gradio_thread = threading.Thread(target=start_gradio)
    gradio_thread.daemon = True
    gradio_thread.start()

    # Iniciar el bot
    app.run()

    # Iniciar el servidor web
    flask_app.run(host='0.0.0.0', port=8000)
