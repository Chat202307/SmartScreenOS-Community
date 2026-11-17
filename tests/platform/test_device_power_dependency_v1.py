from src.smartscreen_platform.device_data import (
    DeviceDefinition,
    DeviceParameterDefinition,
    DeviceParameterStore,
    DeviceRegistry,
)
from src.smartscreen_platform.device_data.power_dependency import (
    DevicePowerDependencyResolver,
)


def make_registry():
    power_source = DeviceDefinition(
        device_id="dining.light_power_1",
        name="餐灯物理电源",
        location_id="dining",
        adapter_id="home_assistant",
        parameters={
            "power": DeviceParameterDefinition(
                parameter="power",
                source_id="light.dining_power",
                value_type="bool",
            ),
        },
    )

    table_light = DeviceDefinition(
        device_id="dining.table_light_east",
        name="餐桌灯东",
        location_id="dining",
        adapter_id="home_assistant",
        parameters={
            "power": DeviceParameterDefinition(
                parameter="power",
                source_id="light.table_east",
                value_type="bool",
            ),
        },
        power_source_device_id=(
            "dining.light_power_1"
        ),
    )

    return DeviceRegistry(
        devices=[
            power_source,
            table_light,
        ]
    )


def make_resolver():
    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry
    )

    resolver = DevicePowerDependencyResolver(
        registry=registry,
        store=store,
    )

    return resolver, store


def test_available_parameter_remains_available():
    resolver, store = make_resolver()

    store.update(
        device_id="dining.table_light_east",
        parameter="power",
        value=True,
        available=True,
    )

    assert resolver.resolve(
        device_id="dining.table_light_east",
        parameter="power",
    ) == "available"


def test_unavailable_downstream_with_power_source_off_is_powered_off_by_upstream():
    resolver, store = make_resolver()

    store.update(
        device_id="dining.light_power_1",
        parameter="power",
        value=False,
        available=True,
    )

    store.update(
        device_id="dining.table_light_east",
        parameter="power",
        value="unavailable",
        available=False,
    )

    assert resolver.resolve(
        device_id="dining.table_light_east",
        parameter="power",
    ) == "powered_off_by_upstream"


def test_unavailable_downstream_with_power_source_on_remains_unavailable():
    resolver, store = make_resolver()

    store.update(
        device_id="dining.light_power_1",
        parameter="power",
        value=True,
        available=True,
    )

    store.update(
        device_id="dining.table_light_east",
        parameter="power",
        value="unavailable",
        available=False,
    )

    assert resolver.resolve(
        device_id="dining.table_light_east",
        parameter="power",
    ) == "unavailable"


def test_missing_power_source_state_does_not_assume_powered_off():
    resolver, store = make_resolver()

    store.update(
        device_id="dining.table_light_east",
        parameter="power",
        value="unavailable",
        available=False,
    )

    assert resolver.resolve(
        device_id="dining.table_light_east",
        parameter="power",
    ) == "unavailable"


def test_unavailable_power_source_does_not_assume_powered_off():
    resolver, store = make_resolver()

    store.update(
        device_id="dining.light_power_1",
        parameter="power",
        value="unavailable",
        available=False,
    )

    store.update(
        device_id="dining.table_light_east",
        parameter="power",
        value="unavailable",
        available=False,
    )

    assert resolver.resolve(
        device_id="dining.table_light_east",
        parameter="power",
    ) == "unavailable"


def test_unavailable_device_without_power_dependency_remains_unavailable():
    standalone = DeviceDefinition(
        device_id="living.light_1",
        name="客厅灯",
        location_id="living",
        adapter_id="home_assistant",
        parameters={
            "power": DeviceParameterDefinition(
                parameter="power",
                source_id="light.living",
                value_type="bool",
            ),
        },
    )

    registry = DeviceRegistry(
        devices=[
            standalone,
        ]
    )

    store = DeviceParameterStore(
        registry=registry
    )

    store.update(
        device_id="living.light_1",
        parameter="power",
        value="unavailable",
        available=False,
    )

    resolver = DevicePowerDependencyResolver(
        registry=registry,
        store=store,
    )

    assert resolver.resolve(
        device_id="living.light_1",
        parameter="power",
    ) == "unavailable"


def test_missing_referenced_power_source_does_not_assume_powered_off():
    dependent = DeviceDefinition(
        device_id="dining.table_light_east",
        name="餐桌灯东",
        location_id="dining",
        adapter_id="home_assistant",
        parameters={
            "power": DeviceParameterDefinition(
                parameter="power",
                source_id="light.table_east",
                value_type="bool",
            ),
        },
        power_source_device_id=(
            "dining.missing_power_source"
        ),
    )

    registry = DeviceRegistry(
        devices=[
            dependent,
        ]
    )

    store = DeviceParameterStore(
        registry=registry
    )

    store.update(
        device_id="dining.table_light_east",
        parameter="power",
        value="unavailable",
        available=False,
    )

    resolver = DevicePowerDependencyResolver(
        registry=registry,
        store=store,
    )

    assert resolver.resolve(
        device_id="dining.table_light_east",
        parameter="power",
    ) == "unavailable"


def test_upstream_power_off_overrides_still_available_downstream_state():
    resolver, store = make_resolver()

    store.update(
        device_id="dining.light_power_1",
        parameter="power",
        value=False,
        available=True,
    )

    # HA/cloud may still expose the child as available
    # briefly after the physical supply has been removed.
    store.update(
        device_id="dining.table_light_east",
        parameter="power",
        value=True,
        available=True,
    )

    assert resolver.resolve(
        device_id="dining.table_light_east",
        parameter="power",
    ) == "powered_off_by_upstream"
