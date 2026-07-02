export class SceneExecutor {
  constructor(lessonJson) {
    this.lesson = lessonJson;
  }

  getInitialScene() {
    return this.lesson.initialScene || "s1";
  }

  getSlide(slideId) {
    return this.lesson.slides.find(s => s.slideId === slideId) || null;
  }

  getNextSceneId(currentSlide, eventType) {
    if (!currentSlide || !currentSlide.transitions) return null;
    return currentSlide.transitions[eventType] || null;
  }
}