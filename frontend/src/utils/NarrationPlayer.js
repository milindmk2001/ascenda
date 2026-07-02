export class NarrationPlayer {
  constructor() {
    this.utterance = null;
  }

  speak(text, onEndCallback) {
    if (!window.speechSynthesis) return;
    this.stop();

    this.utterance = new SpeechSynthesisUtterance(text);
    this.utterance.rate = 0.95;
    this.utterance.pitch = 1.0;
    
    if (onEndCallback) {
      this.utterance.onend = onEndCallback;
    }

    window.speechSynthesis.speak(this.utterance);
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