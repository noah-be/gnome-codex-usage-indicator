import Adw from 'gi://Adw';
import Gio from 'gi://Gio';
import Gtk from 'gi://Gtk';

import {ExtensionPreferences} from 'resource:///org/gnome/Shell/Extensions/js/extensions/prefs.js';

export default class CodexUsageIndicatorPreferences extends ExtensionPreferences {
    fillPreferencesWindow(window) {
        const settings = this.getSettings();
        const page = new Adw.PreferencesPage({
            title: 'Codex Usage Indicator',
            icon_name: 'utilities-system-monitor-symbolic',
        });
        const group = new Adw.PreferencesGroup({
            title: 'Panel display',
            description: 'Choose how the weekly Codex usage window appears.',
        });

        const displayModes = ['Remaining percentage', 'Used percentage'];
        const displayValues = ['remaining', 'used'];
        const displayRow = new Adw.ComboRow({
            title: 'Percentage',
            subtitle: 'Value displayed in the GNOME top panel',
            model: Gtk.StringList.new(displayModes),
        });
        displayRow.selected = Math.max(
            0,
            displayValues.indexOf(settings.get_string('display-mode')));
        displayRow.connect('notify::selected', row => {
            settings.set_string('display-mode', displayValues[row.selected]);
        });
        group.add(displayRow);

        const resetRow = new Adw.SwitchRow({
            title: 'Show reset time',
            subtitle: 'Append the local reset day and time to the panel label',
        });
        settings.bind(
            'show-reset-time',
            resetRow,
            'active',
            Gio.SettingsBindFlags.DEFAULT);
        group.add(resetRow);

        const iconRow = new Adw.SwitchRow({
            title: 'Show icon',
            subtitle: 'Display a symbolic monitor icon beside the percentage',
        });
        settings.bind(
            'show-icon',
            iconRow,
            'active',
            Gio.SettingsBindFlags.DEFAULT);
        group.add(iconRow);

        const refreshRow = new Adw.SpinRow({
            title: 'Refresh interval (minutes)',
            subtitle: 'Minutes between automatic updates',
            adjustment: new Gtk.Adjustment({
                lower: 1,
                upper: 60,
                step_increment: 1,
                page_increment: 5,
                value: settings.get_uint('refresh-interval') / 60,
            }),
            digits: 0,
            numeric: true,
        });
        refreshRow.connect('notify::value', row => {
            const minutes = Math.round(row.value);
            settings.set_uint('refresh-interval', minutes * 60);
        });
        group.add(refreshRow);

        page.add(group);
        window.add(page);
    }
}
