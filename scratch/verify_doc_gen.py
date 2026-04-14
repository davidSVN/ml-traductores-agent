import asyncio
import os
import sys
from pathlib import Path

# Agregar src al path si es necesario
sys.path.append(str(Path(__file__).parent.parent))

from src.services.cotizacion import calcular_borrador
from src.services.documento import generar_word, docx_a_pdf

async def test():
    print("--- 1. Ejecutando calcular_borrador ---")
    # Usando los IDs que el usuario confirmó que existen
    result = await calcular_borrador(
        cliente_id=1,
        contacto_id=1,
        conversacion_id=None,
        tipo_servicio='interpretacion_simultanea_presencial',
        idioma_destino='ingles',
        idioma_origen='español',
        cantidad=8.0,
        num_interpretes=2,
        num_receptores=50,
        num_dias=1,
        ubicacion='Bogotá, Centro de Convenciones',
        horario='9am a 5pm',
        fecha_str='15 de mayo de 2026',
    )
    
    if 'error' in result:
        print(f"Error en calcular_borrador: {result['mensaje']}")
        return

    cotizacion_id = result['cotizacion_id']
    numero = result['numero_cotizacion']
    print(f"Borrador creado: {numero} (ID: {cotizacion_id})")

    # Asegurar que el directorio de storage existe
    os.makedirs("src/storage", exist_ok=True)

    print("--- 2. Generando Word ---")
    try:
        docx_bytes = await generar_word(cotizacion_id)
        docx_path = f"src/storage/{numero}.docx"
        with open(docx_path, "wb") as f:
            f.write(docx_bytes)
        print(f"Word guardado en: {docx_path} ({len(docx_bytes)} bytes)")
    except Exception as e:
        print(f"Error al generar Word: {e}")
        import traceback
        traceback.print_exc()
        return

    print("--- 3. Generando PDF ---")
    try:
        pdf_bytes = docx_a_pdf(docx_bytes)
        pdf_path = f"src/storage/{numero}.pdf"
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"PDF guardado en: {pdf_path} ({len(pdf_bytes)} bytes)")
    except Exception as e:
        print(f"Error al generar PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
