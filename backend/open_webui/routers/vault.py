# backend/open_webui/routers/vault.py
import os
from urllib.parse import quote

import httpx
from fastapi import APIRouter, HTTPException, Depends, Request

from open_webui.utils.auth import get_verified_user

router = APIRouter(tags=["vault"])


async def get_vault_user(request: Request, user=Depends(get_verified_user)):
    if not request.app.state.config.ENABLE_USER_PARAMETERS:
        raise HTTPException(status_code=404, detail="Not found")
    return user


def _kv_mount() -> str:
    return os.getenv("VAULT_KV_MOUNT", "kv")


def vault_secret_path(user) -> str:
    """Logical Vault KV path segment for this user (no client-controlled path)."""
    email = (getattr(user, "email", None) or "").strip().lower()
    if email:
        return email.replace("/", "_")
    uid = getattr(user, "id", None)
    if uid is not None:
        return str(uid)
    return "unknown"


def _vault_data_url(vault_addr: str, path: str) -> str:
    mount = _kv_mount()
    encoded = quote(path, safe="")
    return f"{vault_addr}/v1/{mount}/data/{encoded}"


async def _ensure_kv_secret_exists(
    client: httpx.AsyncClient, vault_url: str, headers: dict
) -> None:
    """Create an empty KV v2 secret at vault_url if it does not exist."""
    response = await client.get(vault_url, headers=headers)
    if response.status_code == 200:
        return
    if response.status_code == 404:
        post = await client.post(vault_url, headers=headers, json={"data": {}})
        post.raise_for_status()
        return
    response.raise_for_status()


@router.get("/keys")
async def get_vault_keys(user=Depends(get_vault_user)):
    """List key names in the current user's Vault KV secret (values not returned)."""
    vault_addr = os.getenv("VAULT_ADDR", "http://localhost:8200")
    vault_token = os.getenv("VAULT_ROOT_TOKEN_ID")

    if not vault_token:
        raise HTTPException(status_code=500, detail="VAULT_ROOT_TOKEN_ID not configured")

    path = vault_secret_path(user)
    vault_url = _vault_data_url(vault_addr, path)

    headers = {
        "X-Vault-Token": vault_token,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(vault_url, headers=headers)

            if response.status_code == 404:
                await _ensure_kv_secret_exists(client, vault_url, headers)
                response = await client.get(vault_url, headers=headers)

            response.raise_for_status()
            data = response.json()
            vault_data = data.get("data", {}).get("data", {})
            return {"keys": list(vault_data.keys())}

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Vault unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.put("/data")
async def save_vault_data(
    form_data: dict,
    user=Depends(get_vault_user),
):
    """
    Merge one key/value into the current user's Vault KV secret.

    form_data: {"key": "param_name", "value": "param_value"}
    """
    vault_addr = os.getenv("VAULT_ADDR", "http://localhost:8200")
    vault_token = os.getenv("VAULT_ROOT_TOKEN_ID")

    if not vault_token:
        raise HTTPException(status_code=500, detail="VAULT_ROOT_TOKEN_ID not configured")

    key = form_data.get("key", "").strip()
    value = form_data.get("value", "")

    if not key:
        raise HTTPException(status_code=400, detail="Key is required")

    path = vault_secret_path(user)
    vault_url = _vault_data_url(vault_addr, path)

    headers = {
        "X-Vault-Token": vault_token,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            existing_response = await client.get(vault_url, headers=headers)
            existing_data = {}

            if existing_response.status_code == 200:
                resp_json = existing_response.json()
                existing_data = resp_json.get("data", {}).get("data", {})
            elif existing_response.status_code != 404:
                existing_response.raise_for_status()

            existing_data[key] = value

            payload = {"data": existing_data}
            response = await client.post(vault_url, headers=headers, json=payload)
            response.raise_for_status()

            return {"status": "ok", "key": key}

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Vault unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.delete("/data")
async def delete_vault_key(
    key: str,
    user=Depends(get_vault_user),
):
    """Remove one key from the current user's Vault KV secret."""
    vault_addr = os.getenv("VAULT_ADDR", "http://localhost:8200")
    vault_token = os.getenv("VAULT_ROOT_TOKEN_ID")

    if not vault_token:
        raise HTTPException(status_code=500, detail="VAULT_ROOT_TOKEN_ID not configured")

    path = vault_secret_path(user)
    vault_url = _vault_data_url(vault_addr, path)

    headers = {
        "X-Vault-Token": vault_token,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(vault_url, headers=headers)
            if response.status_code == 404:
                return {"status": "ok", "deleted": key}

            response.raise_for_status()
            data = response.json()
            existing_data = data.get("data", {}).get("data", {})

            if key in existing_data:
                del existing_data[key]

                payload = {"data": existing_data}
                post = await client.post(vault_url, headers=headers, json=payload)
                post.raise_for_status()

            return {"status": "ok", "deleted": key}

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Vault unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
