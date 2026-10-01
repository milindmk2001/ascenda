// src/services/api.js

const rawBase = import.meta.env.VITE_API_BASE_URL || '';
const API_BASE_URL = rawBase ? `${rawBase.replace(/\/$/, '')}/api` : '/api';

/**
 * Curriculum & Visual Lesson API Functions
 */

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

    // 1. Unwrap nested payload objects or stringified JSON DB blobs
    let rawPayload = data.payload || data.lesson_json || data;

    while (typeof rawPayload === 'string') {
      try {
        rawPayload = JSON.parse(rawPayload);
      } catch (e) {
        break;
      }
    }

    if (rawPayload && rawPayload.payload) {
      rawPayload = typeof rawPayload.payload === 'string'
        ? JSON.parse(rawPayload.payload)
        : rawPayload.payload;
    }

    // 2. Sanitize SVG string artifacts (non-breaking spaces, escaped newlines, extra tabs)
    if (rawPayload && Array.isArray(rawPayload.slides)) {
      rawPayload.slides = rawPayload.slides.map((slide) => {
        let rawSvg = slide.svgCache || slide.svgContent || slide.svg || slide.svg_cache || '';

        if (typeof rawSvg === 'string') {
          rawSvg = rawSvg
            .replace(/\\n/g, '\n')         // Convert escaped \n to real newlines
            .replace(/\u00a0/g, ' ')       // Replace non-breaking spaces (\u00a0) with normal spaces
            .replace(/[\r\t]+/g, ' ')      // Clean control characters
            .trim();
        }

        return {
          ...slide,
          svgCache: rawSvg,
          svgContent: rawSvg,
          svg_cache: rawSvg,
          svg: rawSvg
        };
      });
    }

    return {
      mode: "visual",
      payload: rawPayload
    };
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

/**
 * Hub Navigation Endpoints
 */

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