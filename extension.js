import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import St from 'gi://St';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const MIN_REFRESH_SECONDS = 60;

const CodexUsageIndicator = GObject.registerClass(
class CodexUsageIndicator extends PanelMenu.Button {
    _init(extension) {
        super._init(0.0, extension.metadata.name, false);

        this._extension = extension;
        this._settings = extension.getSettings();
        this._timeoutId = 0;
        this._settingsChangedId = 0;
        this._running = false;
        this._destroyed = false;
        this._process = null;
        this._cancellable = null;

        this._box = new St.BoxLayout({style_class: 'panel-status-menu-box'});
        this._icon = new St.Icon({
            icon_name: 'utilities-system-monitor-symbolic',
            style_class: 'system-status-icon',
        });
        this._label = new St.Label({
            text: 'Codex …',
            y_align: Clutter.ActorAlign.CENTER,
        });
        this._box.add_child(this._icon);
        this._box.add_child(this._label);
        this.add_child(this._box);

        this._summaryItem = this._addInformationalItem('Loading usage…');
        this._resetItem = this._addInformationalItem('Reset: —');
        this._windowItem = this._addInformationalItem('Window: —');
        this._updatedItem = this._addInformationalItem('Updated: —');

        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        const refreshItem = new PopupMenu.PopupMenuItem('Refresh now');
        refreshItem.connect('activate', () => this.refresh());
        this.menu.addMenuItem(refreshItem);

        const preferencesItem = new PopupMenu.PopupMenuItem('Preferences');
        preferencesItem.connect('activate', () => this._extension.openPreferences());
        this.menu.addMenuItem(preferencesItem);

        this._settingsChangedId = this._settings.connect('changed',
            (_settings, key) => this._onSettingChanged(key));

        this._applyVisualSettings();
        this._scheduleRefresh();
        this.refresh();
    }

    _addInformationalItem(text) {
        const item = new PopupMenu.PopupMenuItem(text, {
            reactive: false,
            can_focus: false,
        });
        this.menu.addMenuItem(item);
        return item;
    }

    _onSettingChanged(key) {
        if (key === 'refresh-interval')
            this._scheduleRefresh();

        this._applyVisualSettings();
    }

    _applyVisualSettings() {
        this._icon.visible = this._settings.get_boolean('show-icon');

        if (this._lastPayload)
            this._showUsage(this._lastPayload);
    }

    _scheduleRefresh() {
        if (this._timeoutId) {
            GLib.source_remove(this._timeoutId);
            this._timeoutId = 0;
        }

        const configured = this._settings.get_uint('refresh-interval');
        const interval = Math.max(MIN_REFRESH_SECONDS, configured);
        this._timeoutId = GLib.timeout_add_seconds(
            GLib.PRIORITY_DEFAULT,
            interval,
            () => {
                this.refresh();
                return GLib.SOURCE_CONTINUE;
            });
        GLib.Source.set_name_by_id(
            this._timeoutId,
            '[codex-usage-indicator] refresh');
    }

    refresh() {
        if (this._running || this._destroyed)
            return;

        this._running = true;
        this._label.text = 'Codex …';

        const helperPath = GLib.build_filenamev([
            this._extension.path,
            'bin',
            'codex-usage',
        ]);
        const flags = Gio.SubprocessFlags.STDOUT_PIPE |
            Gio.SubprocessFlags.STDERR_PIPE;

        try {
            this._process = Gio.Subprocess.new(
                [helperPath, '--format', 'json'],
                flags);
            this._cancellable = new Gio.Cancellable();
        } catch (error) {
            this._running = false;
            this._showError(error.message);
            return;
        }

        this._process.communicate_utf8_async(
            null,
            this._cancellable,
            (subprocess, result) => {
                try {
                    const [, stdout, stderr] =
                        subprocess.communicate_utf8_finish(result);

                    let payload = null;
                    try {
                        payload = JSON.parse(stdout);
                    } catch (_error) {
                        // The more useful process error is reported below.
                    }

                    if (!payload?.ok) {
                        const message = payload?.error || stderr.trim() ||
                            'The Codex usage helper failed.';
                        throw new Error(message);
                    }

                    if (!subprocess.get_successful())
                        throw new Error(stderr.trim() || 'The usage helper exited unsuccessfully.');

                    if (!this._destroyed)
                        this._showUsage(payload);
                } catch (error) {
                    if (!this._destroyed &&
                        !error.matches?.(Gio.IOErrorEnum, Gio.IOErrorEnum.CANCELLED))
                        this._showError(error.message);
                } finally {
                    this._running = false;
                    this._process = null;
                    this._cancellable = null;
                }
            });
    }

    _showUsage(payload) {
        this._lastPayload = payload;

        const used = Math.round(payload.used_percent);
        const remaining = Math.round(payload.remaining_percent);
        const mode = this._settings.get_string('display-mode');
        const percentage = mode === 'used' ? used : remaining;
        const suffix = mode === 'used' ? ' used' : '';

        let panelText = `Codex ${percentage}%${suffix}`;
        const reset = GLib.DateTime.new_from_unix_local(payload.resets_at);
        if (this._settings.get_boolean('show-reset-time') && reset) {
            const formatted = reset.format('%a %H:%M');
            if (formatted)
                panelText += ` · ${formatted}`;
        }
        this._label.text = panelText;

        this._label.remove_style_class_name('codex-usage-warning');
        this._label.remove_style_class_name('codex-usage-danger');
        if (remaining <= 10)
            this._label.add_style_class_name('codex-usage-danger');
        else if (remaining <= 25)
            this._label.add_style_class_name('codex-usage-warning');

        this._summaryItem.label.text = `${remaining}% remaining · ${used}% used`;
        this._resetItem.label.text = reset
            ? `Reset: ${reset.format('%c')}`
            : 'Reset: unknown';

        const days = payload.window_minutes / 1440;
        const windowText = Number.isInteger(days)
            ? `${days} day${days === 1 ? '' : 's'}`
            : `${payload.window_minutes} minutes`;
        const plan = payload.plan_type
            ? ` · ${payload.plan_type}`
            : '';
        this._windowItem.label.text = `Window: ${windowText}${plan}`;

        const updated = GLib.DateTime.new_from_unix_local(payload.retrieved_at);
        this._updatedItem.label.text = updated
            ? `Updated: ${updated.format('%c')}`
            : 'Updated: just now';
    }

    _showError(message) {
        this._lastPayload = null;
        this._label.text = 'Codex !';
        this._label.remove_style_class_name('codex-usage-warning');
        this._label.add_style_class_name('codex-usage-danger');
        this._summaryItem.label.text = 'Usage unavailable';
        this._resetItem.label.text = message || 'Unknown error';
        this._windowItem.label.text = 'Check that Codex CLI is installed and logged in.';
        this._updatedItem.label.text = 'Use “Refresh now” to retry.';
    }

    destroy() {
        this._destroyed = true;

        if (this._timeoutId) {
            GLib.source_remove(this._timeoutId);
            this._timeoutId = 0;
        }

        if (this._settingsChangedId) {
            this._settings.disconnect(this._settingsChangedId);
            this._settingsChangedId = 0;
        }

        if (this._cancellable)
            this._cancellable.cancel();
        if (this._process)
            this._process.force_exit();

        this._settings = null;
        this._extension = null;
        super.destroy();
    }
});

export default class CodexUsageIndicatorExtension extends Extension {
    enable() {
        this._indicator = new CodexUsageIndicator(this);
        Main.panel.addToStatusArea(this.uuid, this._indicator);
    }

    disable() {
        this._indicator?.destroy();
        this._indicator = null;
    }
}
