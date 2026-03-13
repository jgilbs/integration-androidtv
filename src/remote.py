"""
Remote entity for Android TV Remote integration.

:copyright: (c) 2023-2024 by Unfolded Circle ApS.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import EntityTypes, StatusCodes
from ucapi.media_player import Attributes as MediaAttr
from ucapi.media_player import States as MediaState
from ucapi.remote import Attributes, Commands, Features, Remote, States

import tv
from config import AtvDevice, create_entity_id
from profiles import Profile

_LOG = logging.getLogger(__name__)


class AndroidTVRemote(Remote):
    """Representation of an Android TV Remote entity."""

    def __init__(self, device_config: AtvDevice, device: tv.AndroidTv, profile: Profile):
        """Initialize the class."""
        self._device = device
        self._device_config = device_config

        entity_id = create_entity_id(device_config.id, EntityTypes.REMOTE)
        features = [Features.ON_OFF, Features.TOGGLE, Features.SEND_CMD]
        attributes = {Attributes.STATE: States.UNKNOWN}

        super().__init__(
            entity_id,
            device_config.name,
            features,
            attributes,
            simple_commands=profile.simple_commands if profile.simple_commands else None,
        )

    async def command(self, cmd_id: str, params: dict[str, Any] | None = None, *, websocket: Any) -> StatusCodes:
        """
        Remote entity command handler.

        :param cmd_id: command
        :param params: optional command parameters
        :param websocket: websocket connection
        :return: status code of the command request
        """
        if self._device is None:
            _LOG.warning(
                "Cannot execute command %s: no Android TV device found for entity %s",
                cmd_id,
                self._device_config.id,
            )
            return StatusCodes.NOT_FOUND

        _LOG.info("[%s] remote command: %s %s", self._device.log_id, cmd_id, params if params else "")

        if cmd_id == Commands.ON:
            return await self._device.turn_on()
        if cmd_id == Commands.OFF:
            return await self._device.turn_off()
        if cmd_id == Commands.TOGGLE:
            return await self._device.send_media_player_command("toggle")
        if cmd_id == Commands.SEND_CMD:
            if params is None or "command" not in params:
                return StatusCodes.BAD_REQUEST
            return await self._device.send_media_player_command(params["command"])
        if cmd_id == Commands.SEND_CMD_SEQUENCE:
            if params is None or "sequence" not in params:
                return StatusCodes.BAD_REQUEST
            delay = params.get("delay", 0)
            for cmd in params["sequence"]:
                res = await self._device.send_media_player_command(cmd)
                if res != StatusCodes.OK:
                    return res
                if delay:
                    import asyncio
                    await asyncio.sleep(delay / 1000)
            return StatusCodes.OK

        return StatusCodes.NOT_IMPLEMENTED

    def filter_changed_attributes(self, update: dict[str, Any]) -> dict[str, Any]:
        """
        Filter the given attributes and return only the changed values.

        Maps media player state updates to remote entity state.

        :param update: dictionary with attributes.
        :return: filtered entity attributes containing changed attributes only.
        """
        attributes = {}

        if MediaAttr.STATE in update:
            media_state = update[MediaAttr.STATE]
            if media_state == MediaState.UNAVAILABLE:
                new_state = States.UNAVAILABLE
            elif media_state == MediaState.OFF:
                new_state = States.OFF
            elif media_state in (MediaState.UNKNOWN,):
                new_state = States.UNKNOWN
            else:
                new_state = States.ON

            if self.attributes.get(Attributes.STATE) != new_state:
                attributes[Attributes.STATE] = new_state

        return attributes
