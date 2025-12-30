"""Import all models from all services for Alembic migrations.

This file centralizes model imports to avoid path and module conflicts.
"""

import sys
from pathlib import Path

# Get paths
auth_service_root = Path(__file__).resolve().parent.parent.parent
backend_root = auth_service_root.parent

# Add services to path
sys.path.insert(0, str(auth_service_root))
sys.path.insert(0, str(backend_root / "catalog-service"))
sys.path.insert(0, str(backend_root / "installation-service"))

# Import base classes
from .base import Base, BaseModel

# Import auth-service models
from .user import User

# Import catalog-service models by creating wrapper modules
catalog_models_path = backend_root / "catalog-service" / "app" / "models"

# Import Cat model
cat_module_code = (catalog_models_path / "cat.py").read_text(encoding="utf-8")
cat_module_code = cat_module_code.replace("from .base import Base, BaseModel", "")
cat_globals = {
    "Base": Base,
    "BaseModel": BaseModel,
    "__name__": "catalog_cat_model",
    "__file__": str(catalog_models_path / "cat.py"),
}
exec(cat_module_code, cat_globals)  # pylint: disable=exec-used
Cat = cat_globals.get("Cat")

# Import Permission model
perm_module_code = (catalog_models_path / "permission.py").read_text(encoding="utf-8")
perm_module_code = perm_module_code.replace("from .base import Base, BaseModel", "")
perm_globals = {
    "Base": Base,
    "BaseModel": BaseModel,
    "__name__": "catalog_permission_model",
    "__file__": str(catalog_models_path / "permission.py"),
}
exec(perm_module_code, perm_globals)  # pylint: disable=exec-used
Permission = perm_globals.get("Permission")

# Import installation-service models
install_models_path = backend_root / "installation-service" / "app" / "models"

# Import Installation model
inst_module_code = (install_models_path / "installation.py").read_text(encoding="utf-8")
inst_module_code = inst_module_code.replace("from .base import Base, BaseModel", "")
inst_globals = {
    "Base": Base,
    "BaseModel": BaseModel,
    "__name__": "installation_model",
    "__file__": str(install_models_path / "installation.py"),
}
exec(inst_module_code, inst_globals)  # pylint: disable=exec-used
Installation = inst_globals.get("Installation")

# Import InstallationPermission model
instperm_module_code = (install_models_path / "installation_permission.py").read_text(
    encoding="utf-8"
)
instperm_module_code = instperm_module_code.replace("from .base import Base", "")
instperm_globals = {
    "Base": Base,
    "__name__": "installation_permission_model",
    "__file__": str(install_models_path / "installation_permission.py"),
}
exec(instperm_module_code, instperm_globals)  # pylint: disable=exec-used
InstallationPermission = instperm_globals.get("InstallationPermission")

# Export all models
__all__ = [
    "Base",
    "BaseModel",
    "User",
    "Cat",
    "Permission",
    "Installation",
    "InstallationPermission",
]

print(f"Loaded models: {list(Base.metadata.tables.keys())}")
