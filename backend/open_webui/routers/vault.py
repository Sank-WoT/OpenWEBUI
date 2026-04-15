import os
import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/vault", tags=["vault"])

@router.get("/keys/{path:path}")
async def get_vault_keys(path: str):
    """
    Получает список ключей из HashiCorp Vault KV v2
    Path: URL-encoded путь, например: 40serobabovas@region.cbr.ru
    """
    vault_addr = os.getenv("VAULT_ADDR", "http://localhost:8200")
    vault_token = os.getenv("VAULT_ROOT_TOKEN_ID")
    
    if not vault_token:
        raise HTTPException(status_code=500, detail="VAULT_ROOT_TOKEN_ID not configured")
    
    # KV v2 API требует префикса /kv/data/ для чтения данных
    vault_url = f"{vault_addr}/v1/kv/data/{path}"
    
    headers = {
        "X-Vault-Token": vault_token,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(vault_url, headers=headers)
            
            if response.status_code == 404:
                # Путь не найден — возвращаем пустой список
                return {"keys": []}
            
            response.raise_for_status()
            data = response.json()
            
            # KV v2 структура: data.data содержит сами пары ключ-значение
            vault_data = data.get("data", {}).get("data", {})
            
            # Возвращаем ТОЛЬКО ключи (как требовалось)
            return {"keys": list(vault_data.keys())}
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Vault unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
