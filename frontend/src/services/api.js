export async function fetchSubjectTree(subjectId) {
  const response = await fetch(`/api/curriculum/subjects/${subjectId}/tree`);
  if (!response.ok) {
    throw new Error(`Failed to fetch tree: ${response.status}`);
  }
  return response.json();
}

export async function fetchVisualLesson(nodeId) {
  try {
    const response = await fetch(`/api/visual-lesson/${nodeId}`);
    if (!response.ok) {
      return { mode: "classic", fallbackExplanation: "No cached visual slide found for this concept." };
    }

    const data = await response.json();

    // Case A: Endpoint returns normalized object { mode: 'visual', payload: {...} }
    if (data.mode === "visual" && data.payload) {
      return data;
    }

    // Case B: Endpoint returns raw DB record from visual_lesson_cache
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
  return fetch(`/api/ai_tutor/stream?node_id=${encodeURIComponent(nodeId)}&meta_tag=${encodeURIComponent(metaTag || '')}`, {
    method: 'GET',
    headers: {
      'Accept': 'text/event-stream',
    },
  });
}