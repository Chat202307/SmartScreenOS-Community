from __future__ import annotations

import argparse
import os
from collections.abc import Callable, Sequence

import paho.mqtt.client as mqtt
from pathlib import Path

from src.smartscreen_runtime.runtime.bootstrap import (
    create_runtime_host_from_config,
)
from src.smartscreen_platform.household_state import (
    HouseholdStateChangeNotifier,
    HouseholdStateEngine,
)

from .location_labels_config import (
    load_location_labels,
    load_location_orders,
    load_location_zones,
)
from .dashboard_presentation_config import (
    load_dashboard_presentation_areas,
)
from .household_actions import (
    HouseholdActionExecutor,
)
from .household_actions_config import (
    load_household_actions,
)
from .presentation import (
    DashboardPresentationBuilder,
)
from src.smartscreen_platform.state_pipeline import (
    PlatformStatePipeline,
)
from src.smartscreen_platform.knowledge import (
    StaticKnowledge,
)
from src.smartscreen_platform.observation_accumulator import (
    ObservationAccumulator,
)
from src.smartscreen_platform.freshness_sweep import (
    ObservationFreshnessSweep,
)
from src.smartscreen_platform.device_data import (
    DeviceDataIngestionService,
    DeviceParameterStore,
    DevicePowerDependencyResolver,
    DeviceRegistry,
)
from src.smartscreen_platform.device_control import (
    DeviceControlDispatcher,
    DeviceControlRegistry,
    build_device_control_bindings,
)
from src.smartscreen_platform.interpretation import (
    IlluminanceInterpreter,
    PresenceInterpreter,
    ThermalInterpreter,
)
from src.smartscreen_platform.capabilities.comfort import (
    ComfortCapability,
)
from src.smartscreen_platform.capabilities.occupancy import (
    OccupancyCapability,
)
from src.smartscreen_platform.capabilities.lighting import (
    LightingCapability,
)
from src.smartscreen_platform.capabilities.weather_advice import (
    WeatherAdviceCapability,
)
from src.smartscreen_platform.capabilities.weather_status import (
    WeatherStatusCapability,
)

from .server import (
    SnapshotApplication,
    create_http_server,
)
from .calendar_config import (
    load_calendar_config,
)
from .calendar_source import (
    CalendarEventService,
)
from .caldav_calendar_source import CalDAVCalendarSource
from .calendar_background import BackgroundCalendarSource
from .eventkit_calendar_source import (
    EventKitCalendarSource,
    EventKitSubprocessRunner,
)

from .home_assistant_source import (
    create_home_assistant_provider,
)
from .home_assistant_state_events import (
    HomeAssistantStateEventConsumer,
)
from .home_assistant_state_stream import (
    HomeAssistantStateStream,
)
from .home_status_change_notifier import (
    HomeStatusChangeNotifier,
)
from .home_assistant_observations import (
    HomeAssistantObservationAdapter,
)
from .home_assistant_device_data import (
    HomeAssistantDeviceDataAdapter,
)
from .home_assistant_client import (
    HomeAssistantClient,
)
from .home_assistant_device_control_executor import (
    HomeAssistantDeviceControlExecutor,
)
from .home_assistant_weather import (
    HomeAssistantWeatherForecastAdapter,
    HomeAssistantWeatherForecastSource,
)
from .xingoo_client import (
    XingooClient,
)
from .xingoo_device_data import (
    XingooDeviceDataAdapter,
)
from .xingoo_device_controller import (
    XingooDeviceController,
)
from .xingoo_device_control_executor import (
    XingooDeviceControlExecutor,
)
from .xingoo_source import (
    XingooDeviceDataSource,
)
from .dnake_mqtt_device_data import (
    DnakeMqttDeviceDataAdapter,
)
from .dnake_mqtt_device_control_executor import (
    DnakeMqttDeviceControlExecutor,
)
from .dnake_mqtt_source import (
    DnakeMqttDeviceDataSource,
)
from .platform_entities_config import (
    load_platform_entities,
)
from .device_data_config import (
    load_device_definitions,
)
from .occupancy_interpretation_config import (
    load_occupancy_interpretation_policies,
)
from .lighting_interpretation_config import (
    load_lighting_interpretation_knowledge,
)


DnakeMqttClient = mqtt.Client


DEFAULT_CONFIG_PATH = Path("config/runtime.yaml")


def run_display_server(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    bind_host: str = "127.0.0.1",
    port: int = 8080,
    photo_dir: Path | None = None,
    todo_file: Path | None = None,
    home_file: Path | None = None,
    home_entities_file: Path | None = None,
    platform_entities_file: Path | None = None,
    device_data_file: Path | None = None,
    occupancy_interpretation_file: Path | None = None,
    lighting_interpretation_file: Path | None = None,
    location_config_file: Path | None = None,
    dashboard_presentation_file: Path | None = None,
    household_actions_file: Path | None = None,
    calendar_config_file: Path | None = None,
    runtime_factory: Callable = create_runtime_host_from_config,
    server_factory: Callable = create_http_server,
    state_stream=None,
    household_state_source=None,
) -> int:
    runtime = runtime_factory(config_path)

    dashboard_state_notifier = (
        HouseholdStateChangeNotifier()
    )

    resolved_household_state_source = (
        household_state_source
        if household_state_source is not None
        else HouseholdStateEngine(
            change_notifier=dashboard_state_notifier,
        )
    )

    resolved_photo_dir = (
        photo_dir
        if photo_dir is not None
        else Path.home() / "SmartScreen" / "photos"
    )

    resolved_todo_file = (
        todo_file
        if todo_file is not None
        else Path.home() / "SmartScreen" / "todos" / "todos.json"
    )

    resolved_home_file = (
        home_file
        if home_file is not None
        else Path.home() / "SmartScreen" / "home" / "home.json"
    )

    resolved_home_entities_file = (
        home_entities_file
        if home_entities_file is not None
        else Path("config/home_entities.json")
    )

    resolved_platform_entities_file = (
        platform_entities_file
        if platform_entities_file is not None
        else Path("config/platform_entities.json")
    )

    resolved_device_data_file = (
        device_data_file
        if device_data_file is not None
        else Path("config/device_data.json")
    )

    resolved_occupancy_interpretation_file = (
        occupancy_interpretation_file
        if occupancy_interpretation_file is not None
        else Path(
            "config/occupancy_interpretation.json"
        )
    )

    resolved_lighting_interpretation_file = (
        lighting_interpretation_file
        if lighting_interpretation_file is not None
        else Path(
            "config/lighting_interpretation.json"
        )
    )

    resolved_location_config_file = (
        location_config_file
        if location_config_file is not None
        else Path("config/home.json")
    )

    location_labels = load_location_labels(
        resolved_location_config_file
    )

    location_orders = load_location_orders(
        resolved_location_config_file
    )

    location_zones = load_location_zones(
        resolved_location_config_file
    )

    resolved_dashboard_presentation_file = (
        dashboard_presentation_file
        if dashboard_presentation_file is not None
        else (
            Path(
                "config/dashboard_presentation.json"
            )
            if location_config_file is None
            else None
        )
    )

    dashboard_presentation_areas = (
        load_dashboard_presentation_areas(
            resolved_dashboard_presentation_file
        )
        if resolved_dashboard_presentation_file
        is not None
        else {}
    )

    resolved_household_actions_file = (
        household_actions_file
        if household_actions_file is not None
        else Path(
            "config/household_actions.json"
        )
    )

    household_actions = (
        load_household_actions(
            resolved_household_actions_file
        )
    )

    for (
        presentation_id,
        presentation_area,
    ) in dashboard_presentation_areas.items():
        location_labels[
            presentation_id
        ] = presentation_area["label"]

        presentation_order = (
            presentation_area.get("order")
        )

        if presentation_order is not None:
            location_orders[
                presentation_id
            ] = presentation_order

        location_zones[
            presentation_id
        ] = {
            "room_ids": tuple(
                presentation_area.get(
                    "room_ids",
                    (),
                )
            ),
            "summary_location_id": (
                presentation_area.get(
                    "summary_location_id"
                )
            ),
            "show_on_home": (
                presentation_area.get(
                    "show_on_home"
                ) is True
            ),
            "sheet_extra_device_ids": tuple(
                presentation_area.get(
                    "sheet_extra_device_ids",
                    (),
                )
            ),
            "sheet_device_order": tuple(
                presentation_area.get(
                    "sheet_device_order",
                    (),
                )
            ),
            "sheet_wide_device_ids": tuple(
                presentation_area.get(
                    "sheet_wide_device_ids",
                    (),
                )
            ),
        }

    presentation_builder = (
        DashboardPresentationBuilder(
            location_labels=location_labels,
            location_orders=location_orders,
            location_zones=location_zones,
        )
    )

    platform_entities = load_platform_entities(
        resolved_platform_entities_file
    )

    device_definitions = load_device_definitions(
        resolved_device_data_file
    )

    device_registry = DeviceRegistry(
        devices=device_definitions
    )

    device_control_registry = (
        DeviceControlRegistry(
            bindings=(
                build_device_control_bindings(
                    devices=device_definitions
                )
            )
        )
    )

    device_parameter_store = (
        DeviceParameterStore(
            registry=device_registry
        )
    )

    device_power_dependency_resolver = (
        DevicePowerDependencyResolver(
            registry=device_registry,
            store=device_parameter_store,
        )
    )

    device_data_ingestion = (
        DeviceDataIngestionService(
            registry=device_registry,
            store=device_parameter_store,
        )
    )

    home_assistant_device_data_adapter = (
        HomeAssistantDeviceDataAdapter(
            registry=device_registry,
            ingestion=device_data_ingestion,
        )
    )

    occupancy_policies = (
        load_occupancy_interpretation_policies(
            resolved_occupancy_interpretation_file
        )
    )

    lighting_knowledge_values = (
        load_lighting_interpretation_knowledge(
            resolved_lighting_interpretation_file
        )
    )

    platform_knowledge = StaticKnowledge(
        global_values=(
            lighting_knowledge_values[
                "global"
            ]
        ),
        location_values=(
            lighting_knowledge_values[
                "locations"
            ]
        ),
    )

    observation_adapter = (
        HomeAssistantObservationAdapter(
            entities=platform_entities,
        )
    )

    canonical_source_ids = {
        definition.source_id
        for device in device_definitions
        for definition in device.parameters.values()
    }

    legacy_freshness_entities = [
        entity
        for entity in platform_entities
        if (
            entity.get("entity_id")
            not in canonical_source_ids
        )
    ]

    freshness_by_parameter = {
        entity["parameter"]: entity["max_age_seconds"]
        for entity in legacy_freshness_entities
        if (
            "max_age_seconds" in entity
            and not entity.get("location_id")
        )
    }

    freshness_by_location_parameter = {
        (
            entity["location_id"],
            entity["parameter"],
        ): entity["max_age_seconds"]
        for entity in legacy_freshness_entities
        if (
            "max_age_seconds" in entity
            and entity.get("location_id")
        )
    }

    # Canonical Device Data owns freshness policy
    # for migrated sources. Once a source is present
    # in Device Data, legacy platform_entities must
    # not provide freshness for that source.
    for device in device_definitions:
        for (
            parameter,
            definition,
        ) in device.parameters.items():
            max_age_seconds = getattr(
                definition,
                "max_age_seconds",
                None,
            )

            if max_age_seconds is None:
                continue

            observation_location_id = (
                definition.observation_location_id
                or device.location_id
            )

            freshness_by_location_parameter[
                (
                    observation_location_id,
                    parameter,
                )
            ] = max_age_seconds

    # Canonical weather observations are produced
    # directly by the weather source rather than
    # through platform_entities or Device Data.
    # Their freshness therefore belongs in the
    # runtime observation policy assembled here.
    weather_max_age_seconds = 3600

    for weather_parameter in (
        "weather_condition",
        "temperature",
        "humidity",
        "apparent_temperature",
        "wind_speed",
        "forecast_precipitation",
        "forecast_condition",
    ):
        freshness_by_location_parameter[
            (
                "outdoor",
                weather_parameter,
            )
        ] = weather_max_age_seconds

    observation_accumulator = (
        ObservationAccumulator(
            max_age_by_parameter=(
                freshness_by_parameter
            ),
            max_age_by_location_parameter=(
                freshness_by_location_parameter
            ),
        )
    )

    platform_state_pipeline = PlatformStatePipeline(
        household_state=resolved_household_state_source,
        knowledge=platform_knowledge,
        interpreters=[
            ThermalInterpreter(),
            IlluminanceInterpreter(),
            PresenceInterpreter(
                source_policies=occupancy_policies,
            ),
        ],
        capabilities=[
            ComfortCapability(),
            OccupancyCapability(),
            LightingCapability(),
            WeatherAdviceCapability(),
            WeatherStatusCapability(),
        ],
    )

    freshness_sweep = ObservationFreshnessSweep(
        accumulator=observation_accumulator,
        observation_sink=platform_state_pipeline,
    )

    home_status_notifier = (
        HomeStatusChangeNotifier()
    )

    xingoo_iot_ids = []
    xingoo_device_iot_ids = {}

    for device in device_definitions:
        if device.adapter_id != "xingoo":
            continue

        device_iot_ids = []

        for definition in device.parameters.values():
            source_id = definition.source_id

            if ":" not in source_id:
                continue

            iot_id, _ = source_id.split(
                ":",
                1,
            )

            if not iot_id:
                continue

            if iot_id not in xingoo_iot_ids:
                xingoo_iot_ids.append(
                    iot_id
                )

            if iot_id not in device_iot_ids:
                device_iot_ids.append(
                    iot_id
                )

        if len(device_iot_ids) == 1:
            xingoo_device_iot_ids[
                device.device_id
            ] = device_iot_ids[0]

    xingoo_source = None
    xingoo_device_controller = None
    dnake_mqtt_source = None
    device_control_dispatcher = None
    household_action_executor = None
    device_control_executors = {}

    dnake_mqtt_source_topics = []
    dnake_mqtt_retained_restore_topics = []
    dnake_mqtt_device_topics = {}
    dnake_mqtt_device_control_topics = {}

    for device in device_definitions:
        if device.adapter_id != "dnake_mqtt":
            continue

        adapter_config = (
            device.adapter_config
            if isinstance(
                device.adapter_config,
                dict,
            )
            else {}
        )

        state_topic = adapter_config.get(
            "state_topic"
        )

        if (
            isinstance(
                state_topic,
                str,
            )
            and state_topic.strip()
        ):
            resolved_state_topics = [
                state_topic.strip()
            ]
        else:
            resolved_state_topics = [
                definition.source_id
                for definition
                in device.parameters.values()
                if definition.source_id
            ]

        for source_topic in (
            resolved_state_topics
        ):
            if (
                source_topic
                not in dnake_mqtt_source_topics
            ):
                dnake_mqtt_source_topics.append(
                    source_topic
                )

        retained_restore = adapter_config.get(
            "retained_restore"
        )

        if isinstance(
            retained_restore,
            list,
        ):
            for parameter in retained_restore:
                if (
                    not isinstance(
                        parameter,
                        str,
                    )
                    or parameter
                    not in device.parameters
                ):
                    continue

                source_topic = (
                    device.parameters[
                        parameter
                    ].source_id
                )

                if (
                    source_topic
                    and source_topic
                    not in (
                        dnake_mqtt_retained_restore_topics
                    )
                ):
                    dnake_mqtt_retained_restore_topics.append(
                        source_topic
                    )

        command_topic = adapter_config.get(
            "command_topic"
        )

        if (
            device.controls
            and isinstance(
                command_topic,
                str,
            )
            and command_topic.strip()
        ):
            dnake_mqtt_device_topics[
                device.device_id
            ] = command_topic.strip()

        command_topics = adapter_config.get(
            "command_topics"
        )

        if (
            device.controls
            and isinstance(
                command_topics,
                dict,
            )
        ):
            resolved_control_topics = {
                control_id: topic.strip()
                for control_id, topic
                in command_topics.items()
                if (
                    control_id
                    in device.controls
                    and isinstance(
                        topic,
                        str,
                    )
                    and topic.strip()
                )
            }

            if resolved_control_topics:
                dnake_mqtt_device_control_topics[
                    device.device_id
                ] = resolved_control_topics

    xingoo_token = os.environ.get(
        "SMARTSCREEN_XINGOO_TOKEN"
    )
    xingoo_username = os.environ.get(
        "SMARTSCREEN_XINGOO_USERNAME"
    )
    xingoo_password = os.environ.get(
        "SMARTSCREEN_XINGOO_PASSWORD"
    )

    if (
        xingoo_iot_ids
        and xingoo_username
        and (
            xingoo_token
            or xingoo_password
        )
    ):
        xingoo_client = XingooClient(
            token=(
                xingoo_token
                or ""
            ),
            username=xingoo_username,
        )

        if xingoo_password:
            xingoo_client.login(
                password=xingoo_password,
            )

        xingoo_adapter = (
            XingooDeviceDataAdapter(
                registry=device_registry,
                ingestion=(
                    device_data_ingestion
                ),
            )
        )

        xingoo_source = (
            XingooDeviceDataSource(
                client=xingoo_client,
                adapter=xingoo_adapter,
                iot_ids=xingoo_iot_ids,
                observation_accumulator=(
                    observation_accumulator
                ),
                observation_sink=(
                    platform_state_pipeline
                ),
            )
        )

        if xingoo_device_iot_ids:
            xingoo_device_controller = (
                XingooDeviceController(
                    client=xingoo_client,
                    device_iot_ids=(
                        xingoo_device_iot_ids
                    ),
                )
            )

            xingoo_control_executor = (
                XingooDeviceControlExecutor(
                    controller=(
                        xingoo_device_controller
                    )
                )
            )

            device_control_executors[
                "xingoo"
            ] = xingoo_control_executor

    if dnake_mqtt_source_topics:
        dnake_mqtt_host = os.environ.get(
            "SMARTSCREEN_DNAKE_MQTT_HOST",
            "127.0.0.1",
        )
        dnake_mqtt_port = int(
            os.environ.get(
                "SMARTSCREEN_DNAKE_MQTT_PORT",
                "1883",
            )
        )
        dnake_mqtt_keepalive = 60

        dnake_mqtt_client = DnakeMqttClient(
            mqtt.CallbackAPIVersion.VERSION2
        )

        # Restore runtime authentication that was absent from the GitHub
        # baseline. Configure the same data/control client before source.start
        # performs connect; never bake credentials into the image.
        dnake_mqtt_username = os.environ.get("SMARTSCREEN_DNAKE_MQTT_USERNAME")
        dnake_mqtt_password = os.environ.get("SMARTSCREEN_DNAKE_MQTT_PASSWORD")
        if bool(dnake_mqtt_username) != bool(dnake_mqtt_password):
            raise ValueError("Dnake MQTT username and password must be supplied together")
        if dnake_mqtt_username and dnake_mqtt_password:
            dnake_mqtt_client.username_pw_set(dnake_mqtt_username, dnake_mqtt_password)

        dnake_mqtt_adapter = (
            DnakeMqttDeviceDataAdapter(
                registry=device_registry,
                ingestion=device_data_ingestion,
            )
        )

        dnake_mqtt_source = (
            DnakeMqttDeviceDataSource(
                client=dnake_mqtt_client,
                adapter=dnake_mqtt_adapter,
                source_topics=(
                    dnake_mqtt_source_topics
                ),
                retained_restore_topics=(
                    dnake_mqtt_retained_restore_topics
                ),
                observation_accumulator=(
                    observation_accumulator
                ),
                observation_sink=(
                    platform_state_pipeline
                ),
                host=dnake_mqtt_host,
                port=dnake_mqtt_port,
                keepalive=(
                    dnake_mqtt_keepalive
                ),
            )
        )

        if (
            dnake_mqtt_device_topics
            or dnake_mqtt_device_control_topics
        ):
            dnake_mqtt_control_executor = (
                DnakeMqttDeviceControlExecutor(
                    client=dnake_mqtt_client,
                    device_topics=(
                        dnake_mqtt_device_topics
                    ),
                    device_control_topics=(
                        dnake_mqtt_device_control_topics
                    ),
                )
            )

            device_control_executors[
                "dnake_mqtt"
            ] = (
                dnake_mqtt_control_executor
            )

    ha_url = os.environ.get(
        "SMARTSCREEN_HA_URL"
    )
    ha_token = os.environ.get(
        "SMARTSCREEN_HA_TOKEN"
    )

    home_assistant_client = None

    if ha_url and ha_token:
        home_assistant_client = (
            HomeAssistantClient(
                ha_url,
                ha_token,
            )
        )

        home_assistant_device_entity_ids = {
            device.device_id: (
                device.adapter_config[
                    "entity_id"
                ]
            )
            for device in device_definitions
            if (
                device.adapter_id
                == "home_assistant"
                and isinstance(
                    device.adapter_config.get(
                        "entity_id"
                    ),
                    str,
                )
                and device.adapter_config[
                    "entity_id"
                ].strip()
                and device.controls
            )
        }

        home_assistant_device_adapter_configs = {
            device.device_id: dict(
                device.adapter_config
            )
            for device in device_definitions
            if (
                device.device_id
                in home_assistant_device_entity_ids
            )
        }

        if home_assistant_device_entity_ids:
            home_assistant_control_executor = (
                HomeAssistantDeviceControlExecutor(
                    client=(
                        home_assistant_client
                    ),
                    device_entity_ids=(
                        home_assistant_device_entity_ids
                    ),
                    device_adapter_configs=(
                        home_assistant_device_adapter_configs
                    ),
                )
            )

            device_control_executors[
                "home_assistant"
            ] = (
                home_assistant_control_executor
            )

    if device_control_executors:
        device_control_dispatcher = (
            DeviceControlDispatcher(
                registry=(
                    device_control_registry
                ),
                executors=(
                    device_control_executors
                ),
            )
        )

    if (
        device_control_dispatcher is not None
        and household_actions
    ):
        household_action_executor = (
            HouseholdActionExecutor(
                dispatcher=(
                    device_control_dispatcher
                ),
                actions=household_actions,
            )
        )

    home_provider = (
        None
        if home_file is not None
        else create_home_assistant_provider(
            client=home_assistant_client,
            entities_file=resolved_home_entities_file,
            change_notifier=home_status_notifier,
        )
    )

    weather_forecast_source = None

    if (
        state_stream is None
        and home_provider is not None
    ):
        if ha_url and ha_token:
            weather_forecast_adapter = (
                HomeAssistantWeatherForecastAdapter(
                    entity_id=(
                        "weather.demo_entity_065"
                    ),
                    location_id="outdoor",
                    forecast_horizon_hours=12,
                )
            )

            weather_forecast_source = (
                HomeAssistantWeatherForecastSource(
                    base_url=ha_url,
                    token=ha_token,
                    entity_id=(
                        "weather.demo_entity_065"
                    ),
                    adapter=(
                        weather_forecast_adapter
                    ),
                    observation_accumulator=(
                        observation_accumulator
                    ),
                    observation_sink=(
                        platform_state_pipeline
                    ),
                )
            )
            state_consumer = (
                HomeAssistantStateEventConsumer(
                    home_provider,
                    observation_adapter=observation_adapter,
                    observation_sink=platform_state_pipeline,
                    observation_accumulator=(
                        observation_accumulator
                    ),
                    device_data_adapter=(
                        home_assistant_device_data_adapter
                    ),
                )
            )

            state_stream = (
                HomeAssistantStateStream(
                    base_url=ha_url,
                    token=ha_token,
                    consumer=state_consumer,
                )
            )

    calendar_event_service = None
    calendar_background = None

    if calendar_config_file is not None:
        calendar_config = load_calendar_config(
            calendar_config_file
        )

        if calendar_config.enabled:
            if calendar_config.provider == "caldav":
                calendar_background = BackgroundCalendarSource(
                    CalDAVCalendarSource(config=calendar_config), config=calendar_config)
                calendar_source = calendar_background
            else:
                calendar_runner = EventKitSubprocessRunner(
                    executable=(
                        calendar_config.bridge_executable
                    )
                )

                calendar_source = EventKitCalendarSource(
                    runner=calendar_runner
                )

            calendar_event_service = (
                CalendarEventService(
                    source=calendar_source,
                    calendar_id=(
                        calendar_config.calendar_id
                    ),
                )
            )

    app = SnapshotApplication(
        runtime,
        photo_dir=resolved_photo_dir,
        todo_file=resolved_todo_file,
        home_file=(
            resolved_home_file
            if home_provider is None
            else None
        ),
        home_provider=home_provider,
        household_state_source=(
            resolved_household_state_source
        ),
        observation_source=(
            observation_accumulator
        ),
        presentation_builder=(
            presentation_builder
        ),
        device_control_dispatcher=(
            device_control_dispatcher
        ),
        household_action_executor=(
            household_action_executor
        ),
        device_state_refresher=(
            xingoo_source
        ),
        device_definitions=(
            device_definitions
        ),
        device_parameter_store=(
            device_parameter_store
        ),
        device_power_dependency_resolver=(
            device_power_dependency_resolver
        ),
        calendar_event_service=(
            calendar_event_service
        ),
    )

    server = server_factory(
        app,
        host=bind_host,
        port=port,
        home_status_notifier=home_status_notifier,
        dashboard_state_notifier=(
            dashboard_state_notifier
        ),
    )

    try:
        runtime.start_background()
        if calendar_background is not None:
            calendar_background.start()
        freshness_sweep.start()

        if state_stream is not None:
            state_stream.start()

        if weather_forecast_source is not None:
            weather_forecast_source.start()

        if xingoo_source is not None:
            xingoo_source.start()

        if dnake_mqtt_source is not None:
            dnake_mqtt_source.start()

        server.serve_forever()

    except KeyboardInterrupt:
        return 0

    finally:
        if calendar_background is not None:
            calendar_background.stop()
            calendar_background.join(timeout=1)
        if dnake_mqtt_source is not None:
            dnake_mqtt_source.stop()

        if xingoo_source is not None:
            xingoo_source.stop()
            xingoo_source.join(
                timeout=5.0
            )

        if weather_forecast_source is not None:
            weather_forecast_source.stop()
            weather_forecast_source.join(
                timeout=5.0
            )

        if state_stream is not None:
            state_stream.stop()
            state_stream.join(timeout=5.0)

        freshness_sweep.stop()
        freshness_sweep.join(
            timeout=5.0
        )

        server.server_close()
        runtime.stop()
        runtime.join(timeout=5.0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="smartscreen-display",
        description="Run the SmartScreenOS display HTTP server.",
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the runtime YAML configuration file.",
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP bind address.",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="HTTP listen port.",
    )

    parser.add_argument(
        "--photo-dir",
        type=Path,
        default=None,
        help="Directory containing dashboard photos.",
    )

    parser.add_argument(
        "--todo-file",
        type=Path,
        default=None,
        help="Path to the dashboard todo JSON file.",
    )

    parser.add_argument(
        "--home-file",
        type=Path,
        default=None,
        help="Path to the dashboard home status JSON file.",
    )

    parser.add_argument(
        "--home-entities-file",
        type=Path,
        default=None,
        help="Path to the Home Assistant entity configuration JSON file.",
    )

    parser.add_argument(
        "--calendar-config-file",
        type=Path,
        default=None,
        help="Path to the calendar configuration JSON file.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    return run_display_server(
        config_path=args.config,
        bind_host=args.host,
        port=args.port,
        photo_dir=args.photo_dir,
        todo_file=args.todo_file,
        home_file=args.home_file,
        home_entities_file=args.home_entities_file,
        calendar_config_file=args.calendar_config_file,
    )


if __name__ == "__main__":
    raise SystemExit(main())
