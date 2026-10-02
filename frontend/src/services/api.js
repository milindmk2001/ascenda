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

export const api = {
  // ── CURRICULUM ENDPOINTS ───────────────────────────────────

  /**
   * Fetches available grade levels
   */
  getGrades: () => request("/api/admin/curriculum/grades"),

  /**
   * Resolves hub course cards based on track code and grade
   */
  resolveHub: (trackCode, gradeName) => {
    const params = new URLSearchParams({
      track_code: trackCode || "",
      grade_name: gradeName || "",
    });
    return request(`/api/curriculum/resolve-hub?${params.toString()}`);
  },

  /**
   * Fetches full curriculum tree for a subject/course ID
   */
  getCurriculumTree: (subjectId) =>
    request(`/api/curriculum/subjects/${subjectId}/tree`),

  /**
   * Fetches content/metadata for a leaf node
   */
  getLeafContent: (leafId) => request(`/api/curriculum/leaf/${leafId}`),

  // ── VISUAL LESSON ENDPOINTS ────────────────────────────────

  /**
   * Retrieves visual lesson cache payload for a curriculum node ID
   */
  getVisualLesson: (curriculumNodeId) =>
    request(`/api/visual-lesson/${curriculumNodeId}`),

  /**
   * Posts student interactions to the adaptive Socratic tutor engine
   */
  postTutorAction: (payload) =>
    request("/api/visual-lesson/tutor-action", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // ── INTERACTIVE VIDEO ENDPOINTS ───────────────────────────

  /**
   * Interacts with video frame analyzer
   */
  interactVideo: (timestamp, query) =>
    request("/api/interact", {
      method: "POST",
      body: JSON.stringify({ timestamp, query }),
    }),

  // ── STREAMING ENDPOINTS ────────────────────────────────────

  /**
   * Returns a raw ReadableStream response for AI Socratic explanations
   */
  streamAiExplanation: (leafId, subjectMeta = "general") => {
    return fetch(`${API_BASE}/api/ai_tutor/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        leaf_id: leafId,
        subject_meta: subjectMeta,
      }),
    });
  },
};

export default api;