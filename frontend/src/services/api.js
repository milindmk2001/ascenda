const rawBase = import.meta.env.VITE_API_BASE_URL || '';
const API_BASE_URL = rawBase ? `${rawBase.replace(/\/$/, '')}/api` : '/api';

// Curriculum & Visual Lesson API Functions
export async function fetchSubjectTree(subjectId) {
  const response = await fetch(`${API_BASE_URL}/curriculum/subjects/${subjectId}/tree`);
  if (!response.ok) {
    throw new Error(`Failed to fetch tree: ${response.status}`);
  }
  return response.json();
}

export async function fetchVisualLesson(nodeId) {
  try {
    const response = await fetch(`${API_BASE_URL}/visual-lesson/${nodeId}`);
    if (!response.ok) {
      return { mode: "classic", fallbackExplanation: "No cached visual slide found for this concept." };
    }

    const data = await response.json();

    if (data.mode === "visual" && data.payload) {
      return data;
    }

    if (data.lesson_json || data.payload) {
      const rawPayload = data.lesson_json || data.payload;
      const parsedPayload = typeof rawPayload === 'string' ? JSON.parse(rawPayload) : rawPayload;

      return {
        mode: "visual",
        payload: parsedPayload
      };
    }

    return { mode: "classic", fallbackExplanation: "Reviewing layout structure..." };
  } catch (err) {
    console.warn("fetchVisualLesson fallback active:", err);
    return { mode: "classic", fallbackExplanation: "Reviewing layout structure..." };
  }
}

export async function fetchAiStreamResponse(nodeId, metaTag) {
  return fetch(`${API_BASE_URL}/ai_tutor/stream?node_id=${encodeURIComponent(nodeId)}&meta_tag=${encodeURIComponent(metaTag || '')}`, {
    method: 'GET',
    headers: {
      'Accept': 'text/event-stream',
    },
  });
}

// Hub Navigation Endpoints
export async function getTracks() {
  const response = await fetch(`${API_BASE_URL}/curriculum/tracks`);
  if (!response.ok) {
    throw new Error(`Failed to fetch tracks: ${response.status}`);
  }
  return response.json();
}

export async function getGrades(trackId) {
  const response = await fetch(`${API_BASE_URL}/curriculum/grades?track_id=${encodeURIComponent(trackId || '')}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch grades: ${response.status}`);
  }
  return response.json();
}

export async function resolveHubSubjects(trackCode, gradeName) {
  const response = await fetch(`${API_BASE_URL}/curriculum/resolve-hub?track_code=${encodeURIComponent(trackCode || '')}&grade_name=${encodeURIComponent(gradeName || '')}`);
  if (!response.ok) {
    throw new Error(`Failed to resolve subjects: ${response.status}`);
  }
  return response.json();
}