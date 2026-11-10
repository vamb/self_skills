---
name: dark-card-background
description: 为深色科技风卡片、统计面板应用“深色卡片背景色”方案：深蓝底色、底部蓝色渐变、轻网格光效，以及共用背景的透明内部模块。适用于用户要求复用此配色或统一同类卡片背景时。
---

# 深色卡片背景色

## 配色与层次

使用一层连续背景覆盖整张卡片，避免相邻模块分别绘制渐变造成拼接处颜色突变。

- 主背景：`#05203F`，顶部至约 45% 保持深蓝。
- 底部渐变：`#0A3F78`。
- 底部柔光：`#00CFFF26`，椭圆径向渐变，中心在 `50% 110%`，约 65% 处透明。
- 边框及模块分隔线：`#168EC3`，1px。
- 文字参考：`#D5F4FF`；保留业务状态已有的语义色。
- 可选网格：`#25CAFF25`，28px × 12px，限制在底部约一半区域；暗色面板网格层 opacity 为 0.6。
- 可选内侧底部光晕：`inset 0 -2px 10px #00CFFF30`。

小型统计条的网格、光晕应轻微，避免影响数字阅读；不用添加设计稿中的插画或大标题。

## 组合规则

整个面板承担背景；主任务信息框、统计内容框和它们的边框伪元素均使用透明背景。内部透明不是将整个面板 opacity 降低，文字和图标应保持清晰。

保留外框和模块间的竖向分隔边框。两部分相接处使用直角，仅最外侧保留 8px 圆角。若主信息框可单独出现：单独显示时四角为圆角，右侧内容展开时其右上、右下角过渡成直角，但右边框仍保留。

裁切溢出时在对应容器使用 `overflow-x: hidden; overflow-y: hidden`。检查窄屏是否裁掉必要信息，必要时调整内部排列，而不是悄悄隐藏业务内容。

在既有项目中遵循其样式体系；React 项目已有 styled-components 时优先使用它。保留现有展开动画、布局和业务行为；这套配色不要求新增动画。明色主题保持现有方案，除非用户要求同时修改。

## 可复用 CSS

以下样式可移入 styled-components。网格伪元素如与现有装饰冲突，应改为独立装饰层；装饰层不得拦截点击。

```css
.dark-card {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  border-radius: 8px;
  color: #d5f4ff;
  background:
    radial-gradient(ellipse at 50% 110%, #00cfff26, transparent 65%),
    linear-gradient(180deg, #05203f 0%, #05203f 45%, #0a3f78 100%);
  box-shadow: inset 0 -2px 10px #00cfff30;
}
.dark-card::before {
  content: '';
  position: absolute;
  left: -10%; right: -10%; bottom: 0; height: 50%;
  background-image:
    linear-gradient(#25caff25 1px, transparent 1px),
    linear-gradient(90deg, #25caff25 1px, transparent 1px);
  background-size: 28px 12px;
  transform: perspective(100px) rotateX(35deg);
  transform-origin: center bottom;
  mask-image: linear-gradient(to bottom, transparent, #000);
  opacity: .6;
  pointer-events: none;
  z-index: 0;
}
.dark-card > * { position: relative; z-index: 1; }
.dark-card__section { background: transparent; }
```

外边框可由整体容器绘制，也可保留已有分段边框；不要两者叠加成双线。展开动画如用伪元素绘制边框，伪元素也应保持背景透明。

## 检查结果

- 展开前后背景连续，无模块交界色块或渐变重启。
- 外框和中间分隔线仍可见，接缝无圆角缺口或双边框。
- 网格处于文字下层，装饰不影响点击或遮挡内容。
- 统计数字、状态色和原有动效保持可用；窄屏无不必要滚动条。