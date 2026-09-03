---
name: frontend-filter-data
description: Build or update frontend local filtering for already-loaded list data, especially React table modals using search state, display list state, and a reusable filterArr helper with input, select, and multi-select matching.
---

# 前端过滤数据

Use this skill when a frontend page already has a complete list in memory and the user wants filtering done on the client instead of calling the backend again. It is especially relevant for React + Ant Design `Table` or modal picker components where filters include text inputs, single-select fields, and multi-select fields.

## Core Pattern

Keep three pieces distinct:

- The original list: the complete unfiltered data, usually from props or a state value such as `rpaList`, `projectList`, or `allList`.
- The filter state: a `search` object containing input text, single-select values, and multi-select arrays.
- The display list: a state value such as `tblList` that is recomputed from the original list whenever filters change.

Do not repeatedly filter from the current display list as the canonical data source. Always start each recomputation from the original list so clearing filters can restore the full result set.

When the page also has an API query, keep API querying and frontend filtering separate:

- API calls initialize or refresh the original list only. For example, opening a modal can call `queryList({ tab: 1 })`, and a "查询" button may call the same API again to refresh the original list.
- Frontend filter controls such as `Input`, `Select`, and multi-select `Select` must filter the local original list and update the display list only.
- Do not merge frontend-only filter conditions into the API request parameters when the backend does not support those filters.
- After refreshing the original list from the API, apply the current local filter state to the newly returned list before updating the table.

## filterArr Helper

The reusable helper should support these modes:

```js
export const filterArr = (arr, param, key, isInput, isMultiple = false) => {
  if(param[key] !== null && param[key] !== undefined && param[key] !== "" && !(Array.isArray(param[key]) && param[key]?.length <= 0)){
    const temp = []
    arr?.map(item => {
      if(isInput) {
        if(item?.[key]?.includes(param?.[key])) {
          temp.push(item)
        }
      }else if(isMultiple) {
        const selectVal = Array.isArray(param?.[key]) ? param?.[key] : [param?.[key]]
        if(selectVal.includes(item?.[key])) {
          temp.push(item)
        }
      }else{
        if(item?.[key] === param?.[key]) {
          temp.push(item)
        }
      }
    })
    return temp
  }else{
    return arr
  }
}
```

Use `isInput = true` for text input fuzzy matching, `isInput = false` for exact select matching, and `isMultiple = true` when the filter value can be an array from an Ant Design `Select mode="multiple"`.

Treat `null`, `undefined`, an empty string, and an empty array as "no filter" so clearing a control does not accidentally return an empty table.

The `key` argument must correspond to the related Ant Design table column's `dataIndex`:

- For a normal column such as `dataIndex: "name"`, call `filterArr(list, search, "name", true)`.
- For a nested column such as `dataIndex: ["rpa", "name"]`, prefer enhancing the shared `filterArr` helper to support array keys, then call `filterArr(list, search, ["rpa", "name"], true)`.
- Do not invent extra frontend-only field names such as `_filterName`, `rpaName`, or `policeDisplayName` when they do not match the table's `dataIndex`.
- If a display value is calculated in `render`, first check whether an existing real data field can be used. Only introduce a derived field when the table column itself also uses that same field as `dataIndex`.

## Applying It

Recompute the display list by chaining filters from broad to narrow:

```js
const fetchTblData = param => {
  const reqParam = param ? param : search
  const nameList = filterArr(sourceList, reqParam, "name", true)
  const stateList = filterArr(nameList, reqParam, "state", false)
  const workStateList = filterArr(stateList, reqParam, "workState", false, true)
  setTblList(workStateList)
}
```

For input controls, debounce if the local list is large or the existing page already uses delayed input search. For select controls, filtering can usually run immediately.

If the original list is loaded from an API, split the code into two clear responsibilities:

```js
const filterTblData = (param, list = sourceList) => {
  const reqParam = param ? param : search
  const nameList = filterArr(list, reqParam, "name", true)
  const stateList = filterArr(nameList, reqParam, "state", false)
  setTblList(stateList)
}

const refreshTblData = param => {
  const reqParam = param ? param : search
  queryList({ tab: 1 }).then(res => {
    const nextSourceList = Array.isArray(res) ? res : []
    setSourceList(nextSourceList)
    filterTblData(reqParam, nextSourceList)
  })
}
```

In this pattern, filter controls call `filterTblData`, while opening the modal or clicking the API refresh/query button calls `refreshTblData`.

For Ant Design multi-select filters, store the selected value as an array and keep the default value as an array too:

```jsx
const initSearch = {
  workState: [WORK_STATE_MAP.FREE.value],
}

<Select
  mode="multiple"
  maxTagCount="responsive"
  allowClear
  value={search?.workState}
  onChange={value => handleFilterSearch({ workState: value })}
/>
```

## Checks

After updating code, verify:

- Clearing any filter restores results from the original list.
- Single-select filters still use exact matching.
- Multi-select filters return rows whose field value is contained in the selected array.
- Existing callers of `filterArr` continue to work because `isMultiple` defaults to `false`.
- Each `filterArr` key matches the related table column's `dataIndex`.
- Frontend-only filters are not included in API request parameters unless the backend explicitly supports them.
