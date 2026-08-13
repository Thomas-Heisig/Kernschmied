import { registerWidgetRenderer } from './widgetRegistry';
import CalendarWidget from '../components/widgets/CalendarWidget';
import SystemHealthWidget from '../components/widgets/SystemHealthWidget';
import AuditLogWidget from '../components/widgets/AuditLogWidget';
import RegistryEditorWidget from '../components/widgets/RegistryEditorWidget';

// Register known safe renderers here.
registerWidgetRenderer('calendar_widget', (widget, ctx) => {
  return <CalendarWidget nodeId={ctx?.nodeId} configuration={widget.configuration} />;
});

registerWidgetRenderer('system_health_widget', (widget, ctx) => {
  return <SystemHealthWidget widget={widget} nodeId={ctx?.nodeId} />;
});

registerWidgetRenderer('audit_log_widget', (widget, ctx) => {
  return <AuditLogWidget widget={widget} nodeId={ctx?.nodeId} />;
});

registerWidgetRenderer('registry_editor_widget', (widget, ctx) => {
  return <RegistryEditorWidget widget={widget} nodeId={ctx?.nodeId} />;
});

export default {};
