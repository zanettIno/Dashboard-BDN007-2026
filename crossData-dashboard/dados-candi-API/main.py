import datetime
import logging
import json
import os
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr
from botocore.config import Config

load_dotenv_available = False
try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv_available = True
except ImportError:
    pass

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────
# DynamoDB setup
# ─────────────────────────────────────────────

dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1',  
    config=boto3.session.Config(
        connect_timeout=10,
        read_timeout=10,
        retries={'max_attempts': 2}
    )
)

sentimentos_tabela = dynamodb.Table('CANDIFeelings')
sintomas_tabela    = dynamodb.Table('CANDISymptoms')

# ─────────────────────────────────────────────
# Serialization
# ─────────────────────────────────────────────

def convert_decimal(obj):
    """Recursively convert DynamoDB Decimal types to int/float."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    return obj

# ─────────────────────────────────────────────
# Full table scan with pagination
# ─────────────────────────────────────────────

def scan_full_table(tabela, projection: str) -> list:
    """
    Scans an entire DynamoDB table with pagination support.
    Uses ProjectionExpression to fetch only the columns the dashboard needs,
    reducing read costs and payload size.
    """
    items = []
    kwargs = {"ProjectionExpression": projection}

    try:
        while True:
            response = tabela.scan(**kwargs)
            items.extend(response.get('Items', []))

            # DynamoDB paginates at 1MB — keep going until no more pages
            last_key = response.get('LastEvaluatedKey')
            if not last_key:
                break
            kwargs['ExclusiveStartKey'] = last_key

        logger.info(f"Tabela {tabela.name}: {len(items)} itens escaneados.")
        return items

    except ClientError as e:
        logger.error(f"Erro ao escanear {tabela.name}: {e}", exc_info=True)
        return []

# ─────────────────────────────────────────────
# Lambda handler
# ─────────────────────────────────────────────

def lambda_handler(event, context):
    """
    Dashboard Data API — returns all CANDIFeelings and CANDISymptoms
    formatted as flat records, ready for pandas/Dask consumption.

    Routes:
        GET /           → health check
        GET /dashboard  → full data export
    """
    path = event.get("path", "/dashboard")

    # ── Health check ────────────────────────────────────────────────
    if path == "/":
        try:
            sentimentos_tabela.table_status
            return _response(200, {
                "status": "healthy",
                "timestamp": _now()
            })
        except Exception as e:
            logger.error(f"Health check falhou: {e}")
            return _response(503, {"status": "unhealthy", "error": str(e)})

    # ── Full data export ─────────────────────────────────────────────
    try:
        # Only fetch the columns the dashboard actually uses
        sentimentos_raw = scan_full_table(
            sentimentos_tabela,
            "happiness, created_at, observation"
        )
        sintomas_raw = scan_full_table(
            sintomas_tabela,
            "description, created_at"
        )

        sentimentos_clean = convert_decimal(sentimentos_raw)
        sintomas_clean    = convert_decimal(sintomas_raw)

        return _response(200, {
            "candiSentimentos": sentimentos_clean,
            "candiSintomas":    sintomas_clean,
            "meta": {
                "total_sentimentos": len(sentimentos_clean),
                "total_sintomas":    len(sintomas_clean),
                "timestamp":         _now()
            }
        })

    except ClientError as e:
        logger.error(f"AWS ClientError: {e}", exc_info=True)
        return _response(503, {"error": "Serviço indisponível.", "codigo": "STORAGE_ERROR"})

    except Exception as e:
        logger.error(f"Erro inesperado: {e}", exc_info=True)
        return _response(500, {"error": "Erro interno.", "codigo": "INTERNAL_ERROR"})


def _response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            # Allow your Streamlit app to call this from any origin
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }

def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()