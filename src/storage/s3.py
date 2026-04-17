"""
Upload de archivos a AWS S3 y generación de presigned URLs.
Con fallback local (/tmp) si S3 no está configurado (desarrollo).
"""
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.config import get_settings

logger = logging.getLogger(__name__)


async def upload_contrato(cotizacion_id: int, pdf_bytes: bytes, numero: str) -> str:
    """
    Sube el PDF del contrato a S3 y retorna la URL presigned (7 días).
    numero: número de cotización base (ej: COT-20260417-001).
    """
    settings = get_settings()
    numero_cont = numero.replace("COT-", "CONT-")
    key = f"contratos/{cotizacion_id}/{numero_cont}.pdf"

    if not settings.aws_s3_bucket:
        local_path = f"/tmp/{numero_cont}.pdf"
        with open(local_path, "wb") as f:
            f.write(pdf_bytes)
        logger.warning(f"S3 no configurado. Contrato guardado en {local_path}.")
        return local_path

    try:
        s3 = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )
        s3.put_object(
            Bucket=settings.aws_s3_bucket,
            Key=key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
        logger.info(f"Contrato subido a S3: s3://{settings.aws_s3_bucket}/{key}")
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.aws_s3_bucket, "Key": key},
            ExpiresIn=604800,
        )
        return url
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Error subiendo contrato a S3: {e}")
        raise


async def upload_cotizacion(cotizacion_id: int, pdf_bytes: bytes, numero: str) -> str:
    """
    Sube el PDF de la cotización a S3 y retorna la URL presigned (7 días).

    Si aws_s3_bucket está vacío, guarda localmente en /tmp y retorna la ruta
    (solo útil para desarrollo — WhatsApp no puede acceder a rutas locales).

    Args:
        cotizacion_id: ID de la cotización (para armar la key S3).
        pdf_bytes:     Bytes del PDF generado.
        numero:        Número de cotización (ej: COT-20260413-001).

    Returns:
        URL pública/presigned del PDF.
    """
    settings = get_settings()
    key = f"cotizaciones/{cotizacion_id}/{numero}.pdf"

    if not settings.aws_s3_bucket:
        # Fallback local para desarrollo
        local_path = f"/tmp/{numero}.pdf"
        with open(local_path, "wb") as f:
            f.write(pdf_bytes)
        logger.warning(
            f"S3 no configurado (aws_s3_bucket vacío). PDF guardado en {local_path}. "
            "WhatsApp no podrá acceder a esta URL."
        )
        return local_path

    try:
        s3 = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )

        s3.put_object(
            Bucket=settings.aws_s3_bucket,
            Key=key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
        logger.info(f"PDF subido a S3: s3://{settings.aws_s3_bucket}/{key}")

        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.aws_s3_bucket, "Key": key},
            ExpiresIn=604800,  # 7 días
        )
        return url

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Error subiendo PDF a S3: {e}")
        raise
