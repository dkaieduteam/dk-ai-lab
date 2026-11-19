// Pre-flight IMAP sign-in probe. Called from Start-StudentMcp.ps1 before launching server.mjs
// so a wrong NAVER WORKS ID/password surfaces immediately as an exit code (no mailbox read).
// Credentials come from env vars and are deleted from process.env right after being captured.
// Only our own PROBE_RESULT codes reach stdout/stderr. No account value, no raw IMAP response.
import { ImapFlow } from "imapflow";
import { classifyMailError } from "./imap-errors.mjs";

const IMAP_HOST = "imap.worksmobile.com";
const IMAP_PORT = 993;

const user = process.env.NW_IMAP_USER ?? "";
const pass = process.env.NW_IMAP_PASSWORD ?? "";

delete process.env.NW_IMAP_USER;
delete process.env.NW_IMAP_PASSWORD;

if (!user || !pass) {
  console.error("PROBE_RESULT: MISSING_IMAP_CREDENTIALS");
  process.exit(2);
}

// Exit code map lets Start-StudentMcp.ps1 branch without parsing stdout.
const EXIT_CODES = Object.freeze({
  SUCCESS: 0,
  MISSING_IMAP_CREDENTIALS: 2,
  IMAP_AUTH_FAILED: 10,
  IMAP_ACCESS_NOT_ALLOWED: 11,
  IMAP_CONNECTION_FAILED: 12,
  IMAP_DNS_FAILED: 13,
  IMAP_TIMEOUT: 14,
  IMAP_TLS_FAILED: 15,
  IMAP_SERVER_REJECTED: 16,
  UNKNOWN: 20,
});

const client = new ImapFlow({
  host: IMAP_HOST,
  port: IMAP_PORT,
  secure: true,
  auth: { user, pass },
  logger: false,
  connectionTimeout: 15_000,
  greetingTimeout: 15_000,
  socketTimeout: 30_000,
});
client.on("error", () => {
  // Raw ImapFlow errors may carry account hints; never let them surface.
});

try {
  await client.connect();
  console.log("PROBE_RESULT: SUCCESS");
  try { await client.logout(); } catch { /* ignore */ }
  process.exit(EXIT_CODES.SUCCESS);
} catch (error) {
  if (error && typeof error === "object" && !error.trainingPhase) error.trainingPhase = "connect";
  const { code } = classifyMailError(error);
  console.error(`PROBE_RESULT: ${code}`);
  process.exit(EXIT_CODES[code] ?? EXIT_CODES.UNKNOWN);
}
