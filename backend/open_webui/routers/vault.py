# backend/open_webui/routers/vault.py
import os
import httpx
from fastapi import APIRouter, HTTPException, Depends, Request

# 🔐 Импорт функции авторизации из open_webui.utils.auth
from open_webui.utils.auth import get_verified_user

router = APIRouter(tags=["vault"])  # ✅ prefix задаётся в main.py


@router.get("/keys/{path:path}")
async def get_vault_keys(path: str):
    """
    Получает список ключей из HashiCorp Vault KV v2
    Path: URL-encoded путь, например: 40serobabovas@40region.cbr.ru
    """
    vault_addr = os.getenv("VAULT_ADDR", "http://localhost:8200")
    vault_token = os.getenv("VAULT_ROOT_TOKEN_ID")
    
    if not vault_token:
        raise HTTPException(status_code=500, detail="VAULT_ROOT_TOKEN_ID not configured")
    
    vault_url = f"{vault_addr}/v1/kv/data/{path}"
    
    headers = {
        "X-Vault-Token": vault_token,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(vault_url, headers=headers)
            
            if response.status_code == 404:
                return {"keys": []}
            
            response.raise_for_status()
            data = response.json()
            vault_data = data.get("data", {}).get("data", {})
            return {"keys": list(vault_data.keys())}
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Vault unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.put("/data/{path:path}")
async def save_vault_data(
    path: str, 
    form_data: dict, 
    request: Request,
    user=Depends(get_verified_user)  # 🔐 Требует авторизации
):
    """
    Сохраняет параметр в HashiCorp Vault KV v2
    
    path: URL-encoded путь, например: 40serobabovas%4040region.cbr.ru
    form_data: {"key": "param_name", "value": "param_value"}
    
    Возвращает: {"status": "ok", "key": "param_name"}
    """
    vault_addr = os.getenv("VAULT_ADDR", "http://localhost:8200")
    vault_token = os.getenv("VAULT_ROOT_TOKEN_ID")
    
    if not vault_token:
        raise HTTPException(status_code=500, detail="VAULT_ROOT_TOKEN_ID not configured")
    
    key = form_data.get("key", "").strip()
    value = form_data.get("value", "")
    
    if not key:
        raise HTTPException(status_code=400, detail="Key is required")
    
    vault_url = f"{vault_addr}/v1/kv/data/{path}"
    headers = {
        "X-Vault-Token": vault_token,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # 1️⃣ Читаем существующие данные (если есть)
            existing_response = await client.get(vault_url, headers=headers)
            existing_data = {}
            
            if existing_response.status_code == 200:
                resp_json = existing_response.json()
                existing_data = resp_json.get("data", {}).get("data", {})
            elif existing_response.status_code != 404:
                existing_response.raise_for_status()
            
            # 2️⃣ Добавляем/обновляем ключ
            existing_data[key] = value
            
            # 3️⃣ Записываем обратно в Vault (KV v2 требует обёртку {"data": {...}})
            payload = {"data": existing_data}
            response = await client.post(vault_url, headers=headers, json=payload)
            response.raise_for_status()
            
            return {"status": "ok", "key": key}
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Vault unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.delete("/data/{path:path}")
async def delete_vault_key(
    path: str, 
    key: str,  # передаётся как query param: ?key=param_name
    user=Depends(get_verified_user)
):
    """
    Удаляет конкретный ключ из данных в Vault (без удаления всего секрета)
    """
    vault_addr = os.getenv("VAULT_ADDR", "http://localhost:8200")
    vault_token = os.getenv("VAULT_ROOT_TOKEN_ID")
    
    if not vault_token:
        raise HTTPException(status_code=500, detail="VAULT_ROOT_TOKEN_ID not configured")
    
    vault_url = f"{vault_addr}/v1/kv/data/{path}"
    headers = {
        "X-Vault-Token": vault_token,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Читаем текущие данные
            response = await client.get(vault_url, headers=headers)
            if response.status_code == 404:
                return {"status": "ok", "deleted": key}  # уже не существует
            
            response.raise_for_status()
            data = response.json()
            existing_data = data.get("data", {}).get("data", {})
            
            # Удаляем ключ
            if key in existing_data:
                del existing_data[key]
                
                # Если остались данные — обновляем
                if existing_data:
                    payload = {"data": existing_data}
                    await client.post(vault_url, headers=headers, json=payload)
            
            return {"status": "ok", "deleted": key}
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Vault unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
