import { sidebar } from "vuepress-theme-hope";

export default sidebar({
  "/": [
    "",
    "portfolio",
    {
      text: "探索",
      icon: "lightbulb",
      prefix: "docx/",
      link: "docx/",
      children: "structure",
    },
    {
      text: "联系我们",
      icon: "book",
      prefix: "communicate/",
      children: "structure",
    },
    {
      text: "幻灯片",
      icon: "person-chalkboard",
      link: "https://ecosystem.vuejs.press/zh/plugins/markdown/revealjs/demo.html",
    },
  ],
});
