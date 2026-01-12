# Copyright (c) OpenMMLab. All rights reserved.
from typing import Any, Dict

from mmengine.utils import ManagerMixin


class ObjectHub(ManagerMixin):
    """A global registry for runtime dependency injection and instance
    management.

    Args:
        name (str): Name of the instance context (usually experiment name).
            Defaults to ''
    """

    def __init__(self, name: str = ''):
        super().__init__(name)
        self._objects: Dict[str, Any] = {}

    def register(self, alias: str, obj: Any, force: bool = False) -> None:
        """Register an object with a unique alias.

        Args:
            alias (str): The unique alias to register the object under.
            obj (Any): The live object instance.
            force (bool): Whether to overwrite existing alias.
                Defaults to False.
        """
        if not isinstance(alias, str) or not alias:
            raise ValueError(
                f"Invalid alias: '{alias}'. Must be a non-empty string.")

        if alias in self._objects and not force:
            raise ValueError(
                f"Alias collision: '{alias}' is already registered. "
                'Use force=True to overwrite.')
        self._objects[alias] = obj

    def resolve(self, key_path: str) -> Any:
        """Resolve a reference string to an object or its attribute.

        Args:
            key_path (str): The reference path, e.g. 'backbone.out_channels'.

        Returns:
            Any: The resolved object.
        """
        parts = key_path.split('.')
        ref_name = parts[0]

        if ref_name not in self._objects:
            available = list(self._objects.keys())
            raise KeyError(f"Resolution Failed: Instance '{ref_name}' "
                           f"not found in ObjectHub('{self.instance_name}'). "
                           f'Available aliases: {available}')
        current_obj = self._objects[ref_name]

        for attr in parts[1:]:
            if attr.startswith('_'):
                raise PermissionError(
                    f"Access to private attribute '{attr}' is denied.")
            try:
                if isinstance(current_obj, dict):
                    current_obj = current_obj[attr]
                elif isinstance(current_obj, (list, tuple)) and attr.isdigit():
                    current_obj = current_obj[int(attr)]
                else:
                    current_obj = getattr(current_obj, attr)
            except (KeyError, AttributeError, IndexError) as e:
                raise ValueError(
                    f"Resolution Failed: '@{key_path}' "
                    f"stopped at '{attr}' on {type(current_obj).__name__}"
                ) from e

        return current_obj

    def unregister(self, alias: str) -> None:
        """Unregister an object by its alias."""
        if alias in self._objects:
            del self._objects[alias]

    def clear(self) -> None:
        """Clear all registered objects in this hub."""
        self._objects.clear()
