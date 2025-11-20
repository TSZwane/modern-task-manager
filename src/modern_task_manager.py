#!/usr/bin/env python3

"""
Modern Task Manager
Author: Thabiso	Zwane
Ubuntu 22+ | GTK3 (PyGObject) | Python 3.x

A dark-themed task manager with real-time process monitoring,
system performance, and basic systemd service visibility.

Repository: https://github.com/TSZwane/modern-task-manager
"""

import gi
import os
import psutil
import threading
import time
from datetime import datetime

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango

class ModernTaskManager:
    def __init__(self):
        # Create main window
        self.window = Gtk.Window()
        self.window.set_title("Modern Task Manager")
        self.window.set_default_size(900, 600)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        
        # Set window icon
        self.set_window_icon()
        
        # Apply dark theme and rounded edges
        self.setup_styling()
        
        # Store scroll positions
        self.processes_scroll_pos = 0
        self.services_scroll_pos = 0
        
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window.add(main_box)
        
        # Create notebook (tabs)
        self.notebook = Gtk.Notebook()
        self.notebook.set_show_tabs(True)
        self.notebook.set_show_border(False)
        main_box.pack_start(self.notebook, True, True, 0)
        
        # Create status bar
        self.status_bar = Gtk.Statusbar()
        main_box.pack_start(self.status_bar, False, False, 0)
        
        # Create tabs
        self.create_processes_tab()
        self.create_services_tab()
        self.create_performance_tab()
        
        # Connect scroll events
        self.connect_scroll_events()
        
        # Update data periodically
        self.update_interval = 10  # seconds
        self.update_data()
        
        # Connect signals
        self.window.connect("destroy", Gtk.main_quit)
        
    def set_window_icon(self):
        """Set the window icon from multiple possible locations"""
        icon_names = [
            "modern-task-manager",
            "system-task-manager",
            "utilities-system-monitor"
        ]
        
        # Try to set icon from theme first
        for icon_name in icon_names:
            try:
                self.window.set_icon_name(icon_name)
                break
            except:
                continue
        
        # If theme icon not found, try to load from file
        icon_paths = [
            os.path.expanduser("~/.local/share/icons/hicolor/scalable/apps/modern-task-manager.svg"),
            os.path.expanduser("~/.local/share/icons/hicolor/256x256/apps/modern-task-manager.png"),
            "/usr/share/icons/hicolor/scalable/apps/modern-task-manager.svg",
            "/usr/share/pixmaps/modern-task-manager.png"
        ]
        
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                try:
                    self.window.set_icon_from_file(icon_path)
                    break
                except Exception as e:
                    print(f"Could not load icon from {icon_path}: {e}")

    def setup_styling(self):
        """Apply dark theme and rounded edges with smaller borders"""
        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        
        css = """
        * {
            background-color: #2b2b2b;
            color: #ffffff;
            font-family: 'Ubuntu', sans-serif;
        }
        
        .window {
            border-radius: 8px;
            background: #1e1e1e;
        }
        
        .tab-content {
            background: #2d2d2d;
            border-radius: 4px;
            margin: 4px;
            padding: 4px;
        }
        
        .process-row {
            padding: 4px;
            border-bottom: 1px solid #404040;
        }
        
        .process-row:hover {
            background: #404040;
        }
        
        button {
            background: linear-gradient(135deg, #007acc, #005a9e);
            border: none;
            border-radius: 1px;
            padding: 6px 12px;
            color: white;
            margin: 1px;
            border-width: 0px;
        }
        
        button:hover {
            background: linear-gradient(135deg, #005a9e, #004578);
        }
        
        button:active {
            background: linear-gradient(135deg, #004578, #003356);
        }
        
        button.danger {
            background: linear-gradient(135deg, #d13438, #a4262c);
        }
        
        button.danger:hover {
            background: linear-gradient(135deg, #a4262c, #7a1c1f);
        }
        
        notebook {
            border-width: 0px;
        }
        
        notebook tab {
            background: #333333;
            border-radius: 1px 1px 0 0;
            padding: 6px 12px;
            margin: 0 1px;
            border-width: 0px;
            min-height: 0px;
        }
        
        notebook tab:checked {
            background: #007acc;
            border-width: 0px;
        }
        
        treeview {
            background: #252525;
            border-radius: 4px;
            border-width: 0px;
        }
        
        treeview:hover {
            border-width: 0px;
        }
        
        .performance-widget {
            background: #333333;
            border-radius: 4px;
            padding: 8px;
            margin: 4px;
            border-width: 0px;
        }
        
        frame {
            border-radius: 4px;
            border-width: 1px;
            border-color: #404040;
        }
        
        frame > label {
            color: #cccccc;
            background-color: #333333;
        }
        
        scrollbar slider {
            border-radius: 2px;
            background: #007acc;
            min-width: 8px;
            min-height: 8px;
        }
        
        scrollbar trough {
            background: #333333;
            border-radius: 2px;
        }
        
        scrollbar:hover slider {
            background: #005a9e;
        }
        """
        
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        self.window.set_name("window")

    def create_processes_tab(self):
        """Create processes tab with list and controls"""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_name("tab-content")
        
        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        vbox.pack_start(toolbar, False, False, 0)
        
        # End process button
        end_btn = Gtk.Button(label="End Process")
        end_btn.set_name("danger")
        end_btn.connect("clicked", self.on_end_process)
        toolbar.pack_start(end_btn, False, False, 0)
        
        # Refresh button
        refresh_btn = Gtk.Button(label="Refresh")
        refresh_btn.connect("clicked", self.on_refresh)
        toolbar.pack_start(refresh_btn, False, False, 0)
        
        # Create scrolled window for process list
        self.processes_scrolled = Gtk.ScrolledWindow()
        self.processes_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(self.processes_scrolled, True, True, 0)
        
        # Create tree view for processes
        self.process_list = Gtk.ListStore(str, int, str, str, float, float)
        self.treeview = Gtk.TreeView(model=self.process_list)
        
        # Add columns
        columns = [
            ("Process Name", 0),
            ("PID", 1),
            ("Status", 2),
            ("User", 3),
            ("CPU %", 4),
            ("Memory %", 5)
        ]
        
        for i, (title, col_id) in enumerate(columns):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_resizable(True)
            column.set_sort_column_id(col_id)
            if i == 0:  # Process Name column
                column.set_min_width(200)
            elif i == 1:  # PID column
                column.set_min_width(80)
            self.treeview.append_column(column)
        
        self.processes_scrolled.add(self.treeview)
        
        self.notebook.append_page(vbox, Gtk.Label("Processes"))

    def create_services_tab(self):
        """Create services tab"""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_name("tab-content")
        
        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        vbox.pack_start(toolbar, False, False, 0)
        
        start_btn = Gtk.Button(label="Start Service")
        stop_btn = Gtk.Button(label="Stop Service")
        restart_btn = Gtk.Button(label="Restart Service")
        
        toolbar.pack_start(start_btn, False, False, 0)
        toolbar.pack_start(stop_btn, False, False, 0)
        toolbar.pack_start(restart_btn, False, False, 0)
        
        # Services list
        self.services_scrolled = Gtk.ScrolledWindow()
        self.services_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(self.services_scrolled, True, True, 0)
        
        self.services_list = Gtk.ListStore(str, str, str, str)
        self.services_treeview = Gtk.TreeView(model=self.services_list)
        
        services_columns = [
            ("Service Name", 0),
            ("Status", 1),
            ("Description", 2),
            ("PID", 3)
        ]
        
        for title, col_id in services_columns:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_resizable(True)
            if title == "Service Name":
                column.set_min_width(200)
            self.services_treeview.append_column(column)
        
        self.services_scrolled.add(self.services_treeview)
        
        self.notebook.append_page(vbox, Gtk.Label("Services"))

    def create_performance_tab(self):
        """Create performance monitoring tab"""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_name("tab-content")
        
        # CPU Usage
        cpu_frame = Gtk.Frame(label="CPU Usage")
        cpu_frame.set_name("performance-widget")
        cpu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        cpu_frame.add(cpu_box)
        
        self.cpu_label = Gtk.Label()
        self.cpu_progress = Gtk.ProgressBar()
        self.cpu_progress.set_show_text(True)
        
        cpu_box.pack_start(self.cpu_label, False, False, 0)
        cpu_box.pack_start(self.cpu_progress, False, False, 0)
        
        # Memory Usage
        mem_frame = Gtk.Frame(label="Memory Usage")
        mem_frame.set_name("performance-widget")
        mem_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        mem_frame.add(mem_box)
        
        self.mem_label = Gtk.Label()
        self.mem_progress = Gtk.ProgressBar()
        self.mem_progress.set_show_text(True)
        
        mem_box.pack_start(self.mem_label, False, False, 0)
        mem_box.pack_start(self.mem_progress, False, False, 0)
        
        # Disk Usage
        disk_frame = Gtk.Frame(label="Disk Usage")
        disk_frame.set_name("performance-widget")
        disk_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        disk_frame.add(disk_box)
        
        self.disk_label = Gtk.Label()
        self.disk_progress = Gtk.ProgressBar()
        self.disk_progress.set_show_text(True)
        
        disk_box.pack_start(self.disk_label, False, False, 0)
        disk_box.pack_start(self.disk_progress, False, False, 0)
        
        # System Info
        info_frame = Gtk.Frame(label="System Information")
        info_frame.set_name("performance-widget")
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_frame.add(info_box)
        
        self.info_label = Gtk.Label()
        self.info_label.set_line_wrap(True)
        self.info_label.set_halign(Gtk.Align.START)
        info_box.pack_start(self.info_label, False, False, 0)
        
        # Pack all frames
        vbox.pack_start(cpu_frame, False, False, 0)
        vbox.pack_start(mem_frame, False, False, 0)
        vbox.pack_start(disk_frame, False, False, 0)
        vbox.pack_start(info_frame, False, False, 0)
        
        self.notebook.append_page(vbox, Gtk.Label("Performance"))

    def connect_scroll_events(self):
        """Connect scroll events to save positions"""
        # Connect to the scrolled windows' adjustments
        vadj_process = self.processes_scrolled.get_vadjustment()
        vadj_process.connect("value-changed", self.on_processes_scroll)
        
        vadj_services = self.services_scrolled.get_vadjustment()
        vadj_services.connect("value-changed", self.on_services_scroll)

    def on_processes_scroll(self, adjustment):
        """Save processes scroll position"""
        self.processes_scroll_pos = adjustment.get_value()

    def on_services_scroll(self, adjustment):
        """Save services scroll position"""
        self.services_scroll_pos = adjustment.get_value()

    def restore_scroll_positions(self):
        """Restore scroll positions after update"""
        # Restore processes scroll position
        vadj_process = self.processes_scrolled.get_vadjustment()
        vadj_process.set_value(self.processes_scroll_pos)
        
        # Restore services scroll position
        vadj_services = self.services_scrolled.get_vadjustment()
        vadj_services.set_value(self.services_scroll_pos)

    def update_data(self):
        """Update all data in a separate thread"""
        def update_thread():
            while True:
                # Update processes
                processes = self.get_processes()
                services = self.get_services()
                performance = self.get_performance_data()
                
                GLib.idle_add(self.update_ui, processes, services, performance)
                time.sleep(self.update_interval)
        
        thread = threading.Thread(target=update_thread, daemon=True)
        thread.start()

    def get_processes(self):
        """Get current processes information"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'status', 'username', 'cpu_percent', 'memory_percent']):
            try:
                processes.append((
                    proc.info['name'],
                    proc.info['pid'],
                    proc.info['status'],
                    proc.info['username'],
                    proc.info['cpu_percent'],
                    proc.info['memory_percent']
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes

    def get_services(self):
        """Get system services information"""
        services = []
        try:
            # Try to get systemd services
            import subprocess
            result = subprocess.run(['systemctl', 'list-units', '--type=service', '--no-pager'], 
                                 capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            for line in lines[1:6]:  # Show first 5 services as example
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        services.append((
                            parts[0],
                            parts[3],
                            "System Service",
                            "N/A"
                        ))
        except:
            # Fallback to some example data
            services = [
                ("ssh.service", "active", "OpenSSH Server", "1234"),
                ("cron.service", "active", "Cron Daemon", "5678"),
                ("nginx.service", "active", "Web Server", "9012"),
            ]
        return services

    def get_performance_data(self):
        """Get system performance data"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used': memory.used // (1024**3),  # GB
            'memory_total': memory.total // (1024**3),  # GB
            'disk_percent': disk.percent,
            'disk_used': disk.used // (1024**3),  # GB
            'disk_total': disk.total // (1024**3),  # GB
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        }

    def update_ui(self, processes, services, performance):
        """Update UI with new data (called from main thread)"""
        # Store current selection
        process_selection = self.treeview.get_selection()
        process_model, process_iter = process_selection.get_selected()
        selected_pid = process_model[process_iter][1] if process_iter else None
        
        services_selection = self.services_treeview.get_selection()
        services_model, services_iter = services_selection.get_selected()
        selected_service = services_model[services_iter][0] if services_iter else None
        
        # Update processes
        self.process_list.clear()
        for proc in processes:
            self.process_list.append(proc)
        
        # Update services
        self.services_list.clear()
        for service in services:
            self.services_list.append(service)
        
        # Restore selections if possible
        if selected_pid:
            for i, row in enumerate(self.process_list):
                if row[1] == selected_pid:
                    process_selection.select_iter(row.iter)
                    break
        
        if selected_service:
            for i, row in enumerate(self.services_list):
                if row[0] == selected_service:
                    services_selection.select_iter(row.iter)
                    break
        
        # Update performance
        self.update_performance_ui(performance)
        
        # Restore scroll positions
        self.restore_scroll_positions()
        
        # Update status bar
        context_id = self.status_bar.get_context_id("info")
        self.status_bar.push(context_id, 
                           f"Processes: {len(processes)} | "
                           f"CPU: {performance['cpu_percent']:.1f}% | "
                           f"Memory: {performance['memory_percent']:.1f}%")

    def update_performance_ui(self, performance):
        """Update performance tab widgets"""
        # CPU
        self.cpu_label.set_text(f"Total CPU Usage: {performance['cpu_percent']:.1f}%")
        self.cpu_progress.set_fraction(performance['cpu_percent'] / 100)
        self.cpu_progress.set_text(f"{performance['cpu_percent']:.1f}%")
        
        # Memory
        mem_text = (f"Used: {performance['memory_used']}GB / "
                   f"{performance['memory_total']}GB "
                   f"({performance['memory_percent']:.1f}%)")
        self.mem_label.set_text(mem_text)
        self.mem_progress.set_fraction(performance['memory_percent'] / 100)
        self.mem_progress.set_text(f"{performance['memory_percent']:.1f}%")
        
        # Disk
        disk_text = (f"Used: {performance['disk_used']}GB / "
                    f"{performance['disk_total']}GB "
                    f"({performance['disk_percent']:.1f}%)")
        self.disk_label.set_text(disk_text)
        self.disk_progress.set_fraction(performance['disk_percent'] / 100)
        self.disk_progress.set_text(f"{performance['disk_percent']:.1f}%")
        
        # System info
        info_text = (f"Boot Time: {performance['boot_time']}\n"
                    f"CPU Cores: {psutil.cpu_count()}\n"
                    f"Memory Total: {performance['memory_total']}GB")
        self.info_label.set_text(info_text)

    def on_end_process(self, widget):
        """End selected process"""
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        
        if treeiter is not None:
            pid = model[treeiter][1]
            process_name = model[treeiter][0]
            
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK_CANCEL,
                text=f"End Process?"
            )
            dialog.format_secondary_text(f"Are you sure you want to end '{process_name}' (PID: {pid})?")
            
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                try:
                    process = psutil.Process(pid)
                    process.terminate()
                    self.status_bar.push(self.status_bar.get_context_id("info"), 
                                       f"Process {process_name} terminated")
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    error_dialog = Gtk.MessageDialog(
                        transient_for=self.window,
                        flags=0,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text="Error terminating process"
                    )
                    error_dialog.format_secondary_text(str(e))
                    error_dialog.run()
                    error_dialog.destroy()
            
            dialog.destroy()

    def on_refresh(self, widget):
        """Manual refresh"""
        self.status_bar.push(self.status_bar.get_context_id("info"), "Refreshing...")

    def show(self):
        """Show the window"""
        self.window.show_all()
        Gtk.main()

if __name__ == "__main__":
    # Check if running on Ubuntu/Linux
    if os.name != 'posix':
        print("This task manager is designed for Linux systems")
        exit(1)
    
    app = ModernTaskManager()
    app.show()
