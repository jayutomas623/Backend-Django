import os

# Carpeta base de tu proyecto (cámbiala si es necesario)
BASE_DIR = r"C:\Jayu\Sistemas\Proyecto-Django"
# Nombre del archivo que se generará
OUTPUT_FILE = "proyecto_completo_para_ia.txt"

# Carpetas que la IA NO necesita leer (para ahorrar espacio)
IGNORE_DIRS = {'node_modules', '.git', '__pycache__', 'venv', 'env', 'build', 'dist', '.idea', '.vscode'}

# Tipos de archivos que sí queremos incluir
ALLOWED_EXTENSIONS = {'.py', '.js', '.jsx', '.html', '.css', '.json'}

with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
    for root, dirs, files in os.walk(BASE_DIR):
        # Ignorar las carpetas pesadas/basura
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        # Escribir la ruta del archivo y luego su contenido
                        outfile.write(f"\n{'='*50}\n")
                        outfile.write(f"{filepath}\n")
                        outfile.write(f"{'='*50}\n")
                        outfile.write(f"{content}\n\n")
                except Exception as e:
                    print(f"No se pudo leer {filepath}: {e}")

print(f"¡Listo! Se ha creado el archivo {OUTPUT_FILE} con todo tu código.")