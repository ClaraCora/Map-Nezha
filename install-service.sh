#!/usr/bin/env bash
# Nezha API systemd service manager
# Usage: sudo ./install-service.sh [install|-y] | uninstall | status | logs | restart | reload | enable | disable

set -Eeuo pipefail

SERVICE_NAME="nezha-api"
UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

# -------- colors --------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info(){ echo -e "${GREEN}[INFO]${NC} $*"; }
warn(){ echo -e "${YELLOW}[WARN]${NC} $*"; }
err(){ echo -e "${RED}[ERROR]${NC} $*" 1>&2; }

cleanup(){ :; }
error_handler(){ err "failed at line $1"; exit 1; }
trap 'error_handler $LINENO' ERR
trap cleanup EXIT

require_root(){
  if [[ $EUID -ne 0 ]]; then
    err "need root. try: sudo $0 $*"
    exit 1
  fi
}

# Paths
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
VENV_DIR="${VENV_DIR:-${SCRIPT_DIR}/venv}"
PYTHON="${PYTHON:-${VENV_DIR}/bin/python}"
PIP="${PIP:-${VENV_DIR}/bin/pip}"

detect_user(){
  if [[ -n "${SERVICE_USER:-}" ]]; then
    user="$SERVICE_USER"
  elif [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
    user="$SUDO_USER"
  elif logname &>/dev/null; then
    user="$(logname)"
  else
    user="root"
  fi
  echo "$user"
}

verify_env(){
  info "verifying environment..."
  if [[ ! -x "$PYTHON" ]]; then
    err "python not found: $PYTHON"
    exit 1
  fi
  if [[ ! -f "${SCRIPT_DIR}/app.py" ]]; then
    err "app.py not found in ${SCRIPT_DIR}"
    exit 1
  fi
  # dependency check via heredoc; note redirection order and lack of extra 'then'
  if ! "$PYTHON" - 2>/dev/null <<'PY'
import importlib
for m in ("flask","flask_cors","requests","websocket"):
    importlib.import_module(m)
PY
  then
    err "missing deps. install: ${PIP} install -r ${SCRIPT_DIR}/requirements.txt"
    exit 1
  fi
  info "env ok"
}

python_ver(){
  "$PYTHON" - <<'PY'
import sys
print(".".join(map(str, sys.version_info[:2])))
PY
}

render_unit(){
  local user="$1"
  local pyver="$2"
  cat <<EOF
[Unit]
Description=Nezha API Python Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${user}
Group=${user}
WorkingDirectory=${SCRIPT_DIR}
Environment=PATH=${VENV_DIR}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=VIRTUAL_ENV=${VENV_DIR}
Environment=PYTHONPATH=${VENV_DIR}/lib/python${pyver}/site-packages
EnvironmentFile=-${SCRIPT_DIR}/.env
ExecStart=${PYTHON} ${SCRIPT_DIR}/app.py
Restart=always
RestartSec=5
TimeoutStartSec=30
TimeoutStopSec=30
LimitNOFILE=65536
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
}

install_unit(){
  require_root
  verify_env
  local user="$(detect_user)"
  local pyver="$(python_ver)"
  info "service user: ${user}"
  local tmp="/tmp/${SERVICE_NAME}.service.$$"
  render_unit "$user" "$pyver" > "$tmp"
  info "unit preview:"
  echo "----------------------------------------"
  cat "$tmp"
  echo "----------------------------------------"
  if [[ "${1:-}" != "-y" && "${ASSUME_YES:-0}" != "1" ]]; then
    read -r -p "Proceed to install and start service? [y/N] " ans || true
    [[ "${ans,,}" == "y" ]] || { info "aborted"; rm -f "$tmp"; exit 0; }
  fi
  mv "$tmp" "$UNIT_PATH"
  systemctl daemon-reload
  if command -v systemd-analyze >/dev/null 2>&1; then
    systemd-analyze verify "$UNIT_PATH" || true
  fi
  systemctl enable --now "$SERVICE_NAME"
  info "installed and started"
  systemctl --no-pager --full status "$SERVICE_NAME" || true
}

uninstall_unit(){
  require_root
  info "stopping ${SERVICE_NAME}..."
  systemctl stop "${SERVICE_NAME}" 2>/dev/null || true
  info "disabling ${SERVICE_NAME}..."
  systemctl disable "${SERVICE_NAME}" 2>/dev/null || true
  if [[ -f "$UNIT_PATH" ]]; then
    rm -f "$UNIT_PATH"
    info "removed unit: $UNIT_PATH"
  else
    warn "unit not found: $UNIT_PATH"
  fi
  systemctl daemon-reload
  info "uninstalled"
}

usage(){
  cat <<USAGE
Usage: sudo $0 [install|-y] | uninstall | status | logs | restart | reload | enable | disable

ENV:
  SERVICE_USER    override systemd User= (default: sudo user or logname)
  VENV_DIR        virtualenv dir (default: ${SCRIPT_DIR}/venv)
  ASSUME_YES=1    non-interactive install

Examples:
  sudo $0                 # install with prompt
  sudo ASSUME_YES=1 $0    # install no prompt
  sudo $0 uninstall       # uninstall service
USAGE
}

cmd="${1:-install}"
shift || true

case "$cmd" in
  install|-y) install_unit "${cmd}";;
  uninstall) uninstall_unit;;
  status) systemctl status "$SERVICE_NAME";;
  logs) journalctl -u "$SERVICE_NAME" -f;;
  restart) systemctl restart "$SERVICE_NAME";;
  reload) systemctl daemon-reload && systemctl restart "$SERVICE_NAME";;
  enable) systemctl enable "$SERVICE_NAME";;
  disable) systemctl disable "$SERVICE_NAME";;
  help|-h|--help) usage;;
  *) err "unknown command: $cmd"; usage; exit 1;;
esac
