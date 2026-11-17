from src.smartscreen_platform.contracts import Interpretation

class ThermalInterpreter:
    def interpret(self, observations, knowledge=None, context=None):
        by_parameter = {item.parameter: item for item in observations}
        temperature = by_parameter.get("temperature")
        if temperature is None:
            return []

        location_id = temperature.location_id
        low = 22.0
        high = 27.0
        hot = 30.0
        cold = 18.0

        if knowledge is not None:
            low = float(
                knowledge.get(
                    "thermal_preferred_low",
                    location_id,
                    low,
                )
            )
            high = float(
                knowledge.get(
                    "thermal_preferred_high",
                    location_id,
                    high,
                )
            )
            hot = float(
                knowledge.get(
                    "thermal_hot_threshold",
                    location_id,
                    hot,
                )
            )
            cold = float(
                knowledge.get(
                    "thermal_cold_threshold",
                    location_id,
                    cold,
                )
            )

        value = float(temperature.value)
        if value >= hot:
            state = "hot"
        elif value > high:
            state = "warm"
        elif value <= cold:
            state = "cold"
        elif value < low:
            state = "cool"
        else:
            state = "comfortable"

        humidity = by_parameter.get("humidity")
        completeness = 0.7 + (0.2 if humidity is not None else 0.0)
        confidence = min(
            float(temperature.confidence),
            completeness,
        )

        return [
            Interpretation.create(
                interpretation_type="thermal_state",
                name="thermal_state",
                value=state,
                confidence=confidence,
                location_id=location_id,
                evidence_refs=[
                    item.observation_id
                    for item in (temperature, humidity)
                    if item is not None
                ],
                expires_in_seconds=300,
                metadata={
                    "preferred_low": low,
                    "preferred_high": high,
                },
            )
        ]
