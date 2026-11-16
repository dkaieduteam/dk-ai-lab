// Case_배포용_v2 · config.mjs
// .env 로드 + 검증. 설계 명세 §2 기준.
// 검증 실패 시 상세 메시지와 함께 Error throw (server.mjs가 로그 기록 후 종료).
// .env는 Starter_kit/ 루트에 위치 — server.mjs의 cwd(naverworks-mail-mcp/)와 다르므로 경로 명시.

import dotenv from "dotenv";
import { fileURLToPath } from "node:url";
import { resolve, dirname } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const STARTER_KIT_ROOT = resolve(dirname(__filename), "..", "..");
dotenv.config({ path: resolve(STARTER_KIT_ROOT, ".env") });

// ---------------------------------------------------------------
// 허용 리스트·범위 (코드 하드코딩 — 가드레일 축)
// ---------------------------------------------------------------
const ALLOWED_FOLDERS = ["AI메일함", "[AI교육_실습]"];
const ALLOWED_FOLDER_PATTERNS = [/^AI/, /^\[AI/];
const ALLOWED_HOSTS = ["imap.worksmobile.com"];
const ALLOWED_PORTS = [993];
const RANGE_MAX_COUNT = { min: 1, max: 100 };
const RANGE_DAYS = { min: 1, max: 60 };
const RANGE_MAX_MESSAGE_MB = { min: 1, max: 50 };

// ---------------------------------------------------------------
// 패턴
// ---------------------------------------------------------------
const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const TUNNEL_ID_PATTERN = /^tunnel_[a-z0-9]{32}$/;

// ---------------------------------------------------------------
// 검증
// ---------------------------------------------------------------
function validateEnv() {
  const errors = [];

  // 인증
  const nwId = (process.env.NW_ID || "").trim();
  if (!nwId) {
    errors.push("NW_ID: empty");
  } else if (!EMAIL_PATTERN.test(nwId)) {
    errors.push(`NW_ID: invalid email format (${nwId})`);
  }

  const nwPw = process.env.NW_PW ?? "";
  if (!nwPw) {
    errors.push("NW_PW: empty");
  }

  const tunnelId = (process.env.TUNNEL_ID || "").trim();
  if (!tunnelId) {
    errors.push("TUNNEL_ID: empty");
  } else if (!TUNNEL_ID_PATTERN.test(tunnelId)) {
    errors.push("TUNNEL_ID: invalid format (expected tunnel_ + 32 lowercase/digit chars, total 39)");
  }

  const apiKey = (process.env.API_KEY || "").trim();
  if (!apiKey) {
    errors.push("API_KEY: empty");
  } else if (!apiKey.startsWith("sk-")) {
    errors.push("API_KEY: must start with sk-");
  }

  // IMAP
  const imapHost = (process.env.NW_IMAP_HOST || "").trim();
  if (!ALLOWED_HOSTS.includes(imapHost)) {
    errors.push(`NW_IMAP_HOST=${imapHost || "(empty)"} not allowed (allowed: ${ALLOWED_HOSTS.join(", ")})`);
  }

  const imapPortRaw = (process.env.NW_IMAP_PORT || "").trim();
  const imapPort = Number.parseInt(imapPortRaw, 10);
  if (!Number.isInteger(imapPort) || !ALLOWED_PORTS.includes(imapPort)) {
    errors.push(`NW_IMAP_PORT=${imapPortRaw || "(empty)"} not allowed (allowed: ${ALLOWED_PORTS.join(", ")})`);
  }

  // 조회 범위 — 폴더 (화이트리스트 + 패턴)
  const folder = (process.env.NW_MAIL_FOLDER || "").trim();
  const folderAllowed =
    folder &&
    (ALLOWED_FOLDERS.includes(folder) ||
      ALLOWED_FOLDER_PATTERNS.some((p) => p.test(folder)));
  if (!folderAllowed) {
    errors.push(
      `NW_MAIL_FOLDER=${folder || "(empty)"} not allowed ` +
        `(허용: ${ALLOWED_FOLDERS.join(", ")} 또는 AI/[AI 로 시작하는 폴더)`
    );
  }

  // 접두어 — 검증 없음 (공란·임의 값 모두 허용)
  const prefix = (process.env.NW_MAIL_PREFIX || "").trim();

  // 조회 범위 — 건수 (기본 50)
  const maxCountRaw = (process.env.MCP_MAX_COUNT || "").trim();
  const maxCount = maxCountRaw ? Number.parseInt(maxCountRaw, 10) : 50;
  if (
    !Number.isInteger(maxCount) ||
    maxCount < RANGE_MAX_COUNT.min ||
    maxCount > RANGE_MAX_COUNT.max
  ) {
    errors.push(
      `MCP_MAX_COUNT=${maxCountRaw || "(empty)"} out of range ` +
        `(${RANGE_MAX_COUNT.min}~${RANGE_MAX_COUNT.max})`
    );
  }

  // 조회 범위 — 기간 (기본 30)
  const daysRaw = (process.env.MCP_DAYS || "").trim();
  const days = daysRaw ? Number.parseInt(daysRaw, 10) : 30;
  if (
    !Number.isInteger(days) ||
    days < RANGE_DAYS.min ||
    days > RANGE_DAYS.max
  ) {
    errors.push(
      `MCP_DAYS=${daysRaw || "(empty)"} out of range ` +
        `(${RANGE_DAYS.min}~${RANGE_DAYS.max})`
    );
  }

  // read_training_mail 1건 최대 메일 크기(MB · 첨부 포함 · 기본 10)
  const maxMbRaw = (process.env.MCP_MAX_MESSAGE_MB || "").trim();
  const maxMessageMb = maxMbRaw ? Number.parseInt(maxMbRaw, 10) : 10;
  if (
    !Number.isInteger(maxMessageMb) ||
    maxMessageMb < RANGE_MAX_MESSAGE_MB.min ||
    maxMessageMb > RANGE_MAX_MESSAGE_MB.max
  ) {
    errors.push(
      `MCP_MAX_MESSAGE_MB=${maxMbRaw || "(empty)"} out of range ` +
        `(${RANGE_MAX_MESSAGE_MB.min}~${RANGE_MAX_MESSAGE_MB.max})`
    );
  }

  // 로그 경로 — 존재 체크만 (없으면 ./logs 기본값)
  const logDir = (process.env.LOG_DIR || "./logs").trim();

  if (errors.length > 0) {
    const detail = errors.map((e) => `  - ${e}`).join("\n");
    const error = new Error(`[FAIL] env validation failed:\n${detail}`);
    error.code = "ENV_VALIDATION_FAILED";
    error.violations = errors;
    throw error;
  }

  return Object.freeze({
    nwId,
    nwPw,
    tunnelId,
    apiKey,
    imapHost,
    imapPort,
    folder,
    prefix, // "" 가능
    maxCount,
    days,
    maxMessageMb,
    maxMessageBytes: maxMessageMb * 1024 * 1024,
    logDir,
  });
}

// ---------------------------------------------------------------
// 마스킹 (로그·진단 출력용)
// ---------------------------------------------------------------
function maskSensitive(cfg) {
  const mask = (s, keep = 10) => {
    if (!s) return "(empty)";
    if (s.length <= keep) return "*".repeat(s.length);
    return s.slice(0, keep) + "*****";
  };
  return {
    nwId: cfg.nwId ? cfg.nwId.replace(/(^[^@]{2})[^@]*(@.*)/, "$1***$2") : "(empty)",
    nwPw: "***",
    tunnelId: mask(cfg.tunnelId, 10),
    apiKey: cfg.apiKey ? `sk-${"*".repeat(8)}` : "(empty)",
    imapHost: cfg.imapHost,
    imapPort: cfg.imapPort,
    folder: cfg.folder,
    prefix: cfg.prefix || "(empty · 폴더 내 전체 조회)",
    maxCount: cfg.maxCount,
    days: cfg.days,
    maxMessageMb: cfg.maxMessageMb,
    logDir: cfg.logDir,
  };
}

// ---------------------------------------------------------------
// Export
// ---------------------------------------------------------------
export const config = validateEnv();
export { maskSensitive, ALLOWED_FOLDERS, ALLOWED_FOLDER_PATTERNS, RANGE_MAX_COUNT, RANGE_DAYS, RANGE_MAX_MESSAGE_MB };
