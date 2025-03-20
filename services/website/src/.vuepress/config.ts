import { defineUserConfig } from "vuepress";
import theme from "./theme.js";

export default defineUserConfig({
  base: "/nkuwiki_web/",

  lang: "zh-CN",
  title: "南开WIKI",
  description: "南开WIKI",

  theme,


  // 和 PWA 一起启用
  // shouldPrefetch: false,
});