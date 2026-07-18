const scenarios = {
  intersection: {
    number: "01",
    type: "INTERSECTION / LEFT TURN",
    title: "无保护左转中的多车交互",
    shortTitle: "交叉口左转",
    heroLabel: "交叉口 · 无保护左转",
    description: "自车需要在横向与纵向交通流之间完成左转决策，动作时机与安全间距共同构成决策难点。",
    features: ["多方向交通流", "时序冲突明显", "连续控制决策"],
    video: "./assets/video/intersection.mp4",
    safeGif: "./assets/sim/intersection-safe.gif",
    ablationGif: "./assets/sim/intersection-ablation.gif",
    safeAlt: "ASFCRL 在交叉口左转场景中的仿真动画",
    ablationAlt: "w/o ASF 在交叉口左转场景中的仿真动画",
  },
  roundabout: {
    number: "02",
    type: "ROUNDABOUT / 1-IN-3-OUT",
    title: "多车道环岛中的连续博弈",
    shortTitle: "多车道环岛",
    heroLabel: "环岛 · 1 进 3 出",
    description: "自车在进入、环行与驶出阶段持续面对周车交互，连续交通流使策略需要不断更新决策。",
    features: ["1 进 3 出", "环流持续交互", "多车道决策"],
    video: "./assets/video/roundabout.mp4",
    safeGif: "./assets/sim/roundabout-safe.gif",
    ablationGif: "./assets/sim/roundabout-ablation.gif",
    safeAlt: "ASFCRL 在多车道环岛场景中的仿真动画",
    ablationAlt: "w/o ASF 在多车道环岛场景中的仿真动画",
  },
};

const header = document.querySelector(".site-header");
const menuToggle = document.querySelector(".menu-toggle");
const navigation = document.querySelector(".site-nav");
const tabs = [...document.querySelectorAll(".scenario-tab")];
const scenarioVideo = document.querySelector("#scenario-video");
const heroVideo = document.querySelector("#hero-video");
const playControl = document.querySelector("#play-control");
const progressBar = document.querySelector("#video-progress-bar");
const safeGif = document.querySelector("#safe-gif");
const ablationGif = document.querySelector("#ablation-gif");
let activeScenario = "intersection";

function setScenario(key) {
  const scenario = scenarios[key];
  if (!scenario) return;
  activeScenario = key;
  tabs.forEach((tab) => {
    const selected = tab.dataset.scenario === key;
    tab.classList.toggle("is-active", selected);
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });
  document.querySelector("#scene-number").textContent = scenario.number;
  document.querySelector("#scene-type").textContent = scenario.type;
  document.querySelector("#scene-title").textContent = scenario.title;
  document.querySelector("#scene-description").textContent = scenario.description;
  document.querySelector("#hero-scene-label").textContent = scenario.heroLabel;
  document.querySelector("#comparison-scene").textContent = scenario.shortTitle;
  const featureList = document.querySelector("#scene-features");
  featureList.replaceChildren(...scenario.features.map((feature) => {
    const item = document.createElement("li");
    item.textContent = feature;
    return item;
  }));
  [scenarioVideo, heroVideo].forEach((video) => {
    video.src = scenario.video;
    video.load();
    video.play().catch(() => {});
  });
  playControl.classList.remove("is-paused");
  playControl.querySelector("b").textContent = "PAUSE";
  playControl.setAttribute("aria-label", "暂停视频");
  safeGif.src = scenario.safeGif;
  safeGif.alt = scenario.safeAlt;
  ablationGif.src = scenario.ablationGif;
  ablationGif.alt = scenario.ablationAlt;
}

tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => setScenario(tab.dataset.scenario));
  tab.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
    event.preventDefault();
    const direction = event.key === "ArrowRight" ? 1 : -1;
    const nextIndex = (index + direction + tabs.length) % tabs.length;
    tabs[nextIndex].focus();
    setScenario(tabs[nextIndex].dataset.scenario);
  });
});

playControl.addEventListener("click", () => {
  if (scenarioVideo.paused) {
    scenarioVideo.play().catch(() => {});
    playControl.classList.remove("is-paused");
    playControl.querySelector("b").textContent = "PAUSE";
    playControl.setAttribute("aria-label", "暂停视频");
  } else {
    scenarioVideo.pause();
    playControl.classList.add("is-paused");
    playControl.querySelector("b").textContent = "PLAY";
    playControl.setAttribute("aria-label", "播放视频");
  }
});

scenarioVideo.addEventListener("timeupdate", () => {
  const progress = scenarioVideo.duration ? (scenarioVideo.currentTime / scenarioVideo.duration) * 100 : 0;
  progressBar.style.width = `${progress}%`;
});

document.querySelector("#replay-gifs").addEventListener("click", () => {
  const scenario = scenarios[activeScenario];
  const stamp = `?replay=${Date.now()}`;
  safeGif.src = `${scenario.safeGif}${stamp}`;
  ablationGif.src = `${scenario.ablationGif}${stamp}`;
});

menuToggle.addEventListener("click", () => {
  const expanded = menuToggle.getAttribute("aria-expanded") === "true";
  menuToggle.setAttribute("aria-expanded", String(!expanded));
  menuToggle.setAttribute("aria-label", expanded ? "打开导航菜单" : "关闭导航菜单");
  navigation.classList.toggle("is-open", !expanded);
});

navigation.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    navigation.classList.remove("is-open");
    menuToggle.setAttribute("aria-expanded", "false");
    menuToggle.setAttribute("aria-label", "打开导航菜单");
  });
});

window.addEventListener("scroll", () => header.classList.toggle("is-scrolled", window.scrollY > 24), { passive: true });

const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    entry.target.classList.add("is-visible");
    revealObserver.unobserve(entry.target);
  });
}, { threshold: 0.1 });

document.querySelectorAll(".reveal").forEach((element) => revealObserver.observe(element));

document.addEventListener("visibilitychange", () => {
  if (document.hidden) return;
  [heroVideo, scenarioVideo].forEach((video) => {
    if (video.muted && video.paused && !playControl.classList.contains("is-paused")) video.play().catch(() => {});
  });
});
