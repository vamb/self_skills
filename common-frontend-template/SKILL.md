---
name: common-frontend-template
description: 通用前端业务列表模块模板。Use when Codex needs to migrate, refactor, or create React/Vue admin pages with a standard split of Content/context state, Page/list logic, Modal form components, detail/selector dialogs, and services APIs; especially for pages like user-group management, menu management, app-version management, or any Ant Design table page with search, pagination, CRUD dialogs, and API integration.
---

# 通用前端模板

## Core Pattern

Use this skill to split a frontend business module into predictable layers instead of placing page state, table logic, forms, dialogs, and API calls in one large component.

Model the structure after mature admin modules:

```text
FeatureName/
  FeatureContent.tsx
  FeaturePage.tsx
  FeatureConstant.ts
  components/
    FeatureFormModal.tsx
    FeatureDetailModal.tsx
    FeatureSelectorModal.tsx
  index.ts
services/
  featureName.ts
```

Read `references/module-structure.md` when implementation details, code skeletons, or naming conventions are needed.

## Responsibilities

Keep each layer narrow:

- `Content`: Own reducer/context state for cross-component modal visibility and current record.
- `Page`: Own list state, table columns, search params, pagination, loading, fetch/delete handlers, and modal open dispatches.
- `FormModal`: Own Ant Design form instance, submit loading, field initialization, close/reset behavior, and create/update submit.
- `DetailModal`: Own read-only display and optional detail fetches.
- `SelectorModal`: Own selection state and submit callback for assignment/configuration flows.
- `services`: Own API URL, request method, request/response mapping, and TypeScript types. Do not create page-local `api.ts` unless the codebase already requires it.

## Standard List Flow

Use a single search object as the list query source of truth.

- `handleInputSearch`: update search state, debounce API calls, reset to first page.
- `handleFilterSearch`: update search state, call API immediately, reset to first page.
- `handleOnChange`: update page/size from table pagination and call API.
- `fetchTableData`: clone/normalize params, set loading, call service, set `tableData` and `total`, handle errors.
- When every search control has `allowClear=true` and any search value change triggers list querying, do not add a separate reset button. Clearing a field should flow through the same search-change handler and refresh the list.

For Ant Design table loading inside flexible layouts, prefer a custom absolute-position overlay around the table panel instead of `Table loading` or `Spin` wrapping the table, because generated `ant-spin-container` DOM can disturb flex height.

## Table Toolbar

For standard Ant Design table pages, keep the right-side table toolbar purposeful and minimal:

- Do not add a refresh icon button unless the source page or user explicitly requires it.
- Add one density/size icon button, commonly using `VerticalAlignMiddleOutlined`, to configure the table `size` prop such as `large`, `middle`, and `small`.
- Add one settings icon button, commonly using `SettingOutlined`, to configure which table columns are visible.
- Render column visibility options in a vertical column layout, not a single horizontal row, so long column names remain readable.
- Keep add/create actions separate from these table configuration icons.

## Migration Checklist

1. Inspect the source page before coding: route, service calls, child modals, table columns, search controls, and page shell styles.
2. Create or update `services/<module>.ts` first with typed API functions and response mapping.
3. Add `FeatureConstant.ts` for reducer action names and stable enums.
4. Add `FeatureContent.tsx` for reducer/context state.
5. Move list-only logic into `FeaturePage.tsx`.
6. Move create/update form into `components/FeatureFormModal.tsx`.
7. Move detail and selector dialogs into their own files.
8. Check search controls: if they are `allowClear` and change-driven, remove redundant reset buttons and let clearing trigger the standard list query.
9. Configure table toolbar icons: keep density tied to `Table size`, settings tied to column visibility, and avoid redundant refresh buttons unless required.
10. Keep route entry `index.ts` small and export the content-wrapped page.
11. Build after each major split.

## Page Shell Rules

Respect the existing application shell. For migrated Vue-style admin pages, preserve:

- outer layout spacing from the app layout;
- page body margin and padding;
- transparent card body when the original page used one;
- table body height behavior;
- modal close/reset behavior.

Do not invent a new visual language when migrating a module. Match the existing module's operational layout first, then improve only where requested.
