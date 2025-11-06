import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from opspilot.tools import base
from opspilot.tools.base import ToolError, tool

DESCRIPTION = (
    "Get the current weather for a city. "
    'Example: get_weather(city="Paris", unit="celsius")'
)


class GetWeatherInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    city: str = Field(min_length=1, description="City name, e.g. 'Paris'")
    unit: Literal["celsius", "fahrenheit"] = Field(
        "celsius", description="Temperature unit. Defaults to celsius."
    )


_FAKE_WEATHER = {
    "paris": (14.0, "overcast"),
    "san francisco": (17.0, "foggy"),
    "new york": (9.0, "clear"),
    "bengaluru": (27.0, "humid, light rain"),
}


@tool("get_weather", DESCRIPTION, GetWeatherInput)
def get_weather(city: str, unit: str = "celsius") -> str:
    time.sleep(base.FAKE_LATENCY_S)   # read at call time, so tests can turn it off
    key = city.split(",")[0].strip().lower()
    if key not in _FAKE_WEATHER:
        raise ToolError(
            f"no weather data for {city!r}. Known cities: "
            + ", ".join(sorted(_FAKE_WEATHER))
        )
    celsius, conditions = _FAKE_WEATHER[key]
    if unit == "fahrenheit":
        return f"{celsius * 9 / 5 + 32:.1f}°F, {conditions}"
    return f"{celsius:.1f}°C, {conditions}"