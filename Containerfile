FROM python:3.14-alpine AS builder

RUN mkdir -p /opt/shitcapitalxauvnd

COPY . /opt/shitcapitalxauvnd/

RUN python3 -m pip install -r requirements_static.txt


FROM python:3.14-alpine AS runner

LABEL com.github.actions.name="ShitCapital XAUVND Tracker"
LABEL com.github.actions.description="Action that automatically updates the gold price index in the given repository."

RUN apk add --update --no-cache ca-certificates && mkdir -p /opt/shitcapitalxauvnd

WORKDIR /opt/shitcapitalxauvnd

COPY --from=builder /opt/shitcapitalxauvnd/fetch.py /opt/shitcapitalxauvnd/fetch.py

ENTRYPOINT ["python3", "fetch.py"]
