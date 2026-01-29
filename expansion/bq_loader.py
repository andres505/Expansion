# expansion/bq_loader.py

import os
import json
from typing import Dict

from google.cloud import bigquery
from google.oauth2 import service_account


# =====================================================
# CLIENT
# =====================================================
def get_bq_client() -> bigquery.Client:
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON no definido")

    info = json.loads(raw)

    creds = service_account.Credentials.from_service_account_info(info)

    return bigquery.Client(
        credentials=creds,
        project=info["project_id"]
    )


# =====================================================
# LOAD PARQUET
# =====================================================
def load_parquet_to_bq(
    *,
    parquet_path: str,
    table_id: str,
    write_disposition: str = "WRITE_APPEND"
) -> Dict[str, str]:
    """
    Carga un archivo Parquet a una tabla existente en BigQuery.
    """

    if not os.path.exists(parquet_path):
        raise FileNotFoundError(parquet_path)

    client = get_bq_client()

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=write_disposition,
        autodetect=False  # 🔑 usa el schema existente
    )

    with open(parquet_path, "rb") as f:
        job = client.load_table_from_file(
            f,
            table_id,
            job_config=job_config
        )

    job.result()  # espera a que termine

    return {
        "table_id": table_id,
        "rows_loaded": job.output_rows,
        "job_id": job.job_id,
    }
