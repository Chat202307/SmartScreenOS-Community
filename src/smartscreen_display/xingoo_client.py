from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class XingooClientError(RuntimeError):
    pass


class XingooAuthenticationError(
    XingooClientError
):
    pass


class XingooClient:
    BASE_URL = "https://xapp.ixingoo.com/xapp/"

    def __init__(
        self,
        *,
        token,
        username,
        timeout=15,
        opener=urlopen,
    ):
        self._token = str(token)
        self._username = str(username)
        self._timeout = timeout
        self._opener = opener
        self._password = None

    def _headers(
        self,
        *,
        content_type,
    ):
        return {
            "Content-Type": content_type,
            "token": self._token,
            "userName": self._username,
            "appVersion": "3.4.3",
            "phTypeName": "Mac",
            "phOSVersion": "15",
            "osType": "2",
        }

    @staticmethod
    def _is_authentication_failure(
        payload,
    ):
        message = str(
            payload.get(
                "message",
                "",
            )
        )

        return (
            "登录状态" in message
            or "另一台手机登录" in message
        )

    def _execute(
        self,
        request,
    ):
        try:
            response = self._opener(
                request,
                timeout=self._timeout,
            )

            payload = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

        except Exception as exc:
            raise XingooClientError(
                "xingoo request failed"
            ) from exc

        if not isinstance(
            payload,
            dict,
        ):
            raise XingooClientError(
                "invalid xingoo response"
            )

        if str(
            payload.get("status")
        ) != "1000":
            message = str(
                payload.get(
                    "message",
                    "xingoo request failed",
                )
            )

            if (
                self
                ._is_authentication_failure(
                    payload
                )
            ):
                raise (
                    XingooAuthenticationError(
                        message
                    )
                )

            raise XingooClientError(
                message
            )

        return payload

    def _execute_authenticated(
        self,
        request_factory,
    ):
        try:
            return self._execute(
                request_factory()
            )

        except XingooAuthenticationError:
            if not self._password:
                raise

            self.login(
                password=self._password,
            )

            return self._execute(
                request_factory()
            )

    def login(
        self,
        *,
        password,
    ):
        body = urlencode(
            {
                "userName":
                    self._username,
                "password":
                    password,
                "version":
                    "1.0.0",
            }
        ).encode("utf-8")

        request = Request(
            self.BASE_URL
            + "user/login",
            data=body,
            headers=self._headers(
                content_type=(
                    "application/"
                    "x-www-form-urlencoded"
                ),
            ),
            method="POST",
        )

        payload = self._execute(
            request
        )

        result = payload.get(
            "result"
        )

        if not isinstance(
            result,
            dict,
        ):
            raise XingooClientError(
                "invalid xingoo login result"
            )

        token = result.get(
            "token"
        )

        if (
            not isinstance(
                token,
                str,
            )
            or not token
        ):
            raise XingooClientError(
                "missing xingoo login token"
            )

        username = result.get(
            "userName"
        )

        if (
            isinstance(
                username,
                str,
            )
            and username
        ):
            self._username = (
                username
            )

        self._token = token
        self._password = str(
            password
        )

        return dict(
            result
        )

    def get_all_properties(
        self,
        *,
        iot_id,
    ):
        def request_factory():
            body = urlencode(
                {
                    "deviceId":
                        iot_id,
                    "version":
                        "3.5.0",
                }
            ).encode("utf-8")

            return Request(
                (
                    self.BASE_URL
                    + "devOperate/"
                    + "findDevAllProperties"
                ),
                data=body,
                headers=self._headers(
                    content_type=(
                        "application/"
                        "x-www-form-urlencoded"
                    ),
                ),
                method="POST",
            )

        payload = (
            self._execute_authenticated(
                request_factory
            )
        )

        result = payload.get(
            "result"
        )

        if not isinstance(
            result,
            dict,
        ):
            raise XingooClientError(
                "invalid xingoo properties"
            )

        return result

    def send_command(
        self,
        *,
        iot_id,
        command,
    ):
        if (
            not isinstance(
                command,
                dict,
            )
            or not command
        ):
            raise XingooClientError(
                "invalid xingoo command"
            )

        def request_factory():
            body = json.dumps(
                {
                    "deviceId":
                        iot_id,
                    "operCmd":
                        command,
                },
                separators=(",", ":"),
            ).encode("utf-8")

            return Request(
                (
                    self.BASE_URL
                    + "devOperate/operCmd"
                ),
                data=body,
                headers=self._headers(
                    content_type=(
                        "application/json"
                    ),
                ),
                method="POST",
            )

        payload = (
            self._execute_authenticated(
                request_factory
            )
        )

        return payload.get(
            "result"
        )

    def set_power(
        self,
        *,
        iot_id,
        on,
    ):
        return self.send_command(
            iot_id=iot_id,
            command={
                "PowerSwitch":
                    1 if on else 0,
            },
        )
