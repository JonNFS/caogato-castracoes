"""
make_icon.py
Converte Logo.png para Logo.ico com fundo transparente e múltiplos tamanhos.
Executado automaticamente pelo build_exe.bat antes de compilar.
"""
import sys, os

try:
    from PIL import Image
except ImportError:
    print("Instalando Pillow..."); os.system("pip install Pillow --quiet")
    from PIL import Image

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Logo.png")
if not os.path.exists(path):
    print("Logo.png não encontrado — pulando geração de ícone.")
    sys.exit(0)

img = Image.open(path).convert("RGBA")

# Remove fundo preto (torna transparente)
alpha = img.convert("RGB").convert("L").point(lambda v: 0 if v < 28 else 255, "L")
img.putalpha(alpha)

out = os.path.join(os.path.dirname(path), "Logo.ico")
img.save(out, format="ICO",
         sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
print(f"Logo.ico criado com sucesso → {out}")
