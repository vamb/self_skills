# Module Structure Reference

Use this reference when implementing the common frontend template.

## Directory

```text
src/pages/<domain>/<feature>/
  <Feature>Content.tsx
  <Feature>Page.tsx
  <Feature>Constant.ts
  components/
    <Feature>FormModal.tsx
    <Feature>DetailModal.tsx
    <Feature>SelectorModal.tsx
  index.ts
src/services/<feature>.ts
```

## Constant

```ts
export const FEATURE_ACTION = {
  UPDATE_DATA: 'update_data',
} as const
```

## Content

```tsx
import { createContext, useMemo, useReducer, type Dispatch, type ReactNode } from 'react'
import { FEATURE_ACTION } from './FeatureConstant'

type FeatureState = {
  formModalShow: boolean
  detailModalShow: boolean
  selectorModalShow: boolean
  recordData: FeatureRecord | null
}

type FeatureAction = {
  type: typeof FEATURE_ACTION.UPDATE_DATA
  data: Partial<FeatureState>
}

const initialState: FeatureState = {
  formModalShow: false,
  detailModalShow: false,
  selectorModalShow: false,
  recordData: null,
}

export const FeatureContext = createContext<{
  featureData: FeatureState
  featureDispatch: Dispatch<FeatureAction>
}>({
  featureData: initialState,
  featureDispatch: () => undefined,
})

function reducer(state: FeatureState, action: FeatureAction): FeatureState {
  if (action.type === FEATURE_ACTION.UPDATE_DATA) return { ...state, ...action.data }
  return state
}

export function FeatureContent({ children }: { children: ReactNode }) {
  const [featureData, featureDispatch] = useReducer(reducer, initialState)
  const value = useMemo(() => ({ featureData, featureDispatch }), [featureData])
  return <FeatureContext.Provider value={value}>{children}</FeatureContext.Provider>
}
```

## Page

```tsx
const [search, setSearch] = useState({ page: 1, size: 10, name: undefined })
const [loading, setLoading] = useState(false)
const [tableData, setTableData] = useState<FeatureRecord[]>([])
const [total, setTotal] = useState(0)

const fetchTableData = useCallback(async (params = search) => {
  const requestParams = { ...params }
  setLoading(true)
  try {
    const result = await loadFeaturePage(requestParams)
    setTableData(result.records)
    setTotal(result.total)
  } finally {
    setLoading(false)
  }
}, [search])

const handleInputSearch = (param: Partial<typeof search>) => {
  clearTimeout(inputTimer)
  const next = { ...search, ...param, page: 1, size: 10 }
  setSearch(next)
  inputTimer = window.setTimeout(() => fetchTableData(next), 1000)
}

const handleFilterSearch = (param?: Partial<typeof search>) => {
  const next = { ...search, ...param, page: 1, size: 10 }
  setSearch(next)
  void fetchTableData(next)
}

const handleOnChange = (pagination: TablePaginationConfig) => {
  const next = {
    ...search,
    page: pagination.current || 1,
    size: pagination.pageSize || 10,
  }
  setSearch(next)
  void fetchTableData(next)
}
```

## Form Modal

```tsx
function FeatureFormModal({ fetchTableData }: { fetchTableData: () => void }) {
  const { featureData, featureDispatch } = useContext(FeatureContext)
  const { formModalShow, recordData } = featureData
  const [form] = Form.useForm<FeatureSubmitData>()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!formModalShow) return
    form.setFieldsValue(recordData ? mapRecordToForm(recordData) : getDefaultFormValues())
  }, [form, formModalShow, recordData])

  const modalClose = () => {
    featureDispatch({
      type: FEATURE_ACTION.UPDATE_DATA,
      data: { formModalShow: false, recordData: null },
    })
    form.resetFields()
  }

  const onFinish = async (values: FeatureSubmitData) => {
    setLoading(true)
    try {
      await submitFeatureForm(recordData?.id, values)
      fetchTableData()
      modalClose()
    } finally {
      setLoading(false)
    }
  }
}
```

## Table Loading Overlay

```tsx
<div ref={panelRef} className={styles.tablePanel} aria-busy={loading}>
  <Table loading={false} scroll={{ x: 1000, y: tableScrollY }} />
  {loading ? (
    <div className={styles.loadingMask}>
      <Spin tip="正在加载数据" />
    </div>
  ) : null}
</div>
```

```scss
.tablePanel {
  position: relative;
  flex: 1 1 auto;
  min-height: 0;
}

.loadingMask {
  position: absolute;
  inset: 0;
  z-index: 5;
  display: grid;
  place-items: center;
  background: rgba(240, 247, 255, 0.62);
}
```

## Service

```ts
import request from '@/utils/request'

export type FeaturePageParams = {
  page?: number
  size?: number
  name?: string
}

export async function loadFeaturePage(params: FeaturePageParams) {
  const result = await request<ApiPageData>('/feature/page', { params })
  return {
    records: result.list.map(mapApiItemToRecord),
    total: result.total || 0,
  }
}

export function createFeature(data: FeatureSubmitData) {
  return request.post('/feature', { data })
}

export function updateFeature(id: string | number, data: FeatureSubmitData) {
  return request.put(`/feature/${id}`, { data })
}

export function deleteFeature(id: string | number) {
  return request.delete(`/feature/${id}`)
}
```
