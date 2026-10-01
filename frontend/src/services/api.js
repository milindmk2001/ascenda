const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
export const getTracks = async () => {
  const res = await fetch(`${API_BASE}/api/curriculum/tracks`);
  if (!res.ok) {
    throw new Error(`Failed to fetch tracks: ${res.statusText}`);
  }
  return await res.json();
};

export const getGrades = async () => {
  const res = await fetch(`${API_BASE}/api/curriculum/grades`);
  if (!res.ok) {
    throw new Error(`Failed to fetch grades: ${res.statusText}`);
  }
  return await res.json();
};

export const resolveHubSubjects = async (trackCode, gradeName) => {
  const params = new URLSearchParams({
    track_code: trackCode,
    grade_name: gradeName,
  });
  const res = await fetch(`${API_BASE}/api/curriculum/resolve-hub?${params}`);
  if (!res.ok) {
    throw new Error(`Failed to resolve hub: ${res.statusText}`);
  }
  return await res.json();
};
/**
 * Core JSON request handler
 */
async function request(endpoint, options = {}) {
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, config);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP Error ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

/* ==========================================================================
   Curriculum & Hub
   ========================================================================== */

export async function fetchGrades() {
  return request('/api/curriculum/grades');
}

export async function resolveHubSubjects(trackCode, gradeName) {
  const params = new URLSearchParams({
    track_code: trackCode,
    grade_name: gradeName,
  });
  return request(`/api/curriculum/resolve-hub?${params.toString()}`);
}

export async function fetchSubjectTree(subjectId) {
  return request(`/api/curriculum/subjects/${subjectId}/tree`);
}

/* ==========================================================================
   Visual Lesson Engine & Interaction
   ========================================================================== */

export async function fetchVisualLesson(curriculumNodeId) {
  return request(`/api/visual-lesson/${curriculumNodeId}`);
}

export async function sendTutorAction(payload) {
  return request('/api/visual-lesson/tutor-action', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function interactWithVideoFrame(timestamp, query) {
  return request('/api/interact', {
    method: 'POST',
    body: JSON.stringify({ timestamp, query }),
  });
}

/* ==========================================================================
   Content Studio & DB Sync
   ========================================================================== */

export async function syncLessonToStudio(lessonPayload) {
  return request('/api/studio/lesson', {
    method: 'POST',
    body: JSON.stringify(lessonPayload),
  });
}

/* ==========================================================================
   AI Tutor Stream
   ========================================================================== */

export async function fetchAiStreamResponse(leafId, subjectMeta) {
  return fetch(`${API_BASE}/api/ai_tutor/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      leaf_id: leafId,
      subject_meta: subjectMeta || 'general',
    }),
  });
}