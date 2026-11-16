// Case_배포용_v2 · training-scope.mjs
// 조회 범위 상수와 제목 범위 검증 함수.
// v1: 상수가 하드코딩됨. v2: config.mjs(.env)에서 로드.

import { config } from "./config.mjs";

// .env 값으로 노출 (v1 API 호환)
export const TRAINING_FOLDER = config.folder;
export const REQUIRED_SUBJECT_PREFIX = config.prefix; // 공란 가능
export const LOOKBACK_DAYS = config.days;
export const MAX_RESULTS = config.maxCount;

// 접두어 공란 허용 — 사용자가 titleCategory 생략해도 통과
const TITLE_CATEGORY_PATTERN = /^\[[^\[\]\r\n]{1,30}\]$/u;

export function normalizeTitleCategory(value) {
  const normalized = String(value ?? "").trim();
  // 공란 허용: 접두어·titleCategory 둘 다 비면 제목 필터 없음
  if (normalized === "") {
    if (!REQUIRED_SUBJECT_PREFIX) {
      return ""; // 전체 제목 허용 모드
    }
    const error = new Error("TITLE_CATEGORY_INVALID");
    error.code = "TITLE_CATEGORY_INVALID";
    throw error;
  }
  if (!TITLE_CATEGORY_PATTERN.test(normalized)) {
    const error = new Error("TITLE_CATEGORY_INVALID");
    error.code = "TITLE_CATEGORY_INVALID";
    throw error;
  }
  return normalized;
}

export function buildSubjectPrefix(titleCategory) {
  const category = normalizeTitleCategory(titleCategory);
  // prefix·category 모두 비면 빈 문자열 (제목 필터 없음)
  if (!REQUIRED_SUBJECT_PREFIX && !category) return "";
  return `${REQUIRED_SUBJECT_PREFIX}${category}`;
}

export function isSubjectInScope(subject, titleCategory) {
  const prefix = buildSubjectPrefix(titleCategory);
  if (prefix === "") return true; // 전체 허용 모드
  return String(subject ?? "").startsWith(prefix);
}
