import os

from config.router import get_router_mode, RouterMode
from config.model_registry import MODEL_REGISTRY
from models.tenant import Tenant


def get_router_mode_dep() -> RouterMode:
    return get_router_mode()


def get_tenant_dep() -> Tenant:
    allowed_models_env = os.getenv("AGENTICLABS_ALLOWED_MODELS")
    if allowed_models_env:
        allowed = [
            model.strip()
            for model in allowed_models_env.split(",")
            if model.strip()
        ]
    else:
        allowed = list(MODEL_REGISTRY.keys())

    return Tenant(id="default", name="Default", allowed_models=allowed)
