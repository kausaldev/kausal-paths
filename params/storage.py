from __future__ import annotations

import hashlib
import json
import typing
from typing import Any, Optional

from loguru import logger

if typing.TYPE_CHECKING:
    from django.contrib.sessions.backends.base import SessionBase

    from nodes.instance import Instance


class SettingStorage:
    def reset(self):
        """Resets all customized settings to their default values."""
        raise NotImplementedError()

    def set_param(self, id: str, val: Any):
        """Sets a parameter value."""
        raise NotImplementedError()

    def reset_param(self, id: str):
        """Resets a parameter to its default value."""
        raise NotImplementedError()

    def set_option(self, id: str, val: Any):
        """Sets a global option."""
        raise NotImplementedError()

    def reset_option(self, id: str):
        """Reset a global option to its default value."""
        raise NotImplementedError()

    def get_customized_param_values(self) -> dict[str, Any]:
        """Returns ids of all currently customized parameters with their values."""
        raise NotImplementedError()

    def set_active_scenario(self, id: str | None):
        """Mark the supplied scenario as active."""
        raise NotImplementedError()

    def get_active_scenario(self) -> Optional[str]:
        """Returns the scenario currently marked as active."""
        raise NotImplementedError()


class SessionStorage(SettingStorage):
    session: SessionBase
    instance: Instance

    def __init__(self, instance: Instance, session: SessionBase):
        self.session = session
        self.instance = instance
        self.log = logger.bind(session=session.session_key)

    def reset(self):
        self.session[self.instance.id] = {}

    @property
    def _instance_settings(self):
        return self.session.setdefault(self.instance.id, {})

    @property
    def _instance_params(self) -> dict[str, Any]:
        return self._instance_settings.setdefault('params', {})

    @property
    def _instance_options(self) -> dict[str, Any]:
        return self._instance_settings.setdefault('options', {})

    def get_instance_settings(self, instance_id: str) -> dict | None:
        settings = self.session.get(instance_id, None)
        if settings is None:
            return None
        if not isinstance(settings, dict):
            self.log.error('invalid settings type: %s' % type(settings))
            self.session[instance_id] = {}
            self.session.modified = True
            return None
        return settings

    def set_param(self, id: str, val: Any):
        self._instance_params[id] = val
        self.session.modified = True

    def reset_param(self, id: str):
        if id in self._instance_params:
            del self._instance_params[id]
            self.session.modified = True

    def set_option(self, id: str, val: Any):
        self._instance_options[id] = val
        self.session.modified = True

    def has_option(self, id: str) -> bool:
        return id in self._instance_options

    def get_option(self, id: str) -> Any:
        return self._instance_options.get(id)

    def reset_option(self, id: str):
        if id in self._instance_options:
            del self._instance_options[id]
            self.session.modified = True

    def get_customized_param_values(self) -> dict[str, Any]:
        return self._instance_params.copy()

    def set_active_scenario(self, id: Optional[str]):
        self._instance_settings['active_scenario'] = id
        self.session.modified = True

    def get_active_scenario(self) -> Optional[str]:
        return self._instance_settings.get('active_scenario')

    @classmethod
    def get_cache_key(cls, session: SessionBase, instance_id: str) -> str | None:
        ip = session.get(instance_id, None)
        if not ip or not isinstance(ip, dict):
            return ''
        active_scenario = ip.get('active_scenario')
        if active_scenario and active_scenario != 'default':
            return None

        opts = ip.get('options', None)
        if not opts:
            return ''

        s = hashlib.md5(json.dumps(opts, sort_keys=True, ensure_ascii=True).encode('ascii')).hexdigest()
        return s
