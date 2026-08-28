---
name: antd-form-item-info-tips
description: Build Ant Design Form.Item-level info tips beside form controls without breaking field binding, validation, label layout, or submit behavior.
---

# 不影响antdForm的form.item级别infoTips

Use this skill when adding or reviewing an Ant Design form field that needs an info/help icon with a Tooltip next to the control, especially inside `Form.Item` layouts where the field must keep normal `name`, validation, `valuePropName`, and submit behavior.

## Core Pattern

Preserve Ant Design Form behavior by separating layout from field binding:

- Use an outer `Form.Item` for the visible `label`, `labelCol`, `wrapperCol`, validation help space, and row-level layout.
- Put the real field control inside an inner `Form.Item noStyle name="fieldName"` so Ant Design still binds the child input/select/switch correctly.
- Place the `Tooltip` icon as a sibling of the inner `Form.Item`, not inside the bound control.
- Wrap the inner item and icon in a small flex row such as `.one-line`.

```jsx
<Form.Item
  label="分配模式"
  labelCol={{ span: 6 }}
  wrapperCol={{ span: 18 }}
>
  <div className="one-line">
    <Form.Item noStyle name="allocative">
      <Select
        allowClear
        style={{ width: '80%' }}
        placeholder="任务分配模式"
        getPopupContainer={triggerNode => triggerNode.parentNode}
      >
        {ProjectConstant.ALLOCATIVE_TYPE_LIST.map((item, idx) => (
          <Select.Option value={item.value} key={`pjt-allocative-opt-${idx}`}>
            {checkInputNone(item.label || item.value)}
          </Select.Option>
        ))}
      </Select>
    </Form.Item>

    <Tooltip
      placement="right"
      overlayInnerStyle={{ width: '380px' }}
      title={
        <div>
          <div style={{ marginBottom: '0.5rem' }}>
            {ProjectConstant.ALLOCATIVE_TYPE_MAP.SNATCH.tipsInfo}
          </div>
          <div style={{ marginBottom: '0.5rem' }}>
            {ProjectConstant.ALLOCATIVE_TYPE_MAP.EVENLY.tipsInfo}
          </div>
          <div style={{ marginBottom: '0.5rem' }}>
            {ProjectConstant.ALLOCATIVE_TYPE_MAP.RANDOM.tipsInfo}
          </div>
        </div>
      }
    >
      <InfoCircleOutlined className="tips-icon" />
    </Tooltip>
  </div>
</Form.Item>
```

## Tooltip Title Formatting

When a tooltip contains multiple explanation lines, format each line as a child `<div>`. Apply `style={{ marginBottom: '0.5rem' }}` to every line except the last one so the popover is readable and consistent with existing QuickBot form tips.

Prefer storing repeated business copy in constants, for example `tipsInfo` fields in a local `ProjectConstant` map, then compose the tooltip title from those constants.

## Required Styles

Use or adapt these styles near the component's existing styled wrapper:

```css
.one-line {
  display: flex;
  flex-direction: row;
  justify-content: flex-start;
  align-items: baseline;
  gap: 10px;
}

.tips-icon {
  cursor: pointer;
  font-size: 1.125rem;
}
```

## Checks

Before finishing, verify that:

- The submitted form value still appears under the intended field name.
- Existing `rules`, `required`, `valuePropName`, and conditional rendering still work.
- The Tooltip icon does not become the child of a named `Form.Item`.
- The field width and icon spacing match nearby form rows.
- Long tooltip text has an explicit width such as `overlayInnerStyle={{ width: '380px' }}` when needed.
