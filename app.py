import streamlit as st
import yt_dlp
import os
import glob
import re

st.set_page_config(page_title="Gestor de Descargas yt-dlp", page_icon="🎥", layout="centered")

st.title("🎥 Gestor Avanzado yt-dlp (Optimizado)")

# Carpeta temporal
TEMP_DIR = "temp_descargas"
os.makedirs(TEMP_DIR, exist_ok=True)

url = st.text_input("🔗 Enlace del video o lista de reproducción:")

col1, col2 = st.columns(2)
with col1:
    tipo_descarga = st.selectbox("Formato de Salida", ["Video (MP4)", "Solo Audio"])
    resolucion = st.selectbox("Resolución Máxima", ["1080", "720", "480", "Mejor"], disabled=(tipo_descarga == "Solo Audio"))
with col2:
    formato_audio = st.selectbox("Formato de Audio", ["mp3", "m4a", "wav"], disabled=(tipo_descarga == "Video (MP4)"))
    descargar_subs = st.checkbox("Incluir Subtítulos")

st.divider()

if st.button("🚀 Iniciar Descarga", type="primary"):
    if not url:
        st.warning("⚠️ Ingresa una URL válida.")
    else:
        # Limpieza de descargas previas
        for f in glob.glob(f"{TEMP_DIR}/*"):
            try:
                os.remove(f)
            except Exception:
                pass

        ydl_opts = {
            'outtmpl': f'{TEMP_DIR}/%(title)s.%(ext)s',
            'writesubtitles': descargar_subs,
            'subtitleslangs': ['es', 'en'],
            'quiet': True,
            'no_warnings': True,
            'color': 'no_color',
            # 'ffmpeg_location': 'C:/ruta/exacta/hacia/la/carpeta/bin', # Usa esto si ffmpeg.exe no está en esta carpeta
        }

        # 🔥 OPTIMIZACIÓN DE VELOCIDAD AQUÍ 🔥
        if tipo_descarga == "Solo Audio":
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': formato_audio,
                # Se eliminó la recodificación forzada de calidad para hacerlo más rápido
            }]
        else:
            # Forzamos MP4 y M4A desde el servidor. FFmpeg solo los unirá en 2 segundos sin recodificar.
            if resolucion == "Mejor":
                ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            else:
                ydl_opts['format'] = f'bestvideo[ext=mp4][height<={resolucion}]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            
            # Se eliminó el convertidor de video (FFmpegVideoConvertor) porque ya no es necesario

        with st.status("Iniciando...", expanded=True) as status:
            progress_bar = st.progress(0.0)
            
            def download_hook(d):
                if d['status'] == 'downloading':
                    percent_str = d.get('_percent_str', '0.0%').replace('%', '').strip()
                    percent_str = re.sub(r'\x1b\[[0-9;]*m', '', percent_str) 
                    try:
                        progress_bar.progress(float(percent_str) / 100.0)
                    except ValueError:
                        pass
                    status.update(label=f"⬇️ Descargando: {d.get('_percent_str', '')} (Velocidad: {d.get('_speed_str', '')})", state="running")
                elif d['status'] == 'finished':
                    progress_bar.progress(1.0)
                    status.update(label="✅ Descarga completada. Uniendo pistas (fase rápida)...", state="running")

            def post_hook(d):
                if d['status'] == 'started':
                    status.update(label="⚙️ FFmpeg trabajando...", state="running")
                elif d['status'] == 'finished':
                    status.update(label="✅ Procesamiento terminado.", state="running")

            ydl_opts['progress_hooks'] = [download_hook]
            ydl_opts['postprocessor_hooks'] = [post_hook]

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(url, download=True)
                    
                status.update(label="🎉 ¡Proceso finalizado!", state="complete", expanded=False)
                
                archivos_generados = glob.glob(f"{TEMP_DIR}/*")
                if archivos_generados:
                    archivo_final = archivos_generados[0]
                    nombre_archivo = os.path.basename(archivo_final)
                    
                    with open(archivo_final, "rb") as file:
                        st.success("¡El archivo está listo!")
                        st.download_button(
                            label=f"💾 Guardar {nombre_archivo}",
                            data=file,
                            file_name=nombre_archivo,
                            mime="application/octet-stream",
                            type="primary"
                        )
            except Exception as e:
                status.update(label=f"❌ Error: {str(e)}", state="error")