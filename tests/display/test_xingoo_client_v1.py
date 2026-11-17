import json

import pytest

from src.smartscreen_display.xingoo_client import (
    XingooAuthenticationError,
    XingooClient,
    XingooClientError,
)


class FakeResponse:
    def __init__(
        self,
        payload,
    ):
        self._payload = payload

    def read(self):
        return json.dumps(
            self._payload
        ).encode("utf-8")


def test_client_fetches_properties():
    captured = {}

    def opener(
        request,
        timeout,
    ):
        captured["request"] = request
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "status": "1000",
                "message": "执行成功",
                "result": {
                    "CurrentTemperature": 28,
                    "CurrentHumidity": 74,
                    "PM25": 33,
                    "HCHO": 0.02,
                },
            }
        )

    client = XingooClient(
        token="test-token",
        username="13800138000",
        opener=opener,
    )

    result = (
        client.get_all_properties(
            iot_id="device-1"
        )
    )

    assert result == {
        "CurrentTemperature": 28,
        "CurrentHumidity": 74,
        "PM25": 33,
        "HCHO": 0.02,
    }

    request = captured[
        "request"
    ]

    assert (
        request.full_url
        == (
            "https://xapp.ixingoo.com/"
            "xapp/devOperate/"
            "findDevAllProperties"
        )
    )

    assert captured[
        "timeout"
    ] == 15


def test_client_sends_app_headers():
    captured = {}

    def opener(
        request,
        timeout,
    ):
        captured[
            "request"
        ] = request

        return FakeResponse(
            {
                "status": "1000",
                "result": {},
            }
        )

    client = XingooClient(
        token="abc",
        username="13800138000",
        opener=opener,
    )

    client.get_all_properties(
        iot_id="device-1"
    )

    headers = {
        key.lower(): value
        for key, value
        in captured[
            "request"
        ].header_items()
    }

    assert (
        headers["token"]
        == "abc"
    )

    assert (
        headers["username"]
        == "13800138000"
    )

    assert (
        headers["appversion"]
        == "3.4.3"
    )

    assert (
        headers["ostype"]
        == "2"
    )


def test_client_rejects_api_failure():
    def opener(
        request,
        timeout,
    ):
        return FakeResponse(
            {
                "status": "1040",
                "message": (
                    "您的登录状态已经过期"
                ),
                "result": None,
            }
        )

    client = XingooClient(
        token="expired",
        username="13800138000",
        opener=opener,
    )

    with pytest.raises(
        XingooClientError,
        match="登录状态",
    ):
        client.get_all_properties(
            iot_id="device-1"
        )


def test_client_rejects_invalid_result():
    def opener(
        request,
        timeout,
    ):
        return FakeResponse(
            {
                "status": "1000",
                "result": None,
            }
        )

    client = XingooClient(
        token="abc",
        username="13800138000",
        opener=opener,
    )

    with pytest.raises(
        XingooClientError,
    ):
        client.get_all_properties(
            iot_id="device-1"
        )


def test_client_sets_power_on():
    captured = {}

    def opener(
        request,
        timeout,
    ):
        captured["request"] = request
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "status": "1000",
                "message": "执行成功",
                "result": "command-123",
            }
        )

    client = XingooClient(
        token="abc",
        username="13800138000",
        opener=opener,
    )

    result = client.set_power(
        iot_id="iot-123",
        on=True,
    )

    request = captured["request"]

    assert (
        request.full_url
        == (
            "https://xapp.ixingoo.com/"
            "xapp/devOperate/operCmd"
        )
    )

    assert request.method == "POST"

    assert json.loads(
        request.data.decode("utf-8")
    ) == {
        "deviceId": "iot-123",
        "operCmd": {
            "PowerSwitch": 1,
        },
    }

    headers = {
        key.lower(): value
        for key, value
        in request.header_items()
    }

    assert (
        headers["content-type"]
        == "application/json"
    )

    assert result == "command-123"


def test_client_sets_power_off():
    captured = {}

    def opener(
        request,
        timeout,
    ):
        captured["request"] = request

        return FakeResponse(
            {
                "status": "1000",
                "message": "执行成功",
                "result": "command-456",
            }
        )

    client = XingooClient(
        token="abc",
        username="13800138000",
        opener=opener,
    )

    result = client.set_power(
        iot_id="iot-123",
        on=False,
    )

    assert json.loads(
        captured["request"].data.decode(
            "utf-8"
        )
    ) == {
        "deviceId": "iot-123",
        "operCmd": {
            "PowerSwitch": 0,
        },
    }

    assert result == "command-456"


def test_client_rejects_power_command_api_failure():
    def opener(
        request,
        timeout,
    ):
        return FakeResponse(
            {
                "status": "1040",
                "message": "control failed",
                "result": None,
            }
        )

    client = XingooClient(
        token="abc",
        username="13800138000",
        opener=opener,
    )

    with pytest.raises(
        XingooClientError,
        match="control failed",
    ):
        client.set_power(
            iot_id="iot-123",
            on=True,
        )


def test_client_logs_in_with_password():
    from urllib.parse import parse_qs

    captured = {}

    def opener(
        request,
        timeout,
    ):
        captured["request"] = request
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "status": "1000",
                "message": "登录成功",
                "result": {
                    "userName": "13800138000",
                    "userId": "user-123",
                    "token": "new-token",
                    "imSign": "sign-123",
                },
            }
        )

    client = XingooClient(
        token="",
        username="13800138000",
        opener=opener,
    )

    result = client.login(
        password="secret-password",
    )

    request = captured["request"]

    assert (
        request.full_url
        == (
            "https://xapp.ixingoo.com/"
            "xapp/user/login"
        )
    )

    assert request.method == "POST"

    assert parse_qs(
        request.data.decode("utf-8")
    ) == {
        "userName": [
            "13800138000"
        ],
        "password": [
            "secret-password"
        ],
        "version": [
            "1.0.0"
        ],
    }

    headers = {
        key.lower(): value
        for key, value
        in request.header_items()
    }

    assert (
        headers["content-type"]
        == (
            "application/"
            "x-www-form-urlencoded"
        )
    )

    assert captured["timeout"] == 15

    assert result == {
        "userName": "13800138000",
        "userId": "user-123",
        "token": "new-token",
        "imSign": "sign-123",
    }


def test_client_login_replaces_token_for_later_requests():
    requests = []

    def opener(
        request,
        timeout,
    ):
        requests.append(
            request
        )

        if (
            request.full_url.endswith(
                "/user/login"
            )
        ):
            return FakeResponse(
                {
                    "status": "1000",
                    "message": "登录成功",
                    "result": {
                        "userName":
                            "13800138000",
                        "userId":
                            "user-123",
                        "token":
                            "fresh-token",
                        "imSign":
                            "sign-123",
                    },
                }
            )

        return FakeResponse(
            {
                "status": "1000",
                "result": {
                    "PM25": 12,
                },
            }
        )

    client = XingooClient(
        token="expired-token",
        username="13800138000",
        opener=opener,
    )

    client.login(
        password="secret-password",
    )

    client.get_all_properties(
        iot_id="iot-123",
    )

    property_request = (
        requests[1]
    )

    headers = {
        key.lower(): value
        for key, value
        in property_request.header_items()
    }

    assert (
        headers["token"]
        == "fresh-token"
    )


def test_client_logs_in_with_password():
    from urllib.parse import parse_qs

    captured = {}

    def opener(
        request,
        timeout,
    ):
        captured["request"] = request
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "status": "1000",
                "message": "登录成功",
                "result": {
                    "userName": "13800138000",
                    "userId": "user-123",
                    "token": "new-token",
                    "imSign": "sign-123",
                },
            }
        )

    client = XingooClient(
        token="",
        username="13800138000",
        opener=opener,
    )

    result = client.login(
        password="secret-password",
    )

    request = captured["request"]

    assert (
        request.full_url
        == (
            "https://xapp.ixingoo.com/"
            "xapp/user/login"
        )
    )

    assert request.method == "POST"

    assert parse_qs(
        request.data.decode("utf-8")
    ) == {
        "userName": [
            "13800138000"
        ],
        "password": [
            "secret-password"
        ],
        "version": [
            "1.0.0"
        ],
    }

    headers = {
        key.lower(): value
        for key, value
        in request.header_items()
    }

    assert (
        headers["content-type"]
        == (
            "application/"
            "x-www-form-urlencoded"
        )
    )

    assert captured["timeout"] == 15

    assert result == {
        "userName": "13800138000",
        "userId": "user-123",
        "token": "new-token",
        "imSign": "sign-123",
    }


def test_client_login_replaces_token_for_later_requests():
    requests = []

    def opener(
        request,
        timeout,
    ):
        requests.append(
            request
        )

        if (
            request.full_url.endswith(
                "/user/login"
            )
        ):
            return FakeResponse(
                {
                    "status": "1000",
                    "message": "登录成功",
                    "result": {
                        "userName":
                            "13800138000",
                        "userId":
                            "user-123",
                        "token":
                            "fresh-token",
                        "imSign":
                            "sign-123",
                    },
                }
            )

        return FakeResponse(
            {
                "status": "1000",
                "result": {
                    "PM25": 12,
                },
            }
        )

    client = XingooClient(
        token="expired-token",
        username="13800138000",
        opener=opener,
    )

    client.login(
        password="secret-password",
    )

    client.get_all_properties(
        iot_id="iot-123",
    )

    property_request = (
        requests[1]
    )

    headers = {
        key.lower(): value
        for key, value
        in property_request.header_items()
    }

    assert (
        headers["token"]
        == "fresh-token"
    )


def test_client_logs_in_with_password():
    from urllib.parse import parse_qs

    captured = {}

    def opener(
        request,
        timeout,
    ):
        captured["request"] = request
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "status": "1000",
                "message": "登录成功",
                "result": {
                    "userName": "13800138000",
                    "userId": "user-123",
                    "token": "new-token",
                    "imSign": "sign-123",
                },
            }
        )

    client = XingooClient(
        token="",
        username="13800138000",
        opener=opener,
    )

    result = client.login(
        password="secret-password",
    )

    request = captured["request"]

    assert (
        request.full_url
        == (
            "https://xapp.ixingoo.com/"
            "xapp/user/login"
        )
    )

    assert request.method == "POST"

    assert parse_qs(
        request.data.decode("utf-8")
    ) == {
        "userName": [
            "13800138000"
        ],
        "password": [
            "secret-password"
        ],
        "version": [
            "1.0.0"
        ],
    }

    headers = {
        key.lower(): value
        for key, value
        in request.header_items()
    }

    assert (
        headers["content-type"]
        == (
            "application/"
            "x-www-form-urlencoded"
        )
    )

    assert captured["timeout"] == 15

    assert result == {
        "userName": "13800138000",
        "userId": "user-123",
        "token": "new-token",
        "imSign": "sign-123",
    }


def test_client_login_replaces_token_for_later_requests():
    requests = []

    def opener(
        request,
        timeout,
    ):
        requests.append(
            request
        )

        if (
            request.full_url.endswith(
                "/user/login"
            )
        ):
            return FakeResponse(
                {
                    "status": "1000",
                    "message": "登录成功",
                    "result": {
                        "userName":
                            "13800138000",
                        "userId":
                            "user-123",
                        "token":
                            "fresh-token",
                        "imSign":
                            "sign-123",
                    },
                }
            )

        return FakeResponse(
            {
                "status": "1000",
                "result": {
                    "PM25": 12,
                },
            }
        )

    client = XingooClient(
        token="expired-token",
        username="13800138000",
        opener=opener,
    )

    client.login(
        password="secret-password",
    )

    client.get_all_properties(
        iot_id="iot-123",
    )

    property_request = (
        requests[1]
    )

    headers = {
        key.lower(): value
        for key, value
        in property_request.header_items()
    }

    assert (
        headers["token"]
        == "fresh-token"
    )



def test_client_classifies_authentication_failure():
    def opener(
        request,
        timeout,
    ):
        return FakeResponse(
            {
                "status": "1040",
                "message": (
                    "您的账号在另一台手机登录。"
                    "如非本人操作，则密码可能已泄露，"
                    "建议修改密码"
                ),
                "result": None,
            }
        )

    client = XingooClient(
        token="expired",
        username="10000000001",
        opener=opener,
    )

    with pytest.raises(
        XingooAuthenticationError,
        match="另一台手机登录",
    ):
        client.get_all_properties(
            iot_id="iot-123"
        )


def test_client_relogs_once_and_retries_property_request():
    requests = []

    def opener(
        request,
        timeout,
    ):
        requests.append(
            request
        )

        path = request.full_url

        if path.endswith(
            "/user/login"
        ):
            return FakeResponse(
                {
                    "status": "1000",
                    "message": "登录成功",
                    "result": {
                        "userName":
                            "10000000001",
                        "userId":
                            "user-123",
                        "token":
                            (
                                "token-"
                                + str(
                                    sum(
                                        item.full_url.endswith(
                                            "/user/login"
                                        )
                                        for item
                                        in requests
                                    )
                                )
                            ),
                    },
                }
            )

        property_requests = [
            item
            for item in requests
            if item.full_url.endswith(
                "/findDevAllProperties"
            )
        ]

        if len(
            property_requests
        ) == 1:
            return FakeResponse(
                {
                    "status": "1040",
                    "message":
                        "您的登录状态已经过期",
                    "result": None,
                }
            )

        return FakeResponse(
            {
                "status": "1000",
                "message": "执行成功",
                "result": {
                    "PM25": 5,
                },
            }
        )

    client = XingooClient(
        token="",
        username="10000000001",
        opener=opener,
    )

    client.login(
        password="test-password",
    )

    result = (
        client.get_all_properties(
            iot_id="iot-123"
        )
    )

    assert result == {
        "PM25": 5,
    }

    login_requests = [
        request
        for request in requests
        if request.full_url.endswith(
            "/user/login"
        )
    ]

    property_requests = [
        request
        for request in requests
        if request.full_url.endswith(
            "/findDevAllProperties"
        )
    ]

    assert len(
        login_requests
    ) == 2

    assert len(
        property_requests
    ) == 2

    retry_headers = {
        key.lower(): value
        for key, value
        in property_requests[
            -1
        ].header_items()
    }

    assert (
        retry_headers["token"]
        == "token-2"
    )


def test_client_relogs_once_and_retries_command():
    requests = []

    def opener(
        request,
        timeout,
    ):
        requests.append(
            request
        )

        if request.full_url.endswith(
            "/user/login"
        ):
            return FakeResponse(
                {
                    "status": "1000",
                    "message": "登录成功",
                    "result": {
                        "userName":
                            "10000000001",
                        "userId":
                            "user-123",
                        "token":
                            "fresh-token",
                    },
                }
            )

        command_requests = [
            item
            for item in requests
            if item.full_url.endswith(
                "/devOperate/operCmd"
            )
        ]

        if len(
            command_requests
        ) == 1:
            return FakeResponse(
                {
                    "status": "1040",
                    "message":
                        "您的登录状态已经过期",
                    "result": None,
                }
            )

        return FakeResponse(
            {
                "status": "1000",
                "message": "执行成功",
                "result": "command-123",
            }
        )

    client = XingooClient(
        token="",
        username="10000000001",
        opener=opener,
    )

    client.login(
        password="test-password",
    )

    result = client.set_power(
        iot_id="iot-123",
        on=True,
    )

    assert result == "command-123"

    command_requests = [
        request
        for request in requests
        if request.full_url.endswith(
            "/devOperate/operCmd"
        )
    ]

    assert len(
        command_requests
    ) == 2


def test_client_does_not_retry_authentication_forever():
    requests = []

    def opener(
        request,
        timeout,
    ):
        requests.append(
            request
        )

        if request.full_url.endswith(
            "/user/login"
        ):
            return FakeResponse(
                {
                    "status": "1000",
                    "message": "登录成功",
                    "result": {
                        "userName":
                            "10000000001",
                        "userId":
                            "user-123",
                        "token":
                            "fresh-token",
                    },
                }
            )

        return FakeResponse(
            {
                "status": "1040",
                "message":
                    "您的登录状态已经过期",
                "result": None,
            }
        )

    client = XingooClient(
        token="",
        username="10000000001",
        opener=opener,
    )

    client.login(
        password="test-password",
    )

    with pytest.raises(
        XingooAuthenticationError,
    ):
        client.get_all_properties(
            iot_id="iot-123"
        )

    login_requests = [
        request
        for request in requests
        if request.full_url.endswith(
            "/user/login"
        )
    ]

    property_requests = [
        request
        for request in requests
        if request.full_url.endswith(
            "/findDevAllProperties"
        )
    ]

    assert len(
        login_requests
    ) == 2

    assert len(
        property_requests
    ) == 2
