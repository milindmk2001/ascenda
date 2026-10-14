export class NarrationPlayer {
  constructor() {
    this.utterance = null;
  }

  speak(text, onEndCallback) {
    if (!window.speechSynthesis || !text) {
      if (onEndCallback) onEndCallback();
      return;
    }

    this.stop();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    // Prevent Chrome garbage collection by storing on global window context
    window._activeUtterance = utterance;

    let executed = false;
    const handleCompletion = () => {
      if (!executed) {
        executed = true;
        window._activeUtterance = null;
        if (onEndCallback) onEndCallback();
      }
    };

    utterance.onend = handleCompletion;
    utterance.onerror = (err) => {
      console.warn("SpeechSynthesis error encountered, forcing scene transition:", err);
      handleCompletion();
    };

    // Fallback timer in case the browser blocks audio autoplay entirely
    const estimatedDuration = Math.max((text.length / 15) * 1000, 3000);
    setTimeout(() => {
      if (window._activeUtterance === utterance && !executed) {
        console.warn("SpeechSynthesis onend timed out, advancing scene.");
        handleCompletion();
      }
    }, estimatedDuration);

    window.speechSynthesis.speak(utterance);
  }

  pause() {
    if (window.speechSynthesis) window.speechSynthesis.pause();
  }

  resume() {
    if (window.speechSynthesis) window.speechSynthesis.resume();
  }

  stop() {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  }
}