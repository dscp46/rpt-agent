#!/usr/bin/env bash
INST_DIR=/usr/local/src/rpt-agent
if [ ! -d "$INST_DIR" ]; then
	mkdir -p "$INST_DIR"
	cp rpt-agent.py "$INST_DIR"
	cp rpt-agent /etc/default/rpt-agent
	cp rpt-agent.service /etc/systemd/system/
	chmod -x "$INST_DIR/rpt-agent.py"
	systemctl daemon-reload
	systemctl enable rpt-agent
	systemctl start rpt-agent
fi
