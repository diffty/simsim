import os
import shutil
import markdown2


def generate_page(page, output_path):
    header = '''
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="utf-8">
            <link rel="stylesheet" href="css/pygments/monokai.css">
        </head>
        <body>
    '''

    footer = '''
        </body>
    </html>
    '''

    tree_html = generate_reverse_tree(page, curr_page=page, sublevels_to_show=2, with_links=True)
    page_html = page.generate_page()

    fp = open(output_path + "/" + page.get_html_filename(), "wb")
    fp.write(header.encode("utf8"))
    fp.write("<p><pre>".encode("utf8"))
    fp.write(tree_html.encode("utf8"))
    fp.write("</pre><p>".encode("utf8"))
    fp.write(page_html.encode("utf8"))
    fp.write(footer.encode("utf8"))
    fp.close()


def generate_child_entry(curr_obj, curr_page=None, lvl=0, with_links=False):
    line_str = "    " * lvl + "└─ "

    if with_links:
        line_str = line_str + '<a href="' + curr_obj.get_html_filename() + '">' + curr_obj.name + "</a>"
    else:
        line_str = line_str + curr_obj.name
    
    if curr_obj == curr_page:
        line_str += " <"
    
    return line_str


def generate_tree(curr_obj, curr_page=None, lvl=0, breadcrumb=None, sublevels_to_show=0, with_links=False):
    if breadcrumb is None:
        breadcrumb = []    

    tree_str = ""
    
    if sublevels_to_show <= 0 and curr_obj not in breadcrumb and curr_page != curr_obj:
        return tree_str
    
    if type(curr_obj) == Page:
        return tree_str
    
    for child_obj in curr_obj.children:
        line_str = generate_child_entry(child_obj, curr_page, lvl, with_links)
        tree_str += line_str + "\n"

        if type(child_obj) is Folder:
            leaf_str = generate_tree(child_obj, curr_page, lvl+1, breadcrumb[1:], sublevels_to_show-1, with_links)
            tree_str += leaf_str
    
    return tree_str


def generate_reverse_tree(curr_obj, curr_page=None, sublevels_to_show=0, with_links=False):
    breadcrumb = []
    nb_level = 0
    curr_parent = curr_obj.parent

    while curr_parent:
        breadcrumb.insert(0, curr_parent)
        curr_parent = curr_parent.parent
        nb_level += 1
    
    root = breadcrumb[0]
    
    tree_html = generate_tree(root, curr_page, 0, breadcrumb, sublevels_to_show, with_links)

    return tree_html


def copy_medias(medias_path):
    shutil.copytree(medias_path, "./html/media")


class Folder:
    def __init__(self, path, parent_folder=None):
        self.path = path
        self.name = os.path.basename(os.path.splitext(self.path)[0])
        self.children = []
        self.parent = None
        self.level = -1

        if parent_folder:
            self.set_parent(parent_folder)
    
    def add_child(self, child):
        if child not in self.children:
            self.children.append(child)

    def get_html_filename(self):
        return self.name + "-Index.html"
    
    def generate_tree(self, with_links=False):
        return generate_tree(self, with_links=with_links)
    
    def generate_page(self):
        index_md_filepath = self.path + "/" + "index.md"
        if os.path.exists(index_md_filepath):
            fp = open(index_md_filepath, "rb")
            file_content = fp.read().decode("utf8")
            fp.close()
            return markdown2.markdown(file_content, extras=["fenced-code-blocks"])
        else:
            return "WIP"
        
    def set_parent(self, new_parent):
        self.parent = new_parent
        self.parent.add_child(self)
    
    def __repr__(self):
        return "<Folder: %s (%s)>" % (self.name, self.path)


class Page:
    def __init__(self, path, parent_folder=None):
        self.path = path
        self.name = os.path.basename(os.path.splitext(self.path)[0])
        self.parent = None
        self.level = -1

        if parent_folder:
            self.set_parent(parent_folder)
    
    def get_html_filename(self):
        return self.name + ".html"
    
    def generate_page(self):
        fp = open(self.path, "rb")
        file_content = fp.read().decode("utf8")
        fp.close()
        return markdown2.markdown(file_content, extras=["fenced-code-blocks"])

    def set_parent(self, new_parent):
        self.parent = new_parent
        self.parent.add_child(self)

    def __repr__(self):
        return "<Page: %s (%s)>" % (self.name, self.path)


def discover_docs(docs_root, curr_dir=None, curr_lvl=0):
    if curr_dir is None:
        curr_dir = docs_root

    curr_folder = Folder(curr_dir)

    for filename in os.listdir(curr_dir):
        full_path = curr_dir + "/" + filename

        if os.path.isdir(full_path):
            child_folder = discover_docs(
                docs_root,
                curr_dir=curr_dir + "/" + filename,
                curr_lvl=curr_lvl+1)

            child_folder.level = curr_lvl
            child_folder.set_parent(curr_folder)

        if os.path.splitext(filename)[1].lower() == ".md":
            new_page = Page(full_path)
            new_page.level = curr_lvl
            new_page.set_parent(curr_folder)

    return curr_folder

def get_all_pages(page, include_folders=False):
    pages = []

    for c in page.children:
        if type(c) is Folder:
            pages.extend(get_all_pages(c, include_folders))

            if include_folders:
                pages.append(c)

        elif type(c) is Page:
            pages.append(c)

    return pages


root_folder = discover_docs("docs/")
all_pages = get_all_pages(root_folder, include_folders=True)

for p in all_pages:
    generate_page(p, "html/")
    copy_medias("Notes/media")
