export class AnimationController {
  constructor(hostRef) {
    this.hostRef = hostRef;
    this.timeouts = [];
  }

  getEl(target) {
    return this.hostRef.current?.querySelector(`#${CSS.escape(target)}`);
  }

  clear() {
    this.timeouts.forEach(clearTimeout);
    this.timeouts = [];
  }

  executeStep(step) {
    return new Promise((resolve) => {
      const el = this.getEl(step.target);
      if (!el) {
        resolve();
        return;
      }

      el.classList.remove("highlight-target", "pulse-target", "shake-target");

      switch (step.action) {
        case "fadeIn":
        case "show":
        case "reveal":
          el.style.opacity = "1";
          el.style.transition = `opacity ${step.duration || 500}ms ease-in-out`;
          break;
        case "hide":
          el.style.opacity = "0";
          break;
        case "highlight":
          el.classList.add("highlight-target");
          const hTimer = setTimeout(() => el.classList.remove("highlight-target"), step.duration || 700);
          this.timeouts.push(hTimer);
          break;
        case "pulse":
          el.classList.add("pulse-target");
          const pTimer = setTimeout(() => el.classList.remove("pulse-target"), step.duration || 800);
          this.timeouts.push(pTimer);
          break;
        case "shake":
          el.classList.add("shake-target");
          const sTimer = setTimeout(() => el.classList.remove("shake-target"), 500);
          this.timeouts.push(sTimer);
          break;
        case "drawPath":
          el.style.strokeDasharray = "1000";
          el.style.strokeDashoffset = "1000";
          el.style.transition = `stroke-dashoffset ${step.duration || 1000}ms ease-in-out`;
          requestAnimationFrame(() => {
            el.style.strokeDashoffset = "0";
          });
          break;
        default:
          break;
      }

      const stepTimer = setTimeout(resolve, step.duration || 700);
      this.timeouts.push(stepTimer);
    });
  }

  async runTimeline(timeline, onStepComplete) {
    this.clear();
    for (const step of timeline) {
      if (step.narration && onStepComplete) {
        onStepComplete(step.narration);
      }
      await this.executeStep(step);
    }
  }
}