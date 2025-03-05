import os
import tkinter as tk
import json
import datetime
from tkinter import ttk, filedialog, messagebox, simpledialog
import collections

class FileTypeDialog(tk.Toplevel):
    def __init__(self, parent, ignored_types):
        super().__init__(parent)
        self.title("File Merger with Tree Select")
        self.geometry("800x600")
        self.result = None
        self.ignored_types = list(ignored_types)
        self.ignored_filetypes = [".scml", ".pyc", ".pyo", ".pyd"]
        self.ignored_directories = ["__pycache__", ".git", ".vscode"]

        self.load_preferences()
        
        # Main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Instructions
        ttk.Label(main_frame, text="Manage file types to ignore:").pack(anchor=tk.W)
        
        # Current types frame
        types_frame = ttk.LabelFrame(main_frame, text="Ignored Extensions")
        types_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Listbox with scrollbar
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

    def load_preferences(self):
        try:
            with open("filemerger_prefs.json", "r") as f:
                preferences = json.load(f)
                # Only load ignored_filetypes from preferences
                saved_types = preferences.get("ignored_filetypes", [])
                # Update the ignored_types list if needed
                if saved_types:
                    self.ignored_types = list(saved_types)
        except (FileNotFoundError, json.JSONDecodeError):
            # Use defaults if file doesn't exist or is invalid
            pass  # The ignored_types list is already initialized in __init__
    
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

        # State variables (MUST come before other dependencies)
        self.include_line_numbers = tk.BooleanVar(value=False)
        self.ignored_filetypes = [".scml", ".pyc", ".pyo", ".pyd"]
        self.ignored_directories = ["__pycache__", ".git", ".vscode"]
        self.include_structure = tk.BooleanVar(value=True)
        self.check_states = {}

        # Create menu bar FIRST
        self.menu_bar = tk.Menu(root)
        self.root.config(menu=self.menu_bar)

        # Build menus
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Select Root Folder", command=self.select_root)
        self.file_menu.add_command(label="Merge Files", command=self.merge_files)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=root.quit)

        self.pref_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Preferences", menu=self.pref_menu)
        self.pref_menu.add_command(label="File Type Filters", command=self.edit_filetypes)
        self.pref_menu.add_checkbutton(label="Include File Structure",
                                      variable=self.include_structure,
                                      command=self.save_preferences)
        self.pref_menu.add_checkbutton(label="Include Line Numbers",
                              variable=self.include_line_numbers,
                              command=self.save_preferences)



        # Main container (Treeview)
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

                # FIXED FOR BUTTON VISIBILITY: Button panel FIRST
        self.btn_frame = ttk.Frame(root)
        self.btn_frame.pack(fill=tk.X, pady=5, before=self.main_frame)  # Critical position fix


        ttk.Button(self.btn_frame, 
                 text="Select Root Folder", 
                 command=self.select_root).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.btn_frame, 
                 text="Merge Files", 
                 command=self.merge_files).pack(side=tk.LEFT, padx=5)
        
        # Treeview with checkboxes
        self.tree = ttk.Treeview(self.main_frame, columns=("check"), selectmode="none")
        self.tree.heading("#0", text="File Structure", anchor=tk.W)
        self.tree.heading("check", text="Include")
        self.tree.column("check", width=60, anchor="center")
        self.tree.tag_configure('oddrow', background='lightgray')
        self.tree.tag_configure('evenrow', background='white')
        
        # Scrollbar
        self.scroll = ttk.Scrollbar(self.main_frame, 
                                orient="vertical", 
                                command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scroll.set)
        
        # 3. PACKING ORDER
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, 
                                textvariable=self.status_var, 
                                relief=tk.SUNKEN, 
                                anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # After creating and configuring self.tree
        self.tree.bind("<Button-1>", self.on_tree_click)

        # 4. FINAL INITIALIZATION
        self.load_preferences()
        self.update_status()
        self.root_dir = os.getcwd()  # Set after loading prefs
        self.build_tree(self.root_dir)

    
    def update_status(self):
        if self.ignored_filetypes:
            self.status_var.set(f"Ignoring: {', '.join(self.ignored_filetypes)}")
        else:
            self.status_var.set("Showing all file types")

    def generate_file_structure(self, files):
        """Generate visual directory structure with metadata
        
        Features:
        - Colored emoji indicators
        - File count statistics
        - Ignored file tracking
        - Size visualization
        - Nested hierarchy
        """
        if not files:
            return "No files selected"
            
        base_path = os.path.commonpath(files)
        structure = [
            f"📁 ROOT: {os.path.basename(base_path)}/",
            f"📌 Location: {base_path}",
            "┄"*50
        ]
        
        # Tracking stats
        stats = {
            'total_files': 0,
            'included_files': len(files),
            'ignored_ext': collections.defaultdict(int),
            'dir_count': 0
        }
        
        # Build directory map
        dir_map = collections.defaultdict(list)
        for path in files:
            rel_path = os.path.relpath(path, base_path)
            parts = rel_path.split(os.sep)
            for i in range(1, len(parts)):
                dir_path = os.path.join(base_path, *parts[:i])
                dir_map[dir_path].append(os.path.join(*parts[:i+1]))
        
        # Walk through directory structure
        for root, dirs, files in os.walk(base_path):
            # Filter ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignored_directories]
            
            # Calculate depth
            rel_root = os.path.relpath(root, base_path)
            depth = rel_root.count(os.sep) + 1 if rel_root != '.' else 0
            
            # Header for directory
            if root != base_path:
                stats['dir_count'] += 1
                dir_name = os.path.basename(root)
                structure.append(f"{'│   '*(depth-1)}└── 📁 {dir_name}/")
            
            # Process files

            for f in sorted(files):
                full_path = os.path.join(root, f)
                _, ext = os.path.splitext(f)
                
                if full_path not in files:
                    stats['ignored_ext'][ext] += 1
                    continue
                    
                # File entry
                line = [
                    f"{'│   '*depth}└── 📄 {f}",
                    f" [Size: {os.path.getsize(full_path):,} bytes]"
                ]
                structure.append(''.join(line))
                stats['total_files'] += 1
        
        # Add summary section
        structure.extend([
            "\n" + "┄"*50,
            "📊 STATISTICS:",
            f"• Included files: {stats['included_files']}",
            f"• Directories scanned: {stats['dir_count']}",
            f"• Ignored extensions: {sum(stats['ignored_ext'].values())}",
            "⚡ Ignored breakdown:"
        ] + [f"  - {k}: {v}" for k,v in stats['ignored_ext'].items()])
        
        return '\n'.join(structure)



    def edit_filetypes(self):
        dialog = FileTypeDialog(self.root, self.ignored_filetypes)
        self.root.wait_window(dialog)
        
        if dialog.result is not None:
            self.ignored_filetypes = dialog.result
            self.save_preferences()
            # Rebuild the tree with new filters
            if self.root_dir:
                self.build_tree(self.root_dir)
            self.update_status()
    
    def load_preferences(self):
        try:
            with open("filemerger_prefs.json", "r") as f:
                preferences = json.load(f)
                self.ignored_filetypes = preferences.get("ignored_filetypes", [])
                self.saved_path_states = preferences.get("selected_paths", {})
                saved_root = preferences.get("root_dir")
                if saved_prefs := preferences.get("include_line_numbers"):
                    self.include_line_numbers.set(saved_prefs)
                if saved_root and os.path.exists(saved_root):
                    self.root_dir = saved_root
        except (FileNotFoundError, json.JSONDecodeError):
            # Use defaults if file doesn't exist or is invalid
            self.saved_path_states = {}

    def save_preferences(self):
        try:
            # Load existing preferences to preserve other settings
            preferences = {}
            try:
                with open("filemerger_prefs.json", "r") as f:
                    preferences = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass

            # Update critical settings
            preferences.update({
                "ignored_filetypes": self.ignored_filetypes,
                "include_line_numbers": self.include_line_numbers.get(),
                "include_structure": self.include_structure.get(),
                "root_dir": self.root_dir,
                "version": 2.0  # Add version for future compatibility
            })

            # Save selected paths state
            selected_paths = {}
            for item_id, state in self.check_states.items():
                if state and self.tree.exists(item_id):
                    item_tags = self.tree.item(item_id, "tags")
                    if len(item_tags) >= 2:
                        path = item_tags[1]
                        selected_paths[path] = state
            preferences["selected_paths"] = selected_paths

            # Atomic write operation
            with open("filemerger_prefs.json", "w") as f:
                json.dump(preferences, f, indent=2)

        except Exception as e:
            print(f"Preferences save failed: {str(e)}")
            messagebox.showerror("Save Error", 
                f"Failed to save preferences:\n{str(e)}")


    def restore_selections(self):
        if not hasattr(self, 'saved_path_states'):
            return
            
        # Process all tree items to restore their selection state
        def process_item(item_id):
            tags = self.tree.item(item_id, "tags")
            if len(tags) >= 2:
                path = tags[1]
                if path in self.saved_path_states and self.saved_path_states[path]:
                    self.check_states[item_id] = True
                    self.tree.item(item_id, values=("☑"))
                    
            # Process children recursively
            for child_id in self.tree.get_children(item_id):
                process_item(child_id)
                
        # Start processing from root items
        for root_item in self.tree.get_children(""):
            process_item(root_item)
            
        # Update parent states
        for item_id in self.check_states:
            if self.check_states[item_id]:
                self.update_parents(item_id)
            
    def select_root(self):
        folder = filedialog.askdirectory(initialdir=os.getcwd())  # Set initial directory
        if folder:
            self.root_dir = folder
            self.build_tree(folder)
            
    def build_tree(self, path):
        self.tree.delete(*self.tree.get_children())
        self.check_states.clear()
        
        root_id = self.add_node("", os.path.basename(path), path, "folder")
        self.process_directory(path, root_id)
        
        # Restore saved selections
        self.restore_selections()
        
    def add_node(self, parent, text, full_path, node_type):
        count = len(self.tree.get_children(parent))  # Count children of parent
        tag = 'oddrow' if count % 2 == 0 else 'evenrow'  # Alternate tags
        
        node_id = self.tree.insert(
            parent, "end", 
            text=text,
            values=("☐"),
            tags=(node_type, full_path, tag)  # Apply tag for coloring
        )
        self.check_states[node_id] = False
        return node_id
        
    def process_directory(self, path, parent_id):
        try:
            entries = sorted(os.listdir(path), key=lambda x: x.lower())
            
            for entry in entries:
                full_path = os.path.join(path, entry)
                
                # Skip directories in the ignore list
                if os.path.isdir(full_path) and entry in self.ignored_directories:
                    continue
                    
                if os.path.isdir(full_path):
                    node_id = self.add_node(parent_id, entry, full_path, "folder")
                    self.process_directory(full_path, node_id)
                else:
                    # Skip files with ignored extensions
                    _, ext = os.path.splitext(entry.lower())
                    if ext not in self.ignored_filetypes:
                        self.add_node(parent_id, entry, full_path, "file")
                    
        except PermissionError:
            pass
            
    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            item_type = self.tree.item(item, "tags")[0]
            if item_type == "file":
                # Get file extension
                file_path = self.tree.item(item, "tags")[1]
                _, ext = os.path.splitext(file_path.lower())
                
                # Clear previous menu
                self.context_menu.delete(0, tk.END)
                
                # Add options based on file type
                self.context_menu.add_command(label=f"Ignore {ext} files", 
                                            command=lambda e=ext: self.ignore_extension(e))
                self.context_menu.add_command(label="Show file details", 
                                            command=lambda p=file_path: self.show_file_details(p))
                
                # Display the menu
                self.context_menu.post(event.x_root, event.y_root)

    def ignore_extension(self, extension):
        if extension not in self.ignored_filetypes:
            self.ignored_filetypes.append(extension)
            self.save_preferences()
            if self.root_dir:
                self.build_tree(self.root_dir)
            self.update_status()
            messagebox.showinfo("Filter Applied", f"Files with extension {extension} will now be hidden")

    def show_file_details(self, path):
        # Show file details in a dialog
        size = os.path.getsize(path)
        modified = os.path.getmtime(path)
        modified_date = datetime.datetime.fromtimestamp(modified).strftime('%Y-%m-%d %H:%M:%S')
        
        details = f"Path: {path}\n"
        details += f"Size: {size:,} bytes\n"
        details += f"Modified: {modified_date}"
        
        messagebox.showinfo("File Details", details)
            
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
        for child in self.tree.get_children(parent):
            self.check_states[child] = state
            self.tree.item(child, values=("☑" if state else "☐"))
            if self.tree.item(child, "tags")[0] == "folder":
                self.toggle_children(child, state)
                
    def update_parents(self, child):
        parent = self.tree.parent(child)
        if not parent:
            return
            
        children = self.tree.get_children(parent)
        states = [self.check_states[c] for c in children]
        
        # Reapply alternating colors
        for index, child_item in enumerate(children):
            tag = 'oddrow' if index % 2 == 0 else 'evenrow'
            current_tags = list(self.tree.item(child_item)['tags'])
            
            if 'oddrow' in current_tags:
                current_tags.remove('oddrow')
            if 'evenrow' in current_tags:
                current_tags.remove('evenrow')
                
            current_tags.append(tag)
            self.tree.item(child_item, tags=current_tags)
        
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
        selected = []
        for item in self.check_states:
            if (self.check_states[item] and 
                "file" in self.tree.item(item, "tags") and
                not self.tree.get_children(item)):
                selected.append(self.tree.item(item, "tags")[1])
        return selected
        
    def merge_files(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("No Selection", "No files selected")
            return
            
        output_file = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")]
        )
        
        if not output_file:
            return
            
        try:
            with open(output_file, "w", encoding="utf-8") as outfile:
                if self.include_structure.get():
                    structure = self.generate_file_structure(files)
                    outfile.write(f"FILE STRUCTURE OVERVIEW\n{'='*40}\n")
                    outfile.write(structure)
                    outfile.write("\n\n" + "="*40 + "\n\n")
                total = len(files)
                
                for idx, file_path in enumerate(files, 1):
                    header = f"\n{'#' * 40}\n### {idx}/{total}: {os.path.basename(file_path)}\n{'#' * 40}\n\n"
                    outfile.write(header)
                    
                    try:
                        with open(file_path, "r", encoding="utf-8") as infile:
                            if self.include_line_numbers.get():
                                for line_num, line in enumerate(infile, 1):
                                    outfile.write(f"{line_num:04d}| {line}")
                            else:
                                outfile.write(infile.read())
                    except UnicodeDecodeError:
                        with open(file_path, "r", encoding="latin-1") as infile:
                            if self.include_line_numbers.get():
                                for line_num, line in enumerate(infile, 1):
                                    outfile.write(f"{line_num:04d}| {line}")
                            else:
                                outfile.write(infile.read())
                    except Exception as e:
                        messagebox.showerror("Read Error", f"Error reading {file_path}:\n{str(e)}")
                        continue
                        
                    footer = f"\n{'#' * 40}\n### END: {os.path.basename(file_path)}\n{'#' * 40}\n\n"
                    outfile.write(footer)
                    
            messagebox.showinfo("Success", f"Merged {len(files)} files successfully!")
        except Exception as e:
            messagebox.showerror("Merge Error", f"Failed to create output file:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileMergerApp(root)
    root.mainloop()
