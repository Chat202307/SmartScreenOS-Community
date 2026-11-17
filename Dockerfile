FROM python:3.13-slim-bookworm@sha256:a5a7017efc5969e00ae2b91c8eb0631049a569652aa4ffc4501769049ae45c72
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock && useradd --uid 10001 --create-home smartscreen
COPY src ./src
COPY examples ./examples
COPY config/runtime.yaml config/home.json config/home_entities.json config/platform_entities.json config/device_data.json config/occupancy_interpretation.json config/lighting_interpretation.json config/dashboard_presentation.json config/household_actions.json config/calendar.json config/demo_home_status.json ./config/
COPY LICENSE NOTICE THIRD_PARTY_NOTICES.md ./
COPY third_party ./third_party
COPY tools/run_demo.py ./tools/run_demo.py
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["python", "tools/run_demo.py", "--host", "0.0.0.0", "--port", "8080"]
