"""Rights-gated video URL import with a small, auditable resolver boundary.

The resolver accepts public HTTP(S) media and a short allowlist of platform
pages. It never persists credentials, cookies, signed URL parameters, or other
sensitive query values in receipts; a stable public content identifier may be
retained. Direct downloads validate every redirect against public-network
address rules before reading bytes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
from http.client import HTTPConnection, HTTPResponse, HTTPSConnection
import importlib.util
import ipaddress
import mimetypes
from pathlib import Path
import re
import socket
import time
from typing import Any, Iterator
from urllib.parse import parse_qsl, unquote, urlencode, urljoin, urlsplit, urlunsplit


DEFAULT_MAX_SOURCE_BYTES = 1024 * 1024 * 1024
MAX_SOURCE_URL_LENGTH = 4096
MAX_REDIRECTS = 5
MAX_PLATFORM_DURATION_SECONDS = 4 * 60 * 60
MAX_PLATFORM_DOWNLOAD_SECONDS = 30 * 60
MAX_PLATFORM_SUBTITLE_BYTES = 5 * 1024 * 1024
VIDEO_SUFFIXES = {
    ".3gp",
    ".avi",
    ".flv",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".webm",
    ".wmv",
}
PLATFORM_HOSTS = {
    "youtube": ("youtube.com", "youtu.be"),
    "bilibili": ("bilibili.com", "b23.tv"),
    "douyin": ("douyin.com", "iesdouyin.com"),
}


class SourceImportError(ValueError):
    """Raised when a URL cannot safely become a local media source."""


@dataclass(frozen=True, slots=True)
class VideoSourceDescriptor:
    source_kind: str
    platform: str
    display_url: str
    transport_secure: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_kind": self.source_kind,
            "platform": self.platform,
            "display_url": self.display_url,
            "transport_secure": self.transport_secure,
        }


@dataclass(frozen=True, slots=True)
class VideoSourceImport:
    source_path: Path
    metadata: dict[str, Any]


@dataclass(slots=True)
class _DownloadBudget:
    """Shared byte and wall-clock budget for one platform import."""

    max_bytes: int
    deadline: float
    downloaded_by_stream: dict[str, int]

    @classmethod
    def start(cls, max_bytes: int) -> "_DownloadBudget":
        return cls(
            max_bytes=max_bytes,
            deadline=time.monotonic() + MAX_PLATFORM_DOWNLOAD_SECONDS,
            downloaded_by_stream={},
        )

    def check(self, stream: str, downloaded_bytes: int) -> None:
        if time.monotonic() > self.deadline:
            raise SourceImportError("平台视频下载或合并超过 30 分钟原型时限。")
        self.downloaded_by_stream[stream] = max(0, int(downloaded_bytes))
        if sum(self.downloaded_by_stream.values()) > self.max_bytes:
            raise SourceImportError("平台音视频下载合计超过本次工作区预算。")

    def progress_hook(self, stream: str):
        def hook(status: dict[str, Any]) -> None:
            if status.get("status") not in {"downloading", "finished"}:
                return
            downloaded = status.get("downloaded_bytes")
            if downloaded is None:
                downloaded = status.get("total_bytes") or status.get("total_bytes_estimate") or 0
            self.check(stream, int(downloaded or 0))

        return hook


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _matching_platform(hostname: str) -> str | None:
    host = hostname.lower().rstrip(".")
    for platform, suffixes in PLATFORM_HOSTS.items():
        if any(host == suffix or host.endswith(f".{suffix}") for suffix in suffixes):
            return platform
    return None


def _validated_platform_duration_seconds(metadata: dict[str, Any]) -> float:
    """Require a finite, declared VOD duration before downloading media.

    yt-dlp metadata resolution happens before the download budget starts. A
    missing duration must therefore fail closed instead of silently bypassing
    the four-hour guard, and live/upcoming streams are outside this prototype.
    """

    live_status = str(metadata.get("live_status") or "").lower()
    if metadata.get("is_live") is True or live_status in {"is_live", "is_upcoming"}:
        raise SourceImportError("当前原型不支持直播或尚未结束的平台视频。")
    duration = metadata.get("duration")
    if duration is None:
        raise SourceImportError("平台视频未提供可确认的时长；为避免无界下载，当前原型拒绝导入。")
    try:
        duration_seconds = float(duration)
    except (TypeError, ValueError) as exc:
        raise SourceImportError("平台视频时长无效，当前原型拒绝导入。") from exc
    if not 0 < duration_seconds <= MAX_PLATFORM_DURATION_SECONDS:
        if duration_seconds > MAX_PLATFORM_DURATION_SECONDS:
            raise SourceImportError("平台视频超过 4 小时原型时长限制。")
        raise SourceImportError("平台视频时长无效，当前原型拒绝导入。")
    return duration_seconds


def _display_url(value: str, platform: str | None = None) -> str:
    parsed = urlsplit(value)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    origin = urlunsplit((scheme, netloc, "/", "", ""))
    if platform == "youtube" and parsed.path.rstrip("/") == "/watch":
        video_id = next((item for key, item in parse_qsl(parsed.query) if key == "v"), None)
        if video_id and re.fullmatch(r"[A-Za-z0-9_-]{6,32}", video_id):
            return urlunsplit((scheme, netloc, "/watch", urlencode({"v": video_id}), ""))
    if platform == "youtube" and parsed.hostname and parsed.hostname.lower().rstrip(".") == "youtu.be":
        video_id = parsed.path.strip("/").split("/", 1)[0]
        if re.fullmatch(r"[A-Za-z0-9_-]{6,32}", video_id):
            return urlunsplit((scheme, netloc, f"/{video_id}", "", ""))
    if platform == "bilibili":
        match = re.fullmatch(r"/video/(BV[A-Za-z0-9]+|av[0-9]+)/?", parsed.path, re.IGNORECASE)
        if match:
            return urlunsplit((scheme, netloc, f"/video/{match.group(1)}", "", ""))
    if platform == "douyin":
        match = re.fullmatch(r"/video/([0-9]+)/?", parsed.path)
        if match:
            return urlunsplit((scheme, netloc, f"/video/{match.group(1)}", "", ""))
    # Generic paths can contain bearer credentials. Persist only the origin;
    # allowlisted platform identities above are the sole path exceptions.
    return origin


def classify_video_url(value: str) -> VideoSourceDescriptor:
    candidate = value.strip()
    if not candidate:
        raise SourceImportError("请输入视频链接。")
    if len(candidate) > MAX_SOURCE_URL_LENGTH:
        raise SourceImportError("视频链接过长；请移除无关追踪参数后重试。")
    parsed = urlsplit(candidate)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise SourceImportError("只支持 HTTP(S) 视频链接。")
    if not parsed.hostname:
        raise SourceImportError("视频链接缺少有效域名。")
    if parsed.username or parsed.password:
        raise SourceImportError("链接不能包含用户名或密码。")
    platform = _matching_platform(parsed.hostname)
    source_kind = "platform_url" if platform else "direct_url"
    return VideoSourceDescriptor(
        source_kind=source_kind,
        platform=platform or "direct",
        display_url=_display_url(candidate, platform),
        transport_secure=parsed.scheme.lower() == "https",
    )


def _assert_public_destination(value: str) -> tuple[str, ...]:
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise SourceImportError("链接或重定向地址不是有效 HTTP(S) 地址。")
    if parsed.username or parsed.password:
        raise SourceImportError("链接或重定向地址不能包含用户名或密码。")
    try:
        addresses = socket.getaddrinfo(
            parsed.hostname,
            parsed.port or (443 if parsed.scheme.lower() == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise SourceImportError("无法解析视频链接域名。") from exc
    if not addresses:
        raise SourceImportError("视频链接域名没有可用网络地址。")
    public_addresses: list[str] = []
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0].split("%", 1)[0])
        if not ip.is_global:
            raise SourceImportError("出于安全原因，链接不能指向本机、内网或保留地址。")
        rendered = str(ip)
        if rendered not in public_addresses:
            public_addresses.append(rendered)
    return tuple(public_addresses)


class _PinnedHTTPConnection(HTTPConnection):
    def __init__(self, host: str, port: int, pinned_ip: str, timeout: float) -> None:
        super().__init__(host, port=port, timeout=timeout)
        self._pinned_ip = pinned_ip

    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self._pinned_ip, self.port),
            self.timeout,
            self.source_address,
        )


class _PinnedHTTPSConnection(HTTPSConnection):
    def __init__(self, host: str, port: int, pinned_ip: str, timeout: float) -> None:
        super().__init__(host, port=port, timeout=timeout)
        self._pinned_ip = pinned_ip

    def connect(self) -> None:
        raw_socket = socket.create_connection(
            (self._pinned_ip, self.port),
            self.timeout,
            self.source_address,
        )
        try:
            self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)
        except Exception:
            raw_socket.close()
            raise


class _PinnedResponse:
    def __init__(self, response: HTTPResponse, connection: HTTPConnection) -> None:
        self._response = response
        self._connection = connection
        self.headers = response.headers

    def read(self, size: int = -1) -> bytes:
        return self._response.read(size)

    def close(self) -> None:
        try:
            self._response.close()
        finally:
            self._connection.close()


def _open_pinned_connection(value: str, timeout_seconds: float) -> tuple[Any, HTTPResponse]:
    parsed = urlsplit(value)
    hostname = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    addresses = _assert_public_destination(value)
    target = urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
    last_error: OSError | None = None
    for address in addresses:
        connection: HTTPConnection
        if parsed.scheme.lower() == "https":
            connection = _PinnedHTTPSConnection(hostname, port, address, timeout_seconds)
        else:
            connection = _PinnedHTTPConnection(hostname, port, address, timeout_seconds)
        try:
            connection.request(
                "GET",
                target,
                headers={
                    "Accept": "video/*,application/octet-stream;q=0.8,*/*;q=0.2",
                    "User-Agent": "AudienceMirror/0.2 (+https://github.com/YunyueLi/audience-mirror)",
                },
            )
            return connection, connection.getresponse()
        except OSError as exc:
            last_error = exc
            connection.close()
    raise SourceImportError("无法连接视频链接；请检查公开访问权限和网络状态。") from last_error


def _open_public_url(value: str, *, timeout_seconds: float = 30.0) -> tuple[Any, str, list[str]]:
    current = value
    redirects: list[str] = []
    for _ in range(MAX_REDIRECTS + 1):
        connection, response = _open_pinned_connection(current, timeout_seconds)
        if response.status in {301, 302, 303, 307, 308}:
            location = response.headers.get("Location")
            response.close()
            connection.close()
            if not location:
                raise SourceImportError("视频链接返回了没有目标地址的重定向。")
            current = urljoin(current, location)
            redirects.append(_display_url(current))
            continue
        if not 200 <= response.status < 300:
            status = response.status
            response.close()
            connection.close()
            raise SourceImportError(f"视频链接返回 HTTP {status}。")
        return _PinnedResponse(response, connection), current, redirects
    raise SourceImportError(f"视频链接重定向超过 {MAX_REDIRECTS} 次。")


def _safe_filename(final_url: str, content_type: str) -> str:
    raw_name = Path(unquote(urlsplit(final_url).path)).name
    suffix = Path(raw_name).suffix.lower()
    if suffix not in VIDEO_SUFFIXES:
        guessed = mimetypes.guess_extension(content_type) if content_type else None
        suffix = guessed.lower() if guessed and guessed.lower() in VIDEO_SUFFIXES else ".mp4"
    return f"linked-video{suffix}"


def _download_direct(
    value: str,
    output_directory: Path,
    *,
    max_bytes: int,
) -> VideoSourceImport:
    response, final_url, redirects = _open_public_url(value)
    try:
        content_type = response.headers.get_content_type().lower()
        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                if int(content_length) > max_bytes:
                    raise SourceImportError("远程视频超过 1 GiB 原型限制。")
            except ValueError:
                pass
        suffix = Path(urlsplit(final_url).path).suffix.lower()
        if content_type.startswith("text/") or content_type in {"application/json", "application/xml"}:
            raise SourceImportError("该地址返回的是页面或结构化文本，不是视频文件。")
        if not content_type.startswith("video/") and content_type != "application/octet-stream" and suffix not in VIDEO_SUFFIXES:
            raise SourceImportError("该地址没有返回视频文件；平台页面需要使用当前支持的平台链接。")
        output_directory.mkdir(parents=True, exist_ok=True)
        target = output_directory / _safe_filename(final_url, content_type)
        partial = target.with_suffix(f"{target.suffix}.part")
        total = 0
        try:
            with partial.open("wb") as stream:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_bytes:
                        raise SourceImportError("远程视频超过 1 GiB 原型限制。")
                    stream.write(chunk)
            if total == 0:
                raise SourceImportError("视频链接返回了空文件。")
            partial.replace(target)
        except Exception:
            partial.unlink(missing_ok=True)
            raise
    finally:
        response.close()
    descriptor = classify_video_url(value)
    return VideoSourceImport(
        source_path=target,
        metadata={
            **descriptor.to_dict(),
            "retrieval_method": "streamed_http",
            "retrieved_at": _utc_now(),
            "resolved_url": _display_url(final_url),
            "redirect_chain": redirects,
            "content_type": content_type,
            "downloaded_bytes": total,
            "title": target.stem,
            "sensitive_query_parameters_persisted": False,
            "public_content_identifier_persisted": False,
        },
    )


class _QuietYtDlpLogger:
    def debug(self, message: str) -> None:
        return None

    def warning(self, message: str) -> None:
        return None

    def error(self, message: str) -> None:
        return None


def _format_size(format_info: dict[str, Any]) -> int | None:
    value = format_info.get("filesize") or format_info.get("filesize_approx")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _choose_platform_subtitle(
    subtitles: dict[str, Any],
    *,
    preferred_languages: tuple[str, ...] = ("zh-Hans", "zh-Hant", "zh", "en"),
) -> tuple[str, dict[str, Any]] | None:
    """Choose one bounded manual WebVTT track without invoking auto-translation.

    Platform captions are useful evidence, but they are not equivalent to ASR
    and their quality is not guaranteed. The prototype therefore prefers a
    single manually supplied track and records its language explicitly.
    """

    candidates: dict[str, dict[str, Any]] = {}
    for language, tracks in subtitles.items():
        if not isinstance(language, str) or not isinstance(tracks, list):
            continue
        vtt = next(
            (
                track
                for track in tracks
                if isinstance(track, dict)
                and track.get("ext") == "vtt"
                and isinstance(track.get("url"), str)
            ),
            None,
        )
        if vtt is not None:
            candidates[language] = vtt
    if not candidates:
        return None
    for preferred in preferred_languages:
        if preferred in candidates:
            return preferred, candidates[preferred]
        language = next(
            (name for name in sorted(candidates) if name.lower().startswith(f"{preferred.lower()}-")),
            None,
        )
        if language is not None:
            return language, candidates[language]
    language = sorted(candidates)[0]
    return language, candidates[language]


def _download_optional_platform_subtitle(
    metadata: dict[str, Any],
    output_directory: Path,
) -> dict[str, Any] | None:
    selected = _choose_platform_subtitle(metadata.get("subtitles") or {})
    if selected is None:
        return None
    language, track = selected
    subtitle_url = str(track["url"])
    response, _, _ = _open_public_url(subtitle_url, timeout_seconds=30.0)
    subtitle_directory = output_directory / "subtitles"
    subtitle_directory.mkdir(parents=True, exist_ok=True)
    safe_language = re.sub(r"[^A-Za-z0-9._-]", "_", language)[:80] or "und"
    target = subtitle_directory / f"{safe_language}.vtt"
    partial = target.with_suffix(".vtt.part")
    total = 0
    digest = hashlib.sha256()
    try:
        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                if int(content_length) > MAX_PLATFORM_SUBTITLE_BYTES:
                    raise SourceImportError("平台字幕超过 5 MiB 原型限制。")
            except ValueError:
                pass
        with partial.open("wb") as stream:
            while True:
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_PLATFORM_SUBTITLE_BYTES:
                    raise SourceImportError("平台字幕超过 5 MiB 原型限制。")
                digest.update(chunk)
                stream.write(chunk)
        if total == 0:
            raise SourceImportError("平台字幕为空。")
        partial.replace(target)
    except Exception:
        partial.unlink(missing_ok=True)
        target.unlink(missing_ok=True)
        raise
    finally:
        response.close()
    return {
        "language": language,
        "format": "webvtt",
        "source_type": "platform_manual_caption",
        "machine_generated": False,
        "relative_path": str(target.relative_to(output_directory)),
        "content_hash": digest.hexdigest(),
        "downloaded_bytes": total,
    }


def _choose_platform_formats(
    formats: list[dict[str, Any]],
    *,
    max_bytes: int,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Choose a bounded progressive format or a video/audio pair.

    Platform adapters deliberately cap the workbench ingest copy at 720p. The
    product evaluates temporal comprehension rather than archival quality, and
    this bound keeps download, decode, model-upload, and storage costs visible.
    """

    def is_video(item: dict[str, Any]) -> bool:
        return item.get("vcodec") not in {None, "none"}

    def is_audio(item: dict[str, Any]) -> bool:
        return item.get("acodec") not in {None, "none"}

    def within_resolution(item: dict[str, Any]) -> bool:
        height = item.get("height")
        return height is None or int(height) <= 720

    def video_score(item: dict[str, Any]) -> tuple[int, int, int, int, float]:
        protocol = str(item.get("protocol") or "")
        return (
            1 if item.get("ext") == "mp4" else 0,
            int(item.get("height") or 0),
            1 if _format_size(item) is not None else 0,
            1 if protocol in {"http", "https"} else 0,
            float(item.get("tbr") or item.get("vbr") or 0),
        )

    progressive = [
        item
        for item in formats
        if is_video(item)
        and is_audio(item)
        and within_resolution(item)
        and (_format_size(item) is None or _format_size(item) <= max_bytes)
    ]
    if progressive:
        return max(progressive, key=video_score), None

    audio_candidates = [
        item
        for item in formats
        if not is_video(item)
        and is_audio(item)
        and (_format_size(item) is None or _format_size(item) <= max_bytes)
    ]
    video_candidates = [
        item
        for item in formats
        if is_video(item)
        and not is_audio(item)
        and within_resolution(item)
        and (_format_size(item) is None or _format_size(item) <= max_bytes)
    ]
    if not video_candidates or not audio_candidates:
        raise SourceImportError("平台页面没有可读取且满足原型限制的音视频格式。")

    def audio_score(item: dict[str, Any]) -> tuple[int, int, int, float]:
        return (
            1 if item.get("ext") in {"m4a", "mp4"} else 0,
            0 if "drc" in str(item.get("format_id") or "").lower() else 1,
            1 if _format_size(item) is not None else 0,
            float(item.get("abr") or item.get("tbr") or 0),
        )

    audio = max(audio_candidates, key=audio_score)
    audio_size = _format_size(audio) or 0
    bounded_videos = [
        item
        for item in video_candidates
        if _format_size(item) is None or (_format_size(item) or 0) + audio_size <= max_bytes
    ]
    if not bounded_videos:
        raise SourceImportError("平台视频与音频合计超过 1 GiB 原型限制。")
    return max(bounded_videos, key=video_score), audio


def _download_platform_format(
    yt_dlp_module: Any,
    value: str,
    output_directory: Path,
    *,
    format_id: str,
    prefix: str,
    max_bytes: int,
    budget: _DownloadBudget,
) -> tuple[Path, dict[str, Any]]:
    options = {
        "format": format_id,
        "outtmpl": str(output_directory / f"{prefix}.%(ext)s"),
        "noplaylist": True,
        "max_filesize": max_bytes,
        "socket_timeout": 30,
        "retries": 2,
        "fragment_retries": 2,
        "overwrites": True,
        "quiet": True,
        "no_warnings": True,
        "logger": _QuietYtDlpLogger(),
        "progress_hooks": [budget.progress_hook(prefix)],
    }
    with yt_dlp_module.YoutubeDL(options) as downloader:
        info = downloader.extract_info(value, download=True)
    candidates = sorted(
        (
            path
            for path in output_directory.glob(f"{prefix}.*")
            if path.is_file() and not path.name.endswith((".part", ".ytdl"))
        ),
        key=lambda path: path.stat().st_size,
        reverse=True,
    )
    if not candidates:
        raise SourceImportError("平台解析器没有生成可读取的媒体文件。")
    result = candidates[0]
    if result.stat().st_size <= 0 or result.stat().st_size > max_bytes:
        result.unlink(missing_ok=True)
        raise SourceImportError("平台媒体为空或超过 1 GiB 原型限制。")
    budget.check(prefix, result.stat().st_size)
    return result, info


def _next_timestamped_packet(packets: Iterator[Any]) -> Any | None:
    for packet in packets:
        if packet.dts is not None:
            return packet
    return None


def _mux_platform_streams(
    video_path: Path,
    audio_path: Path,
    target: Path,
    *,
    max_workspace_bytes: int,
    deadline: float,
) -> None:
    """Remux independently downloaded streams with PyAV, without system ffmpeg."""

    try:
        import av  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SourceImportError("合并平台音视频需要安装 media extra（PyAV）。") from exc

    partial = target.with_suffix(f"{target.suffix}.part")
    try:
        with (
            av.open(str(video_path)) as video_input,
            av.open(str(audio_path)) as audio_input,
            av.open(str(partial), mode="w", format="mp4") as output,
        ):
            if not video_input.streams.video or not audio_input.streams.audio:
                raise SourceImportError("平台解析结果缺少视频或音频轨道。")
            video_stream = video_input.streams.video[0]
            audio_stream = audio_input.streams.audio[0]
            output_video = output.add_stream_from_template(video_stream)
            output_audio = output.add_stream_from_template(audio_stream)
            video_packets = iter(video_input.demux(video_stream))
            audio_packets = iter(audio_input.demux(audio_stream))
            video_packet = _next_timestamped_packet(video_packets)
            audio_packet = _next_timestamped_packet(audio_packets)
            packet_count = 0
            while video_packet is not None or audio_packet is not None:
                packet_count += 1
                if packet_count % 128 == 0:
                    if time.monotonic() > deadline:
                        raise SourceImportError("平台音视频合并超过 30 分钟原型时限。")
                    workspace_bytes = sum(
                        path.stat().st_size for path in (video_path, audio_path, partial) if path.exists()
                    )
                    if workspace_bytes > max_workspace_bytes:
                        raise SourceImportError("平台音视频合并超过本次工作区预算。")
                video_time = (
                    float(video_packet.dts * video_packet.time_base)
                    if video_packet is not None
                    else float("inf")
                )
                audio_time = (
                    float(audio_packet.dts * audio_packet.time_base)
                    if audio_packet is not None
                    else float("inf")
                )
                if video_time <= audio_time:
                    video_packet.stream = output_video
                    output.mux(video_packet)
                    video_packet = _next_timestamped_packet(video_packets)
                else:
                    audio_packet.stream = output_audio
                    output.mux(audio_packet)
                    audio_packet = _next_timestamped_packet(audio_packets)
        workspace_bytes = sum(
            path.stat().st_size for path in (video_path, audio_path, partial) if path.exists()
        )
        if workspace_bytes > max_workspace_bytes:
            raise SourceImportError("平台音视频合并超过本次工作区预算。")
        partial.replace(target)
    except Exception:
        partial.unlink(missing_ok=True)
        raise


def _clear_platform_temporary_files(output_directory: Path) -> None:
    for pattern in ("source-video.*", "source-audio.*", "source*.part", "source*.ytdl"):
        for temporary_path in output_directory.glob(pattern):
            if temporary_path.is_file():
                temporary_path.unlink(missing_ok=True)


def _download_platform(
    value: str,
    descriptor: VideoSourceDescriptor,
    output_directory: Path,
    *,
    max_bytes: int,
) -> VideoSourceImport:
    if importlib.util.find_spec("yt_dlp") is None:
        raise SourceImportError(
            "平台链接解析器尚未安装；请安装 web extra，或改用直接视频链接／本地文件。"
        )
    import yt_dlp  # type: ignore[import-not-found]

    # Platform input is restricted to a small hostname allowlist and must
    # resolve publicly before yt-dlp sees it. Selected media endpoints are
    # checked again below; unlike direct imports, yt-dlp itself is still an
    # external network trust boundary and must not run in an exposed service.
    _assert_public_destination(value)
    output_directory.mkdir(parents=True, exist_ok=True)
    metadata_options = {
        "noplaylist": True,
        "socket_timeout": 30,
        "retries": 2,
        "fragment_retries": 2,
        "quiet": True,
        "no_warnings": True,
        "logger": _QuietYtDlpLogger(),
    }
    try:
        with yt_dlp.YoutubeDL(metadata_options) as resolver:
            metadata = resolver.extract_info(value, download=False)
        duration_seconds = _validated_platform_duration_seconds(metadata)
        # A split download temporarily stores video, audio, and the remuxed
        # output together. Reserve half the workspace for the final mux copy.
        format_budget = max(1, max_bytes // 2)
        formats = list(metadata.get("formats") or [])
        video_format, audio_format = _choose_platform_formats(formats, max_bytes=max_bytes)
        if audio_format is not None:
            video_format, audio_format = _choose_platform_formats(formats, max_bytes=format_budget)
        for selected_format in (video_format, audio_format):
            media_url = selected_format.get("url") if selected_format else None
            if media_url:
                _assert_public_destination(str(media_url))
        if audio_format is None:
            budget = _DownloadBudget.start(max_bytes)
            source_path, info = _download_platform_format(
                yt_dlp,
                value,
                output_directory,
                format_id=str(video_format["format_id"]),
                prefix="source",
                max_bytes=max_bytes,
                budget=budget,
            )
            retrieval_method = "yt_dlp_progressive_adapter"
        else:
            budget = _DownloadBudget.start(format_budget)
            video_path, info = _download_platform_format(
                yt_dlp,
                value,
                output_directory,
                format_id=str(video_format["format_id"]),
                prefix="source-video",
                max_bytes=format_budget,
                budget=budget,
            )
            audio_path, _ = _download_platform_format(
                yt_dlp,
                value,
                output_directory,
                format_id=str(audio_format["format_id"]),
                prefix="source-audio",
                max_bytes=format_budget,
                budget=budget,
            )
            source_path = output_directory / "source.mp4"
            _mux_platform_streams(
                video_path,
                audio_path,
                source_path,
                max_workspace_bytes=max_bytes,
                deadline=budget.deadline,
            )
            _clear_platform_temporary_files(output_directory)
            retrieval_method = "yt_dlp_split_streams_pyav_mux"
    except Exception as exc:
        _clear_platform_temporary_files(output_directory)
        if isinstance(exc, SourceImportError):
            raise
        raise SourceImportError(
            "平台链接解析失败。链接可能需要登录、Cookie、地区授权或更高访问权限；"
            "请改用可直接访问的公开链接，或上传有权使用的源文件。"
        ) from exc
    downloaded_bytes = source_path.stat().st_size
    if downloaded_bytes <= 0 or downloaded_bytes > max_bytes:
        source_path.unlink(missing_ok=True)
        raise SourceImportError("平台视频为空或超过 1 GiB 原型限制。")
    subtitle = None
    try:
        subtitle = _download_optional_platform_subtitle(metadata, output_directory)
    except Exception:
        # Captions are an optional evidence layer. A missing, expired, or
        # unsupported caption endpoint must not invalidate a valid media import.
        subtitle = None
    return VideoSourceImport(
        source_path=source_path,
        metadata={
            **descriptor.to_dict(),
            "retrieval_method": retrieval_method,
            "retrieved_at": _utc_now(),
            "resolved_url": _display_url(str(info.get("webpage_url") or value), descriptor.platform),
            "redirect_chain": [],
            "content_type": mimetypes.guess_type(source_path.name)[0] or "application/octet-stream",
            "downloaded_bytes": downloaded_bytes,
            "title": str(metadata.get("title") or info.get("title") or source_path.stem)[:200],
            "duration_ms": int(float(metadata["duration"]) * 1000) if metadata.get("duration") is not None else None,
            "sensitive_query_parameters_persisted": False,
            "public_content_identifier_persisted": True,
            "selected_video_format": str(video_format.get("format_id")),
            "selected_audio_format": str(audio_format.get("format_id")) if audio_format else None,
            "ingest_height": int(video_format.get("height") or 0) or None,
            "subtitle": subtitle,
        },
    )


def import_video_url(
    value: str,
    output_directory: str | Path,
    *,
    max_bytes: int = DEFAULT_MAX_SOURCE_BYTES,
) -> VideoSourceImport:
    """Resolve a rights-confirmed public URL into a local video artifact."""

    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")
    descriptor = classify_video_url(value)
    output_path = Path(output_directory).expanduser().resolve()
    if descriptor.source_kind == "platform_url":
        return _download_platform(value, descriptor, output_path, max_bytes=max_bytes)
    return _download_direct(value, output_path, max_bytes=max_bytes)
