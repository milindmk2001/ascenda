// src/services/api.js

// Vite exposes env variables through import.meta.env
const API_BASE = (
  import.meta.env.VITE_API_BASE_URL || 
  import.meta.env.VITE_API_URL || 
  "https://ascenda-production.up.railway.app"
).replace(/\/$/, ""); // Strips trailing slash if accidentally added

/**
 * Helper to execute standard JSON fetch requests
 */
async function request(endpoint, options = {}) {
  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint}`;
  
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const errorBody = await res.text().catch(() => null);
    throw new Error(
      `API Error [${res.status} ${res.statusText}]: ${endpoint} - ${errorBody || "No details"}`
    );
  }

  return res.json();
}

// ── INDIVIDUAL NAMED EXPORTS (Fixes CourseReader.jsx imports) ─────────

export const fetchGrades = () => request("/api/admin/curriculum/grades");

export const fetchResolveHub = (trackCode, gradeName) => {
  const params = new URLSearchParams({
    track_code: trackCode || "",
    grade_name: gradeName || "",
  });
  return request(`/api/curriculum/resolve-hub?${params.toString()}`);
};

export const fetchSubjectTree = (subjectId) =>
  request(`/api/curriculum/subjects/${subjectId}/tree`);

export const fetchLeafContent = (leafId) =>
  request(`/api/curriculum/leaf/${leafId}`);

export const fetchVisualLesson = (curriculumNodeId) =>
  request(`/api/visual-lesson/${curriculumNodeId}`);

export const postTutorAction = (payload) =>
  request("/api/visual-lesson/tutor-action", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const interactVideo = (timestamp, query) =>
  request("/api/interact", {
    method: "POST",
    body: JSON.stringify({ timestamp, query }),
  });

export const fetchAiStreamResponse = (leafId, subjectMeta = "general") => {
  return fetch(`${API_BASE}/api/ai_tutor/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      leaf_id: leafId,
      subject_meta: subjectMeta,
    }),
  });
};

// ── DEFAULT OBJECT EXPORT ──────────────────────────────────────────────

export const api = {
  getGrades: fetchGrades,
  resolveHub: fetchResolveHub,
  getCurriculumTree: fetchSubjectTree,
  getLeafContent: fetchLeafContent,
  getVisualLesson: fetchVisualLesson,
  postTutorAction,
  interactVideo,
  streamAiExplanation: fetchAiStreamResponse,
};

export default api;