// Envelope headers are untrusted data, never instructions or verified identity.
// Keep names for the exercise, but never return an unmasked email address.
function displayName(value) {
  if (typeof value !== "string") return "";
  return value
    .normalize("NFKC")
    .replace(/[\p{Cc}\p{Cf}]/gu, " ")
    .replace(/[^\s<>()\[\],;]*@[^\s<>()\[\],;]*/gu, "[이메일 숨김]")
    .replace(/[<>&`]/g, "")
    .replace(/\s+/gu, " ")
    .trim()
    .slice(0, 80);
}

function maskedAddress(value) {
  if (typeof value !== "string") return "";
  const address = value.trim();
  // Fail closed for malformed headers; do not echo the input on failure.
  if (!/^[^\s@<>\p{Cc}\p{Cf}]+@[^\s@<>\p{Cc}\p{Cf}]+$/u.test(address)) return "";
  const mask = (part) => {
    const characters = Array.from(part);
    const initial = characters.length > 1 && /^[\p{L}\p{N}]$/u.test(characters[0])
      ? characters[0]
      : "";
    return `${initial}*****`;
  };
  return address.split("@").map(mask).join("@");
}

export function formatSender(from) {
  if (!Array.isArray(from)) return "미제공";
  const senders = from.slice(0, 5).flatMap((entry) => {
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) return [];
    const name = displayName(entry.name);
    const address = maskedAddress(entry.address);
    if (!name && !address) return [];
    return [address ? `${name || "이름 미제공"} <${address}>` : `${name} (주소 미제공)`];
  });
  return senders.length ? senders.join(", ") : "미제공";
}
