#!/usr/bin/env bash
#
# verba.sh — Startup script for the Verba web application
#
# Usage:
#   ./verba.sh --start        Start the application in the background
#   ./verba.sh --stop         Gracefully stop the application
#   ./verba.sh --force-stop   Force kill the application
#   ./verba.sh --status       Show application status
#   ./verba.sh --version      Show version information
#   ./verba.sh --clear-cache  Remove venv and __pycache__ directories
#   ./verba.sh --log          Tail the latest log file

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VERBA_VERSION="2.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="${SCRIPT_DIR}/web"
VENV_DIR="${WEB_DIR}/webui"
PYTHON="${VENV_DIR}/bin/python"
PIP="${VENV_DIR}/bin/pip"
PID_FILE="${WEB_DIR}/.verba.pid"
LOG_DIR="${WEB_DIR}/log"
PORT=30319

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
log_info()  { echo "[verba]  $*"; }
log_error() { echo "[verba]  ERROR: $*" >&2; }

get_pid() {
    if [[ -f "$PID_FILE" ]]; then
        cat "$PID_FILE"
    else
        echo ""
    fi
}

is_running() {
    local pid
    pid="$(get_pid)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        return 0
    fi
    return 1
}

cleanup_pid() {
    rm -f "$PID_FILE"
}

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
cmd_start() {
    if is_running; then
        log_info "Verba is already running (PID $(get_pid))."
        log_info "https://localhost:${PORT}"
        exit 0
    fi

    log_info "Starting Verba ..."

    # --- Virtual environment (web/webui) ---
    if [[ ! -d "$VENV_DIR" ]]; then
        log_info "Creating virtual environment in web/webui ..."
        cd "$WEB_DIR"
        python3 -m venv webui
        cd "$SCRIPT_DIR"
    fi

    if [[ ! -x "$PYTHON" ]]; then
        log_error "Python not found at ${PYTHON}"
        exit 1
    fi

    # --- Install / update dependencies ---
    log_info "Installing dependencies ..."
    "$PIP" install --quiet -r "${WEB_DIR}/requirements.txt"
    log_info "Dependencies up to date."

    # --- Log directory ---
    mkdir -p "$LOG_DIR"

    # --- Generate log filename with timestamp ---
    local timestamp
    timestamp="$(date +%Y%m%d_%H%M%S)"
    local log_file="${LOG_DIR}/verba_${timestamp}.log"

    # --- Start the server ---
    log_info "Launching server on https://localhost:${PORT} ..."
    cd "$SCRIPT_DIR"
    nohup "$PYTHON" -m web.run > "$log_file" 2>&1 &
    local server_pid=$!

    # Wait briefly to confirm the process started
    sleep 2
    if kill -0 "$server_pid" 2>/dev/null; then
        echo "$server_pid" > "$PID_FILE"
        log_info "Verba started (PID ${server_pid})."
        log_info "URL:  https://localhost:${PORT}"
        log_info "Logs: ${log_file}"
    else
        log_error "Server failed to start. Check logs: ${log_file}"
        exit 1
    fi
}

cmd_stop() {
    if ! is_running; then
        log_info "Verba is not running."
        cleanup_pid
        exit 0
    fi

    local pid
    pid="$(get_pid)"
    log_info "Stopping Verba (PID ${pid}) ..."

    # Send SIGTERM and wait up to 10 seconds
    kill "$pid" 2>/dev/null
    local waited=0
    while kill -0 "$pid" 2>/dev/null && [[ $waited -lt 10 ]]; do
        sleep 1
        waited=$((waited + 1))
    done

    if kill -0 "$pid" 2>/dev/null; then
        log_error "Process did not stop gracefully. Use --force-stop."
        exit 1
    fi

    cleanup_pid
    log_info "Verba stopped."
}

cmd_force_stop() {
    if ! is_running; then
        log_info "Verba is not running."
        cleanup_pid
        exit 0
    fi

    local pid
    pid="$(get_pid)"
    log_info "Force stopping Verba (PID ${pid}) ..."

    kill -9 "$pid" 2>/dev/null || true

    # Also kill any child processes on the port
    lsof -ti:"$PORT" 2>/dev/null | xargs kill -9 2>/dev/null || true

    cleanup_pid
    log_info "Verba force stopped."
}

cmd_status() {
    if is_running; then
        local pid
        pid="$(get_pid)"
        log_info "Verba is running (PID ${pid})."
        log_info "URL:  https://localhost:${PORT}"

        # Show latest log file
        local latest_log
        latest_log="$(ls -t "${LOG_DIR}"/verba_*.log 2>/dev/null | head -1)"
        if [[ -n "$latest_log" ]]; then
            log_info "Logs: ${latest_log}"
        fi
    else
        log_info "Verba is not running."
        cleanup_pid
    fi
}

cmd_version() {
    echo "Verba v${VERBA_VERSION}"
    echo "  Port: ${PORT}"
    echo "  Root: ${SCRIPT_DIR}"
    if [[ -x "$PYTHON" ]]; then
        echo "  Python: $("$PYTHON" --version 2>&1)"
    else
        echo "  Python: not installed (run --start to initialize)"
    fi
}

cmd_clear_cache() {
    # Stop the app first if it's running
    if is_running; then
        log_info "Verba is running — stopping before clearing cache ..."
        cmd_stop
    fi

    local app_dirs=("web")

    # --- Remove web/webui venv ---
    if [[ -d "$VENV_DIR" ]]; then
        log_info "Removing virtual environment: ${VENV_DIR}"
        rm -rf "$VENV_DIR"
    else
        log_info "No virtual environment found at web/webui."
    fi

    # --- Remove __pycache__ directories ---
    for app in "${app_dirs[@]}"; do
        local app_path="${SCRIPT_DIR}/${app}"
        if [[ -d "$app_path" ]]; then
            local count
            count="$(find "$app_path" -type d -name "__pycache__" 2>/dev/null | wc -l | tr -d ' ')"
            if [[ "$count" -gt 0 ]]; then
                find "$app_path" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
                log_info "Removed ${count} __pycache__ director(ies) from ${app}/"
            else
                log_info "No __pycache__ found in ${app}/"
            fi
        fi
    done

    # --- Remove encrypted API key files (with confirmation) ---
    local key_file="${WEB_DIR}/.verba.key"
    local keys_dat="${WEB_DIR}/.verba_keys.dat"
    if [[ -f "$key_file" ]] || [[ -f "$keys_dat" ]]; then
        echo ""
        log_info "All API Keys will be cleared."
        printf "[verba]  Proceed? (Y/N): "
        read -r answer
        case "$answer" in
            [Yy])
                rm -f "$key_file" "$keys_dat"
                log_info "Removed encrypted API key files."
                ;;
            [Nn])
                log_info "API keys left in place."
                ;;
            *)
                log_info "Invalid selection. API keys left in place."
                ;;
        esac
    else
        log_info "No API key files found."
    fi

    log_info "Cache cleared."
}

cmd_log() {
    local latest_log
    latest_log="$(ls -t "${LOG_DIR}"/verba_*.log 2>/dev/null | head -1)"
    if [[ -z "$latest_log" ]]; then
        log_info "No log files found in ${LOG_DIR}/"
        exit 0
    fi

    log_info "Tailing: ${latest_log}"
    log_info "Press Ctrl+C to stop."
    echo ""
    tail -f "$latest_log"
}

cmd_help() {
    echo "Usage: $(basename "$0") <command>"
    echo ""
    echo "Commands:"
    echo "  --start        Start the Verba web application"
    echo "  --stop         Gracefully stop the application"
    echo "  --force-stop   Force kill the application"
    echo "  --status       Show application status"
    echo "  --version      Show version information"
    echo "  --clear-cache  Remove venv and __pycache__ directories"
    echo "  --log          Tail the latest log file"
    echo "  --help         Show this help message"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if [[ $# -eq 0 ]]; then
    cmd_help
    exit 0
fi

case "$1" in
    --start)       cmd_start       ;;
    --stop)        cmd_stop        ;;
    --force-stop)  cmd_force_stop  ;;
    --status)      cmd_status      ;;
    --version)     cmd_version     ;;
    --clear-cache) cmd_clear_cache ;;
    --log)         cmd_log         ;;
    --help|-h)     cmd_help        ;;
    *)
        log_error "Unknown command: $1"
        cmd_help
        exit 1
        ;;
esac
