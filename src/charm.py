#!/usr/bin/env python3
"""VantageAgentCharm."""

import logging
from pathlib import Path

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, WaitingStatus

from vantage_agents_ops import VantageAgentOps


logger = logging.getLogger()

# Create a sentinel value. For more information about sentinel values and their
# purpose, see the PEP (with some excellent examples and rationale) here:
# https://peps.python.org/pep-0661/
unset = object()


class VantageAgentCharm(CharmBase):
    """Facilitate vantage-agent lifecycle."""

    stored = StoredState()

    def __init__(self, *args):
        """Initialize and observe."""
        super().__init__(*args)

        self.stored.set_default(installed=False)
        self.stored.set_default(config_available=False)
        self.stored.set_default(user_created=False)

        self.vantage_agent_ops = VantageAgentOps(self)

        event_handler_bindings = {
            self.on.install: self._on_install,
            self.on.upgrade_charm: self._on_upgrade,
            self.on.start: self._on_start,
            self.on.config_changed: self._on_config_changed,
            self.on.remove: self._on_remove,
            self.on.upgrade_vtg_action: self._on_upgrade_action,
        }
        for event, handler in event_handler_bindings.items():
            self.framework.observe(event, handler)

    def _on_install(self, event):
        """Install vantage-agent."""
        self.unit.set_workload_version(Path("version").read_text().strip())

        try:
            self.vantage_agent_ops.install()
            self.stored.installed = True
        except Exception as e:
            logger.error(f"## Error installing agent: {e}")
            self.stored.installed = False
            self.unit.status = BlockedStatus("Error installing vantage-agent")
            event.defer()
            return
        # Log and set status
        logger.debug("vantage-agent installed")
        self.unit.status = WaitingStatus("vantage-agent installed")

    def _on_upgrade(self, event):
        """Perform upgrade operations."""
        self.unit.set_workload_version(Path("version").read_text().strip())

    def _on_start(self, event):
        """
        Start vantage-agent.

        Check that we have the needed configuration values and whether the
        vantage agent user is created in the slurmctld node, if so
        start the vantage-agent otherwise defer the event.
        """
        if not self.stored.config_available:
            event.defer()
            return

        logger.info("## Starting Vantage agent")
        self.vantage_agent_ops.start_agent()
        self.unit.status = ActiveStatus("vantage agent started")

    def _on_config_changed(self, event):
        """
        Handle changes to the charm config.

        If all the needed settings are available in the charm config, create the
        environment settings for the charmed app. Also, store the config values in the
        stored state for the charm.

        Note the use of the sentinel ``unset`` value here. This allows us to
        distinguish between *unset* values and values that were *explicitly* set to
        falsey or null values. For more information about sentinel values, see
        `PEP-661 <https://peps.python.org/pep-0661/>_`.
        """

        settings_to_map = {
            "base-api-url": True,
            "scontrol-path": False,
            "oidc-domain": True,
            "oidc-client-id": True,
            "oidc-client-secret": True,
            "task-jobs-interval-seconds": False,
            "task-self-update-interval-seconds": False,
            "cache-dir": False,
        }

        env_context = dict()

        for setting, is_required in settings_to_map.items():
            value = self.model.config.get(setting, unset)

            if value is unset and not is_required:
                # Not set, not required, just continue
                continue
            elif value is unset and is_required:
                # Is unset but required, defer
                event.defer()
                return

            env_context[setting] = value

            self.vantage_agent_ops.configure_env_defaults(env_context)

            mapped_key = setting.replace("-", "_")
            store_value = getattr(self.stored, mapped_key, unset)
            if store_value != value:
                setattr(self.stored, mapped_key, value)

        self.stored.config_available = True

        logger.info("## Restarting the agent")
        self.vantage_agent_ops.restart_agent()
        self.unit.status = ActiveStatus("Vantage agent restarted")

    def _on_remove(self, event):
        """Remove directories and files created by vantage-agent charm."""
        self.vantage_agent_ops.remove()

    def _on_upgrade_action(self, event):
        version = event.params["version"]
        try:
            self.vantage_agent_ops.upgrade(version)
            event.set_results({"upgrade": "success"})
            self.unit.status = ActiveStatus(f"Updated to version {version}")
            self.vantage_agent_ops.restart_agent()
        except Exception:
            self.unit.status = BlockedStatus(f"Error updating to version {version}")
            event.fail()

    def _on_clear_cache_dir_action(self, event):
        try:
            result = self.vantage_agent_ops.clear_cache_dir()
            event.set_results({"cache-clear": "success"})
            self.unit.status = ActiveStatus(result)
            self.vantage_agent_ops.restart_agent()
        except Exception:
            self.unit.status = BlockedStatus("Error clearing cache")
            event.fail()


if __name__ == "__main__":
    main(VantageAgentCharm)
