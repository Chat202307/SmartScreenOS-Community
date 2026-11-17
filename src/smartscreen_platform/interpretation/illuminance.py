from src.smartscreen_platform.contracts import Interpretation

class IlluminanceInterpreter:
    def interpret(
        self,
        observations,
        knowledge=None,
        context=None,
    ):
        by_parameter = {
            item.parameter: item
            for item in observations
        }

        illuminance = by_parameter.get(
            "illuminance"
        )

        if illuminance is None:
            return []

        location_id = (
            illuminance.location_id
        )

        dim_below = 80.0
        bright_above = 1200.0

        if knowledge is not None:
            dim_below = float(
                knowledge.get(
                    "lighting_dim_below_lux",
                    location_id,
                    dim_below,
                )
            )

            bright_above = float(
                knowledge.get(
                    "lighting_bright_above_lux",
                    location_id,
                    bright_above,
                )
            )

        try:
            lux = float(
                illuminance.value
            )
        except (TypeError, ValueError):
            return []

        if lux < dim_below:
            state = "dim"
        elif lux > bright_above:
            state = "bright"
        else:
            state = "comfortable"

        return [
            Interpretation.create(
                interpretation_type=(
                    "lighting_state"
                ),
                name="lighting_state",
                value=state,
                confidence=float(
                    illuminance.confidence
                ),
                location_id=location_id,
                evidence_refs=[
                    illuminance.observation_id,
                ],
                expires_in_seconds=300,
                metadata={
                    "dim_below_lux":
                        float(dim_below),
                    "bright_above_lux":
                        float(bright_above),
                },
            )
        ]
