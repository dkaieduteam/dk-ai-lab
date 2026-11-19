// Turns NAVER WORKS IMAP failures into fixed codes and Korean guidance.
// Only our own codes and short machine identifiers leave this module: never the raw
// error message or server response text (they can contain the account name).

// Scope and safety codes thrown by server.mjs itself.
const OWN_CODES = new Set([
  "TITLE_CATEGORY_INVALID",
  "UID_OUT_OF_SCOPE",
  "ATTACHMENTS_NOT_ALLOWED",
  "MESSAGE_TOO_LARGE",
  "READ_STATE_CHANGED",
  "TRAINING_MARKER_MISSING",
  "MAILBOX_NOT_READ_ONLY",
  "MESSAGE_NOT_FOUND",
  "MESSAGE_SOURCE_INVALID",
]);

export const MAIL_ERROR_GUIDANCE = Object.freeze({
  IMAP_AUTH_FAILED:
    "NAVER WORKS가 로그인을 거부했습니다. 로그인 ID(메일 주소 전체)와 비밀번호를 확인하십시오. 회사 설정에 따라 IMAP 사용 허용 또는 외부 앱 비밀번호가 필요할 수 있습니다. 같은 값으로 반복 시도하지 말고 확인 후 1회만 다시 시도하십시오.",
  IMAP_ACCESS_NOT_ALLOWED:
    "이 계정은 IMAP 접속이 허용되지 않았거나 외부 앱 비밀번호가 필요합니다. NAVER WORKS 메일 환경설정의 IMAP 사용 여부와 회사 보안팀 승인을 확인하십시오.",
  IMAP_DNS_FAILED:
    "메일 서버(imap.worksmobile.com) 주소를 찾지 못했습니다. PC의 인터넷 연결과 DNS·프록시 설정을 확인하십시오.",
  IMAP_CONNECTION_FAILED:
    "메일 서버(imap.worksmobile.com:993)에 연결하지 못했습니다. 사내망 방화벽·프록시가 993 포트를 막고 있는지 확인하십시오.",
  IMAP_TIMEOUT:
    "메일 서버 응답 시간이 초과됐습니다. 네트워크 상태를 확인하고 잠시 후 1회만 다시 시도하십시오.",
  IMAP_TLS_FAILED:
    "메일 서버와 보안 연결(SSL/TLS)을 확인하지 못했습니다. 사내 SSL 검사 장비·백신의 암호화 통신 검사, PC 날짜·시간 설정을 확인하십시오.",
  TRAINING_FOLDER_NOT_FOUND:
    "로그인은 성공했지만 .env의 NW_MAIL_FOLDER로 지정된 교육용 메일 폴더를 찾지 못했습니다. NAVER WORKS 메일에서 폴더 이름(대괄호·밑줄 포함)을 확인하십시오.",
  IMAP_PERMISSION_DENIED:
    "로그인은 성공했지만 지정된 교육용 메일 폴더를 열 권한이 없습니다. 폴더 공유·권한 설정을 강사와 확인하십시오.",
  IMAP_RATE_LIMITED:
    "짧은 시간에 요청이 많아 메일 서버가 접속을 제한했습니다. 1~2분 뒤 다시 시도하십시오.",
  IMAP_SERVER_REJECTED:
    "메일 서버가 요청을 거부했습니다. 잠시 후 다시 시도하고, 반복되면 강사에게 알리십시오.",
  MAILBOX_NOT_READ_ONLY:
    "실습 폴더를 읽기 전용으로 열지 못해 조회를 중단했습니다. 강사에게 알리십시오.",
  TITLE_CATEGORY_INVALID:
    "제목 분류는 [주간보고]처럼 대괄호 1쌍으로 입력하십시오. [AI실습]은 자동으로 붙습니다.",
  UID_OUT_OF_SCOPE:
    "목록에서 확인한 메일이 아니거나 같은 제목 분류가 아니어서 읽지 않았습니다. 안전장치가 정상 작동한 것입니다.",
  ATTACHMENTS_NOT_ALLOWED: "첨부파일이 있는 메일은 실습 범위가 아니어서 읽지 않았습니다.",
  MESSAGE_TOO_LARGE: "메일 크기가 실습 허용 범위를 넘어 읽지 않았습니다.",
  READ_STATE_CHANGED: "읽음 상태가 바뀐 것이 감지돼 중단했습니다. 메뉴 3으로 종료한 뒤 강사에게 알리십시오.",
  TRAINING_MARKER_MISSING: "교육용 더미 데이터 표시가 없는 메일이어서 읽지 않았습니다.",
  MESSAGE_NOT_FOUND: "메일을 찾지 못했습니다. 목록을 다시 조회하십시오.",
  MESSAGE_SOURCE_INVALID: "메일 원문을 안전하게 가져오지 못했습니다. 목록을 다시 조회하십시오.",
  TOOL_FAILED: "요청을 안전하게 처리하지 못했습니다. START_HERE.cmd 메뉴 2로 상태를 확인하십시오.",
});

// Keeps only short identifier-like values for the metadata log (no free text).
export function safeToken(value) {
  const text = String(value ?? "");
  return /^[A-Za-z][A-Za-z0-9_]{0,39}$/.test(text) ? text : "";
}

const DNS_CODES = new Set(["ENOTFOUND", "EAI_AGAIN", "EAI_FAIL", "EAI_NONAME"]);
const CONNECTION_CODES = new Set([
  "ECONNREFUSED", "ECONNRESET", "EHOSTUNREACH", "ENETUNREACH", "ENETDOWN", "EPIPE", "ECONNABORTED",
  "NoConnection", "EConnectionClosed", "ClosedAfterConnectText", "StateLogout",
  "ProxyError", "EPROXY", "UnsupportedProxyAddress",
]);
const TIMEOUT_CODES = new Set(["CONNECT_TIMEOUT", "GREETING_TIMEOUT", "ETIMEDOUT", "ETIMEOUT", "LockTimeout", "ESOCKETTIMEDOUT"]);
const TLS_CODE_PATTERN = /^(ERR_TLS_|ERR_SSL_|CERT_|UNABLE_TO_|SELF_SIGNED_CERT|DEPTH_ZERO_SELF_SIGNED_CERT|EPROTO$|ClosedAfterConnectTLS$|UPGRADE_TIMEOUT$|HOSTNAME_MISMATCH$)/;
const ACCESS_TEXT_PATTERN = /imap[^.]{0,40}(disabled|not\s+(enabled|allowed|permitted)|turned\s+off|사용\s*안\s*함)|app(lication)?([\s-]*specific)?[\s-]*password|two[\s-]*(step|factor)|2[\s-]*(step|factor)|\botp\b/i;
const AUTH_TEXT_PATTERN = /auth|login|password|credential|인증|로그인/i;

/**
 * Classifies an error from ImapFlow or server.mjs.
 * @returns {{code: string, phase: string, details: object}} details are safe tokens only.
 */
export function classifyMailError(error) {
  const own = error?.code ?? error?.message;
  const phase = safeToken(error?.trainingPhase) || "unknown";
  const imapCode = safeToken(error?.code);
  const serverResponseCode = safeToken(error?.serverResponseCode);
  const responseStatus = ["NO", "BAD", "BYE"].includes(error?.responseStatus) ? error.responseStatus : "";
  const details = {};
  if (imapCode) details.imapErrorCode = imapCode;
  if (serverResponseCode) details.serverResponseCode = serverResponseCode;
  if (responseStatus) details.responseStatus = responseStatus;
  if (error?.authenticationFailed === true) details.authenticationFailed = true;
  if (error?.mailboxMissing === true) details.mailboxMissing = true;
  const result = (code) => ({ code, phase, details });

  if (typeof own === "string" && OWN_CODES.has(own)) return result(own);

  // The response text is inspected here only; it is never returned or logged.
  const responseText = String(error?.responseText ?? error?.response ?? "");
  const code = String(error?.code ?? "");
  const upperResponseCode = serverResponseCode.toUpperCase();

  if (error?.authenticationFailed === true || ["AUTHENTICATIONFAILED", "AUTHORIZATIONFAILED", "EXPIRED"].includes(upperResponseCode) ||
      (phase === "connect" && responseStatus === "NO" && AUTH_TEXT_PATTERN.test(responseText))) {
    return result(ACCESS_TEXT_PATTERN.test(responseText) ? "IMAP_ACCESS_NOT_ALLOWED" : "IMAP_AUTH_FAILED");
  }
  if (DNS_CODES.has(code)) return result("IMAP_DNS_FAILED");
  if (TLS_CODE_PATTERN.test(code)) return result("IMAP_TLS_FAILED");
  if (TIMEOUT_CODES.has(code)) return result("IMAP_TIMEOUT");
  if (CONNECTION_CODES.has(code)) return result("IMAP_CONNECTION_FAILED");
  if (code === "ETHROTTLE" || upperResponseCode === "LIMIT") return result("IMAP_RATE_LIMITED");
  if (phase === "folder") {
    if (error?.mailboxMissing === true || upperResponseCode === "NONEXISTENT") return result("TRAINING_FOLDER_NOT_FOUND");
    if (upperResponseCode === "NOPERM" || responseStatus === "NO") return result("IMAP_PERMISSION_DENIED");
  }
  if (upperResponseCode === "NOPERM") return result("IMAP_PERMISSION_DENIED");
  if (responseStatus) return result("IMAP_SERVER_REJECTED");
  return result("TOOL_FAILED");
}

export function mailErrorGuidance(code) {
  return MAIL_ERROR_GUIDANCE[code] ?? MAIL_ERROR_GUIDANCE.TOOL_FAILED;
}
