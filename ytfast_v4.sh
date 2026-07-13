#!/usr/bin/env bash
# YTFAST v4 - ULTIMATE EDITION
# Author: Tassok Imam Wasiy
set -euo pipefail

# ========================= CONFIGURATION =========================
VENV_PATH="${YTFAST_VENV:-$HOME/.venv/bin/activate}"
DEFAULT_SPEED=24
MAX_PARALLEL_JOBS=4
DOWNLOAD_DIR="${YTFAST_DIR:-$HOME/Downloads/YTFAST}"
LOG_DIR="${DOWNLOAD_DIR}/.logs"
CONFIG_FILE="${DOWNLOAD_DIR}/.ytfast.conf"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'
BOLD='\033[1m'

# Format templates
FORMAT_SINGLE="%(title).100s [%(id)s].%(ext)s"
FORMAT_PLAYLIST="%(playlist)s/%(playlist_index)s - %(title).90s [%(id)s].%(ext)s"
FORMAT_AUDIO="%(title).90s [%(id)s].%(ext)s"

# Defaults & globals
SPEED="$DEFAULT_SPEED"
VERBOSE=false
QUIET=false
DRY_RUN=false
ORGANIZE=true
METADATA=true
THUMBNAIL=false
SUBTITLE=false
PARALLEL_MODE=false
COOKIES_FILE=""
PROXY=""
RATE_LIMIT=""
AUTO_RENAME=false

# CLI mode variables
MODES_RAW=""
QUALITY=""   # e.g. 720 or best
CONTAINER="" # mp4 mkv webm avi
AUDIO_OPT="" # audio, mp3, opus, m4a, flac

# INTERNAL
CONTROL_FLAGS=""

# ========================= HELPERS =========================
log() {
  local level="$1"
  shift
  local msg="$*"
  local timestamp
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  case "$level" in
  ERROR) echo -e "${RED}${BOLD}[ERROR]${NC} $msg" >&2 ;;
  SUCCESS) echo -e "${GREEN}${BOLD}[✓]${NC} $msg" ;;
  INFO) echo -e "${BLUE}${BOLD}[INFO]${NC} $msg" ;;
  WARN) echo -e "${YELLOW}${BOLD}[!]${NC} $msg" ;;
  DEBUG) [ "$VERBOSE" = true ] && echo -e "${CYAN}[DEBUG]${NC} $msg" || true ;;
  PROGRESS) echo -e "${MAGENTA}${BOLD}[↻]${NC} $msg" ;;
  esac
  mkdir -p "$LOG_DIR" 2>/dev/null || true
  echo "[$timestamp] [$level] $msg" >>"${LOG_DIR}/ytfast_$(date +%Y%m%d).log" 2>/dev/null || true
}

abort() {
  log ERROR "$1"
  exit 1
}

# Soft fail: log a warning and return non-zero (used in batch/parallel so one
# bad URL doesn't kill the whole run)
soft_fail() {
  log WARN "$1"
  return 1
}

banner() {
  [ "$QUIET" = false ] || return 0
  echo -e "${CYAN}${BOLD}"
  cat <<'EOF'
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ██╗   ██╗████████╗███████╗ █████╗ ███████╗████████╗     ║
║   ╚██╗ ██╔╝╚══██╔══╝██╔════╝██╔══██╗██╔════╝╚══██╔══╝     ║
║    ╚████╔╝    ██║   █████╗  ███████║███████╗   ██║        ║
║     ╚██╔╝     ██║   ██╔══╝  ██╔══██║╚════██║   ██║        ║
║      ██║      ██║   ██║     ██║  ██║███████║   ██║        ║
║      ╚═╝      ╚═╝   ╚═╝     ╚═╝  ╚═╝╚══════╝   ╚═╝        ║
║                                                           ║
║                 ULTIMATE EDITION v4.0                     ║
║         The Most Powerful Downloader Ever Built           ║
╚═══════════════════════════════════════════════════════════╝
EOF
  echo -e "${NC}"
}

# ========================= INIT & DEPENDENCIES =========================
init_environment() {
  mkdir -p "$DOWNLOAD_DIR" "$LOG_DIR"
  if [ ! -f "$CONFIG_FILE" ]; then
    log INFO "Generating default config at $CONFIG_FILE"
    cat >"$CONFIG_FILE" <<'EOF'
SPEED=24
MAX_PARALLEL_JOBS=4
ORGANIZE=true
METADATA=true
THUMBNAIL=false
SUBTITLE=false
QUIET=false
VERBOSE=false
COOKIES_FILE=""
PROXY=""
RATE_LIMIT=""
EOF
    log SUCCESS "Config created"
  fi
  if [ -f "$CONFIG_FILE" ]; then
    # shellcheck disable=SC1090
    source "$CONFIG_FILE" 2>/dev/null || log WARN "Failed to load config"
    log DEBUG "Loaded config"
  fi
}

activate_env() {
  if [ -f "$VENV_PATH" ]; then
    # shellcheck disable=SC1090
    source "$VENV_PATH" 2>/dev/null || log WARN "Failed to source venv"
    log DEBUG "Virtualenv activated"
  else
    log DEBUG "No venv at $VENV_PATH"
  fi
}

check_dependencies() {
  local deps=(yt-dlp ffmpeg)
  local missing=()
  for d in "${deps[@]}"; do
    command -v "$d" >/dev/null 2>&1 || missing+=("$d")
  done
  [ ${#missing[@]} -eq 0 ] || abort "Missing dependencies: ${missing[*]}"
  command -v jq >/dev/null 2>&1 || log WARN "jq not installed (optional, but recommended)"
}

validate_speed() {
  local speed="$1"
  if ! [[ "$speed" =~ ^[0-9]+$ ]]; then
    echo "$DEFAULT_SPEED"
    return
  fi
  case "$speed" in
  4 | 8 | 12 | 16 | 24 | 32 | 48 | 64) echo "$speed" ;;
  *) echo "$DEFAULT_SPEED" ;;
  esac
}

# ========================= MODES PARSING & PRECEDENCE =========================
parse_modes_raw() {
  local raw="$1"
  IFS=',' read -r -a parts <<<"$raw"
  for p in "${parts[@]}"; do
    p="${p// /}"
    [ -z "$p" ] && continue
    case "$p" in
    best | max | 4320 | 2160 | 1440 | 1080 | 720 | 480 | 360 | 240 | 144)
      [ -z "$QUALITY" ] && QUALITY="$p"
      ;;
    audio | mp3 | m4a | opus | flac)
      [ -z "$AUDIO_OPT" ] && AUDIO_OPT="$p"
      ;;
    mp4 | mkv | webm | avi)
      [ -z "$CONTAINER" ] && CONTAINER="$p"
      ;;
    *)
      log WARN "Unknown token in --modes: '$p' (ignoring)"
      ;;
    esac
  done
}

apply_modes_and_flags() {
  if [ -n "$MODES_RAW" ]; then
    parse_modes_raw "$MODES_RAW"
  fi
  if [ -z "$QUALITY" ] && [ -z "$AUDIO_OPT" ]; then
    QUALITY="best"
  fi
}

audio_codec_for() {
  case "$1" in
  opus) echo "libopus" ;;
  mp3) echo "libmp3lame" ;;
  m4a) echo "aac" ;;
  flac) echo "flac" ;;
  audio) echo "" ;;
  *) echo "" ;;
  esac
}

# ========================= URL & INFO =========================
validate_url() {
  local url="$1"
  [[ "$url" =~ ^https?:// ]] || abort "Invalid URL: $url"
}

validate_url_soft() {
  local url="$1"
  if [[ "$url" =~ ^https?:// ]]; then
    return 0
  else
    soft_fail "Skipping invalid URL: $url"
    return 1
  fi
}

get_video_info() {
  local url="$1"
  log INFO "Fetching video info..."
  local info
  info=$(yt-dlp --dump-json --no-warnings --playlist-items 1 "$url" 2>/dev/null | head -n1 || true)
  if [ -z "$info" ]; then
    log WARN "Could not fetch video info"
    return 1
  fi
  if command -v jq >/dev/null 2>&1; then
    local title duration uploader
    title=$(echo "$info" | jq -r '.title    // "Unknown"' 2>/dev/null || echo "Unknown")
    duration=$(echo "$info" | jq -r '.duration // 0' 2>/dev/null || echo 0)
    uploader=$(echo "$info" | jq -r '.uploader // "Unknown"' 2>/dev/null || echo "Unknown")
    log INFO "Title:    $title"
    log INFO "Uploader: $uploader"
    log INFO "Duration: $(format_duration "$duration")"
  fi
  return 0
}

format_duration() {
  local total="$1"
  local h=$((total / 3600))
  local m=$(((total % 3600) / 60))
  local s=$((total % 60))
  if [ "$h" -gt 0 ]; then
    printf "%dh %dm %ds" "$h" "$m" "$s"
  elif [ "$m" -gt 0 ]; then
    printf "%dm %ds" "$m" "$s"
  else
    printf "%ds" "$s"
  fi
}

# ========================= FILE UTILITIES =========================
clean_filename() {
  local name="$1"
  name=$(sed -E 's/\[.*?\]|\(.*?\)//g' <<<"$name")
  name=$(sed -E 's/[^a-zA-Z0-9._-]/_/g' <<<"$name")
  name=$(sed -E 's/[_-]{2,}/_/g' <<<"$name")
  name=$(sed -E 's/^[_.-]+|[_.-]+$//g' <<<"$name")
  echo "${name:0:200}"
}

auto_rename() {
  local dir="${1:-.}"
  local count=0
  log INFO "Auto-renaming files in $dir..."

  local search_dirs=("$dir")
  [ -d "$dir/Videos" ] && search_dirs+=("$dir/Videos")
  [ -d "$dir/Audio" ] && search_dirs+=("$dir/Audio")

  for search_dir in "${search_dirs[@]}"; do
    shopt -s nullglob
    local files=("$search_dir"/*.{mp4,mkv,webm,avi,mp3,m4a,opus,flac})
    for f in "${files[@]}"; do
      [ -f "$f" ] || continue
      local base="${f%.*}"
      local ext="${f##*.}"
      local cleaned
      cleaned=$(clean_filename "$(basename "$base")")
      local np
      np="$(dirname "$f")/${cleaned}.${ext}"
      if [ "$f" != "$np" ] && [ ! -e "$np" ]; then
        mv "$f" "$np" 2>/dev/null && ((count++)) || true
      fi
    done
    shopt -u nullglob
  done

  log SUCCESS "Renamed $count file(s)"
}

# ========================= PLAYLIST CONTROL =========================
parse_playlist_control() {
  local ctrl="$1"
  local flags=""
  case "$ctrl" in
  full | all)
    flags="--yes-playlist"
    ;;
  single | no-playlist)
    flags="--no-playlist"
    ;;
  reverse)
    flags="--playlist-reverse"
    ;;
  random)
    flags="--playlist-random"
    ;;
  first=*)
    local num="${ctrl#first=}"
    # Use --playlist-items 1:N (slice syntax, works on all modern yt-dlp)
    [[ "$num" =~ ^[0-9]+$ ]] && flags="--playlist-items 1:${num}" || log WARN "Invalid first= value: $num"
    ;;
  last=*)
    local num="${ctrl#last=}"
    [[ "$num" =~ ^[0-9]+$ ]] && flags="--playlist-items -${num}:" || log WARN "Invalid last= value: $num"
    ;;
  items=*)
    local items="${ctrl#items=}"
    flags="--playlist-items $items"
    ;;
  range=*)
    local range="${ctrl#range=}"
    local s="${range%-*}"
    local e="${range#*-}"
    if [[ "$s" =~ ^[0-9]+$ ]] && [[ "$e" =~ ^[0-9]+$ ]]; then
      flags="--playlist-items ${s}:${e}"
    else
      log WARN "Invalid range format: $range (expected N-M e.g. 5-15)"
    fi
    ;;
  skip=*)
    local num="${ctrl#skip=}"
    # skip=N → start from item N+1 using slice notation
    if [[ "$num" =~ ^[0-9]+$ ]]; then
      local start=$((num + 1))
      flags="--playlist-items ${start}:"
    else
      log WARN "Invalid skip= value: $num"
    fi
    ;;
  *)
    log WARN "Unknown playlist control: $ctrl"
    flags=""
    ;;
  esac
  echo "$flags"
}

# ========================= CORE: build args + run =========================
execute_download_single() {
  local url="$1"
  local playlist_flags="$2"

  # Determine if audio-only
  local is_audio_only=false
  if [ -n "$AUDIO_OPT" ]; then
    case "$AUDIO_OPT" in
    audio | mp3 | m4a | opus | flac) is_audio_only=true ;;
    *) : ;;
    esac
  fi

  local args=()

  # ALWAYS add --no-playlist by default (safety: prevents accidental full playlist pulls)
  args+=(--no-playlist)

  # Core download flags
  args+=(--concurrent-fragments "$SPEED")
  args+=(--fragment-retries infinite --retries infinite --file-access-retries infinite)
  args+=(--continue --no-overwrites)
  args+=(--restrict-filenames)
  args+=(--no-part)

  # Output template
  if [ "$is_audio_only" = true ]; then
    args+=(-o "$FORMAT_AUDIO")
  elif [ -n "$playlist_flags" ] && [[ ! "$playlist_flags" =~ --no-playlist ]]; then
    args+=(-o "$FORMAT_PLAYLIST")
  else
    args+=(-o "$FORMAT_SINGLE")
  fi

  [ "$METADATA" = true ] && args+=(--write-info-json --write-description --embed-metadata --embed-chapters)
  [ "$THUMBNAIL" = true ] && args+=(--write-thumbnail --embed-thumbnail)
  [ "$SUBTITLE" = true ] && args+=(--write-subs --write-auto-subs --sub-lang en es fr de ar --embed-subs)
  [ -n "$COOKIES_FILE" ] && [ -f "$COOKIES_FILE" ] && args+=(--cookies "$COOKIES_FILE")
  [ -n "$PROXY" ] && args+=(--proxy "$PROXY")
  [ -n "$RATE_LIMIT" ] && args+=(--limit-rate "$RATE_LIMIT")
  [ "$QUIET" = true ] && args+=(--quiet --no-warnings)
  [ "$VERBOSE" = true ] && args+=(--verbose)
  [ "$QUIET" = false ] && [ "$VERBOSE" = false ] && args+=(--progress)

  # Handle playlist control: if user wants a playlist mode, strip the default --no-playlist
  if [ -n "$playlist_flags" ]; then
    if [[ "$playlist_flags" =~ (--playlist-reverse|--playlist-random|--playlist-items) ]]; then
      local temp_args=()
      for arg in "${args[@]}"; do
        [[ "$arg" != "--no-playlist" ]] && temp_args+=("$arg")
      done
      args=("${temp_args[@]}")
      log DEBUG "Playlist mode enabled"
    fi

    IFS=' ' read -r -a pf <<<"$playlist_flags"
    for t in "${pf[@]}"; do
      [ -n "$t" ] && args+=("$t")
    done
  fi

  # Audio or video format selection
  if [ "$is_audio_only" = true ]; then
    args+=(--extract-audio)
    case "$AUDIO_OPT" in
    mp3) args+=(--audio-format mp3 --audio-quality 0) ;;
    m4a) args+=(--audio-format m4a --audio-quality 0) ;;
    opus) args+=(--audio-format opus --audio-quality 0) ;;
    flac) args+=(--audio-format flac) ;;
    audio) args+=(--audio-format best) ;;
    esac
  else
    local format_string
    if [ -z "$QUALITY" ] || [ "$QUALITY" = "best" ] || [ "$QUALITY" = "max" ]; then
      format_string="bestvideo+bestaudio/best"
    else
      if [[ "$QUALITY" =~ ^[0-9]+$ ]]; then
        format_string="bestvideo[height<=${QUALITY}]+bestaudio/best[height<=${QUALITY}]/best"
      else
        log WARN "Invalid quality value: $QUALITY, using best"
        format_string="bestvideo+bestaudio/best"
      fi
    fi
    args+=(-f "$format_string")

    if [ -n "$CONTAINER" ]; then
      args+=(--merge-output-format "$CONTAINER")
    fi

    # Audio codec re-encoding (applies regardless of container)
    local codec
    codec=$(audio_codec_for "$AUDIO_OPT")
    if [ -n "$codec" ]; then
      args+=(--postprocessor-args "ffmpeg:-c:v copy -c:a ${codec} -b:a 128k")
    fi
  fi

  # Always use absolute path for download dir — no cd dependency
  args+=(-P "$DOWNLOAD_DIR")

  # Dry run: print full command and exit
  if [ "$DRY_RUN" = true ]; then
    local cmd="yt-dlp"
    for a in "${args[@]}"; do
      cmd+=" $(printf '%q' "$a")"
    done
    cmd+=" $(printf '%q' "$url")"
    log INFO "DRY RUN - Would run: $cmd"
    return 0
  fi

  log PROGRESS "Starting: quality='${QUALITY:-auto}' container='${CONTAINER:-auto}' audio='${AUDIO_OPT:-source}' → $url"
  if yt-dlp "${args[@]}" "$url"; then
    log SUCCESS "Finished: $url"
    return 0
  else
    log ERROR "Failed: $url"
    return 1
  fi
}

# ========================= BATCH / PARALLEL / ORGANIZE =========================
process_batch_file() {
  local batch_file="$1"
  [ -f "$batch_file" ] || abort "Batch file not found: $batch_file"
  mapfile -t batch_urls < <(tr ',' '\n' <"$batch_file" | sed '/^$/d; /^#/d; s/^[[:space:]]*//; s/[[:space:]]*$//')
  local total=${#batch_urls[@]}
  local curr=0
  local succ=0
  local fail=0

  for url in "${batch_urls[@]}"; do
    ((curr++))
    log PROGRESS "Batch $curr/$total: $url"
    if ! validate_url_soft "$url"; then
      ((fail++))
      continue
    fi
    get_video_info "$url" || true
    if execute_download_single "$url" "$CONTROL_FLAGS"; then
      ((succ++))
    else
      ((fail++))
    fi
    sleep 1
  done
  log SUCCESS "Batch complete: $succ succeeded, $fail failed out of $total"
}

process_parallel() {
  local urls=("$@")
  local total=${#urls[@]}
  log INFO "Parallel: $total URL(s) with $MAX_PARALLEL_JOBS workers"

  local pids=()
  declare -A pid_url_map
  local running=0
  local idx=0
  local completed=0
  local succ=0
  local fail=0

  while [ "$idx" -lt "$total" ] || [ "$running" -gt 0 ]; do
    # Spawn new jobs up to the limit
    while [ "$running" -lt "$MAX_PARALLEL_JOBS" ] && [ "$idx" -lt "$total" ]; do
      local url="${urls[$idx]}"
      if validate_url_soft "$url"; then
        get_video_info "$url" || true
        (execute_download_single "$url" "$CONTROL_FLAGS") &
        local new_pid=$!
        pids+=("$new_pid")
        pid_url_map[$new_pid]="$url"
        ((running++))
      else
        ((fail++))
      fi
      ((idx++))
      sleep 0.2
    done

    # Reap completed jobs and check exit codes
    local new_pids=()
    for pid in "${pids[@]}"; do
      if kill -0 "$pid" 2>/dev/null; then
        new_pids+=("$pid")
      else
        local exit_code=0
        wait "$pid" 2>/dev/null || exit_code=$?
        ((running--))
        ((completed++))
        if [ "$exit_code" -eq 0 ]; then
          ((succ++))
          log SUCCESS "Job done [PID $pid]: ${pid_url_map[$pid]:-unknown}"
        else
          ((fail++))
          log ERROR "Job failed [PID $pid]: ${pid_url_map[$pid]:-unknown}"
        fi
        log PROGRESS "Progress: $completed/$total"
      fi
    done
    pids=("${new_pids[@]}")

    sleep 0.4
  done

  log SUCCESS "Parallel complete: $succ succeeded, $fail failed out of $total"
}

organize_downloads() {
  log INFO "Organizing downloads in $DOWNLOAD_DIR..."
  shopt -s nullglob

  # Video files
  local video_files=("$DOWNLOAD_DIR"/*.mp4 "$DOWNLOAD_DIR"/*.mkv "$DOWNLOAD_DIR"/*.webm "$DOWNLOAD_DIR"/*.avi)
  if [ ${#video_files[@]} -gt 0 ]; then
    mkdir -p "$DOWNLOAD_DIR/Videos"
    for f in "${video_files[@]}"; do
      [ -f "$f" ] && mv "$f" "$DOWNLOAD_DIR/Videos/" 2>/dev/null || true
    done
  fi

  # Audio files
  local audio_files=("$DOWNLOAD_DIR"/*.mp3 "$DOWNLOAD_DIR"/*.m4a "$DOWNLOAD_DIR"/*.opus "$DOWNLOAD_DIR"/*.flac "$DOWNLOAD_DIR"/*.wav)
  if [ ${#audio_files[@]} -gt 0 ]; then
    mkdir -p "$DOWNLOAD_DIR/Audio"
    for f in "${audio_files[@]}"; do
      [ -f "$f" ] && mv "$f" "$DOWNLOAD_DIR/Audio/" 2>/dev/null || true
    done
  fi

  # Metadata files
  local meta_files=("$DOWNLOAD_DIR"/*.json "$DOWNLOAD_DIR"/*.description "$DOWNLOAD_DIR"/*.jpg "$DOWNLOAD_DIR"/*.png "$DOWNLOAD_DIR"/*.webp "$DOWNLOAD_DIR"/*.vtt "$DOWNLOAD_DIR"/*.ass "$DOWNLOAD_DIR"/*.srt)
  if [ ${#meta_files[@]} -gt 0 ]; then
    mkdir -p "$DOWNLOAD_DIR/.metadata"
    for f in "${meta_files[@]}"; do
      [ -f "$f" ] && mv "$f" "$DOWNLOAD_DIR/.metadata/" 2>/dev/null || true
    done
  fi

  shopt -u nullglob
  log SUCCESS "Organization complete"
}

show_stats() {
  log INFO "Statistics:"
  if [ -d "$DOWNLOAD_DIR" ]; then
    local size
    size=$(du -sh "$DOWNLOAD_DIR" 2>/dev/null | cut -f1 || echo "unknown")
    log INFO "Total storage used: $size"
  fi
  if [ -d "$LOG_DIR" ]; then
    local log_count
    log_count=$(find "$LOG_DIR" -name '*.log' 2>/dev/null | wc -l || echo 0)
    log INFO "Log files: $log_count"
  fi
  if [ -d "$DOWNLOAD_DIR/Videos" ]; then
    local vcount
    vcount=$(find "$DOWNLOAD_DIR/Videos" -maxdepth 1 -type f 2>/dev/null | wc -l || echo 0)
    log INFO "Video files: $vcount"
  fi
  if [ -d "$DOWNLOAD_DIR/Audio" ]; then
    local acount
    acount=$(find "$DOWNLOAD_DIR/Audio" -maxdepth 1 -type f 2>/dev/null | wc -l || echo 0)
    log INFO "Audio files: $acount"
  fi
}

# ========================= HELP =========================
show_help() {
  echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║${NC}  ${WHITE}${BOLD}YTFAST ULTIMATE EDITION v4.0${NC}                                 ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${MAGENTA}The Most Powerful Downloader Ever Built${NC}                      ${CYAN}║${NC}"
  echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}\n"

  echo -e "${YELLOW}${BOLD}USAGE:${NC}"
  echo -e "  ./ytfast_v4.sh [OPTIONS] URL [URL2 ...]\n"

  echo -e "${YELLOW}${BOLD}EXAMPLES:${NC}"
  echo -e "  ${CYAN}Basic download:${NC}"
  echo -e "    ./ytfast_v4.sh --modes=720,mkv,opus \"https://youtu.be/ID\""
  echo -e "  ${CYAN}High quality:${NC}"
  echo -e "    ./ytfast_v4.sh --quality=1080 --container=mp4 \"URL\""
  echo -e "  ${CYAN}Audio only:${NC}"
  echo -e "    ./ytfast_v4.sh --modes=audio,opus \"URL\"\n"

  echo -e "${YELLOW}${BOLD}DOWNLOAD MODES:${NC}"
  echo -e "  ${GREEN}--modes=${NC}<list>        Comma-separated tokens"
  echo -e "                        ${CYAN}Quality:${NC} 144, 240, 360, 480, 720, 1080, 1440, 2160, 4320, best, max"
  echo -e "                        ${CYAN}Container:${NC} mp4, mkv, webm, avi"
  echo -e "                        ${CYAN}Audio:${NC} audio, mp3, m4a, opus, flac"
  echo -e "  ${GREEN}--quality=${NC}<Q>         Explicit quality override"
  echo -e "  ${GREEN}--container=${NC}<C>       Explicit container override"
  echo -e "  ${GREEN}--audio=${NC}<A>           Explicit audio format override\n"

  echo -e "${YELLOW}${BOLD}PLAYLIST CONTROL:${NC}"
  echo -e "  ${GREEN}--playlist${NC} <control>  Control playlist downloads:"
  echo -e "  ${GREEN}full, all${NC}             Download entire playlist"
  echo -e "  ${GREEN}single${NC}                Download single video only"
  echo -e "  ${GREEN}reverse${NC}               Download in reverse order"
  echo -e "  ${GREEN}random${NC}                Download in random order"
  echo -e "  ${GREEN}first=${NC}<N>             Download first N videos"
  echo -e "  ${GREEN}last=${NC}<N>              Download last N videos"
  echo -e "  ${GREEN}items=${NC}<list>          Download specific items (e.g., 1,3,5-10)"
  echo -e "  ${GREEN}range=${NC}<N-M>           Download range of videos (e.g., 5-15)"
  echo -e "  ${GREEN}skip=${NC}<N>              Skip first N videos\n"

  echo -e "${YELLOW}${BOLD}PERFORMANCE OPTIONS:${NC}"
  echo -e "  ${GREEN}-s, --speed${NC} <N>       Concurrent fragments (4/8/12/16/24/32/48/64, default: 24)"
  echo -e "  ${GREEN}-p, --parallel${NC}        Enable parallel downloads"
  echo -e "  ${GREEN}-j, --jobs${NC} <N>        Max parallel jobs (default: 4)"
  echo -e "  ${GREEN}--limit-rate${NC} <SIZE>   Limit download rate (e.g., 5M, 500K)\n"

  echo -e "${YELLOW}${BOLD}OUTPUT OPTIONS:${NC}"
  echo -e "  ${GREEN}-d, --dir${NC} <PATH>      Set download directory"
  echo -e "  ${GREEN}--rename${NC}              Auto-clean filenames after download"
  echo -e "  ${GREEN}--no-organize${NC}         Skip folder organization"
  echo -e "  ${GREEN}--thumbnail${NC}           Download and embed thumbnails"
  echo -e "  ${GREEN}--subtitle${NC}            Download subtitles (en,es,fr,de,ar)"
  echo -e "  ${GREEN}--no-metadata${NC}         Skip metadata embedding\n"

  echo -e "${YELLOW}${BOLD}ADVANCED OPTIONS:${NC}"
  echo -e "  ${GREEN}--cookies${NC} <FILE>      Netscape cookies file (for auth-gated content)"
  echo -e "  ${GREEN}--proxy${NC} <URL>         Proxy server URL"
  echo -e "  ${GREEN}--dry-run${NC}             Print yt-dlp command without executing"
  echo -e "  ${GREEN}--stats${NC}               Show storage statistics and exit\n"

  echo -e "${YELLOW}${BOLD}GENERAL OPTIONS:${NC}"
  echo -e "  ${GREEN}-v, --verbose${NC}         Verbose output"
  echo -e "  ${GREEN}-q, --quiet${NC}           Quiet mode"
  echo -e "  ${GREEN}-h, --help${NC}            Show this help message\n"

  echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║${NC}  ${MAGENTA}Pro Tip:${NC} Combine options for maximum power!                  ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ./ytfast_v4.sh -s 32 -p --quality=1080 --container=mkv URL   ${CYAN}║${NC}"
  echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
}

# ========================= MAIN =========================
main() {
  local urls=()
  local playlist_control="single" # safe default: single video unless --playlist used

  mkdir -p "${YTFAST_DIR:-$HOME/Downloads/YTFAST}" 2>/dev/null || true
  if [ -f "$CONFIG_FILE" ]; then
    # shellcheck disable=SC1090
    source "$CONFIG_FILE" 2>/dev/null || true
  fi

  # Parse CLI args (these now override config file values loaded above)
  while [[ $# -gt 0 ]]; do
    case "$1" in
    -h | --help)
      show_help
      exit 0
      ;;
    -s | --speed)
      if [[ "${2:-}" =~ ^[0-9]+$ ]]; then
        SPEED=$(validate_speed "$2")
        shift 2
      else
        log WARN "--speed requires a numeric value (4/8/12/16/24/32/48/64). Using default: $DEFAULT_SPEED"
        shift
      fi
      ;;
    -p | --parallel)
      PARALLEL_MODE=true
      shift
      ;;
    -j | --jobs)
      if [[ "${2:-}" =~ ^[0-9]+$ ]]; then
        MAX_PARALLEL_JOBS="$2"
        shift 2
      else
        log WARN "Invalid --jobs value: ${2:-missing}. Using default: 4"
        shift
      fi
      ;;
    -v | --verbose)
      VERBOSE=true
      QUIET=false
      shift
      ;;
    -q | --quiet)
      QUIET=true
      VERBOSE=false
      shift
      ;;
    -d | --dir)
      DOWNLOAD_DIR="$2"
      LOG_DIR="${DOWNLOAD_DIR}/.logs"
      CONFIG_FILE="${DOWNLOAD_DIR}/.ytfast.conf"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --no-organize)
      ORGANIZE=false
      shift
      ;;
    --no-metadata)
      METADATA=false
      shift
      ;;
    --thumbnail)
      THUMBNAIL=true
      shift
      ;;
    --subtitle)
      SUBTITLE=true
      shift
      ;;
    --cookies)
      COOKIES_FILE="$2"
      shift 2
      ;;
    --proxy)
      PROXY="$2"
      shift 2
      ;;
    --limit-rate)
      RATE_LIMIT="$2"
      shift 2
      ;;
    --rename)
      AUTO_RENAME=true
      shift
      ;;
    --stats)
      init_environment
      activate_env
      show_stats
      exit 0
      ;;
    --playlist)
      playlist_control="$2"
      shift 2
      ;;
    --modes=*)
      MODES_RAW="${1#--modes=}"
      shift
      ;;
    --quality=*)
      QUALITY="${1#--quality=}"
      shift
      ;;
    --container=*)
      CONTAINER="${1#--container=}"
      shift
      ;;
    --audio=*)
      AUDIO_OPT="${1#--audio=}"
      shift
      ;;
    --*)
      log WARN "Unknown option: $1 (ignoring)"
      shift
      ;;
    *)
      urls+=("$1")
      shift
      ;;
    esac
  done

  [ ${#urls[@]} -gt 0 ] || abort "No URL specified. Use --help for usage."

  banner
  init_environment
  activate_env
  check_dependencies

  apply_modes_and_flags
  SPEED=$(validate_speed "$SPEED")

  if ! [[ "$MAX_PARALLEL_JOBS" =~ ^[0-9]+$ ]] || [ "$MAX_PARALLEL_JOBS" -lt 1 ]; then
    log WARN "Invalid MAX_PARALLEL_JOBS, using default (4)"
    MAX_PARALLEL_JOBS=4
  fi

  CONTROL_FLAGS=$(parse_playlist_control "$playlist_control")

  # Dispatch: batch file, parallel, or sequential
  if [[ "${urls[0]}" == *.txt ]] && [ ${#urls[@]} -eq 1 ]; then
    process_batch_file "${urls[0]}"
  elif [ "$PARALLEL_MODE" = true ] && [ ${#urls[@]} -gt 1 ]; then
    process_parallel "${urls[@]}"
  else
    for url in "${urls[@]}"; do
      validate_url "$url"
      get_video_info "$url" || true
      execute_download_single "$url" "$CONTROL_FLAGS" || true
    done
  fi

  [ "$AUTO_RENAME" = true ] && auto_rename "$DOWNLOAD_DIR"
  [ "$ORGANIZE" = true ] && organize_downloads

  log SUCCESS "All operations completed"
  show_stats
}

main "$@"
