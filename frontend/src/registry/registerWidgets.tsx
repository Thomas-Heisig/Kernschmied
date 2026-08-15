import { registerWidgetRenderer } from './widgetRegistry';
import CalendarWidget from '../components/widgets/CalendarWidget';
import SystemHealthWidget from '../components/widgets/SystemHealthWidget';
import AuditLogWidget from '../components/widgets/AuditLogWidget';
import RegistryEditorWidget from '../components/widgets/RegistryEditorWidget';
import FilesWidget from '../components/widgets/FilesWidget';
import ChatWidget from '../components/widgets/ChatWidget';

// Register known safe renderers here.
registerWidgetRenderer('calendar_widget', (widget, ctx) => {
  return <CalendarWidget widget={widget} nodeId={ctx?.nodeId} configuration={widget.configuration} />;
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

registerWidgetRenderer('files_widget', (widget, ctx) => {
  return <FilesWidget widget={widget} nodeId={ctx?.nodeId} />;
});

registerWidgetRenderer('chat_widget', (widget, ctx) => {
  return <ChatWidget widget={widget} nodeId={ctx?.nodeId} />;
});

// Also accept shorthand/legacy type names without the `_widget` suffix.
registerWidgetRenderer('calendar', (widget, ctx) => {
  return <CalendarWidget widget={widget} nodeId={ctx?.nodeId} configuration={widget.configuration} />;
});

registerWidgetRenderer('system_health', (widget, ctx) => {
  return <SystemHealthWidget widget={widget} nodeId={ctx?.nodeId} />;
});

registerWidgetRenderer('audit_log', (widget, ctx) => {
  return <AuditLogWidget widget={widget} nodeId={ctx?.nodeId} />;
});

registerWidgetRenderer('registry_editor', (widget, ctx) => {
  return <RegistryEditorWidget widget={widget} nodeId={ctx?.nodeId} />;
});

registerWidgetRenderer('files', (widget, ctx) => {
  return <FilesWidget widget={widget} nodeId={ctx?.nodeId} />;
});

registerWidgetRenderer('chat', (widget, ctx) => {
  return <ChatWidget widget={widget} nodeId={ctx?.nodeId} />;
});

export default {};
