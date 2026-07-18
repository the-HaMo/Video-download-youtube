from flask import Flask, request, jsonify, send_file, render_template_string
import yt_dlp
import os

app = Flask(__name__)

DOWNLOAD_FOLDER = 'descargas'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template_string(html_code)

@app.route('/convertir', methods=['POST'])
def convertir():
    datos = request.json
    url = datos.get('url')

    if not url:
        return jsonify({"error": "No se proporcionó ningún enlace"}), 400

    opciones_ydl = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'quiet': True,
        'extractor_args': {'youtube': ['player_client=android']}
    }

    try:
        with yt_dlp.YoutubeDL(opciones_ydl) as ydl:
            info = ydl.extract_info(url, download=True)
            nombre_archivo_original = ydl.prepare_filename(info)
            archivo_mp3 = nombre_archivo_original.rsplit('.', 1)[0] + '.mp3'
            
            # Limpiamos el título para evitar errores en nombres de archivo
            titulo_video = info.get('title', 'audio_youtube').replace('/', '_').replace('"', '')
            nombre_descarga = f"{titulo_video}.mp3"
            
            # Enviamos el archivo con el nombre original
            respuesta = send_file(archivo_mp3, as_attachment=True, download_name=nombre_descarga)
            # Exponemos la cabecera para que JavaScript pueda leer el nombre
            respuesta.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
            return respuesta
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

html_code = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Convertidor de YouTube a MP3</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background-color: #f4f4f9; }
        .container { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        input[type="text"] { width: 80%; padding: 10px; margin-bottom: 20px; border: 1px solid #ccc; border-radius: 5px; }
        button { padding: 10px 20px; background-color: #ff0000; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        button:disabled { background-color: #cccccc; }
        #estado { margin-top: 20px; font-weight: bold; color: #333; }
    </style>
</head>
<body>
    <div class="container">
        <h2>YouTube a MP3</h2>
        <input type="text" id="url" placeholder="Pega el enlace de YouTube aquí...">
        <br>
        <button id="btnConvertir" onclick="convertirVideo()">Convertir y Descargar</button>
        <p id="estado"></p>
    </div>

    <script>
        async function convertirVideo() {
            const url = document.getElementById('url').value;
            const estado = document.getElementById('estado');
            const btn = document.getElementById('btnConvertir');

            if (!url) {
                estado.innerText = "Por favor, introduce un enlace válido.";
                return;
            }

            estado.innerText = "Procesando el video... Esto puede tardar unos segundos.";
            btn.disabled = true;

            try {
                const respuesta = await fetch('/convertir', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });

                if (respuesta.ok) {
                    // Extraer el nombre original del archivo de las cabeceras
                    let nombreArchivo = "audio.mp3";
                    const disposicion = respuesta.headers.get('Content-Disposition');
                    if (disposicion && disposicion.includes('filename=')) {
                        nombreArchivo = disposicion.split('filename=')[1].split(';')[0].replace(/["']/g, '');
                    }

                    const blob = await respuesta.blob();
                    const urlDescarga = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = urlDescarga;
                    a.download = nombreArchivo; // Aquí usamos el nombre real
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    
                    estado.innerText = "¡Descarga completada con éxito!";
                } else {
                    const dataError = await respuesta.json();
                    estado.innerText = "Error: " + dataError.error;
                }
            } catch (error) {
                estado.innerText = "Error de conexión con el servidor.";
            } finally {
                btn.disabled = false;
            }
        }
    </script>
</body>
</html>
"""

# Importante: para producción ya no usamos app.run() de Flask, usaremos Gunicorn (ver Dockerfile)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)