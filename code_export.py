import os
import tkinter as tk
import json
import datetime
from tkinter import ttk, filedialog, messagebox, simpledialog
import collections
import logging

# Set up logging
logging.basicConfig(filename="merge_errors.log", level=logging.ERROR)

class FileTypeDialog(tk.Toplevel):
    def __init__(self, parent, ignored_types):
        super().__init__(parent)
        self.title("Manage Ignored File Types")
        self.geometry("400x500")
        self.result = None
        self.ignored_types = list(ignored_types)

        # Main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Instructions
        ttk.Label(main_frame, text="Manage file types to ignore:").pack(anchor=tk.W)

        # Listbox with scrollbar
        types_frame = ttk.LabelFrame(main_frame, text="Ignored Extensions")
        types_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        scrollbar = ttk.Scrollbar(types_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.types_list = tk.Listbox(types_frame, yscrollcommand=scrollbar.set)
        self.types_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.types_list.yview)

        # Populate list
        for ext in self.ignored_types:
            self.types_list.insert(tk.END, ext)

        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Add", command=self.add_type).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Remove", command=self.remove_type).pack(side=tk.LEFT, padx=5)

        # Preset buttons
        preset_frame = ttk.LabelFrame(main_frame, text="Presets")
        preset_frame.pack(fill=tk.X, pady=5)
        ttk.Button(preset_frame, text="Code Files",
                   command=lambda: self.apply_preset([".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".h"])).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text="Documents",
                   command=lambda: self.apply_preset([".txt", ".md", ".doc", ".docx", ".pdf", ".rtf"])).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text="Media",
                   command=lambda: self.apply_preset([".jpg", ".jpeg", ".png", ".gif", ".mp3", ".mp4", ".wav"])).pack(side=tk.LEFT, padx=5)

        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        ttk.Button(control_frame, text="Apply", command=self.apply).pack(side=tk.RIGHT, padx=5)
        ttk.Button(control_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)

    def add_type(self):
        new_type = simpledialog.askstring("Add Type", "Enter file extension (with dot, e.g. '.txt'):")
        if new_type:
            if not new_type.startswith("."):
                new_type = "." + new_type
            if new_type not in self.ignored_types:
                self.ignored_types.append(new_type)
                self.types_list.insert(tk.END, new_type)

    def remove_type(self):
        selected = self.types_list.curselection()
        if selected:
            index = selected[0]
            ext = self.types_list.get(index)
            self.ignored_types.remove(ext)
            self.types_list.delete(index)

    def apply_preset(self, extensions):
        self.types_list.delete(0, tk.END)
        self.ignored_types = extensions
        for ext in extensions:
            self.types_list.insert(tk.END, ext)

    def apply(self):
        self.result = self.ignored_types
        self.destroy()

    def cancel(self):
        self.destroy()

class FileMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Merger with Tree Select")
        self.root.geometry("800x600")

        # State variables
        self.include_line_numbers = tk.BooleanVar(value=False)
        self.ignored_filetypes = [".scml", ".pyc", ".pyo", ".pyd"]
        self.ignored_directories = ["__pycache__", ".git", ".vscode"]
        self.include_ignored_in_structure = tk.BooleanVar(value=True)
        self.include_structure = tk.BooleanVar(value=True)
        self.check_states = {}
        self.default_output_dir = os.getcwd()

        # Menu bar
        self.menu_bar = tk.Menu(root)
        self.root.config(menu=self.menu_bar)

        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Select Root Folder", command=self.select_root)
        self.file_menu.add_command(label="Merge Files", command=self.merge_files)
        
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=root.quit)

        # Preferences menu
        self.pref_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Preferences", menu=self.pref_menu)
        self.pref_menu.add_command(label="File Type Filters", command=self.edit_filetypes)
        self.pref_menu.add_checkbutton(
            label="Show Ignored Files in Structure",
            variable=self.include_ignored_in_structure,
            command=self.save_preferences)
        self.pref_menu.add_checkbutton(label="Include File Structure",
                                       variable=self.include_structure,
                                       command=self.save_preferences)
        self.pref_menu.add_checkbutton(label="Include Line Numbers",
                                       variable=self.include_line_numbers,
                                       command=self.save_preferences)
        self.pref_menu.add_command(label="Set Default Output Directory", command=self.set_default_output_dir)

        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)

        # Search frame
        search_frame = ttk.Frame(root)
        search_frame.pack(fill=tk.X, pady=5)
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<KeyRelease>", self.search_tree)

        # Button frame
        self.btn_frame = ttk.Frame(root)
        self.btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(self.btn_frame, text="Select Root Folder", command=self.select_root).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.btn_frame, text="Merge Files", command=self.merge_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.btn_frame, text="Preview Merge", command=self.preview_merge).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.btn_frame, text="Merge & Auto Save", 
          command=self.auto_save_merge).pack(side=tk.LEFT, padx=5)
        # Main frame (Treeview)
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview with checkboxes
        self.tree = ttk.Treeview(self.main_frame, columns=("check"), selectmode="none")
        self.tree.heading("#0", text="File Structure", anchor=tk.W)
        self.tree.heading("check", text="Include")
        self.tree.column("check", width=60, anchor="center")
        self.tree.tag_configure('oddrow', background='lightgray')
        self.tree.tag_configure('evenrow', background='white')
        self.tree.tag_configure("highlight", background="yellow")

        # Scrollbar
        self.scroll = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind events
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<<TreeviewOpen>>", self.load_children)

        # Initialize
        self.load_preferences()
        self.update_status()
        self.build_tree(self.root_dir)

    def set_default_output_dir(self):
        folder = filedialog.askdirectory(initialdir=self.default_output_dir)
        if folder:
            self.default_output_dir = folder
            self.save_preferences()

    def show_about(self):
        messagebox.showinfo("About", "File Merger with Tree Select\nVersion 1.1\nCreated by [Your Name]")

    def show_user_guide(self):
        guide_window = tk.Toplevel(self.root)
        guide_window.title("User Guide")
        guide_window.geometry("600x400")
        text_widget = tk.Text(guide_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, "User Guide\n\n")
        text_widget.insert(tk.END, "1. Select Root Folder: Choose the directory to merge files from.\n")
        text_widget.insert(tk.END, "2. Use the search bar to find specific files or folders.\n")
        text_widget.insert(tk.END, "3. Check boxes to select files for merging.\n")
        text_widget.insert(tk.END, "4. Use 'Preview Merge' to review the output.\n")
        text_widget.insert(tk.END, "5. Click 'Merge Files' to save the merged content.\n")
        text_widget.insert(tk.END, "6. Configure preferences via the Preferences menu.\n")
        text_widget.config(state=tk.DISABLED)

    def search_tree(self, event):
        search_term = self.search_entry.get().lower()
        if not search_term:
            for item in self.tree.get_children(""):
                self.tree.item(item, tags=self.tree.item(item, "tags"))
            return

        def search_item(item):
            text = self.tree.item(item, "text").lower()
            if search_term in text:
                self.tree.item(item, tags=("highlight",))
                return True
            else:
                self.tree.item(item, tags=self.tree.item(item, "tags"))
                for child in self.tree.get_children(item):
                    if search_item(child):
                        return True
                return False

        for item in self.tree.get_children(""):
            search_item(item)

    def load_children(self, event):
        item = self.tree.focus()
        if not item:
            return
        # Get the full path from the item's tags
        full_path = self.tree.item(item, "tags")[1]
        # Check for placeholder children and delete them
        children = self.tree.get_children(item)
        if children and self.tree.item(children[0], "text") == "Loading...":
            self.tree.delete(children[0])
            # Dynamically load the actual contents
            self.process_directory(full_path, item)

    def preview_merge(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("No Selection", "No files selected")
            return

        preview_window = tk.Toplevel(self.root)
        preview_window.title("Merge Preview")
        preview_window.geometry("800x600")
        text_widget = tk.Text(preview_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True)

        if self.include_structure.get():
            structure = self.generate_file_structure(files)
            text_widget.insert(tk.END, f"FILE STRUCTURE OVERVIEW\n{'='*40}\n")
            text_widget.insert(tk.END, structure)
            text_widget.insert(tk.END, "\n\n" + "="*40 + "\n\n")

        total = len(files)
        for idx, file_path in enumerate(files, 1):
            header = f"\n{'#' * 40}\n### {idx}/{total}: {os.path.basename(file_path)}\n{'#' * 40}\n\n"
            text_widget.insert(tk.END, header)
            try:
                with open(file_path, "r", encoding="utf-8") as infile:
                    if self.include_line_numbers.get():
                        for line_num, line in enumerate(infile, 1):
                            text_widget.insert(tk.END, f"{line_num:04d}| {line}")
                    else:
                        text_widget.insert(tk.END, infile.read())
            except UnicodeDecodeError:
                with open(file_path, "r", encoding="latin-1") as infile:
                    if self.include_line_numbers.get():
                        for line_num, line in enumerate(infile, 1):
                            text_widget.insert(tk.END, f"{line_num:04d}| {line}")
                    else:
                        text_widget.insert(tk.END, infile.read())
            except Exception as e:
                logging.error(f"Error reading {file_path}: {str(e)}")
                text_widget.insert(tk.END, f"Error reading {file_path}: {str(e)}\n")
            footer = f"\n{'#' * 40}\n### END: {os.path.basename(file_path)}\n{'#' * 40}\n\n"
            text_widget.insert(tk.END, footer)
        text_widget.config(state=tk.DISABLED)

    def update_status(self):
        if self.ignored_filetypes:
            self.status_var.set(f"Ignoring: {', '.join(self.ignored_filetypes)}")
        else:
            self.status_var.set("Showing all file types")

    def generate_file_structure(self, files):
        if not files:
            return "No files selected"
        base_path = os.path.commonpath(files)
        structure = [f"📁 ROOT: {os.path.basename(base_path)}/", 
                    f"📌 Location: {base_path}", "┄"*50]
        stats = {
            'total_files': 0,
            'included_files': len(files),
            'excluded_files': 0,
            'ignored_ext': collections.defaultdict(int),
            'dir_count': 0
        }

        for root, dirs, walk_files in os.walk(base_path):
            # Clean up ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignored_directories]
            
            rel_path = os.path.relpath(root, base_path)
            depth = rel_path.count(os.sep) + 1 if rel_path != '.' else 0
            
            # Add directory entry
            if root != base_path:
                stats['dir_count'] += 1
                dir_name = os.path.basename(root)
                structure.append(f"{'│   '*(depth-1)}└── 📁 {dir_name}/")

            # Process files with visual indicators
            for f in sorted(walk_files):
                full_path = os.path.join(root, f)
                _, ext = os.path.splitext(f)
                
                if ext in self.ignored_filetypes:
                    stats['ignored_ext'][ext] += 1
                    if self.include_ignored_in_structure.get():  # New condition
                        structure.append(f"{'│   '*depth}└── ❌ {f} [IGNORED: {ext}]")
                    continue
                else:
                    stats['total_files'] += 1
                    if full_path in files:
                        structure.append(
                            f"{'│   '*depth}└── ✅ 📄 {f} "
                            f"[Size: {os.path.getsize(full_path):,} bytes]"
                        )
                    else:
                        stats['excluded_files'] += 1
                        structure.append(f"{'│   '*depth}└── ❎ 📄 {f} [EXCLUDED]")

        # Update statistics section
        structure.extend([
            "\n┄"*50,
            "📊 STATISTICS:",
            f"• Total files: {stats['total_files']}",
            f"• Included files: {stats['included_files']}",
            f"• Excluded files: {stats['excluded_files']}",
            f"• Ignored by extension: {sum(stats['ignored_ext'].values())}",
            f"• Directories scanned: {stats['dir_count']}",
            "⚡ Ignored breakdown:" 
        ] + [f"  - {ext}: {count}" for ext, count in stats['ignored_ext'].items()])
        
        return '\n'.join(structure)

    def generate_file_structure_old(self, files):
        if not files:
            return "No files selected"
        base_path = os.path.commonpath(files)
        structure = [f"📁 ROOT: {os.path.basename(base_path)}/", f"📌 Location: {base_path}", "┄"*50]
        stats = {'total_files': 0, 'included_files': len(files), 'ignored_ext': collections.defaultdict(int), 'dir_count': 0}
        dir_map = collections.defaultdict(list)
        for path in files:
            rel_path = os.path.relpath(path, base_path)
            parts = rel_path.split(os.sep)
            for i in range(1, len(parts)):
                dir_path = os.path.join(base_path, *parts[:i])
                dir_map[dir_path].append(os.path.join(*parts[:i+1]))
        for root, dirs, files in os.walk(base_path):
            dirs[:] = [d for d in dirs if d not in self.ignored_directories]
            rel_root = os.path.relpath(root, base_path)
            depth = rel_root.count(os.sep) + 1 if rel_root != '.' else 0
            if root != base_path:
                stats['dir_count'] += 1
                dir_name = os.path.basename(root)
                structure.append(f"{'│   '*(depth-1)}└── 📁 {dir_name}/")
            for f in sorted(files):
                full_path = os.path.join(root, f)
                _, ext = os.path.splitext(f)
                if full_path not in files:
                    stats['ignored_ext'][ext] += 1
                    continue
                line = [f"{'│   '*depth}└── 📄 {f}", f" [Size: {os.path.getsize(full_path):,} bytes]"]
                structure.append(''.join(line))
                stats['total_files'] += 1
        structure.extend(["\n" + "┄"*50, "📊 STATISTICS:", f"• Included files: {stats['included_files']}",
                          f"• Directories scanned: {stats['dir_count']}", f"• Ignored extensions: {sum(stats['ignored_ext'].values())}",
                          "⚡ Ignored breakdown:"] + [f"  - {k}: {v}" for k, v in stats['ignored_ext'].items()])
        return '\n'.join(structure)

    def edit_filetypes(self):
        dialog = FileTypeDialog(self.root, self.ignored_filetypes)
        self.root.wait_window(dialog)
        if dialog.result is not None:
            self.ignored_filetypes = dialog.result
            self.save_preferences()
            if self.root_dir:
                self.build_tree(self.root_dir)
            self.update_status()

    def load_preferences(self):
        try:
            with open("filemerger_prefs.json", "r") as f:
                preferences = json.load(f)
                if "include_ignored_in_structure" in preferences:
                    self.include_ignored_in_structure.set(
                        preferences["include_ignored_in_structure"]
                    )
                self.ignored_filetypes = preferences.get("ignored_filetypes", self.ignored_filetypes)
                self.saved_path_states = preferences.get("selected_paths", {})
                self.default_output_dir = preferences.get("default_output_dir", os.getcwd())
                if "include_line_numbers" in preferences:
                    self.include_line_numbers.set(preferences["include_line_numbers"])
                if "include_structure" in preferences:
                    self.include_structure.set(preferences["include_structure"])
                self.default_output_dir = preferences.get("default_output_dir") or os.getcwd()
                self.root_dir = preferences.get("root_dir") or os.getcwd()
                if not os.path.exists(self.root_dir):
                    self.root_dir = os.getcwd()
        except (FileNotFoundError, json.JSONDecodeError):
            self.root_dir = os.getcwd()
            self.default_output_dir = os.getcwd()
            self.saved_path_states = {}

    def save_preferences(self):
        print("self.root_dir",self.root_dir)
        preferences = {
            "ignored_filetypes": self.ignored_filetypes,
            "include_ignored_in_structure": self.include_ignored_in_structure.get(),
            "include_line_numbers": self.include_line_numbers.get(),
            "include_structure": self.include_structure.get(),
            "root_dir": self.root_dir,
            "default_output_dir": self.default_output_dir,
            "selected_paths": {self.tree.item(item_id, "tags")[1]: state for item_id, state in self.check_states.items()
                               if state and self.tree.exists(item_id) and len(self.tree.item(item_id, "tags")) >= 2}
        }
        with open("filemerger_prefs.json", "w") as f:
            json.dump(preferences, f, indent=2)

    def restore_selections(self):
        if not hasattr(self, 'saved_path_states'):
            return
        def process_item(item_id):
            tags = self.tree.item(item_id, "tags")
            if len(tags) >= 2 and tags[1] in self.saved_path_states and self.saved_path_states[tags[1]]:
                self.check_states[item_id] = True
                self.tree.item(item_id, values=("☑"))
            for child_id in self.tree.get_children(item_id):
                process_item(child_id)
        for root_item in self.tree.get_children(""):
            process_item(root_item)
        for item_id in self.check_states:
            if self.check_states[item_id]:
                self.update_parents(item_id)

    def select_root(self):
        folder = filedialog.askdirectory(initialdir=self.default_output_dir)
        if folder:
            self.root_dir = folder
            self.build_tree(folder)

    def build_tree(self, path):
        self.tree.delete(*self.tree.get_children())
        self.check_states.clear()
        root_id = self.add_node("", os.path.basename(path), path, "folder")
        self.process_directory(path, root_id, initial=True)
        self.restore_selections()

    def add_node(self, parent, text, full_path, node_type):
        count = len(self.tree.get_children(parent))
        tag = 'oddrow' if count % 2 == 0 else 'evenrow'
        node_id = self.tree.insert(
            parent, "end",
            text=text,
            values=("☐"),
            tags=(node_type, full_path, tag)
        )
        self.check_states[node_id] = False

        state = self.saved_path_states.get(full_path, False)
        self.check_states[node_id] = state
        self.tree.item(node_id, values=("☑" if state else "☐"))

        if node_type == "folder":
            self.tree.insert(node_id, "end", text="Loading...")
        return node_id

    def process_directory(self, path, parent_id, initial=False):
        try:
            entries = sorted(os.listdir(path), key=lambda x: x.lower())
            for entry in entries:
                full_path = os.path.join(path, entry)
                # Only process valid directories
                if os.path.isdir(full_path) and entry not in self.ignored_directories:
                    self.add_node(parent_id, entry, full_path, "folder")
                # Process files if they are not ignored
                elif os.path.isfile(full_path):
                    _, ext = os.path.splitext(entry.lower())
                    if ext not in self.ignored_filetypes:
                        self.add_node(parent_id, entry, full_path, "file")
        except PermissionError:
            pass

    def on_tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell" or self.tree.identify_column(event.x) != "#1":
            return
        item = self.tree.identify_row(event.y)
        current_state = self.check_states.get(item, False)
        new_state = not current_state
        self.check_states[item] = new_state
        self.tree.item(item, values=("☑" if new_state else "☐"))
        if self.tree.item(item, "tags")[0] == "folder":
            self.toggle_children(item, new_state)
        self.update_parents(item)
        self.save_preferences()

    def toggle_children(self, parent, state):
        children = list(self.tree.get_children(parent))  # Create static list
        
        for child in children:
            # Skip non-existent items (may have been deleted)
            if not self.tree.exists(child):
                continue
                
            # Handle "Loading..." placeholder
            if self.tree.item(child, "text") == "Loading...":
                self.tree.delete(child)
                continue
                
            # Process actual children
            try:
                full_path = self.tree.item(child, "tags")[1]
                if os.path.isdir(full_path):
                    # Load children if not already loaded
                    if not self.tree.get_children(child):
                        self.process_directory(full_path, child)
                    self.toggle_children(child, state)
                    
                self.check_states[child] = state
                self.tree.item(child, values=("☑" if state else "☐"))
            except Exception as e:
                logging.error(f"Error toggling {child}: {str(e)}")
                continue


    def update_parents(self, child):
        parent = self.tree.parent(child)
        if not parent:
            return
        children = self.tree.get_children(parent)
        states = [self.check_states[c] for c in children if self.tree.item(c, "text") != "Loading..."]
        for index, child_item in enumerate(children):
            tag = 'oddrow' if index % 2 == 0 else 'evenrow'
            current_tags = list(self.tree.item(child_item)['tags'])
            if 'oddrow' in current_tags:
                current_tags.remove('oddrow')
            if 'evenrow' in current_tags:
                current_tags.remove('evenrow')
            current_tags.append(tag)
            self.tree.item(child_item, tags=current_tags)
        if not states:
            return
        if all(states):
            new_state = True
        elif any(states):
            new_state = "mixed"
        else:
            new_state = False
        current_parent_state = self.check_states[parent]
        if new_state != current_parent_state and new_state != "mixed":
            self.check_states[parent] = new_state
            self.tree.item(parent, values=("☑" if new_state else "☐"))
            self.update_parents(parent)
        elif new_state == "mixed":
            self.tree.item(parent, values=("☒"))

    def get_selected_files(self):
        return [self.tree.item(item, "tags")[1] for item in self.check_states
                if self.check_states[item] and "file" in self.tree.item(item, "tags") and not self.tree.get_children(item)]

    def write_content(self, file_path, outfile):
        """Helper method to handle file content writing"""
        BUFFER_SIZE = 4096  # 4KB chunks for memory efficiency
        
        def handle_encoding(file_path):
            """Attempt different encodings with fallback"""
            encodings = ['utf-8', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as test_file:
                        test_file.read(1024)
                        return encoding
                except UnicodeDecodeError:
                    continue
            return 'latin-1'  # Final fallback
        
        encoding = handle_encoding(file_path)
        
        try:
            with open(file_path, 'r', encoding=encoding) as infile:
                if self.include_line_numbers.get():
                    buffer = []
                    for line_num, line in enumerate(infile, 1):
                        buffered_line = f"{line_num:04d}| {line}"
                        buffer.append(buffered_line)
                        # Write in chunks to handle large files
                        if len(buffer) >= 100:
                            outfile.write(''.join(buffer))
                            buffer = []
                    # Write remaining lines
                    if buffer:
                        outfile.write(''.join(buffer))
                else:
                    while True:
                        chunk = infile.read(BUFFER_SIZE)
                        if not chunk:
                            break
                        outfile.write(chunk)
        except Exception as e:
            error_msg = f"Error reading {file_path}: {str(e)}"
            logging.error(error_msg)
            outfile.write(f"\n{error_msg}\n")

    def format_line_numbers(self, text):
        """Format text with line numbers if enabled"""
        if self.include_line_numbers.get():
            return '\n'.join(
                f"{idx:04d}| {line}" 
                for idx, line in enumerate(text.split('\n'), 1)
            )
        return text

    def merge_files(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("No Selection", "No files selected")
            return

        output_file = filedialog.asksaveasfilename(
            initialdir=self.default_output_dir,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")]
        )
        
        if output_file:
            try:
                # Add progress callback for UI updates
                def progress_callback(current, total):
                    self.status_var.set(f"Merging {current}/{total} files...")
                    self.root.update_idletasks()
                
                self._perform_merge(files, output_file, progress_callback)
                messagebox.showinfo("Success", 
                    f"Merged {len(files)} files successfully!\nSaved to: {output_file}")
            except PermissionError as e:
                logging.error(f"Permission denied: {str(e)}")
                messagebox.showerror("Permission Error", 
                    f"Cannot write to {output_file}:\n{str(e)}")
            except Exception as e:
                logging.error(f"Merge failed: {traceback.format_exc()}")
                messagebox.showerror("Merge Error", 
                    f"Critical error during merge:\n{str(e)}")
            finally:
                self.status_var.set("Ready")

    def _perform_merge(self, files, output_path, progress_callback=None):
        """Core merge functionality with enhanced features"""
        merge_metadata = {
            'start_time': datetime.datetime.now().isoformat(),
            'file_count': len(files),
            'total_size': sum(os.path.getsize(f) for f in files)
        }
        
        try:
            with open(output_path, "w", encoding="utf-8") as outfile:
                # Write merge header with metadata
                outfile.write(f"FILE MERGE REPORT\n{'='*40}\n")
                outfile.write(f"• Generated: {merge_metadata['start_time']}\n")
                outfile.write(f"• Total files: {merge_metadata['file_count']}\n")
                outfile.write(f"• Total size: {merge_metadata['total_size']:,} bytes\n")
                outfile.write('='*40 + '\n\n')

                if self.include_structure.get():
                    structure = self.generate_file_structure(files)
                    outfile.write(f"FILE STRUCTURE OVERVIEW\n{'='*40}\n")
                    outfile.write(structure)
                    outfile.write("\n\n" + "="*40 + "\n\n")

                for idx, file_path in enumerate(files, 1):
                    if progress_callback:
                        progress_callback(idx, len(files))
                    
                    try:
                        file_stats = os.stat(file_path)
                        header = [
                            f"{'#'*40}",
                            f"### FILE {idx}/{len(files)}: {os.path.basename(file_path)}",
                            f"• Path: {file_path}",
                            f"• Size: {file_stats.st_size:,} bytes",
                            f"• Modified: {datetime.datetime.fromtimestamp(file_stats.st_mtime).isoformat()}",
                            f"{'#'*40}\n\n"
                        ]
                        outfile.write('\n'.join(header))
                        
                        # Enhanced content writing with buffer
                        self.write_content(file_path, outfile)
                        
                        outfile.write(f"\n{'#'*40}\n### END OF FILE\n{'#'*40}\n\n")
                    except Exception as e:
                        logging.error(f"Failed to process {file_path}: {str(e)}")
                        outfile.write(f"\n[ERROR PROCESSING FILE: {str(e)}]\n")
                        continue

        except IOError as e:
            logging.error(f"File system error: {str(e)}")
            raise RuntimeError(f"Could not write to output file: {str(e)}")

    def auto_save_merge(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("No Selection", "No files selected")
            return
        
        # Ensure output directory exists
        output_dir = self.default_output_dir
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("Path Error", 
                    f"Cannot create output directory:\n{str(e)}")
                return
        
        output_file = os.path.join(output_dir, f"code_export.txt")
        
        # Reuse existing merge logic
        try:
            self._perform_merge(files, output_file)
            messagebox.showinfo("Success", 
                f"Auto-saved merge to:\n{output_file}")
        except Exception as e:
            messagebox.showerror("Merge Error", 
                f"Failed to create output file:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = FileMergerApp(root)
    root.mainloop()
